# -*- coding: utf-8 -*-

import random, time, pprint
import serial
from math import log10
from array import array

pp = pprint.PrettyPrinter(indent=4)

class RandomValues:
	def __init__(self,numberValues):
		self.numberValues = numberValues
		self.controllerParams = ["Controller1Param1", "ControllerParam2"]
		self.channelParams = ["ChannelParam1", "ChannelParam2"]

	def getValues(self):
		r = []
		for i in range(0,self.numberValues):
			r.append({'data':random.random()})
		return r

	def queryControllerParam(self,param):
		return "%f" % random.random() 

	def setControllerParam(self,param, value):
		print "set controller param %s to %s" %(param,value)
		
	def queryChannelParam(self,param, numberChannel):
		return "%f" % random.random() 

	def setChannelParam(self,param, numberChannel,value):
		print "set controller channel %d param %s to %s" %(numberChannel, param,value)


class Random6(RandomValues):
	def __init__(self, port):
		RandomValues.__init__(self,6)
		
class Random8(RandomValues):
	def __init__(self, port):
		RandomValues.__init__(self,8)






def getDriverInstance(model, port):
	object = globals()[model]
	return object(port)


#Serial.__init__(port=None, baudrate=9600, bytesize=EIGHTBITS, parity=PARITY_NONE, stopbits=STOPBITS_ONE, timeout=None, xonxoff=0, rtscts=0, interCharTimeout=None)
#    Parameters:	
#
#        * port – Device name or port number number or None.
#        * baudrate – Baud rate such as 9600 or 115200 etc.
#        * bytesize – Number of data bits. Possible values: FIVEBITS, SIXBITS, SEVENBITS, EIGHTBITS
#        * parity – Enable parity checking. Possible values: PARITY_NONE PARITY_EVEN PARITY_ODD PARITY_MARK PARITY_SPACE
#        * stopbits – Number of stop bits. Possible values: STOPBITS_ONE STOPBITS_ONE_POINT_FIVE STOPBITS_TWO
#        * timeout – Set a read timeout value.
#        * xonxoff – Enable software flow control.
#        * rtscts – Enable hardware (RTS/CTS) flow control.
#        * interCharTimeout – Inter-character timeout, None to disable (default).
#
#    Raises ValueError:
#     	
#
#    Will be raised when parameter are out of range, e.g. baud rate, data bits.
#    Raises SerialException:
#     	
#
#    In case the device can not be found or can not be configured.
#
#    The port is immediately opened on object creation, when a port is given. It is not opened when port is None and a successive call to open() will be needed.
#
#    Possible values for the parameter port:
#
#        * Number: number of device, numbering starts at zero.
#        * Device name: depending on operating system. e.g. /dev/ttyUSB0 on GNU/Linux or COM3 on Windows.
#
#    Possible values for the parameter timeout:
#
#        * timeout = None: wait forever
#        * timeout = 0: non-blocking mode (return immediately on read)
#        * timeout = x: set timeout to x seconds (float allowed)
#
#    Note that enabling both flow control methods (xonxoff and rtscts) together may not be supported. It is common to use one of the methods at once, not both.



class ControllerDriver:


	def __del__(self):
		self.serial.close()

	def query(self, command):
      		self.serial.flushInput()	
		self.send(command)
		try:
        		data = self.serial.read(1)              # read one, blocking
                except serial.SerialTimeoutException:
                        print "Timeout exception for %s" % self.serial.port
                        return -1
                #TODO all controllers need this?
                time.sleep(0.1)        
		n = self.serial.inWaiting()             # look if there is more
		if n:
			data = data + self.serial.read(n)   # and get as much as possible
		#print "Data received"
		#pp.pprint(data)
		retdata = str(data).strip()
		if retdata == "":
                        print "No data received in %s " % self.serial.port
       		return retdata
	
	def send(self,command):
                #print(" Send Command on port = %s: " % self.serial.port)
                #pp.pprint(command)

		self.serial.write(command + "\r\n" )




	#TODO
	#los siguientes no se si se pueden usar para los sensores de presion
	#los parametros configurables de los controladores	
	def getControllerParamValue(self,param):
		if not ( param in self.controllerParams):
			#not defined
			return "-"
		return self.queryControllerParam(param)
				
	#los parametros configurables de los canales de los controladores	
	def getChannelParamValue(self,param, numberChannel):
		if not ( param in self.channelParams):
			#not defined
			return "-"
		return self.queryChannelParam(self,param, numberChannel)
	
	def setControllerParamValue(param, value):
		if not ( param in self.channelParams):
			#not defined
			return 
		self.setControllerParam(param, value) 
	

	def setChannelParamValue(param, numberChannel ,value):
		if not ( param in self.channelParams):
			#not defined
			return 
		self.setChannelParam(param, numberChannel, value) 


class LSDriver(ControllerDriver):
	def __init__(self, port):
                #from doc of LS
                #A character is the smallest piece of information that can be transmitted by the interface. Each
                #character is 10 bits long and contains data bits, bits for character timing and an error detection bit.
                #The instrument uses 7 bits for data in the ASCII format. One start bit and one stop bit are necessary
                #to synchronize consecutive characters. Parity is a method of error detection. One parity bit configured
                #for odd parity is included in each character.
                #Baud 300, 1200, 9600
                #handshake - Software timing
                #Character Bits 1 Start, 7 Data, 1 Parity, 1 Stop
                #Parity Odd
                #terminators: CR(0DH) LF(0AH)
                #20 commands per second maximum
                self.serial = serial.Serial(port, timeout = 1, bytesize=serial.SEVENBITS, parity=serial.PARITY_EVEN)

	def queryControllerParam(self,param):
		return self.query("%s?" % param)

	def setControllerParam(self,param, value):
		self.send("%s %s"% (param , value))
		
	def queryChannelParam(self,param, numberChannel):
		return self.query("%s? %d" % (param , (numberChannel + 1)))

	def setChannelParam(self,param, numberChannel,value):
		self.send( "%s %d,%s" % (param , (numberChannel + 1),value))

        def getHashFromValueAndStatus(self,status,value):
                r = {}
                r['data'] = float(value)
                #if status != '000':
                #       r['error'] = status
								s = int(status)
								if(16<=s and s<32):
									r['error'] = "Temp under range"
								elif(32<=s and s<64):
									r['error'] = "Temp over range"
								elif(64<=s and s<128):
									r['error'] = "Units under range"
								elif(128<=s):
									r['error'] = "Units over range"
                return r

