'''
Created on 25.03.2014

@author: mend_ma
'''
from uav_rc.uav.UAV import UAV
import logging
from uav_rc.utils import UAV_Logger
from serial.serialutil import SerialException
import sys
import time
from uav_rc.uav.Models import Command
from uav_rc.uav.UAV_dummy import Dummy

"""-------------------------------------------------------------------------------
-----------------------------Beginning of MAIN------------------------------------
-----------------------------------------------------------------------------------"""
    
######################################################################################
## debugging single serial messages
######################################################################################

def serial_test():
    comport = 3
    drone = startup_plainSerial(comport)
    
    position = drone.getPosition()
    UAV_Logger.log_app_info(position)
    time.sleep(2)
    
    launch(drone)
    time.sleep(2)
    
#     setTarget(drone, maxSpeed, timeToStay, acc, lng, lat, heading, height, autoTrigger)(drone)
#     time.sleep(2)
#     
    goto(drone)
    time.sleep(2)
    
    endFlight(drone)
    time.sleep(2)
    
    comeHome(drone)
    time.sleep(2)
    
    drone.disconnectDrone()
    
    exit(0)

def startup_plainSerial(comport):
    ## logging
    logfile = "LOGS/"+str(time.time())+"_log.txt"
    logging.basicConfig(filename=logfile, format="%(asctime)s - <%(levelname)s> - %(name)s - %(message)s", level=UAV_Logger.APP_DEBUG)
    UAV_Logger.serialLogger_enable(True)
    UAV_Logger.socketIoLogger_enable(False)
    UAV_Logger.appLogger_enable(True)
    
    ## device
    myUAV = Dummy()
    myUAV.connectSerial(comport, False)
    
    ## getting serial instance:
    drone = myUAV.drone
    time.sleep(1)
    return drone

def headNorth(drone):
    position = drone.getPosition()
    setTarget(drone, 10,1,2,float(position["log"])+0.00005,float(position["lat"]), float(position["heading"]), float(position["alt"]), False)

def setTarget(drone, maxSpeed, timeToStay, acc, lng, lat, heading, height, autoTrigger):    
    UAV_Logger.log_app_info("SET TARGET")
    command = Command.getCmd_uploadTarget(maxSpeed, timeToStay, acc, lng, lat, heading, height, autoTrigger)
    drone.writeData(command)
    UAV_Logger.log_app_info("SENT")
    
def goto(drone):
    UAV_Logger.log_app_info("GOTO")
    command = Command.getCmd_goto()
    drone.writeData(command)
    UAV_Logger.log_app_info("GOTO executed")
    
def launch(drone):
    UAV_Logger.log_app_info("launch")
    command = Command.getCmd_launch()
    drone.writeData(command)
    UAV_Logger.log_app_info("launch executed")
    
def endFlight(drone):
    UAV_Logger.log_app_info("endflight")
    command = Command.getCmd_endFlight()
    drone.writeData(command)
    UAV_Logger.log_app_info("endflight executed")
    
def comeHome(drone):
    UAV_Logger.log_app_info("comeHome")
    command = Command.getCmd_comeHome() 
    drone.writeData(command)
    UAV_Logger.log_app_info("comeHome executed")
    
######################################################################################
## Normal stuff
######################################################################################
    
def startup_UAV(host, port):
    myUAV = UAV(host, port)
    myUAV.startReceiving()
    return myUAV
    
def startup_serial(uav, comport, autopublish):
    uav.connectSerial(comport, autopublish)   
    
def debuggingStartup():
    host, port = "localhost", 8081
    comport = 6
    autopublish = True
    
    logging.basicConfig(format="%(asctime)s - <%(levelname)s> - %(name)s - %(message)s", level=UAV_Logger.APP_DEBUG)
    UAV_Logger.serialLogger_enable(True)
    UAV_Logger.socketIoLogger_enable(False)
    UAV_Logger.appLogger_enable(True)
    
    uav = startup_UAV(host, port)
    try:
        startup_serial(uav, comport, autopublish)
    except SerialException, e:
        UAV_Logger.log_error("Serial not available: ", str(e))
        sys.exit(1)
    return uav

######################################################################################
## MAIN
######################################################################################
    
if __name__ == "__main__":
    serial_test()