import manage
import time
import config

def control_loop():
    """
    Main program loop. Refers to state of files in target directory at regular (five
    second) intervals and stores any changes. 

    Arguments:
        dir_path (str): path of target directory
    """
    configure = config.ConfigManager()
    dir_path = configure.get_target_path()
    temp_path = configure.get_temp_path()
    interval = configure.get_interval()

    try:
        manager = manage.FileManager(dir_path, temp_path)
    except manage.InvalidDirectoryError:
        return

    while True:
        time.sleep(interval)
        interval = configure.get_interval()
        active = configure.get_active()
        if dir_path != configure.get_target_path():
            dir_path = configure.get_target_path()
            manager.set_target_directory(dir_path)
            print(f"Change to {dir_path}")
        if not active or not manager.has_changed():
            print(f"No changes (Active: {active})")
            continue
        changes = manager.store_changes()
        print(changes)


if __name__ == "__main__":
    control_loop()
