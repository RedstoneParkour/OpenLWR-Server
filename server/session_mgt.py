import numpy as np
from enum import Enum
import socket
from google.protobuf import message
import server.protocols.common_pb2 as common_proto
import server.protocols.rec_pb2 as rec_proto
import server.protocols.ubc_pb2 as ubc_proto
from server.communication.rec_communication import RecCommunication,RecStatus
from server.communication.ubc_communication import UbcCommunication
import config
import time
from events import Events
import threading
import server.devices as devices
import struct
rec_communication = RecCommunication()
ubc_communication = UbcCommunication()

class SessionManager:
    def __init__(self,ip:str,port:int):
        self.SessionRegistry = SessionRegistry()
        self.SocketRec = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.SocketUbc = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.SocketUbc.bind((ip,port))
        
        self.SocketRec.setsockopt(socket.SOL_SOCKET,socket.SO_LINGER, struct.pack('ii',1,config.config["rec_linger"]))

        self.SocketRec.bind((ip,port+1))
        self.SocketRec.listen()
        print("> Listening for clients on "+ip+":"+str(port))

        self.OnChannelRegistration = Events()
        self.OnInteraction = Events()  # go to devices
        self.OnEvent = Events()  # go somewhere idk
        self.OnInteraction.on_changed += devices.on_interaction

        self.counter_sessionid = 1 #start at 1 to prevent giving out session ID 0



    def ProcessDataRec(self,data,address):

        recmessage = rec_proto.RECMessage()

        recmessage.ParseFromString(data)

        client = None
        Sessions = self.SessionRegistry.GetAll()
        for SessionN in Sessions:
            Ses = Sessions[SessionN]
            IsClient = Ses.RecSession.IsThisMyClient(address)
            if IsClient:
                client = Ses.RecSession
                break

        if (recmessage.type != rec_proto.RECMessageType.REC_HANDSHAKE and recmessage.type != rec_proto.RECMessageType.REC_SERVER_INFO_REQUEST) and client.State != SessionState.Active:
            client.Send(rec_communication.CreateRecSessionClose(rec_proto.RECSessionClose.Reason.PROTOCOL_ERROR,"Unregistered client sent wrong packet"))
            return
        elif recmessage.type == rec_proto.RECMessageType.REC_HANDSHAKE and client.State == SessionState.Active:
            client.Send(rec_communication.CreateRecSessionClose(rec_proto.RECSessionClose.Reason.PROTOCOL_ERROR,"Registered client attempted to handshake"))
            return

        match recmessage.type:

            #TODO: verification types for password access
            case rec_proto.RECMessageType.REC_HANDSHAKE:
                if client.OnHandshake(recmessage,self.counter_sessionid):

                    ClientSession = self.SessionRegistry.Find(address)
                    ClientSession.Username = recmessage.handshake.username
                    ClientSession.RecSession.MinorVersion = recmessage.handshake.client_minor_version

                    ClientSession.RecSession.State = SessionState.Active #declare connection active
                else:  #if we reject them, we just delete their session
                    self.SessionRegistry.Remove(self.SessionRegistry.Find(address).RecSession.SessionId)

            
            case rec_proto.RECMessageType.REC_EVENT:
                self.OnEvent.on_changed(recmessage)

            case rec_proto.RECMessageType.REC_INTERACTION:
                self.OnInteraction.on_changed(client, recmessage)

            case rec_proto.RECMessageType.REC_REGISTER_SESSION:
                client_ip = client.ClientAddress[0]
                self.ubc_channel.register(client.SessionId, (client_ip, 1312))

            case rec_proto.RECMessageType.REC_SERVER_INFO_REQUEST: #no registration required
                msg = rec_communication.RecServerInfo()
                client.Send(msg)
                
    def ProcessDataUBC(self,data,address):
        Heartbeat = common_proto.Heartbeat()

        try: 
            Heartbeat.ParseFromString(data)
        except message.DecodeError:
            #TODO: disconnect client
            print(f"> Invalid or malformed packet sent to UBC from {address}")

        #add response time
        Heartbeat.response_timestamp = int(time.time())


        if Heartbeat.session_id == 0:
            self.SocketUbc.sendto(Heartbeat.SerializeToString(),address)
        else:
            Session = self.SessionRegistry.Get(Heartbeat.session_id)
            if Session == None:
                #TODO: disconnect client
                print(f"> Client specified a session Id while no such session exists")
            else:
                Session.UbcSession.Send(Heartbeat)
        

    def BroadcastUBC(self,tick_context):
        #broadcast dirty devices
        dirty = devices.REGISTRY.get_dirty_devices()
        if not dirty:
            return

        payloads = []
        for device in dirty:
            payload = ubc_communication.CreatePayloadFromDevice(device)
            payloads.append(payload)
            device.clear_dirty()

        Sessions = self.SessionRegistry.GetAll()
        for SessionN in Sessions:
            Ses = Sessions[SessionN]
            if Ses.UbcSession.State == SessionState.Active:
                Ses.UbcSession.Send()

    def Process(self):
        #REC
        conn, addr = self.SocketRec.accept()

        #i dont like how i did this but it works
        def ConnectionManager(connection,address):
            with connection:
                #create a session and rec connection, and register that with session manager
                print("servicing new connection") #TODO: this is a temporary print, we can remove this later

                rec_connection = RecConnection(ClientAddress=address,Client=connection,SessionId=self.counter_sessionid) # we will edit all of this later when we handshake
                self.counter_sessionid += 1 #this will never decrease
                user_session = Session(rec_connection)
                self.SessionRegistry.Add(user_session)


                #receive data and process
                while True:
                    data = connection.recv(1048)
                    self.ProcessDataRec(data,address)

        threading.Thread(target=ConnectionManager,args=(conn,addr)).start()     

    def ProcessUBC(self):
        data,addr = self.SocketUbc.recvfrom(1024)
        self.ProcessDataUBC(data,addr)

    def Process_NoYield(self):

        Sessions = self.SessionRegistry.GetAll()
        for SessionN in Sessions:
            Ses = Sessions[SessionN]

            if Ses.RecSession.State == SessionState.Connecting:
                if time.time()-Ses.RecSession.CreationTime >= config.config["pre_verification_time"]:
                    Ses.RecSession.Send(rec_communication.CreateRecSessionClose(rec_proto.RECSessionClose.Reason.TIMEOUT,"Exceeded pre-verifcation timeout threshold."))
                    Ses.RecSession.Client.close()
                    self.SessionRegistry.Remove(Ses.RecSession.SessionId)

            


    def CloseServer(self,reason:str):

        self.SocketRec.close()

