try:
    import sh
except ImportError:
    # Emulate the sh API with pbs
    import pbs

    class Sh(object):
        def __getattr__(self, attr):
            return pbs.Command(attr)

    sh = Sh()

import os
import shutil


class FileManager:
    """
    Interface enabling the management of the state of a repository, used for automatic
    version control.
    """

    def __init__(self, dir_path):
        """
        Creates new FileManager for directory at given path. 

        Arguments:
            dir_path (str): path of target directory
        """
        self.repo = sh.git.bake(_cwd=dir_path)
        try:
            self.repo("rev-parse", "--is-inside-work-tree")
        except pbs.ErrorReturnCode:
            raise InvalidDirectoryError("Target directory is not a repository")

        self.dir_path = dir_path
        self.temp_path = (
            "C:\\Users\\Liam\\Google Drive\\Projects\\Medium\\file-control\\temp"
        )

    def store_changes(self):
        """
        Stores all changes and returns list of files that were successfully committed.

        Returns: list(str): all files that were committed
        """
        changes = self.get_changes()
        committed = []
        verbose_codes = {"M": "modify", "A": "add", "D": "delete"}
        for change in changes:
            codes, file_path = change
            if "??" in codes:
                codes = self._stage_changes(file_path)
            actions = " and ".join([verbose_codes[x] for x in codes]).capitalize()
            message = f"{actions} {file_path}"
            try:
                self.repo.add(file_path)
                self.repo.commit(m=message)
                committed.append(file_path)
            except pbs.ErrorReturnCode:
                continue
        return committed

    def get_changes(self):
        """
        Returns the changes made to files and the code corresponding to the change, in
        the form:
        
        [([code0A, code0B, ...], file0), ([code1A, code1B, ...], file1), ...]

        Returns: list(tuple(list(str), str)): changes made to files

        Status codes:
        - M: modified
        - A: added
        - D: deleted
        - ??: untracked

        Codes are combined if multiple actions have been performed on a single file
        and the file is tracked (i.e. AM for added then modified, AD for added then
        deleted, and MD for modified then deleted).
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
        (even if file has been renamed). The version list consists of VersionData objects
        storing the the commit hashes, commit messages and commit dates.

        Arguments:
            file_path (str): path of file for which versions will be retrieved

        Returns (list(str)): all versions of given file
        """
        file_log = self.repo.log("--follow", "--oneline", file_path).split("\n")
        versions = []
        for commit in file_log:
            if not commit:
                continue
            log_entry = commit.split() # Log entry is in form "<hash> <message>"
            datetime = self.repo.show('--pretty=format:"%cd"', '--no-patch', commit[0])
            versions.append(VersionData(log_entry[0], " ".join(log_entry[1:]), datetime))
        return versions

    def view_file_version(self, file_path, version_num):
        """
        Open specified version of given file. 
        
        Arguments:
            file_path (str): path of target file
            version_num (int): number of version to be retrieved
        """
        # Get commit date of specific commit: git show --pretty=format:"%cd" --no-patch <hash>
        versions = self.get_file_versions(file_path)
        if version_num >= len(versions) or version_num < 1:
            return
        target_ver = versions[-version_num]
        try:
            self.repo.checkout(target_ver.c_hash, file_path)
            shutil.copy2(file_path, self.temp_path)
            os.startfile(f"{self.temp_path}\\{os.path.split(file_path)[1]}")
            self.repo.reset("HEAD", file_path)
            self.repo.checkout("--", file_path)
        except pbs.ErrorReturnCode:
            print(
                f"Error: Unable to view version {version_num} of {os.path.split(file_path)[1]}"
            )

    def restore_file_version(self, file_path, version_num):
        """
        Restores specified version of given file.

        Arguments:
            file_path (str): path of target file
            version_num (int): number of version to be restored
        """
        versions = self.get_file_versions(file_path)
        if version_num >= len(versions) or version_num < 1:
            return
        target_ver = versions[-version_num]
        try:
            self.repo.checkout(target_ver[0], file_path)
            self.repo.commit(m=f'Restore "{target_ver[1]}"')
        except pbs.ErrorReturnCode:
            print(
                f"Error: Unable to revert to version {version_num} of {os.path.split(file_path)[1]}"
            )

    def has_changed(self):
        """
        Returns true if changes to files have occurred, that is, the stored state of
        files differs from the current state.

        Returns (boolean): true if changes to files have occurred
        """
        return len(self.repo.status("-s").split("\n")[0]) > 0

    def _stage_changes(self, file_path):
        """
        Stages untracked file and returns code corresponding to change.

        Arguments:
            file_path (str): path of file to be staged

        Returns (list(str)): code corresponding to change 
        """
        self.repo.add(file_path)
        changes = self.get_changes()
        for change in changes:
            if change[1] == file_path:
                return change[0]
        return None


@dataclass
class VersionData:
    c_hash: str
    message: str
    datetime: str
        

class InvalidDirectoryError(Exception):
    """
    Exception raised when target directory is not a valid repository.
    """
    def __init__(self, message):
        super().__init__(message)