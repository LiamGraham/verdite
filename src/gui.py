import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import os.path
import textwrap
from functools import partial
import configparser

import manage


class VersionWindow(QTabWidget):
    def __init__(self):
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

        config = configparser.ConfigParser()
        config.read("config.ini")
        dir_path = config["DIRECTORIES"]["Main"]
        temp_path = config["DIRECTORIES"]["Temp"]
        self.manager = manage.FileManager(dir_path, temp_path)
        
        self.init_window()

    def init_window(self):
        """
        Initialises the appearance of the window, including the file versions and
        settings tabs.
        """
        self.tab_names = ["Versions", "Settings", "About"]
        self.versions_tab = VersionsTab(self, self.manager)
        self.settings_tab = SettingsTab(self, self.manager)
        self.about_tab = AboutTab(self)
        self.addTab(self.versions_tab, self.tab_names[0])
        self.addTab(self.settings_tab, self.tab_names[1])
        self.addTab(self.about_tab, self.tab_names[2])

        self.setFixedSize(500, 500)
        self.setWindowTitle("View and Restore File Versions")
        self.setWindowIcon(QIcon("images\\icon_500px_transparent.png"))
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

    def set_current_tab(self, tab_name):
        """
        Set the current tab to the tab having the given name.

        Arguments:
            tab_name (str): name of tab to change to
        """
        if tab_name not in self.tab_names:
            return
        self.setCurrentIndex(self.tab_names.index(tab_name))

