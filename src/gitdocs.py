"""Minimal Git-backed document store: one Git repository is the content authority."""
from pathlib import Path
import subprocess, threading, re

class Conflict(Exception): pass
class InvalidPath(Exception): pass

class GitDocs:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.lock = threading.RLock()  # prototype-only; distributed deployment needs a DB/OS lock
        self.root.mkdir(parents=True, exist_ok=True)
        if not (self.root / '.git').exists():
            self._git('init', '-q'); self._git('config','user.name','Doc Service'); self._git('config','user.email','docs@localhost')
    def _git(self, *args, check=True):
        p = subprocess.run(['git', '-C', str(self.root), *args], text=True, capture_output=True)
        if check and p.returncode: raise RuntimeError(p.stderr.strip())
        return p.stdout.strip()
    def _path(self, name):
        if not re.fullmatch(r'[a-zA-Z0-9_/-]+\.md', name) or '..' in name.split('/') or name.startswith('/'):
            raise InvalidPath(name)
        p = (self.root / name).resolve()
        if not p.is_relative_to(self.root) or any(a.is_symlink() for a in [p,*p.parents] if a != self.root and a.is_relative_to(self.root)):
            raise InvalidPath(name)
        return p
    def read(self, name, commit=None):
        self._path(name)
        if commit is not None:
            if not re.fullmatch(r'[0-9a-f]{40,64}', commit): raise ValueError('bad commit')
            return self._git('show',f'{commit}:{name}')
        p = self._path(name)
        return p.read_text() if p.exists() else None
    def blob_version(self, name):
        self._path(name)
        output=self._git('rev-parse',f'HEAD:{name}',check=False)
        return output if re.fullmatch(r'[0-9a-f]{40,64}', output) else None
    def write(self, name, content, base_blob=None):
        if not isinstance(content,str): raise TypeError('content must be text')
        with self.lock:
            p=self._path(name)
            if self.blob_version(name) != base_blob: raise Conflict('document changed; refresh and merge')
            p.parent.mkdir(parents=True,exist_ok=True); p.write_text(content)
            self._git('add','--',name)
            self._git('commit','-qm',f'docs: update {name}')
            return {'commit':self._git('rev-parse','HEAD'), 'blob':self.blob_version(name)}
