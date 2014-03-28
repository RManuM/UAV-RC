'''
Created on 21.02.2014

@author: mend_ma
'''

import time
    
class Request_Invalid_Exception(Exception):
    def __init__(self, msg):
        Exception.__init__(Exception(msg))
        self.message = msg
        
    def __str__(self):
        return self.message
        
class Request_ValueUnset_Exception(Exception):
    def __init__(self, msg):
        Exception.__init__(Exception())
        self.message = msg
        
    def __str__(self):
        return self.message

class Request(object):
    ''' This Class represents a Request transmitted via socket.io
    You have to initialise a request through either calling newError, newData, acknowledge_withError, acknowledge_withSuccess or parse
    '''
    def __init__(self, moduleName):
        ''' Standardinitialisation of a request
        
        Args:
            moduleName (str): used to specifie the modules name emitting the request
        '''
        self._header = dict()
        self._body = None
        self._error = None
        self._moduleName = moduleName
        self._initialised = False
                
    def _new(self, ack=False, body_object=None, error_object=None):
        ''' Initialising the class by generating a new request
        
        Args:
            ack (bool, optional): should the message be acknowledged
            body_object (object, optional): can be any object, should be dictionary ##TODO: really any?
            error_object (dict, optional): dictionary with the entries code and message ## TODO: you may want to implements a separate class representing a error
        
        Returns:
            This Function returns the object, on which the function got called
        '''
        self._header = self.__generateHeader(ack)
        self.__setContent(body_object, error_object)
        self._initialised = True
        return self
    
    def newError(self, code, description, ack=False):
        ''' Generates a new error requiring error-code and -description
        
        Args:
            code (int): the code describing the occurred error
            description (str): a describing string for the error
            ack (bool, optional): should the error-message be acknowledged (default: False)
            
        Returns:
            This Function returns the object, on which the function got called
        '''
        error = {"code":code, "description":description}
        return self._new(ack=ack, error_object=error)
    
    def newData(self, data, ack=False):
        ''' Generates a new data-request
        
        Args:
            data (object): a object containing the information
            ack (bool, optional): should the error-message be acknowledged (default: False)
            
        Returns:
            This Function returns the object, on which the function got called
        '''
        return self._new(ack=ack, body_object=data)
                
    def _acknowledge(self, body_object=None, error_object=None):
        msg = self._header["msg"]
        self._header = self.__generateHeader()
        self._header["req"] = msg
        self.__setContent(body_object, error_object)
        self._initialised = True
        return self
    
    def acknowledge_withError(self, code, description, ack=False):
        ''' Acknowledge a request with sending an error
        
        Args:
            code (int): the code describing the occurred error
            description (str): a describing string for the error
            ack (bool, optional): should the error-message be acknowledged (default: False)
            
        Returns:
            This Function returns the object, on which the function got called
        '''
        error = {"code":code, "description":description}
        request = Request(self._moduleName).parse(self.toDictionary())
        return request._acknowledge(error_object=error)
        
    def acknowledge_withSuccess(self, data):
        ''' Generates a data acknowledging this request
        
        Args:
            data (object): a object containing the information
            
        Returns:
            This Function returns the object, on which the function got called
        '''
        request = Request(self._moduleName).parse(self.toDictionary())
        return request._acknowledge(body_object=data)
                
    def parse(self, msg_dic):
        ''' Parsing a message-dictionary received by socket.io to initialise a request
        While parsing, parts that can be validated get validated.
        Validating the body requires knowledge of the funktion that should be executed. theirfor validation is required through the receiving module
        
        Args:
            msg_dic (dict): dictionary representing the message
            
        Returns:
            This Function returns the object, on which the function got called
        '''
        ## reading header
        key = "header"
        if msg_dic.has_key(key):
            self._header = self.__parseHeader(msg_dic["header"])
            
        ## reading body
        key = "body"
        if msg_dic.has_key(key):
            self._body = msg_dic[key]
          
        ## reading error  
        key = "error"
        if msg_dic.has_key(key):
            self._error = msg_dic[key]
            
        self._initialised = True
        return self
    
    def __parseHeader(self, header):
        newHeader = dict()
        kk = "msg" ## defining key for new dict
        if header.has_key(kk):
            newHeader[kk] = dict()
            for key, value in header[kk].items():
                newHeader[kk][str(key)] = str(value)
                
        kk = "req" ## defining key for new dict
        if header.has_key(kk):
            newHeader[kk] = dict()
            for key, value in header[kk].items():
                newHeader[kk][str(key)] = str(value)
        return newHeader
    
    def get(self, *args):
        ''' This Function gets a attribute from the dictionary specified by args
        
        Args:
            *args (list): a list with stringidentifiers, which value should be returned
            
        Returns:
            The requested value
            
        Raises:
            Request_ValueUnset_Exception: If the requested value could not be found in the request
        '''
        requested_dict = None
        if len(args) > 0:
            first_id = args[0]
            if first_id == "header":
                requested_dict = self._header
            elif first_id == "body":
                requested_dict = self._body
            elif first_id == "error":
                requested_dict = self._error
            else:
                raise Request_ValueUnset_Exception(first_id)
        
        args_list = list()
        for i in range(1,len(args)):
            args_list.append(args[i])
            
        value = requested_dict
        if requested_dict is None:
            raise Request_ValueUnset_Exception(first_id)
        else:
            for arg in args_list:
                if not value.has_key(arg):
                    raise Request_ValueUnset_Exception(arg)
                value = value[arg]
        return value
    
    def isAckRequired(self):
        '''
        Returns:
            Whether acknowledging a request is required or not
        '''
        if self._header["msg"].has_key("ack"):
            if not str(self._header["msg"]["ack"]).lower() == "false":
                return True
        return False
        
    def __generateHeader(self, ack=None):
        header = dict()
        if ack is None:
            header["msg"] = {"id":generateID(), "emitter":self._moduleName, "timestamp":time.time()*1000}
        else:
            header["msg"] = {"id":generateID(), "emitter":self._moduleName, "timestamp":time.time()*1000, "ack":ack}
        return header
    
    def __setContent(self, body_object=None, error_object=None):
        if error_object is not None and body_object is not None:
            raise Request_Invalid_Exception("Error and Body are set")
        else:
            self._error = None
            self._body = None
            if body_object is not None:
                self._body = body_object
            if error_object is not None:
                self._error = error_object
    
    def validateBody(self, fkt):
        ''' This functions validates the requests body against the given function
        
        Args:
            fkt (function): a function validating a special body
            
        Returns:
            False if not validateable, else True
        '''
        return fkt(self._body)
    
    def toDictionary(self):
        ''' This function is used to process the object to a dictionary sendable by socket.io
        
        Returns:
            Dictionary-representation of the request
        '''
        if not self._initialised:
            raise Exception("Request not initialised")
        else:
            request = dict()
            request["header"] = self._header
            if self._body is not None:
                request["body"] = self._body
            if self._error is not None:
                request["error"] = self._error
            return request
    
    def __str__(self):
        ''' Putting the whole request to a printable string'''
        return "Request-Object: " + str(self.toDictionary())
    
def parse_target(body):
    ## TODO: parsing a supposed target, whether requirements are met
    pass
   
def generateID():
    ''' generating a new random unique ID for a request'''
    return "123456789" ## TODO: yeah well, this should not be unique at all...