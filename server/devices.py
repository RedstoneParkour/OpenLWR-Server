import numpy as np
from typing import Union, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
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

class StateChangeResult:
    OK = 0
    INVALID_FIELD = 1
    INVALID_VALUE = 2
    REJECTED = 3


class DeviceBase(ABC):
    def __init__(self, device_type: str):
        self._deviceid = np.ulonglong(0)
        self._devicetype = device_type
        self._isdirty = False
        self._fields: list[DeviceField] = []
    @property
    def device_id(self) -> np.ulonglong:
        return self._deviceid
    @property
    def device_type(self) -> str:
        return self._devicetype
    @property
    def is_dirty(self) -> bool:
        return self._isdirty
    @property
    def get_fields(self) -> list[DeviceField]:
        return list(self._fields)

    def clear_dirty(self):
        self._isdirty = False

    def get_field_by_id(self, field_id: int) -> Optional[DeviceField]:
        for field in self._fields:
            if field.field_id == field_id:
                return field
        print("Could not find field with id %d" % field_id)
        return None

    def get_field_by_name(self, name: str) -> Optional[DeviceField]:
        for field in self._fields:
            if field.friendly_name == name:
                return field
        print("Could not find field with name %s" % name)
        return None

    def _set_field_value(
            self, field_id: int, new_value: DeviceFieldValue):
        field = self.get_field_by_id(field_id)

        if field is None:
            print("Could not find field with id %d" % field_id)
            return StateChangeResult.INVALID_FIELD


        if not isinstance(new_value, type(field.value)):
            print("Wrong feild type %d" % field_id)
            return StateChangeResult.INVALID_VALUE

        field.value = new_value
        self._isdirty = True
        return StateChangeResult.OK

    @abstractmethod
    def handle_request(self, req: StateChangeRequest) -> StateChangeResult:
        pass

class DeviceRegistry:
    _instance: Optional["DeviceRegistry"] = None
    _devices: dict[np.ulonglong, "DeviceBase"]
    def __new__(cls) -> "DeviceRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._devices = {}
        assert cls._instance is not None
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
                result.append(device.device_id)
        return result

    def add_device(self, device: DeviceBase) -> np.ulonglong:
        # find the next unoccupied id
        new_id = np.ulonglong(0)
        while new_id in self._devices:
            new_id = np.ulonglong(new_id + 1)
        self._devices[new_id] = device
        device._deviceid = new_id
        print("Added device with id %d" % new_id)
        return new_id


    def remove_device(self, device_id: np.ulonglong):
        device_id = np.ulonglong(device_id)
        if device_id in self._devices:
            self._devices.pop(device_id)
            print("Removed device with id %d" % device_id)
        else:
            print("Could not find device with id %d" % device_id)
registry = DeviceRegistry() #the singletron, made it so that it wont let you make more