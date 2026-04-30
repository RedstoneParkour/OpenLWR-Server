import numpy as np
from enum import Enum
from events import Events
from abc import ABC

class SimulationState(Enum):
    Created = 0,
    Running = 1,
    Paused = 2,
    Stopped = 3,

class TickContext:
    TickIndex: np.ulonglong
    Delta: np.double
    Elapsed: np.double


class SimulationModuleData(ABC): #i'm not sure what to do with this yet, its probably just where all simulation module data should go so its neatly packaged in something to send over
    pass

class SimulationContext:
    def __init__(self):
        self.OnModuleRegister = Events()
        self.OnTick = Events()
        self.OnModuleUnregister = Events()

        self.Name = ""
        self.TickContext = TickContext()
        self.State = SimulationState.Created

    def AddModule(module:SimulationModule):
        pass

    def RemoveModule(module:SimulationModule):
        pass

    def Start():
        pass

    def Stop():
        pass


class SimulationModule: #base simulation module, i think we can super this guy
    def __init__(self,NextEvalStep:np.ulonglong):
        self.NextEvalStep = NextEvalStep

    def OnRegister(self,world:SimulationContext):
        pass

    def OnTick(self,world:SimulationContext,data:SimulationModuleData,ctx:TickContext):
        pass

    def OnUnregister(self,world:SimulationContext):
        pass

    def SetNextEvalStep(self,tickIndex:np.ulonglong):
        self.NextEvalStep=tickIndex