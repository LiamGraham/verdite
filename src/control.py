import manage

manager = manage.FileManager("C:\\Users\\Liam\\Google Drive\\Projects\\Small\\test-repo")

def control_loop():
    while True:
        if not manager.has_changed():
            continue
        print(manager.store_changes())

if __name__ == "__main__":
    control_loop()