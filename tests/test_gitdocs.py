import unittest, tempfile, threading
from src.gitdocs import GitDocs, Conflict, InvalidPath

class GitDocsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.store=GitDocs(self.temp.name)
    def tearDown(self): self.temp.cleanup()
    def test_create_read_history(self):
        v=self.store.write('docs/a.md','# First')
        self.assertEqual(self.store.read('docs/a.md'),'# First')
        v2=self.store.write('docs/a.md','# Second',v['blob'])
        self.assertEqual(self.store.read('docs/a.md',v['commit']),'# First')
        self.assertNotEqual(v['commit'],v2['commit'])
    def test_stale_write_rejected(self):
        v=self.store.write('a.md','one')
        self.store.write('a.md','two',v['blob'])
        with self.assertRaises(Conflict): self.store.write('a.md','stale',v['blob'])
        self.assertEqual(self.store.read('a.md'),'two')
    def test_parallel_same_base_only_one_succeeds(self):
        v=self.store.write('a.md','original')
        barrier=threading.Barrier(2); outcomes=[]
        def writer(value):
            barrier.wait()
            try: self.store.write('a.md',value,v['blob']); outcomes.append('ok')
            except Conflict: outcomes.append('conflict')
        ts=[threading.Thread(target=writer,args=(v,)) for v in ['A','B']]
        for t in ts: t.start()
        for t in ts: t.join()
        self.assertEqual(sorted(outcomes),['conflict','ok'])
    def test_path_escape(self):
        for p in ['../secret.md','/etc/passwd.md','a/../../b.md']:
            with self.assertRaises(InvalidPath): self.store.write(p,'bad')

if __name__=='__main__': unittest.main()
