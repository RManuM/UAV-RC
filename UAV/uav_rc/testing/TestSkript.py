"""
Created on Tue Feb 11 15:30:05 2014

@author: mend_ma
"""
from uav_rc.network.Connection import AClient
import uav_rc.utils.UAV_Logger as LOG

class PythonTestClient(AClient):
    def __init__(self, host="localhost", port=8081):
        super(PythonTestClient,self).__init__(host, port, "PythonDummyTest", slots=["dummyPYSignal", "dummyPYSlot"], signals=["dummyPYSignal"])
        
    def sendPySignal(self, request):
        self._sendRequest_requireCallback("dummyPYSignal", request.toDictionary(), self.onPySignal_acknowledged)
        
    def onPySignal_acknowledged(self, *args):
        LOG.log_debug("received callback" + str(args[0]))
        
    def on_dummyPYSignal(self, *args):
        LOG.log_console("Recieved own package")
        request = self._receive(args[0], self._acknowledgeSignal)  # @UnusedVariable
    
    def on_dummyPYSlot(self, *args):
        LOG.log_console("Recieved remote package")
        request = self._receive(args[0], self._acknowledgeSignal)  # @UnusedVariable
#         logToConsole("Forwarding external call to internal slot!", new=False)
#         self.__giveAnswer__(request)
#         
#     def __giveAnswer__(self, request):
#         request = SimpleRequestHandle.generateResponse(request, self.module_id)
#         self.sendPySignal(request)

    def __del__(self):
        super(PythonTestClient, self).__del__()