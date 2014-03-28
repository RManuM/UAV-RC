'''
Created on 11.03.2014

@author: mend_ma
'''
from uav_rc.network.Connection import AClient
import sys
from uav_rc.network.Protocol import Request, Request_ValueUnset_Exception
from uav_rc.uav.serials.AscTec import AscTec
from uav_rc.utils import UAV_Logger


SLOTS = ["UAV_CAM_ANGLE_SET", "UAV_CAM_ANGLE_GET", "UAV_CAM_TRIGGER",   ## cam
         "UAV_STATUS_GET", "UAV_POSITION_GET", "UAV_TARGET_GET",        ## some getter
         "UAV_TARGET_SET", "UAV_SL_LAUNCH", "UAV_SL_COMEHOME", 
         "UAV_SL_GOTO", "UAV_SL_ENDFLIGHT",                             ## something about moving
         "UAV_CONNECT", "UAV_DISCONNECT"]                               ## Connection-handling

ASCTEC_SLOTS = ["UAV_ASCTEC_LL_STATUS_GET", "UAV_ASCTEC_IMU_RAWDATA_GET",
                "UAV_ASCTEC_IMU_CALCDATA_GET", "UAV_ASCTEC_GPS_DATA_GET",
                "UAV_ASCTEC_GPS_DATA_ADVANCED_GET",
                "UAV_ASCTEC_CAM_DATA_GET"]

SIGNALS = ["UAV_CAM_IS",
           "UAV_STATUS_IS",
           "UAV_GOTO_IS",
           "UAV_TARGET_IS",
           "UAV_POSITION_IS",
           "UAV_SI_TARGET_REACHED"]

MODULE_NAME = "UAV_AscTec"

