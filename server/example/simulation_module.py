from server.simulation import simulation
from server import devices

class SBMBreaker(devices.DeviceBase):
    def __init__(self, name: str):
        super().__init__(device_type="SBMBreaker",name=name)
        self._fields = [devices.DeviceField("Position",0,1),devices.DeviceField("Flag",1,1)]

    def on_interaction(self, interaction_id, interaction_type, data):
        self.set_field_value(data.field,getattr(data,data.WhichOneof("data")))






class BlinkenLights(simulation.SimulationModule):
    def __init__(self):
        super().__init__()
        self.LPCS_Pump = SBMBreaker("LPCS_Pump")
        devices.REGISTRY.add_device(self.LPCS_Pump)

    def OnTick(self,world:simulation.SimulationContext,ctx:simulation.TickContext):

        #print(f"executed. dt:{ctx.Delta} elapsed:{ctx.Elapsed} ")
        #store some data
        print(devices.REGISTRY.get_device(self.LPCS_Pump.device_id).get_field_by_id(0))
        self.LPCS_Pump.set_field_value(0, 1)






