import wx
from app_wx import MainFrame
import ConfigParser
import sys,time,os
import pprint
from string import atoi



pp = pprint.PrettyPrinter(indent=4)
def readConfigFile(configFile):
	configReader = ConfigParser.ConfigParser()
	configReader.read(configFile)
	config = {}
	config['name']=configReader.get("GENERAL", "GrupoMedida")
	numControllers = atoi(configReader.get("GENERAL" ,'NumControllers'))
	config['controllers'] = []
	for i in range(0,numControllers):
		c = {}
		c['name'] = configReader.get("CONTROLLER%d" % (i+1) , 'Name')
		c['port'] = configReader.get("CONTROLLER%d" % (i+1) , 'Port')
		c['type'] = configReader.get("CONTROLLER%d" % (i+1) , 'Type')
		c['model'] = configReader.get("CONTROLLER%d" % (i+1) , 'Model')
		numChannels = atoi(configReader.get("CONTROLLER%d" % (i+1) , 'NumChannels'))
		c['channels'] = []
		for j in range(0,numChannels):
				c['channels'].append( {'name': configReader.get("CONTROLLER%d" % (i+1) , "Channel%d" % (j + 1)) } )
		config['controllers'].append(c)
	return config	
        
if __name__ == "__main__":


 
	if len(sys.argv)>1:
		configFile = sys.argv[1]
	else:
		configFile = os.getcwd() + os.sep + "config.txt"
	#TODO values with "" in config file remove ""
        config = readConfigFile(configFile)				
	#pp.pprint(config)	
		
	app = wx.App(redirect = False)
	MainFrame(config).Show(True) 
	app.MainLoop() 

