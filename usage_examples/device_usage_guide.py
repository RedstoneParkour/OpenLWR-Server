from server.devices import DeviceBase, DeviceField, StateChangeRequest, StateChangeResult, REGISTRY


class SpinningMachine9000(DeviceBase):
    def __init__(self, device_type: str, device_name: str):
        super().__init__(device_type, device_name) #make sure devices don't have the same name
        self.field_ids = {"spins/s": 0}
        self._fields = [DeviceField("spins/s", self.field_ids["spins/s"], 0)] #make sure field id = field index

device1 = REGISTRY.add_device(SpinningMachine9000("spinning_machine9000", "placeholder_name")) #make device : returns device object
req = StateChangeRequest(device1.device_id, 0, 9000)# make req by entering device id, field id, new value
print(device1.get_field_by_id(0))
statechangeresult = REGISTRY.request_states_change(req)#request using the request
print(device1.get_field_by_id(0))
print(statechangeresult, ' "0" is OK') #you can view the state change result by making the request a variable
print(device1.device_type)
print(device1.device_name)
# you can look at devices.py for what functions you can use, you can also report to jawo_o for help or bugs 😊 (only for devs 😠)
