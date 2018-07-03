import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon

import manage


class VersionWindow(QTabWidget):
    def __init__(self, dir_path):
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

        Use 'git ls-files --cached' to retrieve list of all cached files. May be used to
        determine if file selected using file dialog is version controlled. 

        Arguments:
            manager (manage.FileManager): interface for target directory/repo
        """
        super(VersionWindow, self).__init__()
        try:
            manager = manage.FileManager(dir_path)
        except manage.InvalidDirectoryError:
            # Error dialog
            pass
        self.init_window()

    def init_window(self):
        self.versions = QWidget()
        self.settings = QWidget()
        self.addTab(self.versions,"Versions")
        self.addTab(self.settings,"Settings")
    
        self.setGeometry(500, 300, 500, 500)
        self.setWindowTitle('View and Restore File Versions')
        # Uncomment when icon has been designed
        # self.setWindowIcon(QIcon('icon.png'))      
        self.center_window()  
        self.show()
    
    def versions_layout(self):
        pass

    def settings_layout(self):
        pass

    def center_window(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

def launch():
    app = QApplication(sys.argv)
    app.setStyleSheet("""
    QTabBar::tab:selected {
        background: white;
        color: rgb(55, 55, 55);
    }
    QTabBar::tab {
        background: rgb(179, 179, 179);
        color: white;
    }
    QTabWidget>QWidget>QWidget {
        background: white;
        color: rgb(55, 55, 55);
    }
    """)
    gui = VersionWindow("C:\\Users\\Liam\\Google Drive\\Projects\\Small\\test-repo")
    sys.exit(app.exec_())

if __name__ == "__main__":
    launch()
    