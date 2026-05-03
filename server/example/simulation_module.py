from server.simulation import simulation
from server import devices

class SBMBreaker(devices.DeviceBase):
    def __init__(self, name: str):
        super().__init__(device_type="SBMBreaker",name=name)
        self._fields = [devices.DeviceField("Position",0,1),devices.DeviceField("Flag",1,1)]

    def on_interaction(self, interaction_id, interaction_type, data):
        self.set_field_value(data.field,getattr(data,data.WhichOneof("data")))

class Indicator(devices.DeviceBase):
    def __init__(self, name: str):
        super().__init__(device_type="Indicator",name=name)
        self._fields = [devices.DeviceField("Lit",0,False)]



class BlinkenLights(simulation.SimulationModule):
    def __init__(self):
        super().__init__()
        self.LPCS_Pump = SBMBreaker("LPCS_Pump")
        self.LPCS_Off = Indicator("LPCS_Off")
        self.LPCS_On = Indicator("LPCS_On")
        devices.REGISTRY.add_device(self.LPCS_Pump)
        devices.REGISTRY.add_device(self.LPCS_Off)
        devices.REGISTRY.add_device(self.LPCS_On)
        self.PumpState = False

    def OnTick(self,world:simulation.SimulationContext,ctx:simulation.TickContext):

        #print(f"executed. dt:{ctx.Delta} elapsed:{ctx.Elapsed} ")
        if devices.REGISTRY.get_device(self.LPCS_Pump.device_id).get_field_by_id(0).value == 2:
            self.PumpState = True
        elif devices.REGISTRY.get_device(self.LPCS_Pump.device_id).get_field_by_id(0).value == 0:
            self.PumpState = False

        self.LPCS_Off.set_field_value(0, not self.PumpState)
        self.LPCS_On.set_field_value(0, self.PumpState)







