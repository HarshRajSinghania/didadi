"""Small standard-library Matrix HTTP client shared by spike and smoke test."""
import json
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


def segment(value):
    return quote(value, safe='')


class MatrixError(Exception):
    def __init__(self, status, body):
        self.status, self.body = status, body
        super().__init__(f'Matrix HTTP {status}: {body.get("errcode", "unknown")}')


def request(base, method, path, token=None, data=None, query=None):
    url = base + path + (('?' + urlencode(query)) if query else '')
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    req = Request(url, method=method, headers=headers,
                  data=None if data is None else json.dumps(data).encode())
    try:
        with urlopen(req, timeout=15) as response:
            return json.load(response)
    except HTTPError as error:
        try:
            body = json.load(error)
        except ValueError:
            body = {}
        if not isinstance(body, dict):
            body = {}
        raise MatrixError(error.code, body) from None
