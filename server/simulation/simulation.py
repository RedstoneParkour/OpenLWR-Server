import numpy as np
from enum import Enum
from events import Events
from abc import ABC
import time
import threading

class SimulationState(Enum):
    Created = 0,
    Running = 1,
    Paused = 2,
    Stopped = 3,

class TickContext:
    TickIndex: np.ulonglong = 0
    Delta: np.double = 0
    Elapsed: np.double = 0



class SimulationModuleData(ABC):
    pass

class SimulationContext:
    def __init__(self):
        self.OnModuleRegister = Events()
        self.OnTick = Events() #whats the point?
        self.OnModuleUnregister = Events()

        self.Name = ""
        self.TickContext = TickContext()
        self.State = SimulationState.Created
        self.TickRate = 0.1 #60fps

        self.Modules = []
        self.SimulationThread = None

    def Execute(self):
        #execute modules
        dt = 0
        while self.State != SimulationState.Stopped:
            StartTime = time.perf_counter()

            self.TickContext.Delta = dt
            self.TickContext.Elapsed += dt
           

            for module in self.Modules:
                if module.NextEvalStep == 0:
                    module.OnTick(self,self.TickContext)
                elif module.NextEvalStep > 0: #only decrement when greater than 0, so modules can disable themselves at -1
                    module.NextEvalStep -= 1

            self.OnTick.on_changed(self.TickContext)
            self.TickContext.TickIndex += 1

            EndTime = time.perf_counter()
            delta = EndTime-StartTime

            if delta < self.TickRate:
                time.sleep(self.TickRate-delta)
            else:
                print(f">Simulation cannot keep up! dT:{delta}, TickRate:{self.TickRate}")

            dt = time.perf_counter() - StartTime #one last time to get total d/t


    def AddModule(self,module):
        
        self.Modules.append(module)
        module.OnRegister(self)
        self.OnModuleRegister.on_change(module)


    def RemoveModule(self,module):

        self.OnModuleUnregister.on_change(module)
        module.OnUnregister(self)
        self.Modules.remove(module)
        

    def Start(self):
        if self.State != SimulationState.Created:
            return
        
        self.SimulationThread = threading.Thread(target=self.Execute).start()
        self.State = SimulationState.Running

    def Stop():
        pass 

    def Pause():
        pass

    def Resume():
        pass


class SimulationModule: #base simulation module, i think we can super this guy
    def __init__(self):
        self.NextEvalStep = 0
        self.Data = SimulationModuleData()

    def OnRegister(self,world:SimulationContext):
        pass

    def OnTick(self,world:SimulationContext,ctx:TickContext):
        pass

    def OnUnregister(self,world:SimulationContext):
        pass

    def SetNextEvalStep(self,tickIndex:np.ulonglong):
        self.NextEvalStep=tickIndex