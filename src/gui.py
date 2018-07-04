import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from os.path import expanduser

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
            self.manager = manage.FileManager(dir_path)
        except manage.InvalidDirectoryError:
            # Error dialog
            raise NotImplementedError(
                "File manager could not be created - error handling not implemented"
            )
        self.current_file = ""
        self.version_labels = []
        self.version_data = []
        self.init_window()

    def update_version_list(self):
        """
        Updates the contents of the file version list with the versions of the currently
        selected file.
        """
        if not self.current_file:
            return
        self.clear_version_list()

        try:
            self.version_data = self.manager.get_file_versions(self.current_file)
        except manage.VersionError:
            raise NotImplementedError(
                "File versions could not be retrieved - error handling not implemented"
            )

        # Maximum length of version number, used for padding
        max_ver_length = len(str(len(self.version_data)))
        for i, x in enumerate(self.version_data):
            version_num = str(len(self.version_data) - i).ljust(max_ver_length)
            self.version_labels.append(
                QLabel(f"Version {version_num}\t({str(x.timestamp.strftime('%x %X'))})")
            ) 
            self.version_list.addWidget(self.version_labels[-1])

    def clear_version_list(self):
        """
        Clears the contents of the file version list.
        """
        for x in self.version_labels:
            self.version_list.removeWidget(x)
            x.deleteLater()
            del (x)
        self.version_labels.clear()

    def select_file(self):
        """
        Sets the current file to the one selected by the user using a file dialog.
        """
        file_name = QFileDialog.getOpenFileName(
            self, "Select File", self.manager.dir_path, "All Files (*.*)"
        )[0]
        if not file_name:
            return
        self.file_text.setText(file_name)
        self.current_file = file_name

    def change_file(self):
        """
        Change the file being displayed to the one selected by the user using a file.
        """
        self.select_file()
        self.update_version_list()

    def init_window(self):
        """
        Initialises the appearance of the window, including the file versions and
        settings tabs.
        """
        self.versions_tab = QWidget()
        self.settings_tab = QWidget()
        self.versions_layout()
        self.settings_layout()
        self.addTab(self.versions_tab, "Versions")
        self.addTab(self.settings_tab, "Settings")

        self.setFixedSize(500, 500)
        self.setWindowTitle("View and Restore File Versions")
        # Uncomment when icon has been designed
        # self.setWindowIcon(QIcon('icon.png'))
        self.centre_window()
        self.show()

    def versions_layout(self):
        """
        Sets the contents and layout of the file versions tab.
        """
        grid = QGridLayout()
        grid.setVerticalSpacing(1)
        grid.setHorizontalSpacing(5)

        self.file_text = QLineEdit()
        self.file_text.setReadOnly(True)
        file_button = QPushButton("Select File")
        file_button.clicked.connect(self.change_file)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.update_version_list)
        refresh_button.setFixedWidth(60)

        version_widget = QWidget()
        self.version_list = QVBoxLayout(self)
        self.version_list.setAlignment(Qt.AlignTop)
        self.version_labels.append(QLabel("No file selected"))
        self.version_list.addWidget(self.version_labels[0])
        version_widget.setLayout(self.version_list)
        """
        self.scroll_area = QScrollArea()
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(False)
        self.scroll_area.setWidget(version_widget)
        
        version_layout = QVBoxLayout(self)
        version_layout.addWidget(self.scroll_area)
        container_widget = QWidget()
        container_widget.setLayout(version_layout) """

        grid.addWidget(self.file_text, 0, 0)
        grid.addWidget(file_button, 0, 2)
        grid.addWidget(version_widget, 1, 0, 1, 2)
        grid.addWidget(refresh_button, 2, 0)

        self.versions_tab.setLayout(grid)

    def settings_layout(self):
        """
        Sets the contents and layout of the settings tab. 
        """
        pass

    def centre_window(self):
        """
        Changes the position of the window so that it is in the centre of the display
        """
        q_rect = self.frameGeometry()
        centre_point = QDesktopWidget().availableGeometry().center()
        q_rect.moveCenter(centre_point)
        self.move(q_rect.topLeft())


def launch():
    app = QApplication(sys.argv)

    app.setStyleSheet(
    """
    QTabBar::tab:selected {
        background: white;
        color: rgb(15, 15, 15);
    }
    QTabBar::tab {
        background: rgb(179, 179, 179);
        color: white;
    }
    QTabWidget>QWidget>QWidget {
        background: white;
        color: rgb(15, 15, 15);
    }
    QLabel {
        font-family: Droid Sans Mono;
        font-size: 12px;
        color: rgb(15, 15, 15);
    }
    """
    )

    gui = VersionWindow("C:\\Users\\Liam\\Google Drive\\Projects\\Small\\test-repo")
    sys.exit(app.exec_())


if __name__ == "__main__":
    launch()