class SessionState(Enum):
    Connecting = 0,
    Active = 1,
    Closed = 2,


class Connection:
    def __init__(self,SessionId:np.uint32,MinorVersion:np.uint32,State:SessionState,ClientAddress:tuple):
        self.SessionId = SessionId
        self.MinorVersion = MinorVersion
        self.State = State
        self.ClientAddress = ClientAddress #ip:port

        self.OnMessage = Events()
        self.OnConnection = Events()
        self.OnClose = Events()

    def IsThisMyClient(self,ClientAddress:tuple):
        return self.ClientAddress[0] == ClientAddress[0] and self.ClientAddress[1] == ClientAddress[1]

    def Send(self,message):
        pass

class UbcConnection(Connection):
    def __init__(self,SessionId:np.uint32,MinorVersion:np.uint32,State:SessionState,ClientAddress:tuple):
        super().__init__(SessionId,MinorVersion,State,ClientAddress)

    def Subscribe(connection:Connection):
        pass

    def Unsubscribe(connection:Connection):
        pass

    def Send(self,message):
        SESSION_MANAGER.SocketUbc.sendto(message.SerializeToString(),self.ClientAddress)

class RecConnection(Connection): 
    def __init__(self,Client,SessionId:np.uint32=-1,MinorVersion:np.uint32=-1,State:SessionState=SessionState.Connecting,ClientAddress:tuple=None):
        super().__init__(SessionId,MinorVersion,State,ClientAddress)

        self.Client = Client #we have to have this because tcp is special i guess
        self.CreationTime = time.time()

    def OnHandshake(self, message, session_id):
        Status, msg = rec_communication.RecHandshake(message, session_id)#temporary magic number
        
        self.Send(msg)
        return Status == RecStatus.OK
    
    def Send(self,message):
        self.Client.send(message.SerializeToString())



class Session:
    def __init__(self,RecSession:Connection,UbcSession:Connection=None,UecSession:Connection=None,Username:str="Test"):
        self.RecSession = RecSession
        self.UbcSession = UbcSession
        self.UecSession = UecSession
        self.Username = Username

    def IsThisMyClient(self,ClientAddress:tuple):
        if self.RecSession != None:
            if self.RecSession.IsThisMyClient(ClientAddress):
                return True, self.RecSession
        
        if self.UbcSession != None:
            if self.UbcSession.IsThisMyClient(ClientAddress):
                return True, self.UbcSession
        
        if self.UecSession != None:
            if self.UecSession.IsThisMyClient(ClientAddress):
                return True, self.UecSession
            
        return False, None

    

class SessionRegistry:
    def __init__(self):
        self.sessions = {}

    def Get(self,sessionId:np.uint32):
        try:
            return self.sessions[sessionId] 
        except:
            return None

    def GetAll(self):
        return self.sessions

    def Add(self,session:Session):
        self.sessions[session.RecSession.SessionId] = session

    def Remove(self,sessionId:np.uint32):
        self.sessions.pop(sessionId)

    def Find(self,address:tuple):
        for v in self.sessions:
            IsSession, Session = self.sessions[v].IsThisMyClient(address)

            if IsSession:
                return self.sessions[v]
            
SESSION_MANAGER = None
