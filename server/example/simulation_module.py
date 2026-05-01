from server.simulation import simulation

class BlinkenLights(simulation.SimulationModule):
    def __init__(self):
        super().__init__()

    def OnTick(self,world:simulation.SimulationContext,ctx:simulation.TickContext):
        #make some lights blink, for now since i cant be bothered to add the devices i will just print some stuff
        print(f"executed. dt:{ctx.Delta} elapsed:{ctx.Elapsed} ")
        #store some data
        self.Data.TestValue = True

class PrintAfter5(simulation.SimulationModule):
    def __init__(self):
        super().__init__()

    def OnRegister(self, world):
        self.SetNextEvalStep(300) #set initial wait until execution

    def OnTick(self,world:simulation.SimulationContext,ctx:simulation.TickContext):
        print("no way")

        #could set eval step here as well to make a module run slower


#quick test

SimContext = simulation.SimulationContext()

SimContext.AddModule(BlinkenLights())
SimContext.AddModule(PrintAfter5())

SimContext.Start()
