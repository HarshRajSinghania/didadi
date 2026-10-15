"""Loopback-only development preview; credentials stay on the server."""
import argparse
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import secrets
import threading
import time
from urllib.parse import parse_qs

from scripts.agent_worker import once
from src.matrix_as import AGENT, PREFIX
from src.matrix_http import request, segment


def serve(state, worker_token, port=8765):
    room = '/rooms/' + segment(state['room'])
    csrf = secrets.token_urlsafe(32)

    def api(method, path, data=None, query=None):
        return request('http://127.0.0.1:8008', method, PREFIX + path, state['tokens'][0], data, query)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def valid_host(self):
            if self.headers.get('Host') not in {f'127.0.0.1:{port}', f'localhost:{port}'}:
                self.send_error(403)
                return False
            return True

        def do_GET(self):
            if not self.valid_host():
                return
            try:
                events = api('GET', room + '/messages', query={'dir': 'b', 'limit': 50})['chunk']
                rows = []
                for event in reversed(events):
                    if event['type'] != 'm.room.message':
                        continue
                    content = event['content']
                    label = 'EXTERNAL AGENT' if event['sender'] == AGENT else 'HUMAN'
                    rows.append('<article><small>' + label + '</small><p>' + escape(content.get('body', '')) +
                                '</p><code>' + escape(event['event_id']) + '</code></article>')
                body = '''<!doctype html><html><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Didadi · Agent gateway</title><style>
body{font:16px system-ui;background:#101722;color:#e1e9f2;max-width:860px;margin:45px auto;padding:0 24px}
h1{font-size:42px;margin-bottom:8px}small{color:#83ddc6;letter-spacing:2px}p{line-height:1.6;white-space:pre-wrap}
article{background:#1b2738;padding:18px 24px;border-radius:14px;margin:14px 0}code{font-size:11px;color:#93a5bb;overflow-wrap:anywhere}
input{width:70%;padding:15px;border-radius:8px;border:0}button{padding:15px;border:0;border-radius:8px;background:#83ddc6}
a{color:#83ddc6}.note{color:#a8b8cb}form{margin:30px 0}</style>
<small>DIDADI / LOCAL DEVELOPMENT</small><h1>A message. A durable task.<br>An external agent reply.</h1>
<p class="note">Live Matrix timeline · SQLite task ledger · independent polling runtime<br>Deterministic example agent; no LLM or document writes.</p>
<form method="post"><input name="body" placeholder="Ask the example agent…" required maxlength="4000">
<input type="hidden" name="csrf" value="''' + csrf + '''"><button>Send to agent</button></form>
<p><a href="/">Refresh timeline ↻</a></p>''' + ''.join(rows) + '</html>'
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(body.encode())
            except Exception:
                self.send_error(503, 'Matrix unavailable')

        def do_POST(self):
            if not self.valid_host():
                return
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size < 20000:
                self.send_error(400)
                return
            form = parse_qs(self.rfile.read(size).decode())
            if not secrets.compare_digest(form.get('csrf', [''])[0], csrf):
                self.send_error(403)
                return
            body = form.get('body', [''])[0].strip()
            if not 0 < len(body) <= 4000:
                self.send_error(400)
                return
            api('PUT', room + '/send/m.room.message/preview-' + secrets.token_hex(12), {
                'msgtype': 'm.text', 'body': body, 'm.mentions': {'user_ids': [AGENT]}})
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()

    def worker():
        while True:
            try:
                once('http://127.0.0.1:9000', worker_token)
            except Exception as error:
                print('worker retry: ' + type(error).__name__, flush=True)
            time.sleep(1)

    threading.Thread(target=worker, daemon=True).start()
    print(f'Preview http://127.0.0.1:{port}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', port), Handler).serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--state-file', required=True)
    parser.add_argument('--token-file', required=True)
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    serve(json.loads(Path(args.state_file).read_text()), Path(args.token_file).read_text().strip(), args.port)
