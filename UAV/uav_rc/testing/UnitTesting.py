'''
Created on 20.02.2014

@author: mend_ma
'''
import time
import uav_rc.utils.UAV_Logger as LOG
import logging
import threading
from uav_rc.testing.TestSkript import PythonTestClient
from uav_rc.network.Connection import AClient
from uav_rc.network.Protocol import Request



logging.basicConfig(level=logging.INFO)

def startup():
    myClient = PythonTestClient("localhost", 8081)
    myClient.startReceiving()
    return myClient
    
def reboot(client):
    client.kill()
    return startup()
    
def kill(client):
    client.kill()
    
def killAll():
    for th in threading.enumerate():
        if isinstance(th, AClient):
            th.kill()
    
def sendSample(client):
    request = Request(client.getModuleName()).newData("This is a String")
    print request
    client.sendPySignal(request)
    
def sendSample_requireAck(client):
    request = Request(client.getModuleName()).newData("This is a String", ack=True)
    print request
    client.sendPySignal(request)

## TESTFUNKTIONS

def startupWithRequest():
    LOG.log_console("started...")
    
    client = startup()  # @UnusedVariable
    
    LOG.log_console("waiting till bootup")
    time.sleep(5)
    LOG.log_console("proceed")
    
#     sendSample_requireAck(client)
#     
#     LOG.log_console("executing finished")
    
startupWithRequest()