class UAV(AClient):
    '''
    A UAV-AscTec connecting to serial socket
    '''
    def __init__(self, host, port):
        '''
        Constructor initailising UAV
        Setting up a Socket.io-Socket
        Setting up the Serial Socket
        '''
        SLOTS.extend(ASCTEC_SLOTS)
        super(UAV ,self).__init__(host, port, MODULE_NAME, SLOTS, SIGNALS)
        self.drone = None
        
    def __notImplementedAcknowledge(self, request):
        if request.isAckRequired():
            self._acknowledgeSignal(request, error_code=666, error_description="not implemented yet")
            
    def ack_positive(self, request):
        self._acknowledgeSignal(request, data={})
        
    def ack_error(self, request, error_code, error_description):
        self._acknowledgeSignal(request, error_code, error_description)
        
    def connectSerial(self, comport, autopublish):
        self.drone = AscTec(self)
        try:
            result = self.drone.connectDrone(comport, autopublish=autopublish)
        except Exception, e:
            print UAV_Logger.log_error("Comport not opened: " + str(e))
            sys.exit(1) 
        return result
    
    
    """-------------------------------------------------------------------------------
    -----------------------------Beginning of true ASCTEC-Slots------------------------
    -----------------------------------------------------------------------------------"""
    
    def on_UAV_ASCTEC_LL_STATUS_GET(self, *args):
        request = self._receive(args[0])
        self.drone.requestStatus()
        self._acknowledgeSignal(request, data={})
        
    def em_UAV_ASCTEC_LL_STATUS_IS(self):
        data = self.drone.getLLStatus()
        request = Request(self.getModuleName()).newData(data, False).toDictionary()
        self._sendRequest("UAV_ASCTEC_LL_STATUS_IS", request)

    ###############################################################################################
            
    def on_UAV_ASCTEC_IMU_RAWDATA_GET(self, *args):
        request = self._receive(args[0])
        self.em_UAV_ASCTEC_IMU_RAWDATA_IS()
        self._acknowledgeSignal(request, data={})
        
    def em_UAV_ASCTEC_IMU_RAWDATA_IS(self):
        data = self.drone.getRAWDATA()
        request = Request(self.getModuleName()).newData(data, False).toDictionary()
        self._sendRequest("UAV_ASCTEC_IMU_RAWDATA_IS", request)
        
    ###############################################################################################
    
    def on_UAV_ASCTEC_IMU_CALCDATA_GET(self, *args):
        request = self._receive(args[0])
        self._acknowledgeSignal(request, data={})
        
    def em_UAV_ASCTEC_IMU_CALCDATA_IS(self):
        data = self.drone.getCALCDATA()
        request = Request(self.getModuleName()).newData(data, False).toDictionary()
        self._sendRequest("UAV_ASCTEC_IMU_CALCDATA_IS", request)
        
    ###############################################################################################
    
    def on_UAV_ASCTEC_GPS_DATA_GET(self, *args):
        request = self._receive(args[0])
        self._acknowledgeSignal(request, data={})
        
    def em_UAV_ASCTEC_GPS_DATA_IS(self):
        data = self.drone.getGPSDATA()
        request = Request(self.getModuleName()).newData(data, False).toDictionary()
        self._sendRequest("UAV_ASCTEC_GPS_DATA_IS", request)
        
    ###############################################################################################
    
    def on_UAV_ASCTEC_GPS_DATA_ADVANCED_GET(self, *args):
        request = self._receive(args[0])
        self._acknowledgeSignal(request, data={})
        
    def em_UAV_ASCTEC_GPS_DATA_ADVANCED_GET(self):
        data = self.drone.getGPSDATA()
        request = Request(self.getModuleName()).newData(data, False).toDictionary()
        self._sendRequest("UAV_ASCTEC_GPS_DATA_ADVANCED_GET", request)
        
    ###############################################################################################
    
    def on_UAV_ASCTEC_CAM_DATA_GET(self, *args):
        request = self._receive(args[0])
        self._acknowledgeSignal(request, data={})
        
    def em_UAV_ASCTEC_CAM_DATA_IS(self):
        data = self.drone.getCAMDATA()
        request = Request(self.getModuleName()).newData(data, False).toDictionary()
        self._sendRequest("UAV_ASCTEC_CAM_DATA_IS", request)
        
        
    """ -------------------------------------------------------------------------------
    -----------------------------Beginning of true UAV-Slots---------------------------
    -----------------------------------------------------------------------------------"""
        
    def on_UAV_CAM_ANGLE_SET(self, *args):
        request = self._receive(args[0])
        error_code, error_desc = 0, ""
        try:
            pitch = request.get("body", "pitch")
            roll = request.get("body", "roll")
            self.drone.setCamAngle(pitch, roll, request)
        except Request_ValueUnset_Exception, e:
            error_code = 1
            error_desc = "Value not set: " + str(e)
            self._acknowledgeSignal(request, error_code=error_code, error_description=error_desc)
        except:
            error_code, error_desc = 1, "unknown error"
            self._acknowledgeSignal(request, error_code=error_code, error_description=error_desc)
        
    def on_UAV_CAM_ANGLE_GET(self, *args):
        request = self._receive(args[0])
        self.em_UAV_CAM_ANGLE_IS()
        self._acknowledgeSignal(request,self.drone.getCamAngle())
    
    def em_UAV_CAM_ANGLE_IS(self):
        data = self.drone.getCamAngle()
        request = Request(self.getModuleName()).newData(data, False).toDictionary()
        self._sendRequest("UAV_CAM_ANGLE_IS", request)
        
    def on_UAV_CAM_TRIGGER(self, *args):
        request = self._receive(args[0])
        self.drone.trigger(request)
        
    #########################################################################################
        
    def on_UAV_STATUS_GET(self, *args):
        request = self._receive(args[0])
        self.em_UAV_STATUS_IS()
        self._acknowledgeSignal(request,self.drone.getStatus())
        
    def em_UAV_STATUS_IS(self):
        data = self.drone.getStatus()
        request = Request(self.getModuleName()).newData(data, False).toDictionary()
        self._sendRequest("UAV_STATUS_IS", request)
        
    #########################################################################################
        
    def on_UAV_SL_COMEHOME(self, *args):
        request = self._receive(args[0])
        self.drone.comeHome(request)
        
    def on_UAV_SL_LAUNCH(self, *args):
        request = self._receive(args[0])
        target = request.get("body")
        ## FIXME: parsing a target?
        if target is None or len(target) == 0:
            self.ack_error(request, 1, "No target specified")
        else:
            self.drone.launch(target, request)
        
    def on_UAV_SL_ENDFLIGHT(self, *args):
        request = self._receive(args[0])
        self.drone.endFlight(request)
        
    def on_UAV_SL_GOTO(self, *args):
        request = self._receive(args[0])
        target = request.get("body")
        ## FIXME: parsing a target?
        if target is None or len(target) == 0:
            self.ack_error(request, 1, "No target specified")
        else:
            self.drone.goto(target, request)
        
    #########################################################################################
        
    def on_UAV_CONNECT(self, *args):
        request = self._receive(args[0])
        try:
            port = int(request.get("body", "comport"))
            autopublish = True
            result = self.connectSerial(port,autopublish)
        except Exception, e:
            result = {"error_code":1, "error_description":"error handling request: " + str(e)}
        if result.has_key("error_code"):
            self._acknowledgeSignal(request, error_code=result["error_code"], error_description=result["error_description"])
        else:
            self._acknowledgeSignal(request,data=result)
       
    def on_UAV_DISCONNECT(self, *args):
        request = self._receive(args[0])
        if self.drone is not None:
            result = self.drone.disconnectDrone()
            if result.has_key("error_code"):
                self._acknowledgeSignal(request, error_code=result["error_code"], error_description=result["error_description"])
            else:
                self._acknowledgeSignal(request,data=result)
        else: 
            self._acknowledgeSignal(request, error_code=1, error_description="Drone not connected")
            
    def em_UAV_CONNECTION_CLOSED(self):
        request = Request(self.getModuleName()).newData({}, False).toDictionary()
        self._sendRequest("UAV_CONNECTIONC_CLOSED", request)
        
            
    #########################################################################################
    
    def on_UAV_POSITION_GET(self, *args):
        request = self._receive(args[0]) 
        self.em_UAV_POSITION_IS()
        self._acknowledgeSignal(request,data={})
        
    def em_UAV_POSITION_IS(self):
        data = self.drone.getPosition()
        request = Request(self.getModuleName()).newData(data, False).toDictionary()
        self._sendRequest("UAV_POSITION_IS", request)
        
    #########################################################################################
    
    def on_UAV_TARGET_GET(self, *args):
        request = self._receive(args[0])
        self.em_UAV_TARGET_IS()
        self._acknowledgeSignal(request,self.drone.getTarget())
        
    def on_UAV_TARGET_SET(self, *args):
        request = self._receive(args[0])
        target = request.get("body")
        ## FIXME: parsing a target?
        if target is None or len(target) == 0:
            self.ack_error(request, 1, "No target specified")
        else:
            self.drone.setTarget(target, request)
        
    def em_UAV_TARGET_IS(self):
        data = self.drone.getTarget()
        request = Request(self.getModuleName()).newData(data, False).toDictionary()
        self._sendRequest("UAV_TARGET_IS", request)
        
    def em_UAV_SI_TARGET_REACHED(self):
        data = self.drone.getTarget()
        request = Request(self.getModuleName()).newData(data, False).toDictionary()
        self._sendRequest("UAV_SI_TARGET_REACHED", request)
        
    #########################################################################################
        
    def __del__(self):
        super(UAV, self).__del__()
