"""Generate local-only configuration once; JSON is a YAML subset."""
import json
import os
from pathlib import Path
import secrets


def initialize(root):
    root.mkdir(parents=True, exist_ok=True)
    secret_file = root / 'secrets.json'
    if not secret_file.exists():
        secret_file.write_text(json.dumps({k: secrets.token_hex(32) for k in
            ('as_token', 'hs_token', 'registration', 'postgres', 'macaroon')}))
    agent_token = root / 'agent-token'
    if not agent_token.exists():
        agent_token.write_text(secrets.token_hex(32))
    s = json.loads(secret_file.read_text())
    (root / 'postgres-password').write_text(s['postgres'])
    registration = {
        'id': 'didadi', 'url': 'http://appservice:9000',
        'as_token': s['as_token'], 'hs_token': s['hs_token'],
        'sender_localpart': '_didadi_service', 'rate_limited': False,
        'namespaces': {'users': [{'exclusive': True,
            'regex': r'^@_didadi_agent_[a-z0-9_]+:didadi\.localhost$'}],
            'aliases': [], 'rooms': []}}
    (root / 'appservice.yaml').write_text(json.dumps(registration, indent=2))
    config = {
        'server_name': 'didadi.localhost', 'public_baseurl': 'http://localhost:8008/',
        'pid_file': '/data/homeserver.pid', 'report_stats': False,
        'listeners': [{'port': 8008, 'type': 'http', 'tls': False,
                       'bind_addresses': ['0.0.0.0'],
                       'resources': [{'names': ['client'], 'compress': False}]}],
        'database': {'name': 'psycopg2', 'args': {'user': 'synapse',
            'password': s['postgres'], 'database': 'synapse', 'host': 'postgres',
            'port': 5432, 'cp_min': 2, 'cp_max': 5}},
        'media_store_path': '/data/media_store',
        'signing_key_path': '/data/didadi.localhost.signing.key',
        'registration_shared_secret': s['registration'],
        'macaroon_secret_key': s['macaroon'], 'enable_registration': False,
        'app_service_config_files': ['/config/appservice.yaml'],
        'trusted_key_servers': [], 'federation_domain_whitelist': [],
        'rc_message': {'per_second': 20, 'burst_count': 100},
        'rc_registration': {'per_second': 10, 'burst_count': 100}}
    (root / 'homeserver.yaml').write_text(json.dumps(config, indent=2))


if __name__ == '__main__':
    initialize(Path(os.environ.get('CONFIG_DIR', '/config')))

    # The Synapse image drops to 991:991 but does not chown an existing data volume.
    os.chown('/synapse-data', 991, 991)
