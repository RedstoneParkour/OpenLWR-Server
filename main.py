import server.session_mgt as session_mgt
import threading
import config as Configuration

def main():
    session_mgr = session_mgt.SessionManager("127.0.0.1",1312)

    threading.Thread(target=SessionManagerProcess,args=(session_mgr,)).start()
    threading.Thread(target=SessionManagerNonYeilding,args=(session_mgr,)).start()

def SessionManagerNonYeilding(session_mgr):
    while True:

        session_mgr.Retransmission()

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

    Configuration.Load()

    print("> Config Loaded")

    main()
