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
    config.read("config.ini")
    dir_path = config["DIRECTORIES"]["Main"]
    temp_path = config["DIRECTORIES"]["Temp"]
    interval = int(config["SETTINGS"]["CheckInterval"])

    try:
        manager = manage.FileManager(dir_path, temp_path)
    except manage.InvalidDirectoryError:
        return

    while True:
        time.sleep(interval)
        config.read("config.ini")
        interval = int(config["SETTINGS"]["CheckInterval"])
        if not manager.has_changed():
            print("No changes")
            continue
        print(manager.store_changes())


if __name__ == "__main__":
    control_loop()
