import socket
import threading
import server.protocols.ubc_pb2 as ubc_proto
import server.devices as devices

class UBCChannel:
    def __init__(self, ip: str):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((ip, 0))
        self.clients: dict[int, tuple] = {}
        self.lock = threading.Lock()

    def register(self, session_id: int, address: tuple):
        with self.lock:
            self.clients[session_id] = address

    def unregister(self, session_id: int):
        with self.lock:
            self.clients.pop(session_id, None)

    def broadcast(self, tick_context):
        dirty = devices.REGISTRY.get_dirty_devices()
        if not dirty:
            return

        payloads = []
        for device in dirty:
            payload = ubc_proto.UBCMessage.Payload()
            payload.device_id = int(device.device_id)
            for field in device.get_fields:
                data = ubc_proto.UBCMessage.Payload.Data()
                data.field = field.field_id
                val = field.value
                if isinstance(val, bool):
                    data.bool_value = val
                elif isinstance(val, int):
                    data.int_value = val
                elif isinstance(val, float):
                    data.float_value = val
                elif isinstance(val, str):
                    data.string_value = val
                elif isinstance(val, bytes):
                    data.bytes_value = val
                payload.data_fields.append(data)
            payloads.append(payload)
            device.clear_dirty()

        with self.lock:
            clients = dict(self.clients)

        for session_id, addr in clients.items():
            msg = ubc_proto.UBCMessage()
            msg.header.magic_number = 4482
            msg.header.protocol_version = 1
            msg.tick = int(tick_context.TickIndex)
            msg.session_id = session_id
            msg.payloads.extend(payloads)
            self.socket.sendto(msg.SerializeToString(), addr)
