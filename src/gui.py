import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QIcon

import manage


class VersionInterface(QWidget):
    def __init__(self, manager):
        """
        Creates a new graphical user interface enabling the viewing and restoration of
        file versions by a user.

        Arguments:
            manager (manage.FileManager): interface for target directory/repo
        """
        self.manager = manager
        super().__init__()
        self.init_interface()

    def init_interface(self):
        self.setGeometry(300, 300, 300, 220)
        self.setWindowTitle('View and Restore File Versions')
        # Uncomment when icon has been designed
        # self.setWindowIcon(QIcon('icon.png'))        
        self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = VersionInterface("C:\\Users\\Liam\\Google Drive\\Projects\\Small\\test-repo")
    sys.exit(app.exec_())
    