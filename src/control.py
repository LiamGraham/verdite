import manage
import time


def control_loop(dir_path):
    """
    Main program loop. Refers to state of files in target directory at regular (five
    second) intervals and stores any changes. 

    Arguments:
        dir_path (str): path of target directory
    """
    try:
        manager = manage.FileManager(dir_path)
    except manage.InvalidDirectoryError:
        return

    while True:
        time.sleep(5)
        if not manager.has_changed():
            print("No changes")
            continue
        print(manager.store_changes())


if __name__ == "__main__":
    control_loop("C:\\Users\\Liam\\Google Drive\\Projects\\Small\\test-repo")
