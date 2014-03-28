'''
Created on 12.03.2014

@author: mend_ma
'''

import serial
import traceback
import threading
from uav_rc.uav.Models import Message, Command, ACK_MAP
from uav_rc.uav.Models import CAM, LLSTATUS, IMUCALC, GPS, GPSADV, IMURAW, RCDAT, CTRLOUT, CURWAY, X60, X61, X62, X64
import time
import uav_rc.utils.UAV_Logger as LOG
import logging

BAUDRATE = 57600
DATABITS = 8
STOPBITS = 1
PARITY = "N"

## TODO: make values setable via remote-call
COMPORT = 5
POLL_INTERVALL = 1
SENDING_INTERVALL = 0.1

class AscTec(object):
    '''   This class offers a serial socket and pulls data from the drone   '''
    serial = None
    
    def __init__(self, parent, *args, **argv):
        ## initializing serial data
        self.__baud = BAUDRATE
        self.__comport = COMPORT
        self.__databits = DATABITS
        self.__stopbits = STOPBITS
        self.__parity = PARITY
        
        self.__sendingIntervall = SENDING_INTERVALL
        self.__pollIntervall = POLL_INTERVALL
        
        ## the internal representation of drone-data
        self.drone_status = {"battery_voltage_1":None, "battery_voltage_2":None, 
                             "status":None, "cpu_load":None, "compass_enabled":None, 
                             "chksum_error":None, "flying":None, "motors_on":None, 
                             "flightMode":None, "up_time":None}
        
        self.drone_rawdata = {"pressure": None, "gyro_x": None, "gyro_y": None, 
                              "gyro_z": None, "mag_x": None, "mag_y": None, 
                              "mag_z": None, "acc_x": None, "acc_y": None,  
                              "acc_z": None, "temp_gyro": None, "temp_ADC": None}
        
        self.drone_calcdata = {"angle_nick":None, "angle_roll":None, "angle_yae":None,
                               "angvel_nick":None, "angvel_roll":None, "angvel_yaw":None,
                               "acc_x_calib":None, "acc_y_calib":None, "acc_z_calib":None,
                               "acc_x":None, "acc_y":None, "acc_z":None,
                               "acc_angle_nick":None, "acc_angle_roll":None,
                               "acc_absolute_value":None, "dheight_reference":None, "height_reference":None,
                               "Hx":None, "Hy":None, "Hz":None,
                               "mag_heading":None, "height":None, "dheight":None,
                               "speed_x":None, "speed_y":None, "speed_z":None}
                               
        self.drone_gpsData = {"latitude": None, "longitude": None, "height": None,
                              "speed_x": None, "speed_y": None, "heading": None, 
                              "horizontal_accuracy": None, "vertical_accuracy": None, 
                              "speed_accuracy": None, "numSV": None, "status": None, 
                              "latitude_best_estimate": None, "longitude_best_estimate": None,  
                              "speed_x_best_estimate": None, "speed_y_best_estimate": None} 
                              
        self.drone_rcData = {"cannels_in":None, "channels_out":None, "lock":None}
        
        self.drone_controlerOutput = {"nick":None, "roll":None, "yaw":None, "thrust":None}
        
        self.drone_cam = {"pitch":None, "roll":None}
        
        ## internal state
        self.connected = False                ## is the drone connected?
        self.abstractUAV = parent             ##  the abstract UAV to emit signals
        self._target = None                     ## where is the drone heading to?
        self.__autopublish = False              ## This var indicates, whether received values are published automatically
        self.__sendLock = threading.Lock()    ## lock for handling the sendingbuffer
        self.writeBuffer = list()
        self.__pending_acks = dict()
        self.__onMission = False
    
    ##########################################################################################
    ## Connection handling
    ##########################################################################################
    
    def connectDrone(self, port, autopublish=None, sending_intervall=None, poll_intervall=None):
        ''' Trys to connect a drone to the serial port specified by this class'''
        
        if autopublish is not None:
            self.__autopublish = autopublish
        if sending_intervall is not None:
            self.__sendingIntervall =  sending_intervall
        if poll_intervall is not None:
            self.__pollIntervall =  poll_intervall
            
        error, message = 0, ""
        self.__comport = port
        if not self.connected:
            try:
                ## connect serial
                AscTec.serial = serial.Serial(port=self.__comport,
                                         baudrate=self.__baud,
                                         parity=self.__parity,
                                         stopbits=self.__stopbits,
                                         bytesize=self.__databits)
            except Exception, e:
                LOG.log_error(str(e))
                error = 1
                message = str(e)
        else:
            error = 801
            message = "already connected"
        if not error == 0:
            return {"error_code":error, "error_description":message}
        else:
            self.connected = True
            self.startReceiving()
            self.startSending()
            self.startPolling()
            return {}
    
    def disconnectDrone(self):
        if self.connected:
            try:
                self.connected = False
                if AscTec.serial is not None:
                    AscTec.serial.close()
                    AscTec.serial = None 
            except Exception, e: 
                traceback.print_exc()
                return {"error_code":1, "error_description":str(e)}
        return {}
    
    def startReceiving(self):
        self.receiver = threading.Thread(target=self._readData)
        self.receiver.start()
    
    def startPolling(self):
        self.poller = threading.Thread(target=self._pollData)
        self.poller.start()
    
    def startSending(self):
        self.sender = threading.Thread(target=self._sendData)
        self.sender.start()
        
    def _onConnectionClosed(self):
        ''' Handling a closed connection (expected or unexpected)'''
        self.disconnectDrone()
        self.abstractUAV.em_UAV_CONNECTION_CLOSED()
    
    ##########################################################################################
    ## Reading data (THREAD)
    ##########################################################################################
    
    def _readData(self):
        ''' Reading data from the serial port, interpretation data
        This function needs to be started in a thread''' 
        while self.connected:
            try:
                reading = self.__readLine()
                if reading is not None:
                    msg, msgType = reading
                    if msgType == "MSG":
                        self.__handleData(msg)
                    elif msgType == "ACK":
                        key = "0x"+msg.encode("hex")
                        if ACK_MAP.has_key(key):
                            ackType = ACK_MAP[key]
                        else:
                            ackType = None
                        self.__handleAck(ackType)
                        log_ack(ackType + " " + key)
            except Exception, e:
                logging.getLogger().error("Reading serial-data: " + str(e))
                self.serial.flush()
            time.sleep(0.01)
           
        if self.connected == False:
            self._onConnectionClosed()
            
    def __readLine(self):
        result = None
        reading = ""
        while result == None and self.connected:
            try:
                reading += AscTec.serial.read(1)
            except AttributeError, e:
                print str(e)
                break
            if reading[:3] == ">*>" and reading[-3:] == "<#<":
                result = reading[:-3], "MSG"
            elif reading[:2] == ">a" and reading[-2:] == "a<":
                reading = reading[2:-2]
                result = reading, "ACK"
        if self.connected:
            return result
        else:
            return None
        
    def __handleAck(self, ackType):
        if ackType is not None:
            if self.__pending_acks.has_key(ackType):
                pending_ack = self.__pending_acks.pop(ackType)
                self.abstractUAV.ack_positive(pending_ack)
                LOG.log_app_info("ACK: " + ackType)
        
    def __handleData(self, reading):
        data_msg = Message(reading)
        data = data_msg.getParams()
        msgType = data_msg.msgType
        
        required_storage = None
        actions = list()
        if msgType == LLSTATUS:
            required_storage = self.drone_status
            #action = self.abstractUAV.em_UAV_ASCTEC_LL_STATUS_IS
            typeName = "LLSTATUS"
            actions.append(self.abstractUAV.em_UAV_STATUS_IS)
        elif msgType == CAM:
            required_storage = self.drone_cam
            actions.append(self.abstractUAV.em_UAV_CAM_ANGLE_IS)
            typeName = "CAM"
        elif msgType == GPS:
            required_storage = self.drone_gpsData
            actions.append(self.abstractUAV.em_UAV_ASCTEC_GPS_DATA_IS)
            actions.append(self.abstractUAV.em_UAV_POSITION_IS)
            typeName = "GPS"
        elif msgType == GPSADV:
            required_storage = self.drone_gpsData
            actions.append(self.abstractUAV.em_UAV_ASCTEC_GPS_DATA_IS)
            actions.append(self.abstractUAV.em_UAV_POSITION_IS)
            typeName = "GPSADV"
        elif msgType == IMUCALC:
            actions.append(self.abstractUAV.em_UAV_ASCTEC_IMU_CALCDATA_IS)
            typeName = "IMUCALC"
        elif msgType == RCDAT:
            typeName = "RCDAT"
        elif msgType == IMURAW:
            typeName = "IMURAW"
        elif msgType == CTRLOUT:
            typeName = "CTRLOUT"
        elif msgType == CURWAY:
            typeName = "CURWAY"
            self.checkWaypointReached(data)
        elif msgType == X60:
            typeName = "X60"
        elif msgType == X61:
            typeName = "X61"
        elif msgType == X62:
            typeName = "X62"
        elif msgType == X64:
            typeName = "X64"
        else:
            typeName = "OTHER"
        
        log_received(data_msg.msgStruct, typeName)
        
        ## reading values
        if required_storage is not None:
            for key, value in data.items():
                required_storage[key] = value
                
        if self.__autopublish and len(actions)>0:
            for task in actions:
                task()
    
    
    ##########################################################################################
    ## writing data to serial bus (THREAD)
    ##########################################################################################
    
    def writeData(self, serial_message, request=None):
        while not self.__sendLock.acquire():
            time.sleep(self.__sendingIntervall/100)
        log_sent(serial_message)
        self.writeBuffer.append((serial_message,request))
        self.__sendLock.release()
        
    def _sendData(self):
        while self.connected:
            while not self.__sendLock.acquire():
                time.sleep(self.__sendingIntervall/10)
            self.__sendNext()
            self.__sendLock.release()
            time.sleep(SENDING_INTERVALL)
        
    def __sendNext(self):
        if len(self.writeBuffer) > 0:
            buffered =  self.writeBuffer.pop(0)
            serial_message, request = buffered
            AscTec.serial.write(serial_message)
            if request is not None:
                self.abstractUAV._acknowledgeSignal(request, data={})
        
    
    ##########################################################################################
    ## polling data (THREAD)
    ##########################################################################################
    
    def _pollData(self):
        while self.connected:
            self.writeData(Command.getCmd_poll(LLSTATUS, IMUCALC, GPS, GPSADV, CAM))
            if self.__onMission:
                print "POLL CURWAY"
                self.writeData(Command.getCmd_poll(CURWAY))
            time.sleep(self.__pollIntervall)
        
            
    ##########################################################################################
    ## Getter and setter
    ##########################################################################################
    
    def getLLStatus(self):
        return self.drone_status
    
    def getCALCDATA(self):
        return self.drone_calcdata
    
    def getRAWDATA(self):
        return self.drone_rawdata
    
    def getRCDATA(self):
        return self.drone_rcData
    
    def getGPSDATA(self):
        return self.drone_gpsData
    
    def getCAMDATA(self):
        return self.drone_cam
    
    ## status
    def getStatus(self):
        ## FIXME: this status is more experimental. for real status specification take your time
        if self.drone_status["battery_voltage_1"] is not None and self.drone_status["battery_voltage_2"] is not None:
            baLevel = float(self.drone_status["battery_voltage_1"]) + float(self.drone_status["battery_voltage_2"])
            baLevel = baLevel /2
            return {"mode":self.drone_status["flightMode"], "batteryLevel":baLevel, 
                    "timeUp":self.drone_status["up_time"]}
        else:
            return None
        
    ## position
    def getPosition(self):
        result = dict()
        result["lat"] = self.drone_gpsData["latitude"]
        result["lon"] = self.drone_gpsData["longitude"]
        result["alt"] = self.drone_gpsData["height"]
        result["heading"] = self.drone_gpsData["heading"]
        result["accuracyHorizontal"] = self.drone_gpsData["horizontal_accuracy"]
        result["accuracyVertical"] = self.drone_gpsData["vertical_accuracy"]
        return result
            
    ## camera:
    def setCamAngle(self, pitch, roll, request):
        LOG.log_app_info("Setting angle to (pitch/roll): (" + str(pitch) + "/" + str(roll) + ")")
        key = "CAM"
        if not self.__pending_acks.has_key(key):
            self.__pending_acks[key] = request
            self.writeData(Command.getCmd_setCam(pitch, roll))
        else:
            self.abstractUAV.ack_error(request, 1, "already pending action")
        
    def getCamAngle(self):
        pitch = self.drone_cam["pitch"]
        roll = self.drone_cam["roll"]
        return {"roll":roll,"pitch":pitch}
    
    def trigger(self, request):
        message = Command.getCmd_triggerCam()
        LOG.log_app_info("Triggering CAM")
        self.writeData(message, request)
        ## TODO: acknowledging trigger?
        
    ## targeting
    def setTarget(self, target, request):
        self._target = target
        ## setting cam
        pitch = float(request.get("body","cam", "pitch"))
        roll = float(request.get("body","cam", "roll"))
        self.setCamAngle(pitch, roll, request)
        
        ## setting waypoint FIXME: setting some values not statically
        LOG.log_app_info("Setting target.")
        maxSpeed= 10 ## in m/s
        timeToStay=1 ## in s
        acc=2 ## in m
        lng=float(target["lon"])
        lat=float(target["lat"])
        heading=float(target["heading"])
        height=float(target["alt"])
        flags = str(request.get("body", "cam", "trigger")).lower() == "true"
        command = Command.getCmd_uploadTarget(maxSpeed, timeToStay, acc, lng, lat, heading, height, flags)
        self.writeData(command)
        key = "WPT"
        if not self.__pending_acks.has_key(key):
            self.__pending_acks[key] = request
        self.__onMission = True
                
    def getTarget(self):
        return self._target
    
    ## Flight control!
    def launch(self, target, request):
        """ Setting the current home-position"""
        command = Command.getCmd_launch()
        self.writeData(command)
        key = "LAUNCH"
        if not self.__pending_acks.has_key(key):
            self.__pending_acks[key] = request
        self.__onMission = True ## FIXME: curway checking?
        LOG.log_app_info(key)
        
    def endFlight(self, request):
        """ ends a flight"""
        command = Command.getCmd_endFlight()
        self.writeData(command)
        key = "ENDFLIGHT"
        if not self.__pending_acks.has_key(key):
            self.__pending_acks[key] = request
        self.__onMission = True ## FIXME: curway checking?
        LOG.log_app_info(key)
    
    def comeHome(self, request):
        """flies to the current home-position"""
        command = Command.getCmd_comeHome()
        self.writeData(command)
        key = "COMEHOME"
        if not self.__pending_acks.has_key(key):
            self.__pending_acks[key] = request
        self.__onMission = True ## FIXME: curway checking?
        LOG.log_app_info(key)
    
    def goto(self, target, request):
        """keeping the target but moving to a different point for resuming"""
        maxSpeed= 10 ## in m/s
        timeToStay=1 ## in s
        acc=2 ## in m
        lng=float(target["lon"])
        lat=float(target["lat"])
        heading=float(target["heading"])
        height=float(target["alt"])
        command = Command.getCmd_goto(maxSpeed,timeToStay,acc,lng,lat,heading,height)
        self.writeData(command)
        key = "GOTO"
        if not self.__pending_acks.has_key(key):
            self.__pending_acks[key] = request
        self.__onMission = True ## FIXME: curway checking?
        LOG.log_app_info(key)
            
    def checkWaypointReached(self, data):
        """ Checks, whether a waypoint is reached and executed till the end"""
        wptReached = data["wptReached"]
        if wptReached:
            LOG.log_app_info("Waypoint reached")
            self.abstractUAV.em_UAV_SI_TARGET_REACHED()
            self.__onMission = False
            self._target = None
        else:
            LOG.log_app_info("Distance to waypoint: " + str(data["distance"]))
    
def log_received(data, typeName):
    LOG.log_serial_communication("RECEIVED (" + str(typeName) + ")  :" + str(data.encode("hex")))
    
def log_sent(command):
    LOG.log_serial_communication("SENT: " + str(command[3:].encode("hex")))
    
def log_ack(ack_type):
    LOG.log_serial_communication("ACK:           " + ack_type + " --")