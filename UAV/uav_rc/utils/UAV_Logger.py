'''
Created on 20.02.2014

@author: mend_ma
'''
import logging
import time

APP_DEBUG = 11
DEBUG = logging.DEBUG
INFO = logging.INFO
logging.addLevelName(APP_DEBUG, "APP_DEBUG")

class Logger():
    serial_logger = None
    uav_logger = None
    app_logger = None

def serialLogger_enable(enabled):
    if enabled:
        Logger.serial_logger = logging.getLogger("UAV-RC <<serial>>")
    else:
        Logger.serial_logger = None

def appLogger_enable(enabled):
    if enabled:
        Logger.app_logger = logging.getLogger("UAV-RC <<APP>>")
    else:
        Logger.app_logger = None
        
def socketIoLogger_enable(enabled):
    if enabled:
        Logger.uav_logger = logging.getLogger("UAV-RC <<socketIO>>")
    else:
        Logger.uav_logger = None
        
def log_app_info(msg):
    if Logger.app_logger is not None:
        Logger.app_logger.log(logging.INFO, msg)

def log(msg):
    """ Method for logging some information """
    if Logger.uav_logger is not None:
        Logger.uav_logger.log(logging.INFO, msg)
    
def log_debug(msg):
    """ Method for logging some debugging-information """
    if Logger.uav_logger is not None:
        Logger.uav_logger.log(APP_DEBUG, msg)
    
def log_console(msg, new=False):
    if new:
        print "-------------------------------------"
    print time.strftime("%d.%m.%Y - %H:%M:%S -"), msg
    
def log_serial_communication(msg):
    if Logger.serial_logger is not None:
        Logger.serial_logger.log(APP_DEBUG, msg)
    
def log_error(msg):
    if Logger.serial_logger is not None:
        Logger.serial_logger.error(msg)