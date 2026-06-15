import server.session_mgt as session_mgt
import threading
import config as Configuration
from server.simulation import simulation
from server.example import simulation_module

simulation_context = None
session_mgr = None

def main():
    session_mgr = session_mgt.SessionManager("127.0.0.1",1312)
    session_mgt.SESSION_MANAGER = session_mgr


    # should i be doing this this way?
    simulation_context = simulation.SimulationContext()
    simulation_context.OnTick.on_changed += session_mgr.BroadcastUBC
    simulation_context.AddModule(simulation_module.BlinkenLights())
    simulation_context.Start()

    #this is a lot of threads?
    threading.Thread(target=SessionManagerProcessUBC, args=(session_mgr,)).start()
    threading.Thread(target=SessionManagerProcess, args=(session_mgr,)).start()
    threading.Thread(target=SessionManagerNonYeilding, args=(session_mgr,)).start()


def SessionManagerNonYeilding(session_mgr:session_mgt.SessionManager):
    while True:
        session_mgr.Process_NoYield()


def SessionManagerProcess(session_mgr:session_mgt.SessionManager):
    while True:
        session_mgr.Process()

def SessionManagerProcessUBC(session_mgr:session_mgt.SessionManager):
    while True:
        session_mgr.ProcessUBC()


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