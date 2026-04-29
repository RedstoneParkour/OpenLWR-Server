import server.session_mgt as session_mgt
import threading
from server.devices import *
import device_usage_guide

session_mgr = None


def main():
    session_mgr = session_mgt.SessionManager("127.0.0.1", 1312)
    device1 = REGISTRY.add_device(device_usage_guide.SpinningMachine9000("spinning_machine9000", "placeholder_name"))
    threading.Thread(target=SessionManagerProcess, args=(session_mgr,)).start()
    threading.Thread(target=SessionManagerNonYeilding, args=(session_mgr,)).start()

def SessionManagerNonYeilding(session_mgr):
    while True:
        pass
def SessionManagerProcess(session_mgr):
    while True:
        session_mgr.Process()


if __name__ == '__main__':
    print("""   ____                   __ _       ______ 
  / __ \\____  ___  ____  / /| |     / / __ \\
 / / / / __ \\/ _ \\/ __ \\/ / | | /| / / /_/ /
/ /_/ / /_/ /  __/ / / / /__| |/ |/ / _, _/ 
\\____/ .___/\\___/_/ /_/_____/__/|__/_/ |_|  
    /_/                                     \n""")
    print("> Welcome to OpenLWR-Server")

    print("> Loading Config...")
    # Configuration.Load() # Assuming you have this implemented
    print("> Config Loaded")

    main()