class AbstractTab(QWidget):
    """
    Abstract tab class containing general tab methods.
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

    def get_truncated_file_name(self):
        file_name = os.path.splitext(os.path.basename(self.current_file))[0]
        return (
            file_name[:15]
            + (file_name[15:] and "[...]")
            + os.path.splitext(self.current_file)[1]
        )

    def show_error_dialog(self, message):
        """
        Shows error dialog displaying the given message.
        """
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

    def remove_layout_contents(self, layout):
        for i in reversed(range(layout.count())):
            item = layout.takeAt(i)
            item.widget().deleteLater()
            del (item)

    def generate_separators(self, num):
        separators = []
        for i in range(0, num):
            separators.append(QFrame())
            separators[i].setFrameShape(QFrame.HLine)
            separators[i].setFrameShadow(QFrame.Plain)
        return separators


class VersionsTab(AbstractTab):
    """
    Tab containing version viewing and restoration interface.
    """

    def __init__(self, parent, manager):
        """
        Creates a new tab widget instance having the given parent and utilising the given
        manager.
        
        Arguments:
            parent (QWidget): parent of this widget
            manager (manage.FileManager): file management interface
        """
        super().__init__(parent, manager)
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
            self.status_label.setText(f"Refreshed '{file_name}'")
        else:
            self.status_label.setText(f"Loaded '{file_name}'")

    def view_version(self, version_num):
        try:
            self.manager.open_file_version(self.current_file, version_num)
            file_name = self.get_truncated_file_name()
            self.status_label.setText(f"Opened version {version_num} of '{file_name}'")
        except manage.VersionError as e:
            self.show_error_dialog(e.message)
            self.status_label.setText("")

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
            self.status_label.setText(
                f"Restored version {version_num} of '{file_name}' (now version {len(self.version_data)})"
            )
        except manage.VersionError as e:
            self.show_error_dialog(e.message)
            self.status_label.setText("")

    def set_status(self, message):
        self.status_label.setText(message)

    def add_version_rows(self):
        # Maximum length of version number, used for padding
        max_ver_length = len(str(len(self.version_data)))
        for i, x in enumerate(self.version_data):
            version_num = len(self.version_data) - i
            print(f"Version {version_num}: {x}")
            version_str = str(version_num).ljust(max_ver_length)
            row = QHBoxLayout()
            label = QLabel(
                f"Version {version_str} ({str(x.timestamp.strftime('%x %X'))})"
            )

            view_button = QPushButton("View")
            restore_button = QPushButton("Restore")

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
            self.status_label.setText("")
            return None

    def change_file(self):
        """
        Change the file being displayed to the one selected by the user using a file.
        """
        self.select_file()
        self.update_version_list(False)

    def add_no_files_row(self):
        no_files_row = QHBoxLayout()
        no_files_row.addWidget(QLabel("No file selected"))
        self.version_rows.append(no_files_row)
        self.version_layout.insertLayout(0, self.version_rows[0])

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

        version_container = QWidget()
        self.version_layout = QVBoxLayout()
        self.version_layout.addStretch()
        self.version_layout.setAlignment(Qt.AlignTop)
        self.add_no_files_row()
        version_container.setLayout(self.version_layout)

        scroll_area = QScrollArea()
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(version_container)
        scroll_area.setVerticalScrollBar(QScrollBar())

        grid.addWidget(self.file_text, 0, 0)
        grid.addWidget(file_button, 0, 2)
        grid.addWidget(scroll_area, 1, 0, 1, 3)

        bottom_row = QHBoxLayout()
        bottom_row.addWidget(refresh_button)
        bottom_row.addWidget(self.status_label)
        grid.addLayout(bottom_row, 2, 0, 1, 3)

        self.setLayout(grid)


class SettingsTab(AbstractTab):
    """
    Tab containing settings interface.

    - Select folder/s to be version controlled
    - Pause/start version control
    - Configure file types to be tracked (e.g. file category checkboxes, ignore list)
    - Set interval for storage of changes
    """

    def __init__(self, parent, manager):
        """
        Creates a new tab widget instance having the given parent and utilising the given
        manager.
        
        Arguments:
            parent (QWidget): parent of this widget
            manager (manage.FileManager): file management interface
        """
        super().__init__(parent, manager)
        self.config = configparser.ConfigParser()
        self.config_name = "config.ini"
        self.ignore_keywords = []
        self.init_layout()

    def init_layout(self):
        self.config.read(self.config_name)
        settings_layout = QVBoxLayout()
        settings_layout.setAlignment(Qt.AlignTop)

        general_layout = QHBoxLayout()
        general_layout.setAlignment(Qt.AlignLeft)
        folder_heading = QLabel("General")
        folder_heading.setObjectName("heading")
        folder_label = QLabel(f"Folder location:")
        dir_label = QLabel(self.manager.dir_path)
        dir_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        general_layout.addWidget(folder_label)
        general_layout.addWidget(dir_label)

        self.active_checkbox = QCheckBox("Track changes to files in this folder")
        self.active_checkbox.toggled.connect(self.toggle_active)
        self.checked_states = {True: Qt.Checked, False: Qt.Unchecked}
        initial_state = self.checked_states[
            self.config["SETTINGS"].getboolean("Active")
        ]
        self.active_checkbox.setCheckState(initial_state)

        interval_layout = QHBoxLayout()
        interval_layout.setAlignment(Qt.AlignLeft)
        interval_heading = QLabel("Change check interval")
        interval_heading.setObjectName("heading")
        interval_label = QLabel("Check for changes every:")
        self.interval_select = QSpinBox()
        self.interval_select.setFixedWidth(50)
        self.interval_select.setMinimum(5)
        self.interval_select.setMaximum(99999999)
        self.interval_select.setValue(self.config["SETTINGS"].getint("CheckInterval"))
        self.interval_select.valueChanged.connect(self.change_interval)
        seconds_label = QLabel("seconds")
        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.interval_select)
        interval_layout.addWidget(seconds_label)

        ignore_heading = QLabel("Tracking preferences")
        ignore_heading.setObjectName("heading")
        ignore_label = QLabel("Ignore files with these extensions:")

        ignore_container = QWidget()
        self.ignore_list_layout = QVBoxLayout()
        self.ignore_list_layout.addStretch()
        self.ignore_list_layout.setAlignment(Qt.AlignTop)
        ignore_container.setLayout(self.ignore_list_layout)

        scroll_area = QScrollArea()
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(ignore_container)
        scroll_area.setVerticalScrollBar(QScrollBar())

        ignore_add_layout = QHBoxLayout()
        ignore_add_layout.setAlignment(Qt.AlignLeft)
        self.ignore_entry = QLineEdit()
        self.ignore_entry.setObjectName("small")
        ignore_button = QPushButton("Add")
        ignore_button.clicked.connect(self.new_ignored)
        ignore_add_layout.addWidget(self.ignore_entry)
        ignore_add_layout.addWidget(ignore_button)
        self.ignore_rows = []

        self.update_ignored_list()

        separators = self.generate_separators(1)

        settings_layout.addWidget(folder_heading)
        settings_layout.addLayout(general_layout)
        settings_layout.addWidget(self.active_checkbox)
        settings_layout.addLayout(interval_layout)
        settings_layout.addWidget(separators[0])
        settings_layout.addWidget(ignore_heading)
        settings_layout.addWidget(ignore_label)
        settings_layout.addWidget(scroll_area)
        settings_layout.addLayout(ignore_add_layout)

        self.setLayout(settings_layout)

    def keyPressEvent(self, e):
        if self.focusWidget() is self.ignore_entry and e.key() == Qt.Key_Return:
            # 'Enter' key is pressed to add new ignore keyword
            self.new_ignored()

    def toggle_active(self):
        """
        Toggle if the files in the tracked directory are currently being tracked.
        """
        state = self.active_checkbox.isChecked()
        self.config["SETTINGS"]["Active"] = str(state)
        with open(self.config_name, "w") as f:
            self.config.write(f)

    def change_interval(self):
        """
        Change check interval to user-defined value.
        """
        interval = self.interval_select.value()
        self.config["SETTINGS"]["CheckInterval"] = str(interval)
        with open(self.config_name, "w") as f:
            self.config.write(f)

    def update_ignored_list(self):
        self.clear_ignored_list()
        ignored = self.manager.get_all_ignored()
        for x in ignored:
            self.add_ignored_row(x)

    def clear_ignored_list(self):
        for x in self.ignore_rows:
            self.remove_layout_contents(x)
            self.ignore_list_layout.removeItem(x)
            x.deleteLater()
            del (x)
        self.ignore_rows.clear()

    def new_ignored(self):
        """
        Add new ignore keyword entered by user.
        """
        keyword = self.parse_ignore_text()
        if not keyword or keyword in self.manager.get_all_ignored():
            return
        try:
            self.manager.add_ignored(keyword)
        except manage.IgnoreError as e:
            self.show_error_dialog(e.message)
            return
        self.update_ignored_list()
        self.ignore_entry.setText("")

    def add_ignored_row(self, keyword):
        """
        Add an ignore row containing the given ignore keyword. The keyword will be added
        to the persistent ignore list if it is new.

        Arguments: 
            keyword (str): ignore keyword
            new (boolean): True if given ignore keyword is new and to be added to
                persistent list
        """
        row_index = self.ignore_list_layout.count() - 1

        row = QHBoxLayout()
        text_label = QLabel(keyword.replace("*", "", 1))
        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(
            partial(self.remove_ignored_row, keyword)
        )
        row.addWidget(text_label)
        row.addWidget(remove_button)

        self.ignore_list_layout.insertLayout(row_index, row)
        self.ignore_rows.append(row)

    def parse_ignore_text(self):
        text = self.ignore_entry.text().strip()
        if not text:
            return ""
        file_ext = ""
        # Add initial '*.' and eliminate duplicate precending '.'s
        for i in range(0, len(text)):
            if text[i] != ".":
                file_ext = "*." + text[i:]
                break
        return file_ext

    def remove_ignored_row(self, keyword):
        """
        Remove ignore row having given keyword from list. 

        Arguments:
            keyword (str): keyword of row to be removed
        """
        try:
            self.manager.remove_ignored(keyword)
        except manage.IgnoreError as e:
            self.show_error_dialog(e.message)
            return
        self.update_ignored_list()


class AboutTab(AbstractTab):
    """
    Tab containing version viewing and restoration interface.
    """

    def __init__(self, parent):
        """
        Creates a new tab widget instance having the given parent and utilising the given
        manager.
        
        Arguments:
            parent (QWidget): parent of this widget
            manager (manage.FileManager): file management interface
        """
        super().__init__(parent, None)
    
    def init_layout(self):
        about_layout = QVBoxLayout()
        about_layout.setAlignment(Qt.AlignTop)

        license_label = QLabel("License")
        license_label.setObjectName("heading")

        about_layout.addWidget(license_label)
        self.setLayout(about_layout)


class SystemTrayIcon(QSystemTrayIcon):

    def __init__(self, parent):
        self.parent = parent
        icon = QIcon("images\\icon_500px_transparent.png")
        super(QSystemTrayIcon, self).__init__(icon, parent)
        self.init_context_menu()
        self.show()

    def init_context_menu(self):
        menu = QMenu(self.parent)
        versionsAction = menu.addAction("View versions")
        versionsAction.triggered.connect(self.view_versions)
        settingsAction = menu.addAction("Settings")
        settingsAction.triggered.connect(self.settings)
        self.setContextMenu(menu)

    def view_versions(self):
        self.parent.showNormal()
        self.parent.set_current_tab("Versions")

    def settings(self):
        self.parent.showNormal()
        self.parent.set_current_tab("Settings")


def launch():
    app = QApplication(sys.argv)
    with open("style.qss", "r") as f:
        app.setStyleSheet(f.read())
    gui = VersionWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    launch()
