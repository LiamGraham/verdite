import manage
import time

def control_loop():
    manager = manage.FileManager("C:\\Users\\Liam\\Google Drive\\Projects\\Small\\test-repo")
    while True:
        time.sleep(5)
        if not manager.has_changed():
            print("No changes")
            continue
        print(manager.store_changes())

if __name__ == "__main__":
    control_loop()