import numpy as np
from typing import Union, Optional
from dataclasses import dataclass
from abc import ABC
from enum import IntEnum
import hashlib
import server.protocols.ubc_pb2 as ubc_pb2
DeviceFieldValue = Union[str, int, float, bool, bytes]
@dataclass
class DeviceField:
    friendly_name: str
    field_id: int
    value: DeviceFieldValue
@dataclass
class StateChangeRequest:
    device_id: np.ulonglong
    field_id: int
    new_value: DeviceFieldValue

class StateChangeResult(IntEnum):
    OK = 0
    INVALID_FIELD = 1
    INVALID_VALUE = 2
    REJECTED = 3


class DeviceBase(ABC):
    def __init__(self, device_type: str, name: str):
        self._device_id = np.ulonglong(int(hashlib.sha256(name.encode()).hexdigest(), 16) % (2**64))
        self._device_type = device_type
        self._is_dirty = False
        self._fields: list[DeviceField] = []
        self._name = name
    @property
    def device_id(self) -> np.ulonglong:
        return self._device_id
    @property
    def device_type(self) -> str:
        return self._device_type
    @property
    def is_dirty(self) -> bool:
        return self._is_dirty
    @property
    def get_fields(self) -> list[DeviceField]:
        return list(self._fields)
    @property
    def device_name(self) -> str:
        return self._name

    def clear_dirty(self):
        self._is_dirty = False

    def get_field_by_id(self, field_id: int) -> Optional[DeviceField]:
        if field_id < 0 or field_id >= len(self._fields):
            print("field_id out of bounds", field_id)
            return None
        return self._fields[field_id]

    def get_field_by_name(self, name: str) -> Optional[DeviceField]:
        for field in self._fields:
            if field.friendly_name == name:
                return field
        print("Could not find field with name %s" % name)
        return None

    def set_field_value(
            self, field_id: int, new_value: DeviceFieldValue):
        field = self.get_field_by_id(field_id)
        if field is None:
            return StateChangeResult.INVALID_FIELD


        if not isinstance(new_value, type(field.value)):
            print("Wrong field type %d" % field_id)
            return StateChangeResult.INVALID_VALUE

        field.value = new_value
        self._is_dirty = True
        return StateChangeResult.OK

class DeviceRegistry:
    _instance: "DeviceRegistry" = None
    _devices: dict[np.ulonglong, "DeviceBase"]
    def __new__(cls) -> "DeviceRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._devices = {}
        return cls._instance

    def get_device(self, device_id: np.ulonglong) -> Optional[DeviceBase]:
        device_id = np.ulonglong(device_id)

        if device_id in self._devices:
            return self._devices[device_id]
        print("Could not find device with id %d" % device_id)
        return None

    def get_devices_by_type(self, device_type: str) -> list[DeviceBase]:
        result = []

        for device in self._devices.values():
            if device.device_type == device_type:
                result.append(device)
        if not result:
            print("Could not find device with type %s" % device_type)
        return result

    def get_dirty_devices(self) -> list[DeviceBase]:
        result = []

        for device in self._devices.values():
            if device.is_dirty:
                result.append(device)
        return result

    def add_device(self, device: DeviceBase) -> DeviceBase:
        device_object = device
        self._devices[device_object.device_id] = device_object
        return device_object


    def remove_device(self, device_id: np.ulonglong):
        device_id = np.ulonglong(device_id)
        if device_id in self._devices:
            self._devices.pop(device_id)
            print("Removed device with id %d" % device_id)
        else:
            print("Could not find device with id %d" % device_id)

    def request_states_change(self, req: StateChangeRequest) -> StateChangeResult | None:
        device = self.get_device(req.device_id)
        if device is not None:
            return device.set_field_value(req.field_id, req.new_value)
        return None

REGISTRY = DeviceRegistry() #the singleton, made it so that it won't let you make more


def on_interaction(client, message):
    interaction = message.interaction
    interaction_id = interaction.interaction_id
    interaction_type = interaction.interaction_type
    target_device_id = interaction.target_device
    device = REGISTRY.get_device(target_device_id)


    if device is None:
        print(f">Rejected Interaction #{interaction_id}: Invalid device ID {target_device_id}")
        # ack the client
        return
    if not interaction.data:
        print(f">Rejected Interaction #{interaction_id}: Empty payload")
        # ack the client
        return
    field = device.get_field_by_id(interaction_type)
    if field is None:
        print(f">Rejected Interaction #{interaction_id}: Unknown field ID {interaction_type} on device {target_device_id}")
        # ack the client
        return
    try:
        field_data = ubc_pb2.UBCMessage.Payload.Data()
        field_data.ParseFromString(interaction.data)
        value_type = field_data.WhichOneof("data")
        if value_type is None:
            print(f">Rejected Interaction #{interaction_id}: Payload has no value set")
            # ack the client
            return
        new_value = getattr(field_data, value_type)
    except Exception as e:
        print(f">Rejected Interaction #{interaction_id}: Failed to deserialize payload: {e}")
        # ack the client
        return


    req = StateChangeRequest(
        device_id=target_device_id,
        field_id=interaction_type,
        new_value=new_value,
    )
    result = REGISTRY.request_states_change(req)
    if result != StateChangeResult.OK:
        print(f">Rejected Interaction #{interaction_id}: State change failed with {result}")
        # ack the client
        return
    print(f">succesfully updated interaction #{interaction_id}")
    # ack the client
    # ----------------------------------
    # there are multiple "ack the client" becuase you must exit on a specific part of code or the rest will error
    # mmm i love the pycharm autocompleting the prints for me yumm!!