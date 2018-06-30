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

git.status("-s") // Status output in short format
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

import time


class FileManager:
    def __init__(self):
        pass

    def commit_changes(self):
        """
        Commits all changes and returns list of files that were successfully committed.

        Returns: list(str): all files that were committed
        """
        changes = self.get_changes()
        committed = []
        verbose_codes = {"M": "modify", "A": "add", "D": "delete"}
        for change in changes:
            try:
                codes = change[0]
                file_name = change[1]
                sh.git.add(file_name)
                actions = " and ".join([verbose_codes[x] for x in codes]).capitalize()
                message = f"{actions} {file_name}"
                sh.git.commit(m=message)
                committed.append(file_name)
            except Exception:
                continue
        return committed

    def get_changes(self):
        """
        Returns the changes made to files and the code corresponding to the change, in
        the form:
        
        [([code0A, code0B, ...], change0), ([code1A, code1B], change1)]

        Returns: list(tuple(list(str), str)): changes made to files

        Status codes:
        - M: modified
        - A: added
        - D: deleted
        - ??: untracked

        Codes can be combined if multiple actions have been performed on a single file
        and the file is tracked (i.e. AM for added then modified, AD for added then
        deleted, and MD for modified then deleted)
        """
        changes = []
        status = sh.git.status("-s").split("\n")
        for line in status:
            if not line:
                continue
            line = line.split()
            codes = list(line[0]) if line[0] != "??" else ["??"]
            changes.append((codes, line[1]))
        return changes


m = FileManager()
print(m.get_changes())
print(m.commit_changes())
