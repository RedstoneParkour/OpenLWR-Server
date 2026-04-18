import numpy as np
from devices import DeviceBase, DeviceField, StateChangeRequest, StateChangeResult, registry


class spinning_machine9000(DeviceBase):
    def __init__(self):
        super().__init__("spinning_machine9000")
        self.FIELDID_SPINS = 0   # int
        self._fields = [DeviceField("spins/s", self.FIELDID_SPINS, 0)]


    def handle_request(self, req: StateChangeRequest) -> int: #this returns int becuase it just takes the number from statechangeresults when returning it instead of returning the statechange then the devices.py coorelate it to a number man what bullshit is this
        if req.field_id == self.FIELDID_SPINS:
            if not isinstance(req.new_value, int):
                return StateChangeResult.INVALID_VALUE
            if req.new_value < 0:
                return StateChangeResult.REJECTED  # cant goon backwards
            return self._set_field_value(self.FIELDID_SPINS, req.new_value)
        return StateChangeResult.INVALID_FIELD

id1 = registry.add_device(spinning_machine9000())
id2 = registry.add_device(spinning_machine9000())
id3 = registry.add_device(spinning_machine9000())
device1 = registry.get_device(id1)
device2 = registry.get_device(id2)
device3 = registry.get_device(id3)
print(id1, id2, id3)
print(device1.device_id, device2.device_id, device3.device_id)
print(device1.device_type)
print(device1.device_id)
print(device1.is_dirty)
print(device1.get_fields)
# the bitween bigger than smaller than (<>) are placeholders
# usage guide, copy boilerplate i made(spinning_machine9000), change name, add self,<random_tempname>(field_id) = <feild_id>
# add self._feilds = [DeviceFeild("friendly name", <randomtempname>, initial state)]
# change handle_request as you may like
# <device_id> = registry.add_device(<class name of your device class)>())
# <device_object> = registry.get_device(<device_id>)
# you can look at devices.py for what functions you can use, you can also report to jawo_o for help or bugs 😊 (only for devs 😠)
