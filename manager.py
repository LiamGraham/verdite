"""
- Add file
- Modify file
- Remove file

Process:
1. Change detected (i.e. file added, modified, or removed)
2. Change staged
3. Change committed

git.Repo
- path (path to either the root git directory or the bare git repo)

Example sh.git Usage:
git = sh.git
repo = git.bake(_cwd='C:\\Users\\Liam\\Google Drive\\Projects\\Small\\test-repo')
print(repo.add('test.docx'))
print(repo.commit(m='Commit message'))
print(git.status())
"""

try:
    import sh
except ImportError:
    # fallback: emulate the sh API with pbs
    import pbs
    class Sh(object):
        def __getattr__(self, attr):
            return pbs.Command(attr)
    sh = Sh()

print(help(sh.git))

import time

class FileManager:

    def __init__(self):
        pass


