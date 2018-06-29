"""
- Add file
- Modify file
- Remove file

git.Repo
- path (path to either the root git directory or the bare git repo)

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

"""
git = sh.git.bake(_cwd='C:\\Users\\Liam\\Google Drive\\Projects\\Small\\test-repo')
print git.add('test.docx')
print git.commit(m='Commit message')
print(git.status())
"""