"""Single-node durable gateway for one explicitly invited external agent."""
from contextlib import contextmanager
import hashlib
import json
import secrets
import sqlite3
import time

from src.matrix_as import AGENT
from src.matrix_http import MatrixError, segment


class Gateway:
    def __init__(self, path, agent):
        self.path, self.agent = str(path), agent
        with self.db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS transactions (id TEXT PRIMARY KEY);
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY, event TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
                    lease TEXT, until REAL DEFAULT 0, result TEXT, reply TEXT);
            ''')

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def allowed(self, room):
        path = '/rooms/' + segment(room)
        try:
            self.agent.api('GET', path + '/state/m.room.encryption')
            return False
        except MatrixError as error:
            if error.status != 404 or error.body.get('errcode') != 'M_NOT_FOUND':
                raise
        return self.agent.api('GET', path + '/state/m.room.member/' + segment(AGENT)).get('membership') == 'join'

    def accept(self, txn, events):
        with self.db() as db:
            if db.execute('SELECT 1 FROM transactions WHERE id=?', (txn,)).fetchone():
                return
        candidates = []
        for event in events:
            content = event.get('content', {})
            if (event.get('type') != 'm.room.message' or 'state_key' in event or
                event.get('sender', '').startswith('@_didadi_') or
                content.get('msgtype') != 'm.text' or
                AGENT not in content.get('m.mentions', {}).get('user_ids', []) or
                not isinstance(content.get('body'), str) or
                not event.get('room_id') or not event.get('event_id')):
                continue
            if self.allowed(event['room_id']):
                candidates.append(event)
        # Commit both transaction and task before ACK; uniqueness also handles concurrent callbacks.
        with self.db() as db:
            for event in candidates:
                db.execute('INSERT OR IGNORE INTO tasks(id,event) VALUES (?,?)',
                           (event['event_id'], json.dumps(event)))
            db.execute('INSERT OR IGNORE INTO transactions VALUES (?)', (txn,))

    def claim(self):
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute("SELECT * FROM tasks WHERE status != 'done' AND until < ? ORDER BY rowid LIMIT 1",
                             (time.time(),)).fetchone()
            if row is None:
                return None
            lease = secrets.token_hex(24)
            db.execute('UPDATE tasks SET lease=?, until=? WHERE id=?', (lease, time.time() + 60, row['id']))
            return {'id': row['id'], 'event': json.loads(row['event']), 'lease': lease,
                    'result': row['result'], 'agent': AGENT}

    def complete(self, task_id, lease, result):
        if not isinstance(result, str) or not 0 < len(result) <= 16000:
            raise ValueError('result must contain 1..16000 characters')
        # Serialize completion against lease replacement. Persist the first result before outbound I/O.
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM tasks WHERE id=?', (task_id,)).fetchone()
            if row is None or not secrets.compare_digest(row['lease'] or '', lease):
                raise ValueError('invalid lease')
            if row['status'] == 'done':
                return {'event_id': row['reply']}
            if row['until'] < time.time():
                raise ValueError('expired lease')
            if row['result'] is not None and row['result'] != result:
                raise ValueError('result already fixed')
            db.execute('UPDATE tasks SET result=? WHERE id=?', (result, task_id))
        event = json.loads(row['event'])
        if not self.allowed(event['room_id']):
            raise ValueError('room no longer authorized or unencrypted')
        relation = event['content'].get('m.relates_to', {})
        root = relation.get('event_id') if relation.get('rel_type') == 'm.thread' else event['event_id']
        txn = hashlib.sha256(('task:' + task_id).encode()).hexdigest()
        reply = self.agent.api('PUT', '/rooms/' + segment(event['room_id']) + '/send/m.room.message/' + txn, {
            'msgtype': 'm.text', 'body': result,
            'm.relates_to': {'rel_type': 'm.thread', 'event_id': root,
                             'm.in_reply_to': {'event_id': event['event_id']}},
            'org.didadi.task': {'id': task_id}})
        with self.db() as db:
            db.execute("UPDATE tasks SET status='done',reply=? WHERE id=?", (reply['event_id'], task_id))
        return reply