class LS218(LSDriver):
	def __init__(self, port):
		LSDriver.__init__(self, port)
		#TODO  put in a file
		self.controllerParams = ["ALMB", "INTYPEA" , "INTYPEB"]
		self.channelParams = ["ALARM", "INCRV", "INPUT" , "RELAY"]
		self.send("*CLS")

	#intype se puede configurar solo por grupos de canales (A 1-4 y B 5-4)
	def queryControllerParam(self , param):
		if param == "INTYPEA":
                        queryparam = "INTYPE? A"
		elif param == "INTYPEB":
			queryparam = "INTYPE? B"
		else:
                        queryparam = param
		return LSDriver.queryControllerParam(self,queryparam)
			
	
	def setControllerParam(self,param, value):
		if param == "INTYPEA":
                        sendparam = "INTYPE A,"
		elif param == "INTYPEB":
                        sendparam = "INTYPE B,"
		else:
                        sendparam = param
		LSDriver.setControllerParam(self,sendparam,value)


	def getValues(self):
                data = self.query("KRDG?0")
                values = data.split(",")
                if(len(values)!=8):
                        r = []
                        for i in range(0,8):
                                r.append({'data':0, 'error':'No Data'})
                        return r
                floatValues = []
                for i,val in enumerate(values):
                        status = self.query("RDGST? %d" % (i+1))
                        floatValues.append( self.getHashFromValueAndStatus(status,val) )
        	return floatValues

	
			
class LS331(LSDriver):

	def __init__(self, port):
		LSDriver.__init__(self, port)
		#TODO  put in a file
		self.controllerParams = ["BEEP" , "RANGE"]
		self.channelParams = ["INTYPE" , "INCRV",  "SETP", "MOUT" , "ALARM" , "RELAY"]
        
		def getValues(self):
                        return [self.getHashFromValueAndStatus(self.query("RDGST? A"),self.query("KRDG? A")) , self.getHashFromValueAndStatus(self.query("RDGST? B"),self.query("KRDG? B"))]

                

class TPGDriver(ControllerDriver):
	def __init__(self, port):
                # FROM doc : 1 Start bit, 8 data bits, 1 stop bit, no parity bit,no hardware handshake
                self.serial = serial.Serial(port, timeout = 10)

	def queryCommand(self,c):
		data = self.query(c)
		stop = False	
		#3 tries
		i = 0	
		while (not stop and i < 3):		
			#NAK
			if data[0] == chr(15):
				i+=1
			else:
				#6 = ascii(ACK)
				if(data[0] == chr(6)):
					stop = True
				else:
					print "Unexpected received %c" % data[0]
					return 0
		
		#send ENQ
		data = self.query(chr(5))
		return data	


	def queryControllerParam(self,param):
		return self.queryCommand("%s" , param) 

	def setControllerParam(self,param, value):
		self.queryCommand("%s ,%s"% (param , value))
		
	def queryChannelParam(self,param, numberChannel):
		return self.queryCommand("%s%d" % (param , (numberChannel + 1)))

	def setChannelParam(self,param, numberChannel,value):
		self.queryCommand( "%s%d ,%s" % (param , (numberChannel +1 ),value))

        def  getHashFromValueAndStatus(self,statusStr,value):
                status = int(statusStr)
                if status == 0:
                        return {'data':float(value)}
                elif status == 1:                        
                        return {'data':0, 'error':'Underrange'}
                elif status == 2:                        
                        return {'data':0, 'error':'Overrange'}
                elif status == 3:                        
                        return {'data':0, 'error':'Sensor error'}
                elif status == 4:                        
                        return {'data':0, 'error':'Sensor off'}
                elif status == 5:                        
                        return {'data':0, 'error':'No sensor'}
                elif status == 6:                        
                        return {'data':0, 'error':'Identification error'}
                else:
                        return {'data':0, 'error':'Unexpected status %d' % status}
                
                
		



class  TPG252(TPGDriver):
	#2 sensores
	def __init__(self, port):
		TPGDriver.__init__(self, port)
		self.controllerParams = []
		self.channelParams = []

	def getValues(self):
		data = self.queryCommand("PRX")
		#decode values
		data1 = data.split(",")
		#data1[0,2] status
		return [self.getHashFromValueAndStatus(data1[0], data1[1])  , self.getHashFromValueAndStatus(data1[2],data1[3]) ]

		
	


class  TPG256(TPGDriver):
	#6 sensores
	#pueden ser configurados menos
	def __init__(self, port):
		TPGDriver.__init__(self, port)
		self.controllerParams = []
		self.channelParams = []

	def getValues(self):
		r = []
		for i in range(0,6):
			data = self.queryCommand("PR%d"  % (i+1))
       			data1 = data.split(",")
       			r.append( self.getHashFromValueAndStatus(data1[0], data1[1]) )
		return r


		

