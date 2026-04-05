import numpy as np
from enum import Enum
import socket
import server.protocols.rec_pb2 as rec_proto
from server.communication.rec_communication import RecCommunication,RecStatus
import config
import time

class SessionManager:
    def __init__(self,ip:str,port:int):
        self.RecCommunciation = RecCommunication()
        self.SessionRegistry = SessionRegistry()
        self.SocketRec = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        
        self.SocketRec.bind((ip,port))
        print("> Listening for clients on "+ip+":"+str(port))


        self.debugsendtimer = time.time()

    def SendMessage(self,address,message):
        self.SocketRec.sendto(message.SerializeToString(),address)



    def ProcessDataRec(self,data,client_address):

        recmessage = rec_proto.RECMessage()

        recmessage.ParseFromString(data)

        client = None
        Sessions = self.SessionRegistry.GetAll()
        for SessionN in Sessions:
            Ses = Sessions[SessionN]
            IsClient = Ses.RecSession.IsThisMyClient(client_address)
            if IsClient:
                client = Ses.RecSession
                break

        if recmessage.type != rec_proto.RECMessageType.REC_HANDSHAKE and client == None:
            self.SendMessage(client_address,self.RecCommunciation.CreateRecSessionClose(rec_proto.RECSessionClose.Reason.PROTOCOL_ERROR,"Unregistered client attempted to negotiate"))
            return
        elif recmessage.type == rec_proto.RECMessageType.REC_HANDSHAKE and client != None:
            self.SendMessage(client_address,self.RecCommunciation.CreateRecSessionClose(rec_proto.RECSessionClose.Reason.PROTOCOL_ERROR,"Registered client attempted to handshake"))
            return

        match recmessage.type:

            #TODO: verification types for password access
            case rec_proto.RECMessageType.REC_HANDSHAKE:
                Status,Response = self.RecCommunciation.RecHandshake(recmessage)

                if Status == RecStatus.OK:
                    SessionId = Response.handshake_ack.session_id
                    MinorVersion = recmessage.handshake.client_minor_version

                    rec_connection = RecConnection(SessionId,MinorVersion,SessionState.Active,client_address)
                    user_session = Session(rec_connection)
                    self.SessionRegistry.Add(user_session)

                self.SendMessage(client_address,Response)
            
            case rec_proto.RECMessageType.REC_EVENT:
                client.ReceivedMessage(recmessage)

            case rec_proto.RECMessageType.REC_ACK_ONLY:
                client.AckedMessage(recmessage.ack)
                

    def Process(self):
        #REC
        RecData, client_address = self.SocketRec.recvfrom(1024)

        self.ProcessDataRec(RecData,client_address)

    def Retransmission(self):


        Sessions = self.SessionRegistry.GetAll()

        for SessionN in Sessions:
            Ses = Sessions[SessionN]
            Data = Ses.RecSession.RetransmitMessages()

            if Data == False:
                #kick the client
                continue
            else:
                for Message in Data:
                    self.SendMessage(Ses.RecSession.ClientAddress,Message)

            if time.time()-self.debugsendtimer > 5:
                msg = self.RecCommunciation.CreateRecEvent(bytes())
                msg.seq = Ses.RecSession.CurrentSeq+1
                Ses.RecSession.CurrentSeq+=1
                Ses.RecSession.ExepectedSeq+=1

                Ses.RecSession.SendMessageWithAck(msg)

                self.SendMessage(Ses.RecSession.ClientAddress,msg)
                self.debugsendtimer = time.time()
            

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

    def IsThisMyClient(self,ClientAddress:tuple):
        return self.ClientAddress[0] == ClientAddress[0] and self.ClientAddress[1] == ClientAddress[1]

class RecConnection(Connection): 
    def __init__(self,SessionId:np.uint32,MinorVersion:np.uint32,State:SessionState,ClientAddress:tuple):
        super().__init__(SessionId,MinorVersion,State,ClientAddress)
        
        self.CurrentSeq = 0
        self.ExepectedSeq = 0

        self.MessagesAcked = []
        self.PendingAck = {} #messages we're waiting for the client to acknowledge (after a timeout we will resend)
        #"seqnumber":{"time":0,"retries":0,"message":msg}
        self.ReceieveBuffer = {} #out of order messages to sort through

    def SendMessageWithAck(self,message):
        self.PendingAck[message.seq] = {"time":time.time(),"retries":0,"message":message}

    def ReceivedMessage(self,message):
        if self.ExepectedSeq == message.seq:
            #parse
            print("Received")
            self.CurrentSeq = message.seq
            self.ExepectedSeq += 1
        elif message.seq < self.ExepectedSeq:
            
            print("Previous message received, acknowledging")
        else:
            self.ReceieveBuffer[message.seq] = message
            print("Out of sequence message received, storing")

    def AckedMessage(self,seq):
        self.MessagesAcked.append(seq)

    def SortReceiveBuffer(self): #gets called every time a message is receieved
        for MessageSeq in self.ReceieveBuffer:
            if MessageSeq == self.ExepectedSeq:
                self.ReceivedMessage(self.ReceieveBuffer[MessageSeq])
                self.ReceieveBuffer.pop(MessageSeq)
            
    
    def RetransmitMessages(self):
        MessagesToResend = []

        for AckedSeq in self.MessagesAcked:
            self.PendingAck.pop(AckedSeq)
            self.MessagesAcked.remove(AckedSeq)

        for PendingSeq in self.PendingAck:
            PendingData = self.PendingAck[PendingSeq]

            if time.time() - PendingData["time"] > config.config["server_ack_timeout"]:
                if PendingData["retries"] < config.config["server_ack_retry_limit"]:
                    PendingData["time"] = time.time()
                    PendingData["retries"] += 1
                    MessagesToResend.append(PendingData["message"])
                    print("Retry")
                else:
                    return False
        
        return MessagesToResend

class Session:
    def __init__(self,RecSession:Connection,UbcSession:Connection=None,UecSession:Connection=None):
        self.RecSession = RecSession
        self.UbcSession = UbcSession
        self.UecSession = UecSession

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