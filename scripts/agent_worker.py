"""Outbound-only example runtime. Replace render() with your own agent, never eval messages."""
import argparse
from pathlib import Path
import time
import logging

from src.matrix_http import request


def render(task):
    return 'External agent received: ' + task['event']['content']['body']


def once(base, token):
    task = request(base, 'GET', '/agent/tasks', token)['task']
    if not task:
        return False
    # A recovered completion reuses the persisted result; execution can be delivered more than once.
    result = task['result'] if task['result'] is not None else render(task)
    request(base, 'POST', '/agent/complete', token,
            {'id': task['id'], 'lease': task['lease'], 'result': result})
    print('completed task=' + task['id'], flush=True)
    return True


def run_loop(run_once, delay=2):
    """Keep polling after transient failures; process interrupts still stop the worker."""
    while True:
        try:
            run_once()
        except Exception as error:
            # Do not log request bodies, tokens, or backend response details.
            logging.warning('Worker iteration failed (%s); retrying', type(error).__name__)
        time.sleep(delay)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:9000')
    parser.add_argument('--token-file', required=True)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    token = Path(args.token_file).read_text().strip()
    if args.once:
        once(args.url, token)
    else:
        run_loop(lambda: once(args.url, token))
