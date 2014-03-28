from uav_rc.utils import UAV_Logger
from uav_rc.uav.UAV import UAV
from serial.serialutil import SerialException
import logging
from optparse import OptionParser

def startup_UAV(host, port):
    myUAV = UAV(host, port)
    myUAV.startReceiving()
    return myUAV
    
def startup_serial(uav, comport, autopublish):
    uav.connectSerial(comport, autopublish)
    
def init_parser():
    parser = OptionParser()
    parser.add_option("--autopublish", help="automatically publish received pollings from drone", default="false")
    parser.add_option("--comport", help="if given, automatically connect to the given comport")
    parser.add_option("--port", help="the port of the socket.io-server", default=8081)
    parser.add_option("--host", help="the socket.io-servers IP", default="localhost")
    parser.add_option("--logging_level", help="Specify logging level: DEBUG,INFO", default="INFO")
#     parser.add_option("--logfile", help="specify a file for logging", default=None)
    return parser
   
if __name__ == "__main__":
    parser = init_parser()
    options, args = parser.parse_args()
    host, port = options.host, options.port
    comport = options.comport
    autopublish = options.autopublish.lower() == "true"
    
    if options.logging_level == "DEBUG":
        logging.basicConfig(level=UAV_Logger.APP_DEBUG)
    else:
        logging.basicConfig(level=UAV_Logger.INFO)
    logging.log(logging.INFO, "---------------Starting new LOG------------------")
    UAV_Logger.serialLogger_enable(True)
    UAV_Logger.socketIoLogger_enable(False)
    UAV_Logger.appLogger_enable(True)
    
    uav = startup_UAV(host, port)
    if comport is not None:
        try:
            comport = int(comport)
            startup_serial(uav, comport, autopublish)
        except SerialException, e:
            UAV_Logger.log_error("Serial not available: " + str(e))
        except Exception,e:
            UAV_Logger.log_error("Unexspected Error: "+ str(e))