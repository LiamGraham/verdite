import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import os.path
import textwrap
from functools import partial

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
        except manage.InvalidDirectoryError as e:
            self.show_error_dialog(e.message)
            # TODO: Prompt to change to valid directory
        self.init_window()

    def init_window(self):
        """
        Initialises the appearance of the window, including the file versions and
        settings tabs.
        """
        self.versions_tab = VersionsTab(self, self.manager)
        self.settings_tab = SettingsTab(self, self.manager)
        self.addTab(self.versions_tab, "Versions")
        self.addTab(self.settings_tab, "Settings")

        self.setFixedSize(500, 500)
        self.setWindowTitle("View and Restore File Versions")
        self.setWindowIcon(QIcon('images\\icon_64px.png'))
        self.centre_window()
        self.show()

    def centre_window(self):
        """
        Changes the position of the window so that it is in the centre of the display
        """
        q_rect = self.frameGeometry()
        centre_point = QDesktopWidget().availableGeometry().center()
        q_rect.moveCenter(centre_point)
        self.move(q_rect.topLeft())


class VersionsTab(QWidget):
    """
    Tab containing version viewing and restoration interface.
    """
    def __init__(self, parent, manager):
        """
        Creates a new QWidget instance having the given parent and utilising the given
        manager.
        
        Arguments:
            parent (QWidget): parent of this widget
            manager (manage.FileManager): file management interface
        """
        super(QWidget, self).__init__(parent)
        self.manager = manager
        self.current_file = ""
        self.version_rows = []
        self.version_data = []
        self.init_layout()

    def update_version_list(self, refresh=False):
        """
        Updates the contents of the file version list with the versions of the currently
        selected file.
        """
        if not self.current_file:
            return
        self.clear_version_list()

        if refresh:
            data = self.get_version_data(self.current_file)
            if not data:
                return
            self.version_data = data

        self.add_version_rows()

        file_name = self.get_truncated_file_name()
        if refresh:
            self.set_status(f"Refreshed '{file_name}'")
        else:
            self.set_status(f"Loaded '{file_name}'")

    def view_version(self, version_num):
        print(f"View version {version_num}")
        try:
            self.manager.open_file_version(self.current_file, version_num)
            file_name = self.get_truncated_file_name()
            self.set_status(
                f"Opened version {version_num} of '{file_name}'"
            )
        except manage.VersionError as e:
            self.show_error_dialog(e.message)

    def restore_version(self, version_num):
        file_name = self.get_truncated_file_name()
        message = f"Do you want to restore version {version_num} of '{file_name}'?"
        confirmed = self.show_confirmation_dialog(message)
        if not confirmed:
            return

        try:
            self.manager.restore_file_version(self.current_file, version_num)
            self.update_version_list(refresh=True)
            file_name = self.get_truncated_file_name()
            self.set_status(
                f"Restored version {version_num} of '{file_name}' (now version {len(self.version_data)})"
            )
        except manage.VersionError as e:
            self.show_error_dialog(e.message)

    def get_truncated_file_name(self):
        file_name = os.path.splitext(os.path.basename(self.current_file))[0]
        return file_name[:15] + (file_name[15:] and '[...]') + os.path.splitext(self.current_file)[1]

    def show_error_dialog(self, message):
        """
        Shows error dialog displaying the given message.
        """
        self.set_status("")
        error_dialog = QMessageBox()
        error_dialog.setText(message)
        error_dialog.setWindowTitle("Error")
        error_dialog.setIcon(QMessageBox.Warning)
        error_dialog.exec_()

    def show_confirmation_dialog(self, message):
        """
        Shows confirmation dialog displaying the given message and returns True if user
        selects the 'Ok' button.

        Returns (bool): True if user selects 'Ok' button
        """
        confirm_dialog = QMessageBox()
        confirm_dialog.setText(message)
        confirm_dialog.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        confirm_dialog.setDefaultButton(QMessageBox.Cancel)
        confirm_dialog.setIcon(QMessageBox.Question)
        choice = confirm_dialog.exec_()
        return choice == QMessageBox.Ok

    def set_status(self, message):
        self.status_label.setText(message)

    def add_version_rows(self):
        # Maximum length of version number, used for padding
        max_ver_length = len(str(len(self.version_data)))
        for i, x in enumerate(self.version_data):
            version_num = len(self.version_data) - i
            version_str = str(version_num).ljust(max_ver_length)
            row = QHBoxLayout()
            label = QLabel(
                f"Version {version_str} ({str(x.timestamp.strftime('%x %X'))})"
            )

            view_button = QPushButton("View")
            restore_button = QPushButton("Restore")

            view_button.setFixedWidth(30)
            restore_button.setFixedWidth(30)
            view_button.clicked.connect(partial(self.view_version, version_num))
            restore_button.clicked.connect(partial(self.restore_version, version_num))
            row.addWidget(label)
            row.addWidget(view_button)
            row.addWidget(restore_button)

            self.version_rows.append(row)
            self.version_layout.insertLayout(
                self.version_layout.count() - 1, self.version_rows[-1]
            )

    def clear_version_list(self):
        """
        Clears the contents of the file version list.
        """
        for x in self.version_rows:
            self.remove_layout_contents(x)
            self.version_layout.removeItem(x)
            x.deleteLater()
            del (x)
        self.version_rows.clear()

    def remove_layout_contents(self, layout):
        for i in reversed(range(layout.count())):
            item = layout.takeAt(i)
            item.widget().deleteLater()
            del (item)

    def select_file(self):
        """
        Sets the current file to the one selected by the user using a file dialog.
        """
        file_name = QFileDialog.getOpenFileName(
            self, "Select File", self.manager.dir_path, "All Files (*.*)"
        )[0]
        if not file_name:
            return
        data = self.get_version_data(file_name)
        if not data:
            return
        self.version_data = data
        self.file_text.setText(file_name)
        self.current_file = file_name

    def get_version_data(self, file_name):
        try:
            data = self.manager.get_file_versions(file_name)
            return data
        except manage.VersionError as e:
            self.show_error_dialog(e.message)
            return None

    def change_file(self):
        """
        Change the file being displayed to the one selected by the user using a file.
        """
        self.select_file()
        self.update_version_list(False)

    def init_layout(self):
        """
        Sets the contents and layout of the file versions tab.
        """
        grid = QGridLayout()
        grid.setVerticalSpacing(5)
        grid.setHorizontalSpacing(5)

        self.file_text = QLineEdit()
        self.file_text.setReadOnly(True)
        file_button = QPushButton("Select")
        file_button.clicked.connect(self.change_file)

        self.status_label = QLabel()

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(partial(self.update_version_list, True))
        refresh_button.setFixedWidth(60)

        version_widget = QWidget()
        self.version_layout = QVBoxLayout()
        self.version_layout.addStretch()
        self.version_layout.setAlignment(Qt.AlignTop)
        no_files_row = QHBoxLayout()
        no_files_row.addWidget(QLabel("No file selected"))
        self.version_rows.append(no_files_row)
        self.version_layout.insertLayout(0, self.version_rows[0])
        version_widget.setLayout(self.version_layout)

        scroll_area = QScrollArea()
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(version_widget)
        scroll_area.setVerticalScrollBar(QScrollBar())

        grid.addWidget(self.file_text, 0, 0)
        grid.addWidget(file_button, 0, 2)
        grid.addWidget(scroll_area, 1, 0, 1, 3)

        bottom_row = QHBoxLayout()
        bottom_row.addWidget(refresh_button)
        bottom_row.addWidget(self.status_label)
        grid.addLayout(bottom_row, 2, 0, 1, 3)

        self.setLayout(grid)


