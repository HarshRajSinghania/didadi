"""Isolated visual-state adapter. Does not modify data or replace successful backend results."""
import argparse
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import time
from src.client_server import Workspace,handler

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--mode',choices=['loading','failure'],required=True)
    parser.add_argument('--state-file',required=True);parser.add_argument('--token-file',required=True)
    parser.add_argument('--repo',required=True);parser.add_argument('--metadata',required=True)
    parser.add_argument('--port',type=int,default=8768)
    args=parser.parse_args()
    workspace=Workspace(json.loads(Path(args.state_file).read_text()),Path(args.token_file).read_text().strip(),
                        args.repo,args.metadata,'http://127.0.0.1:8009','http://127.0.0.1:9001')
    workspace.qa=args.mode
    original=workspace.docs.snapshot
    def snapshot(*a,**kw):
        if args.mode=='failure':raise ConnectionError('isolated visual regression failure')
        time.sleep(30)
        return original(*a,**kw)
    workspace.docs.snapshot=snapshot
    print(f'Isolated {args.mode} visual QA http://127.0.0.1:{args.port}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',args.port),handler(workspace,Path('client/dist'),args.port)).serve_forever()
