import server.session_mgt as session_mgt
import threading
import config as Configuration
from server.simulation import simulation
from server.example import simulation_module
from server.communication.ubc_communication import UBCChannel

session_mgr = None
simulation_context = None

def main():
    ubc_channel = UBCChannel("127.0.0.1")
    session_mgr = session_mgt.SessionManager("127.0.0.1", 1313, ubc_channel)


    # should i be doing this this way?
    simulation_context = simulation.SimulationContext()
    simulation_context.OnTick.on_changed += ubc_channel.broadcast
    simulation_context.AddModule(simulation_module.BlinkenLights())
    simulation_context.Start()

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

    Configuration.Load()

    print("> Config Loaded")

    main()