class SettingsTab(QWidget):
    """
    Tab containing settings interface.
    """
    def __init__(self, parent, manager):
        """
        Creates a new QWidget instance having the given parent and utilising the given
        manager.
        
        Arguments:
            parent (QWidget): parent of this widget
            manager (manage.FileManager): file management interface
        """
        super(QWidget, self).__init__(parent)
        self.manager = manager
        self.init_layout()

    def init_layout(self):
        pass


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
    QPushButton {
        background-color: rgb(72, 133, 237);
        border-style: solid;
        border-style: none;
        border-width: 2px;
        border-radius: 2px;
        border-color: rgb(72, 133, 237);
        padding: 5.5px;
        min-width: 4em;
        font-family: Roboto Light;
        color: white;
    }
    QPushButton:disabled {
        background-color: rgb(145, 145, 145);
    }
    QPushButton:pressed {
        background-color: rgb(46, 88, 160)
    }
    QTabWidget>QWidget>QWidget {
        background: white;
        color: rgb(15, 15, 15);
    }
    QScrollArea>QWidget>QWidget>QPushButton {
        background-color: rgb(245, 245, 245);
        color: rgb(72, 133, 237);
    }
    QScrollArea>QWidget>QWidget>QPushButton:pressed {
        background-color: rgb(225, 225, 225);
        color: rgb(72, 133, 237);
    }
    QScrollArea>QWidget>QWidget {
        background-color: rgb(245, 245, 245);
    }
    QLabel {
        /*font-family: Droid Sans Mono;*/
        font-size: 12px;
        color: rgb(15, 15, 15);
    }
    QScrollBar:vertical {              
        border: 1px solid #999999;
        background: white;
        width: 10px;    
        margin: 0px 0px 0px 0px;
    }
    QScrollBar::handle:vertical {
        background-color: rgb(200, 200, 200);
        border-radius: 2px;
        min-height: 5px;
    }
    QScrollBar::add-line:vertical {
        height: 0px;
        subcontrol-position: bottom;
        subcontrol-origin: margin;
    }
    QScrollBar::sub-line:vertical {
        height: 0 px;
        subcontrol-position: top;
        subcontrol-origin: margin;
    }
    """
    )

    gui = VersionWindow("C:\\Users\\Liam\\Google Drive\\Projects\\Small\\test-repo")
    sys.exit(app.exec_())


if __name__ == "__main__":
    launch()

