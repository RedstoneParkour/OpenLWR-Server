import numpy as np
import server.protocols.rec_pb2 as rec_proto
import time
from enum import Enum

class RecStatus(Enum):
    OK = 0,
    REJECTED = 1,
    UNKNOWN = 2,

class RecCommunication:
    def __init__(self):
        pass
        
    def CreateDefaultRecMessage(self,message_type:rec_proto.RECMessageType):
        msg = rec_proto.RECMessage()
        msg.header.magic_number = 4482
        msg.header.protocol_version = 1
        msg.type = message_type
        return msg
    
    def CreateRecSessionClose(self,reason:rec_proto.RECSessionClose.Reason,message:str):
        #make the close message
        closemsg = rec_proto.RECSessionClose()
        closemsg.reason = reason
        closemsg.message = message

        #make a default rec message, and add the close message as a payload
        def_message = self.CreateDefaultRecMessage(rec_proto.RECMessageType.REC_SESSION_CLOSE)
        def_message.session_close.CopyFrom(closemsg)
        return RecStatus.OK, def_message
      
    def CreateRecHandshakeAck(self,session_id):
        #make the ack message
        msg = rec_proto.RECHandshakeAck()
        msg.session_id = session_id

        msg.server_tick = 0 #TODO: implement tick
        msg.server_time = int(time.time()) #TODO: Make uptime in seconds (int)

        #make a default rec message, and add the message as a payload
        def_message = self.CreateDefaultRecMessage(rec_proto.RECMessageType.REC_HANDSHAKE_ACK)
        def_message.handshake_ack.CopyFrom(msg)

        return RecStatus.OK, def_message

    def CreateRecEvent(self,data:bytes):
        msg = rec_proto.RECEvent()
        msg.data = data

        def_message = self.CreateDefaultRecMessage(rec_proto.RECMessageType.REC_EVENT)
        def_message.event.CopyFrom(msg)
        return RecStatus.OK, def_message


    def RecHandshake(self,data):
        major_ver = data.handshake.client_major_version

        Status = RecStatus.UNKNOWN

        #TODO: change major and minor version to be configurable
        if major_ver != 1:
            msg = self.CreateRecSessionClose(rec_proto.RECSessionClose.Reason.VERSION_MISMATCH,"Server requires major version 1")
            Status = RecStatus.REJECTED
        else:
            msg = self.CreateRecHandshakeAck()
            Status = RecStatus.OK
        
        return Status,msg