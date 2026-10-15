"""Phase 0 synchronous echo agent, not a durable task gateway."""
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading
from urllib.parse import parse_qs, urlsplit

from src.matrix_http import MatrixError, request, segment

AGENT = '@_didadi_agent_echo:didadi.localhost'
PREFIX = '/_matrix/client/v3'


class EchoAgent:
    def __init__(self, base, token):
        self.base, self.token = base, token
        self.lock = threading.Lock()

    def api(self, method, path, data=None):
        return request(self.base, method, PREFIX + path, self.token, data,
                       {'user_id': AGENT})

    def process(self, events):
        # Serialize retries. No task queue or durable transaction ledger in Phase 0.
        with self.lock:
            for event in events:
                room = event.get('room_id')
                if not room:
                    continue
                path = '/rooms/' + segment(room)
                content = event.get('content', {})
                if (event.get('type') == 'm.room.member' and
                    event.get('state_key') == AGENT and content.get('membership') == 'invite'):
                    self.api('POST', path + '/join', {})
                    continue
                if (event.get('type') != 'm.room.message' or 'state_key' in event or
                    event.get('sender', '').startswith('@_didadi_') or
                    content.get('msgtype') != 'm.text' or
                    not content.get('body', '').startswith('!echo ')):
                    continue
                # Fail closed: only confirmed unencrypted rooms with this agent joined.
                try:
                    self.api('GET', path + '/state/m.room.encryption')
                    continue
                except MatrixError as error:
                    if error.status != 404 or error.body.get('errcode') != 'M_NOT_FOUND':
                        raise
                membership = self.api('GET', path + '/state/m.room.member/' + segment(AGENT))
                if membership.get('membership') != 'join':
                    continue
                txn = hashlib.sha256(event['event_id'].encode()).hexdigest()
                self.api('PUT', path + '/send/m.room.message/' + txn, {
                    'msgtype': 'm.text', 'body': 'Echo: ' + content['body'][6:],
                    'm.relates_to': {'m.in_reply_to': {'event_id': event['event_id']}}})
                print('agent_reply source_event=' + event['event_id'], flush=True)


def make_handler(agent, hs_token, gateway=None, agent_token=None):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Never log bearer tokens, query strings or message contents.

        def respond(self, status, body):
            payload = json.dumps(body).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            if self.path == '/agent/tasks':
                if not self.agent_auth():
                    return
                self.respond(200, {'task': gateway.claim()})
            elif urlsplit(self.path).path == '/agent/status':
                if not self.agent_auth():
                    return
                task_id = parse_qs(urlsplit(self.path).query).get('id', [''])[0]
                self.respond(200, {'task': gateway.status(task_id)})
            elif self.path == '/health':
                self.respond(200, {'status': 'ok'})
            else:
                self.respond(404, {'errcode': 'M_UNRECOGNIZED'})

        def agent_auth(self):
            if (gateway is None or not agent_token or not hmac.compare_digest(
                    self.headers.get('Authorization', ''), 'Bearer ' + agent_token)):
                self.respond(403, {'errcode': 'M_FORBIDDEN'})
                return False
            return True

        def do_POST(self):
            if self.path != '/agent/complete':
                self.respond(404, {})
                return
            if not self.agent_auth():
                return
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 65536:
                    raise ValueError('invalid body size')
                data = json.loads(self.rfile.read(size))
                reply = gateway.complete(data['id'], data['lease'], data['result'])
                self.respond(200, reply)
            except (ValueError, KeyError, TypeError):
                self.respond(400, {'error': 'invalid completion or room access'})
            except Exception:
                self.respond(503, {'error': 'retry completion'})

        def do_PUT(self):
            if not hmac.compare_digest(self.headers.get('Authorization', ''), 'Bearer ' + hs_token):
                self.respond(403, {'errcode': 'M_FORBIDDEN'})
                return
            if not urlsplit(self.path).path.startswith('/_matrix/app/v1/transactions/'):
                self.respond(404, {'errcode': 'M_UNRECOGNIZED'})
                return
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 1_048_576:
                    raise ValueError('invalid body size')
                data = json.loads(self.rfile.read(size))
                events = data['events']
                if not isinstance(events, list) or not all(isinstance(e, dict) for e in events):
                    raise ValueError('invalid events')
            except (ValueError, KeyError, TypeError):
                self.respond(400, {'errcode': 'M_BAD_JSON'})
                return
            try:
                agent.process(events)
                if gateway is not None:
                    gateway.accept(urlsplit(self.path).path.rsplit('/', 1)[-1], events)
            except Exception as error:
                print('transaction failed: ' + type(error).__name__, flush=True)
                self.respond(503, {'errcode': 'M_UNKNOWN'})
                return
            self.respond(200, {})
    return Handler


if __name__ == '__main__':
    config = json.loads(Path('/config/appservice.yaml').read_text())
    agent = EchoAgent(os.environ.get('MATRIX_URL', 'http://synapse:8008'), config['as_token'])
    from src.gateway import Gateway
    gateway = Gateway(os.environ.get('GATEWAY_DB', '/gateway/tasks.sqlite'), agent)
    token = Path('/config/agent-token').read_text().strip()
    ThreadingHTTPServer(('0.0.0.0', 9000), make_handler(agent, config['hs_token'], gateway, token)).serve_forever()
