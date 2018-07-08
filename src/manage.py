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
import dataclasses
import datetime
from dataclasses import dataclass
from subprocess import call
from platform import system

class FileManager:
    """
    Interface enabling the management of the state of a repository, used for automatic
    version control.
    """

    def __init__(self, dir_path, temp_path):
        """
        Creates new FileManager for directory at given path. 

        Arguments:
            dir_path (str): path of target directory
            temp_path (str): path of temp directory
        """
        self.repo = sh.git.bake(_cwd=dir_path)
        try:
            self.repo("rev-parse", "--is-inside-work-tree")
        except pbs.ErrorReturnCode:
            raise InvalidDirectoryError("Target directory is not a repository")

        self.dir_path = dir_path
        self.ignore_path = f"{dir_path}\\.gitignore"
        self.temp_path = temp_path

    def store_changes(self):
        """
        Stores all changes and returns list of files that were successfully committed.

        Returns: list(str): all files that were committed
        """
        changes = self.get_changes()
        committed = []
        verbose_codes = {"M": "modify", "A": "add", "D": "delete"}
        for change in changes:
            print(f"Change: {change}")
            codes = change.codes
            file_path = change.file_path

            if "??" in codes:
                codes = self._stage_changes(file_path)

            actions = " and ".join([verbose_codes[x] for x in codes]).capitalize()
            message = f"{actions} {file_path}"
            try:
                self.repo.add(file_path)
                self.repo.commit(m=message)
                committed.append(file_path)
            except pbs.ErrorReturnCode:
                # Any git errors are ignored, enabling changes that weren't committed to
                # be committed with the next function call
                self.repo.reset("HEAD", file_path)
                continue
        return committed

    def get_changes(self):
        """
        Returns the changes made to files and the code corresponding to the change in
        the form of ChangeData objects.

        Returns (ChangeData): changes made to files

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
            # git encloses file names containing spaces with double quotes
            # Must remove quotes so file names can be matched
            file_path = " ".join(line[1:]).replace('"', '')
            changes.append(ChangeData(codes, file_path))
        return changes

    def get_file_versions(self, file_path):
        """
        Returns all versions of given file, in order of most recent to least recent
        (even if file has been renamed). The version list consists of VersionData objects
        storing the the commit hashes, commit messages and commit dates.

        Arguments:
            file_path (str): path of file for which versions will be retrieved

        Returns (list(VersionData)): all versions of given file
        """
        if not os.path.realpath(file_path).startswith(self.dir_path):
            raise VersionError("File is not inside controlled directory")
        try:
            file_log = self.repo.log("--oneline", file_path).split("\n")
        except pbs.ErrorReturnCode:
            raise VersionError("Unable to retrieve file")
        versions = []
        for commit in file_log:
            if not commit:
                continue
            log_entry = commit.split()  # Log entry has form "<hash> <message>"
            timestamp = self._get_commit_timestamp(log_entry[0])
            versions.append(
                VersionData(log_entry[0], " ".join(log_entry[1:]), timestamp)
            )
        return versions

    def open_file_version(self, file_path, version_num):
        """
        Open specified version of given file. Desired version is stored in temp folder
        and working file remains unchanged.
        
        Arguments:
            file_path (str): path of target file. Must be an absolute file path.
            version_num (int): number of version to be retrieved
        """
        target_ver = self._get_target_version(file_path, version_num)
        try:
            # TODO: Breaks if file had different name at given version
            self.repo.checkout(target_ver.c_hash, file_path)
            shutil.copy(file_path, self.temp_path)
            os.startfile(f"{self.temp_path}\\{os.path.split(file_path)[1]}")
            self.repo.reset("HEAD", file_path)
            self.repo.checkout("--", file_path)
        except pbs.ErrorReturnCode:
            raise VersionError(
                f"Unable to view version {version_num} of {os.path.split(file_path)[1]}"
            )

    def restore_file_version(self, file_path, version_num):
        """
        Restores specified version of given file.

        Arguments:
            file_path (str): path of target file
            version_num (int): number of version to be restored
        """
        target_ver = self._get_target_version(file_path, version_num)
        try:
            self.repo.checkout(target_ver.c_hash, file_path)
            if self.repo.status("-s"):
                # Prevent error in case where the most recent versions is the most
                # recent commit
                self.repo.commit(m=f'Restore "{target_ver.message}"')
        except pbs.ErrorReturnCode as e:
            raise VersionError(
                f"Unable to restore version {version_num} of {os.path.split(file_path)[1]}"
            )

    def _get_target_version(self, file_path, version_num):
        """
        Validates given file path and version number and returns target version. Used
        for both version viewing and restoration.

        Arguments:
            file_path (str): path of target file
            version_num (int): number of target version
        
        Returns (VersionData): data for target version
        """
        if not os.path.isabs(file_path):
            raise VersionError("File path must be absolute")

        versions = self.get_file_versions(file_path)
        if version_num > len(versions) or version_num < 1:
            raise VersionError("Invalid version number")
        return versions[-version_num]

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
        print(f"File path: {file_path}")
        self.repo.add(file_path)
        changes = self.get_changes()
        for change in changes:
            if change.file_path == file_path:
                return change.codes
        return None

    def get_all_ignored(self):
        """
        Returns all ignore keywords for target directory.

        Returns (list(str)): ignored keywords for target directory
        """
        if not self._ignore_file_exists():
            self._create_ignore_file()
            return self._collect_all_ignored()

    def add_ignored(self, keyword):
        """
        Add the given ignore keyword to the set of keywords for the taret directory.

        Arguments:
            keyword (str): ignore keyword to add
        """
        if not self._ignore_file_exists():
            self._create_ignore_file()
        ignored = self._collect_all_ignored()
        if keyword in ignored:
            return
        with open(self.ignore_path, "a") as f:
            f.write(keyword + "\n")
            try:
                self.store_changes()
            except pbs.ErrorReturnCode:
                pass

    def remove_ignored(self, keyword):
        """
        Remove the given ignore keyword from the set of keywords for the taret directory.

        Arguments:
            keyword (str): ignore keyword to remove 
        """
        if not self._ignore_file_exists():
            self._create_ignore_file()
            ignored = self._collect_all_ignored()
        with open(self.ignore_path, "w") as f:
            if ignored:
                ignored.remove(keyword)
            for x in ignored:
                f.write(x + "\n")
            try:
                self.store_changes()
            except pbs.ErrorReturnCode:
                pass
    
    def _ignore_file_exists(self):
        return os.path.isfile(self.ignore_path)
    
    def _create_ignore_file(self):
        """
        Create .gitignore file at the top of the target directory. 
        """
        with open(self.ignore_path, "w"):
            self._hide_destination(self.ignore_path)

    def _collect_all_ignored(self):
        """
        Returns a list of ignore keywords, eliminating any blank lines.

        Returns (list(str)): all ignore keywords in ignore file
        """
        with open(self.ignore_path, "r") as f:
            contents = f.read().split("\n")
        ignored = []
        for line in contents:
            line = line.strip()
            if line:
                ignored.append(line)
        return ignored

    def _get_commit_timestamp(self, commit_hash):
        """
        Returns datetime object representing the commit date of the commit corresponding
        to the given commit hash.

        Arguments:
            commit_hash (str): hash of commit for which timestamp will be generated

        Returns (datetime.datetime): timestamp of given commit
        """
        date_str = str(
            self.repo.show('--pretty=format:"%cd"', "--no-patch", commit_hash)
        ).replace('"', "")
        return datetime.datetime.strptime(date_str, "%a %b %d %H:%M:%S %Y %z")

    def _hide_destination(self, path):
        """
        Hide the file or directory with the given path.

        Arguments:
            path (str): path of target file or directory
        """
        operating_system = system()
        if operating_system == "Windows":
            call(["attrib", "+H", path])
        elif operating_system == "Darwin":
            call(["chflags", "hidden", path])


@dataclass
class VersionData:
    """
    Basic data class storing commit information for a specific file version.
    """

    # Commit hash, message, and timestamp
    c_hash: str
    message: str
    timestamp: datetime.datetime


@dataclass
class ChangeData:
    """
    Basic data class storing change information for a specific file.
    """

    codes: list
    file_path: str


class InvalidDirectoryError(Exception):
    """
    Exception raised when target directory is not a valid repository.
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class VersionError(Exception):
    """
    Exception raised for all error cases relating to viewing and restoration of previous
    file versions.
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class IgnoreError(Exception):
    """
    Exception raised for all error cases relating to adding and removal of ignore
    keywords.
    """

    def __init__(self, message):
        super().__init__(message)
        self.message = message
