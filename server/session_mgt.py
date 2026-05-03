import numpy as np
from enum import Enum
import socket
import server.protocols.rec_pb2 as rec_proto
from server.communication.rec_communication import RecCommunication,RecStatus
import config
import time
from events import Events
import threading
import server.devices as devices
rec_communication = RecCommunication()

class SessionManager:
    def __init__(self,ip:str,port:int):
        self.SessionRegistry = SessionRegistry()
        self.SocketRec = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        
        self.SocketRec.bind((ip,port))
        self.SocketRec.listen()
        print("> Listening for clients on "+ip+":"+str(port))

        self.OnChannelRegistration = Events()
        self.OnInteraction = Events()  # go to devices
        self.OnEvent = Events()  # go somewhere idk
        self.OnInteraction.on_changed += devices.on_interaction
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

        #some sanity checking
        #if recmessage.type != rec_proto.RECMessageType.REC_HANDSHAKE and client == None:
        #    self.SendMessage(address,self.RecCommunciation.CreateRecSessionClose(rec_proto.RECSessionClose.Reason.PROTOCOL_ERROR,"Unregistered client attempted to negotiate"))
        #    return
        #elif recmessage.type == rec_proto.RECMessageType.REC_HANDSHAKE and client != None:
        #    self.SendMessage(address,self.RecCommunciation.CreateRecSessionClose(rec_proto.RECSessionClose.Reason.PROTOCOL_ERROR,"Registered client attempted to handshake"))
        #    return

        match recmessage.type:

            #TODO: verification types for password access
            case rec_proto.RECMessageType.REC_HANDSHAKE:
                client.OnHandshake(recmessage)
            
            case rec_proto.RECMessageType.REC_EVENT:
                self.OnEvent.on_changed(recmessage)

            case rec_proto.RECMessageType.REC_INTERACTION:
                self.OnInteraction.on_changed(client, recmessage)
                

    def Process(self):
        #REC

        conn, addr = self.SocketRec.accept()

        #i dont like how i did this but it works
        def ConnectionManager(connection,address):
            with connection:
                #create a session and rec connection, and register that with session manager
                print("servicing new connection") #TODO: this is a temporary print, we can remove this later

                rec_connection = RecConnection(ClientAddress=address,Client=connection) # we will edit all of this later when we handshake
                user_session = Session(rec_connection)
                self.SessionRegistry.Add(user_session)

                #receive data and process
                while True:
                    data = connection.recv(1048)
                    self.ProcessDataRec(data,address)

        threading.Thread(target=ConnectionManager,args=(conn,addr)).start()     
            
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
    

class RecConnection(Connection): 
    def __init__(self,Client,SessionId:np.uint32=-1,MinorVersion:np.uint32=-1,State:SessionState=SessionState.Connecting,ClientAddress:tuple=None):
        super().__init__(SessionId,MinorVersion,State,ClientAddress)

        self.Client = Client #we have to have this because tcp is special i guess

    def OnHandshake(self,message):
        Status,msg = rec_communication.RecHandshake(message,session_id=1) #temporary magic number

        self.Send(msg)
    def Send(self,message):
        self.Client.send(message.SerializeToString())



class Session:
    def __init__(self,RecSession:Connection,UbcSession:Connection=None,UecSession:Connection=None,Username:str="Test"):
        self.RecSession = RecSession
        self.UbcSession = UbcSession
        self.UecSession = UecSession
        self.Username = Username

    def IsThisMyClient(self,ClientAddress:tuple):
        if self.RecSession.IsThisMyClient(ClientAddress):
            return True, self.RecSession
        
        if self.UbcSession.IsThisMyClient(ClientAddress):
            return True, self.UbcSession
        
        if self.UecSession.IsThisMyClient(ClientAddress):
            return True, self.UecSession

    

class SessionRegistry:
    def __init__(self):
        self.sessions = {}

    def Get(self,sessionId:np.uint32):
        return self.sessions[sessionId]

    def GetAll(self):
        return self.sessions

    def Add(self,session:Session):
        self.sessions[session.RecSession.SessionId] = session

    def Remove(self,sessionId:np.uint32):
        self.sessions.pop(sessionId)