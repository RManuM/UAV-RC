from socketIO_client import SocketIO
import time
from threading import Thread
from uav_rc.utils import UAV_Logger
from uav_rc.network.Protocol import Request
     
class AClient(Thread, object):
    """ This class is designed to give the programmer a basic implementation of a socket.io socket.
    The Programmer only needs to implement the methods for receiving and sending, and the getSlotsMap-Method.
    Last one is used to connect a received signal to a slot-method"""
    def __init__(self, host="localhost", port=8080, moduleID="Dummy", slots=[], signals=[]):
        """
        Args:
            host (str, optional): IP-Address of the server hosting the socket.io-Server (default is localhost)
            port (int, optional): Port on which the server is listening (default is 8080)
            name (str, optional): ModuleID of the connecting module (default is Dummy)
            slots (list, optional): list of all slots on which the socket is receiving messages (default is an empty list)
            signals (list, optional): a list of all signals the socket can send (default is an empty list)
        """
        Thread.__init__(self)
        UAV_Logger.log("registring to host")
        self.host = host
        self.port = port
        self.name = moduleID
        self.socketIO = SocketIO(host, port)
        self.slots = slots
#         self.signals = signals
        UAV_Logger.log("initialising listening")
        self.socketIO.on('connect', self.onConnect)
        self.polling_frequenze = 1 # new poll every second
        self.listening = False
        self.__initListening__()
     
    def getSlotMap(self):
        """Required for initialising the connections
         
        Returns:
            dict: A dictionary: key->The Signal-name, value->The Method executed on signal
        """
        slotMap = dict()
        for entry in self.slots:
            slotMap[entry] = self.__getattribute__("on_" + entry)
        return slotMap
         
    def getModuleName(self):
        """
        Returns:
            str: the name of the module, which the socket is connecting for
        """
        return self.name
     
    def __initListening__(self):
        ''' Initially connecting the slots referencend by self.getSlotMap()'''
        for key, value in self.getSlotMap().items():
            self.socketIO.on(key, value)
         
    def _sendRequest(self, signal, request):
        ''' Sending a request under a certain signal
        
        Args:
            signal (str): stringrepresentation of the signal about to be emitted
            request (dict):  dictionary that will be transmitted as a JSON-string'''
        UAV_Logger.log_debug("-->  SIGNAL: " + signal + " | REQUEST: " + str(request))
        self.socketIO.emit(signal, request)
         
    def _sendRequest_requireCallback(self, signal, request, callbackFkt):
        ''' Sending a request under a certain signal
        
        Args:
            signal (str): the signal to emit
            request (dict): dictionary that will be transmitted as a JSON-string
            callbackFkt (type): the callbackfunktion executed on positive response
            '''
        UAV_Logger.log_debug("--> SIGNAL: " + signal + " | REQUEST: " + str(request))
        self.socketIO.emit(signal, request, callbackFkt)
        
    def _receive(self, args):
        ''' First handling a received request, by parsing it'''
        request = Request(self.getModuleName()).parse(args)
        UAV_Logger.log_debug("<-- DATA: " + str(request))
        return request
        
    def _acknowledgeSignal(self, request, error_code=0, error_description="", data=None):
        ''' Acknowledges a received message fulfilling the protocol'''
        if error_code == 0:
            ack = request.acknowledge_withSuccess(data)
        else:
            ack = request.acknowledge_withError(error_code, error_description)
        
        if request.isAckRequired():
            self._sendRequest("ACK", ack.toDictionary())
    
    def onConnect(self, *args):
        """Slot for handling a connect-event"""
        UAV_Logger.log("connect signal recieved")
        self.socketIO.emit('CORE_SL_SLOTS_SET', Request(self.getModuleName()).newData({"slots":self.slots}).toDictionary())
         
    def startReceiving(self):
        """ Starting the socket-thread to recieve without loosing the ability to kill the socket"""
        self.listening = True
        self.start()
         
    def run(self):
        self.socketIO.wait()
        ## enable this if you want to kill the socket
#         LOG.log("listening started")
#         while self.listening:
#         self.socketIO.wait(self.polling_frequenze)
#         LOG.log("listening stoped")
     
    def kill(self):
        """Killing the socket"""
        self.listening = False
        while(self.isAlive()):
            time.sleep(1)
        UAV_Logger.log("Socket killed")
            
    def __del__(self):
        UAV_Logger.log("deleting socket...")
        self.kill()