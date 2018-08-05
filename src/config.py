import configparser


class ConfigManager:

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_name = "config.ini"
        self.refresh()

    def refresh(self):
        self.config.read(self.config_name)

    def store(self):
        with open(self.config_name, "w") as f:
            self.config.write(f)

    def get_target_path(self):
        self.refresh()
        return self.config["DIRECTORIES"]["Target"]

    def get_temp_path(self):
        self.refresh()
        return self.config["DIRECTORIES"]["Temp"]
    
    def get_interval(self):
        self.refresh()
        return self.config["SETTINGS"].getint("CheckInterval")

    def get_active(self):
        self.refresh()
        return self.config["SETTINGS"].getboolean("Active")

    def set_interval(self, interval):
        """
        Sets interval to given value.

        Arguments:
            interval (int): new interval value
        """
        self.config["SETTINGS"]["CheckInterval"] = str(interval)
        self.store()
    
    def set_active(self, active):
        """
        Sets active state to given value.

        Arguments:
            active (bool): new active state
        """
        self.config["SETTINGS"]["Active"] = str(active)
        self.store()

    def set_target_path(self, dir_path):
        """
        Sets active state to given value.

        Arguments:
            active (bool): new active state
        """
        self.config["DIRECTORIES"]["target"] = dir_path
        self.store()
