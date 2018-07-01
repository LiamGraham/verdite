import sys
from PyQt5.QtWidgets import QWidget, QDesktopWidget, QApplication
from PyQt5.QtGui import QIcon

import manage


class VersionInterface(QWidget):
    def __init__(self, manager):
        """
        Creates a new graphical user interface enabling the viewing and restoration of
        file versions by a user.

        Functionality:
        - View version history of a file
        - Open a specific version of a file
        - Restore a specific version of a file
        - Configure settings

        Actions:
        - Select folder/s to be version controlled
        - Pause/start version control
        - Configure file types to be tracked (e.g. file category checkboxes, ignore list)
        - Set interval for storage of changes

        Design:
        - Tab structure
            - Version explorer
                - File to view selected using file dialog
                - Version history of file then displayed
                - Versions may be opened or restored by selecting desired version
            - Settings

        Arguments:
            manager (manage.FileManager): interface for target directory/repo
        """
        self.manager = manager
        super().__init__()
        self.init_interface()

    def init_interface(self):
        self.setGeometry(500, 300, 500, 500)
        self.setWindowTitle('View and Restore File Versions')
        # Uncomment when icon has been designed
        # self.setWindowIcon(QIcon('icon.png'))      
        self.center_window()  
        self.show()

    def center_window(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = VersionInterface("C:\\Users\\Liam\\Google Drive\\Projects\\Small\\test-repo")
    sys.exit(app.exec_())
    