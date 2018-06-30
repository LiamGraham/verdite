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
import os
import shutil

class FileManager:
    def __init__(self, repo_path):
        """
        Creates new FileManager for repository at given path.

        Arguments:
            repo_path (str): path of target repository
        """
        self.repo = sh.git.bake(
            _cwd=repo_path
        )
        self.repo_path = repo_path
        self.temp_path = "C:\\Users\\Liam\\Google Drive\\Projects\\Medium\\file-control\\temp"

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
                file_path = change[1]
                self.repo.add(file_path)
                actions = " and ".join([verbose_codes[x] for x in codes]).capitalize()
                message = f"{actions} {file_path}"
                self.repo.commit(m=message)
                committed.append(file_path)
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
        status = self.repo.status("-s").split("\n")
        for line in status:
            if not line:
                continue
            line = line.split()
            codes = list(line[0]) if line[0] != "??" else ["??"]
            changes.append((codes, line[1]))
        return changes

    def get_file_versions(self, file_path):
        """
        Returns all versions of given file, in order of most recent to least recent
        (even if file has been renamed). The version list consists of pairs of
        corresponding commit hashes and commit messages, in the form:

        [(commit0, message0), (commit1, message1), ..., (commitN, messageN)]

        Arguments:
            file_path (str): path of file for which versions will be retrieved

        Returns (list(str)): all versions of given file
        """
        file_log = self.repo.log("--follow", "--oneline", file_path).split("\n")
        versions = []
        for commit in file_log:
            if not commit:
                continue
            commit = commit.split()
            versions.append((commit[0], " ".join(commit[1:])))
        return versions

    def view_file_version(self, file_path, version_num):
        """
        Open given version of given file. 
        
        Arguments:
            file_path (str): path of file
            version_num (int): number of version to be retrieved

        Notes:
        View commit history of specific file: git log --oneline <file>

        Get commit date of specific commit: git show --pretty=format:"%cd" --no-patch <hash>

        1. View prior version of specific file - git checkout <hash> <file>
        2. Return to current version - git checkout -- <file>
        """
        versions = self.get_file_versions(file_path)
        if version_num >= len(versions) or version_num < 1:
            return
        target_ver = versions[-version_num]
        try:
            self.repo.checkout(target_ver[0], file_path)
            shutil.copy2(file_path, self.temp_path)
            os.startfile(f"{self.temp_path}\\{os.path.split(file_path)[1]}")
            self.repo.reset("HEAD", file_path)
            self.repo.checkout("--", file_path)
        except:
            # Unable to identify appropriate error/exception, therefore one has not been provided
            print(f"Error: Unable to view version {version_num} of {os.path.split(file_path)[1]}")

    def revert_file_version(self, file_path, version_num):
        """
        1. View prior version of specific file - git checkout <hash> <file>
        2. Commit changes

        Retains commit history. 
        """
        versions = self.get_file_versions(file_path)
        if version_num >= len(versions) or version_num < 1:
            return
        target_ver = versions[-version_num]
        try:
            self.repo.checkout(target_ver[0], file_path)
            self.repo.commit(m=f'Restore "{target_ver[1]}"')
        except:
            # Unable to identify appropriate error/exception, therefore one has not been provided
            print(f"Error: Unable to revert to version {version_num} of {os.path.split(file_path)[1]}")


m = FileManager("C:\\Users\\Liam\\Google Drive\\Projects\\Small\\test-repo")
print(m.get_file_versions("file.txt"))
m.revert_file_version("C:\\Users\\Liam\\Google Drive\\Projects\\Small\\test-repo\\file.txt", 15)