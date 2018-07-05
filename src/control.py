import manage
import time
import configparser


def control_loop():
    """
    Main program loop. Refers to state of files in target directory at regular (five
    second) intervals and stores any changes. 

    Arguments:
        dir_path (str): path of target directory
    """
    config = configparser.ConfigParser()
    config_name = "config.ini"
    config.read(config_name)
    dir_path = config["DIRECTORIES"]["Main"]
    temp_path = config["DIRECTORIES"]["Temp"]
    interval = config["SETTINGS"].getint("CheckInterval")

    try:
        manager = manage.FileManager(dir_path, temp_path)
    except manage.InvalidDirectoryError:
        return

    while True:
        time.sleep(interval)
        config.read(config_name)
        interval = config["SETTINGS"].getint("CheckInterval")
        active = config["SETTINGS"].getboolean("Active")
        if not active or not manager.has_changed():
            print(f"No changes (Active: {active})")
            continue
        changes = manager.store_changes()
        print(changes)


if __name__ == "__main__":
    control_loop()
