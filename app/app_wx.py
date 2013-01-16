# -*- coding: utf-8 -*-

import wx
import numpy as num
import matplotlib
matplotlib.use( 'WXAgg' )
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
matplotlib.interactive( True )
import pprint, time, random
from threading import Event, Thread
import drivers
from os import sep

#configuracion de los dispositivos(del fichero)
config = {}

pp = pprint.PrettyPrinter(indent=4)

#plot values
sensorVal = []
timeVal = []


#drivers de los controladores
contrdrivers = []

MAXNUMBERVAL=10


# Some classes to use for the notebook pages.  Obviously you would
# want to use something more meaningful for your application, these
# are just for illustration.


def convertSeconds(x):
	res = ""
	sec = x
	min = int(x / 60)
	if min > 0:
		h = int(min / 60)
		sec -= 60 * min
		if h>0:
			d = int(h / 24)
			min -= h * 60
			if d >0:
				res = "%d:" % d
				h -= d * 24
			res +=  ("%d:" % h)
		res +=  ("%d:" % min)
	res += ("%d" % sec	 )
	return res



class PlotPanel(wx.Panel):

	class ChannelPanel(wx.Panel):
		#i index of controller in the plot
		def __init__(self,parent,outerRef, i, j):
			wx.Panel.__init__(self,parent)	
			self.plotPanel = outerRef
			self.i = i
			self.j = j
			cpps = wx.BoxSizer(wx.HORIZONTAL)
			self.SetSizer(cpps)
			chName = wx.StaticText(self, -1, config['controllers'][outerRef.r[i]]['channels'][j]['name'], size=(100,30))
			chVal = wx.TextCtrl(self, wx.ID_ANY)
			outerRef.tb[i].append(chVal)
			chErrorVal = wx.TextCtrl(self, wx.ID_ANY)
			outerRef.tberror[i].append(chErrorVal)
			colourPicker = wx.ColourPickerCtrl(self, wx.ID_ANY, col= sensorVal[outerRef.r[i]][j]['colour'] )
			colourPicker.Bind(wx.EVT_COLOURPICKER_CHANGED, self.changeColour)
			outerRef.cp[i].append(colourPicker)	
			visButton = wx.Button(self,-1,'Visible')
			self.visVal = wx.TextCtrl(self, wx.ID_ANY)
			self.visVal.SetValue("SI")

			visButton.Bind(wx.EVT_BUTTON, self.pushVisButton)
			outerRef.vis[i].append(True)
			cpps.Add(chName)
			cpps.Add(chVal)
			cpps.Add(chErrorVal)
			cpps.Add(colourPicker)
			cpps.Add(visButton)
			cpps.Add(self.visVal)

		def changeColour(self,event):
			sensorVal[self.plotPanel.r[self.i]][self.j]['colour'] = event.GetColour()

		def pushVisButton(self,event):
			self.onPushVisButton()			

		def onPushVisButton(self):
			self.plotPanel.vis[self.i][self.j] = not self.plotPanel.vis[self.i][self.j]
			self.visVal.SetValue(self.plotPanel.vis[self.i][self.j] and "SI" or 'NO')


	class ControllerPanel(wx.Panel):
		def __init__(self,parent,plotPanel,i):
			wx.Panel.__init__(self,parent)
			self.plotPanel = plotPanel
			self.i = i
			cp = wx.BoxSizer(wx.VERTICAL)
			c = config['controllers'][plotPanel.r[i]]	
			self.chPanels = []
			cpnamesizer = wx.BoxSizer(wx.HORIZONTAL)
			cpname = wx.Panel(self)
			cpnamesizer.Add(wx.StaticText(cpname, -1, c['name'], size=(100,30)), 0)
			visButton = wx.Button(cpname,-1,"Visible(toggle)")
			visButton.Bind(wx.EVT_BUTTON, self.pushVisButton)
			cpnamesizer.Add(visButton)
			cpname.SetSizer(cpnamesizer)
			cp.Add(cpname)
			cpname.SetSizer(cpnamesizer)
			for j,ch in enumerate(c['channels']):
				cpp = PlotPanel.ChannelPanel(self,plotPanel,i,j)
				self.chPanels.append(cpp)
				cp.Add(cpp)
			self.SetSizer(cp)
			

		def pushVisButton(self,event):
			for j in range(0,len(self.plotPanel.vis[self.i])):
				self.chPanels[j].onPushVisButton()



	#type 1 = monitor temp y presion , 2 = monitor temp , 3 = monitor presion, 4 = var temp y pres , 5 = var temp, 6 = var presion
	def __init__( self, parent, type):
		from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
		from matplotlib.figure import Figure
		from matplotlib.ticker import FuncFormatter,LogFormatterExponent, LogLocator, LogFormatterMathtext
                from math import log10

		# initialize Panel
		wx.Panel.__init__(self, parent)
		#scroll
		scroll = wx.ScrolledWindow(self, -1)
		self.type = type				
		self.SetBackgroundColour(wx.NamedColor("WHITE"))

		self.figure = Figure()
		self.ax1 = self.figure.add_subplot(111  , autoscale_on = True)
		
		#gridlines
		self.ax1.xaxis.grid(color='gray', linestyle='dashed')
		self.ax1.yaxis.grid(color='gray', linestyle='dashed')

		self.ax1.set_xlabel('time ([[[d:]h:]m:]s)')
		#x = time value, pos = tick position
		def timeAxisFormat(x, pos):
			#TODO use a python  time func
			return convertSeconds(x)

		self.ax1.xaxis.set_major_formatter(FuncFormatter(timeAxisFormat))
		if type == 1 or type == 4:
			self.r = range(0,len(config['controllers']))
			self.ax2 = self.ax1.twinx()
			self.ax2.xaxis.set_major_formatter(FuncFormatter(timeAxisFormat))
			if type == 1:
				self.ax1.set_ylabel('Temp(K)', color='b')
				self.ax2.set_ylabel('Presion(mbar)', color='r')
				self.ax2.yaxis.set_major_formatter(LogFormatterMathtext())
				#self.ax2.yaxis.set_major_locator(LogLocator())

			else:
				self.ax1.set_ylabel('Variacion Temp(K/h)', color='b')
				self.ax2.set_ylabel('Variacion Presion(mbar/h)', color='r')
				
		else:
			self.r = []
			for i,c in enumerate(config['controllers']):
				if (c['type'] == 'T' and (type == 2 or type == 5)) or (c['type'] == 'P' and (type == 3 or type == 6)) :
					self.r.append(i)
			if type == 2:
				self.ax1.set_ylabel('Temp(K)', color='b')
			elif type == 3:
				self.ax1.set_ylabel('Presion(mbar)', color='r')
				#self.ax1.yaxis.set_major_formatter(LogFormatterExponent())
				self.ax1.yaxis.set_major_formatter(LogFormatterMathtext())
				#self.ax1.yaxis.set_major_locator(LogLocator())
			elif type == 6:
				self.ax1.set_ylabel('Variacion Presion(mbar/h)', color='r')
			else:
				self.ax1.set_ylabel('Variacion Temp(K/h)', color='b')

		sizer = wx.BoxSizer(wx.HORIZONTAL)
		s1 = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(s1, 1)	
		s2 = wx.BoxSizer(wx.VERTICAL)
		sizer.Add(s2)	
		self.cp = []	
		self.vis = []
		self.tb = []
		self.tberror = []
		for i in range(0, len(self.r)):
			tb1 = []
			tberror1 = []
			cp1 = []
			vis1 = []
			self.tb.append(tb1)
			self.tberror.append(tberror1)
			self.cp.append(cp1)
			self.vis.append(vis1)
			s1.Add(PlotPanel.ControllerPanel(scroll,self,i))

		#plot
		self.canvas = FigureCanvas(scroll, -1, self.figure)
		s2.Add(self.canvas, 1)
		self.Fit()
		#plot toolbar 
		toolbar = NavigationToolbar2Wx(self.canvas)
		toolbar.Realize()
		# On Windows platform, default window size is incorrect, so set
		# toolbar width to figure width.
		tw, th = toolbar.GetSizeTuple()
		fw, fh = self.canvas.GetSizeTuple()
		toolbar.SetSize(wx.Size(fw, th))
		s2.Add(toolbar, 0 , wx.EXPAND)
		toolbar.update()

		self.SetSizer(sizer)
		self.Show(True)
		#TODO scroll set size
		scroll.SetSize((wx.DisplaySize()[0], 600))
		scroll.EnableScrolling(False,True)
		#400 = 10*100 - 600(height)	
		#scroll.SetScrollbars(0,10,0,100,0,400)
		scroll.SetScrollbars(0,10,0,100,0,0)



	def OnPaint(self,event):
		repaint(self)
	
	def repaint(self):
                if (len(timeVal)>1):
                        for i in range(0,len(self.r)):
                                c = config['controllers'][self.r[i]]
                                for j in range(0, len(c['channels'])):
                                        #TODO check if colour changed ?
                                        self.cp[i][j].SetColour(sensorVal[self.r[i]][j]['colour'])
                                        if ((self.type == 1) or (self.type == 2) or (self.type == 3)):
                                                dataY = sensorVal[self.r[i]][j]['mon'][-2:]	
                                        else:
                                                dataY = sensorVal[self.r[i]][j]['var']	
                                        #check visible
                                        if(self.vis[i][j]):
                                                if (self.type == 1 or self.type == 4) and c['type'] == 'P':
                                                        self.ax2.plot(timeVal[-2:],dataY, sensorVal[self.r[i]][j]['colour'].GetAsString(flags = wx.C2S_HTML_SYNTAX) )
                                                else:
                                                        self.ax1.plot(timeVal[-2:],dataY, sensorVal[self.r[i]][j]['colour'].GetAsString(flags = wx.C2S_HTML_SYNTAX ) )
                                        #TODO put this out of if because first values are not shown                
                                        self.tb[i][j].SetValue("%E" % dataY[-1])
                                        if(sensorVal[self.r[i]][j].has_key('error')):
                                                self.tberror[i][j].SetValue( sensorVal[self.r[i]][j]['error'])
                                        else:
                                                self.tberror[i][j].SetValue("OK")
                                        
		self.canvas.draw()


def initDriver():
	for  i,c in enumerate(config['controllers']):
		contrdrivers.append(drivers.getDriverInstance(c['model'] , c['port']))
		sensorVal1 = []
		sensorVal.append(sensorVal1)
		for j in range(0,len(c['channels'])):
			sensorVal2 = {'mon':[], 'colour' : wx.Colour( random.randint(0,255) , random.randint(0,255) , random.randint(0,255)) }
			sensorVal1.append(sensorVal2)



class ConfigPanel(wx.Panel):

	class ConfigChannelPanel(wx.Panel):
		
		class ChannelParamButton(wx.Button):
			def __init__(self,parent,i,j,name):
				wx.Button.__init__(self,parent,-1, name)
				self.i = i
				self.j = j
				self.parent = parent
				self.name = name
				self.Bind(wx.EVT_BUTTON, self.pushParamButton)
				
			def pushParamButton(self,event):
				val = contrdrivers[self.i].queryChannelParam(self.name,self.j)
                                dial = wx.TextEntryDialog(self.parent,"current value = %s" % val, "Set Parameter Dialog")
				ret = dial.ShowModal()
				if ret == wx.ID_OK and dial.GetValue().strip()!="":
					contrdrivers[self.i].setChannelParam(self.name,self.j,dial.GetValue())


		def __init__(self,parent, i,j):
			wx.Panel.__init__(self,parent)
			self.i = i
			self.j = j
			self.parent = parent
			ch = config['controllers'][i]['channels'][j]
			cpnamesizer = wx.BoxSizer(wx.HORIZONTAL)
			cpnamesizer.Add(wx.StaticText(self, -1, ch['name'], size=(100,30)), 0)
			for k in range(0, len(contrdrivers[i].channelParams)):	
				cpnamesizer.Add(ConfigPanel.ConfigChannelPanel.ChannelParamButton(self,i, j,contrdrivers[i].channelParams[k]))
			self.SetSizer(cpnamesizer)


	class ConfigControllerPanel(wx.Panel):
		
		class ControllerParamButton(wx.Button):
			def __init__(self,parent,i,name):
				wx.Button.__init__(self,parent,-1, name)
				self.i = i
				self.parent = parent
				self.name = name
				self.Bind(wx.EVT_BUTTON, self.pushParamButton)
				
			def pushParamButton(self,event):
				val = contrdrivers[self.i].queryControllerParam(self.name)
				dial = wx.TextEntryDialog(self.parent,"current value = %s" % val, "Set Parameter Dialog")
				ret = dial.ShowModal()
				if ret == wx.ID_OK and dial.GetValue().strip()!="":
					contrdrivers[self.i].setControllerParam(self.name,dial.GetValue())


		def __init__(self,parent, i):
			wx.Panel.__init__(self,parent)
			self.i = i
			c = config['controllers'][i]
			cp = wx.BoxSizer(wx.VERTICAL)
			cpnamesizer = wx.BoxSizer(wx.HORIZONTAL)
			cpname = wx.Panel(self)
			cpnamesizer.Add(wx.StaticText(cpname, -1, "%s - %s" % (c['name'], c['model']) , size=(200,30)), 0)
			for k in range(0, len(contrdrivers[i].controllerParams)):	
				cpnamesizer.Add(ConfigPanel.ConfigControllerPanel.ControllerParamButton(cpname,i, contrdrivers[i].controllerParams[k]))
			cpname.SetSizer(cpnamesizer)
			cp.Add(cpname)
			cpname.SetSizer(cpnamesizer)
			for j in range(0,len(c['channels'])):
				cpp = ConfigPanel.ConfigChannelPanel(self,i,j)
				cp.Add(cpp)
			self.SetSizer(cp)
	

	def updateTimeValue(self,event):
		self.frameref.createTimer()
		

	def __init__(self, parent, frameref):
		wx.Panel.__init__(self,parent)
		self.frameref = frameref
		sizer = wx.BoxSizer(wx.VERTICAL)
		s1 = wx.BoxSizer(wx.HORIZONTAL)
		sizer.Add(s1)
                #poll time interval
		pTime = wx.Panel(self)
		pTimeSizer = wx.BoxSizer(wx.VERTICAL)
		pTime.SetSizer(pTimeSizer)
		pTimeSizer.Add(wx.StaticText(pTime,-1,"Tiempo(s)"))
		self.timeSlider = wx.Slider(pTime, -1, value = 30, minValue = 5, maxValue = 100, size = (200,-1) , style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
		self.timeSlider.Bind(wx.EVT_SLIDER, self.updateTimeValue)

		pTimeSizer.Add(self.timeSlider)
		s1.Add(pTime)
		#var interval
		pVar = wx.Panel(self)
		pVarSizer = wx.BoxSizer(wx.VERTICAL)
		pVar.SetSizer(pVarSizer)
		pVarSizer.Add(wx.StaticText(pVar,-1,"Variacion(número de valores para la dif)"))
		self.varSlider = wx.Slider(pVar, -1, value = 1, minValue = 1, maxValue = MAXNUMBERVAL , size = (200,-1) , style = wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS)
		pVarSizer.Add(self.varSlider)
		s1.Add(pVar)
                #outputFile name
                sizer.Add(wx.StaticText(self, -1 , "Output File: %s" % frameref.outputFile.name))        
		
		p = wx.Panel(self)
		nb = wx.Notebook(p)
		sizerp = wx.BoxSizer()
		for i in range(0 , len(config['controllers'])):
			nb.AddPage(ConfigPanel.ConfigControllerPanel(nb,i), config['controllers'][i]['name'])
		sizerp.Add(nb)
		p.SetSizer(sizerp)
		sizer.Add(p)
		self.SetSizer(sizer)

		


class MainFrame(wx.Frame):
	def __init__(self , configFromFile):
		global config
		config  = configFromFile
		wx.Frame.__init__(self, None, title="Simple Notebook Example", size=wx.DisplaySize())

		#open output file, defaultDir/File --  wx.FileDialog contr
		dial = wx.FileDialog(self, "Guardar los valores" ,style = wx.FD_SAVE)
		filename = "outfile" #default save file
		ret = dial.ShowModal()
		if ret == wx.ID_OK:
			filename = dial.GetDirectory() + sep + dial.GetFilename()
			#print "filename = %s" % filename
		self.outputFile = open(filename , "w")


		# Here we create a panel and a notebook on the panel
		p = wx.Panel(self)
		nb = wx.Notebook(p)

		#init driver
		initDriver()
		# create the page windows as children of the notebook
		self.page1 = PlotPanel(nb, 1)
		self.page2 = PlotPanel(nb, 2)
		self.page3 = PlotPanel(nb, 3)
		self.page4 = PlotPanel(nb, 4)
		self.page5 = PlotPanel(nb, 5)
		self.page6 = PlotPanel(nb, 6)
		self.configPanel = ConfigPanel(nb, self)

		# add the pages to the notebook with the label to show on the tab
		nb.AddPage(self.page1, "Monitor")
		nb.AddPage(self.page2, "Monitor Temp")
		nb.AddPage(self.page3, "Monitor Presion")
		nb.AddPage(self.page4, "Variacion")
		nb.AddPage(self.page5, "Variacion Temp")
		nb.AddPage(self.page6, "Variacion Presion")
		nb.AddPage(self.configPanel, "Configuracion")
		# finally, put the notebook in a sizer for the panel to manage
		# the layout
		sizer = wx.BoxSizer()
		sizer.Add(nb, 1, wx.EXPAND)
		p.SetSizer(sizer)
		#ask before quit
		self.Bind(wx.EVT_CLOSE, self.OnClose)
		#write header
		fileline = "Tiempo"
		for c in config['controllers']:
			for ch in c['channels']:
				fileline += ("%s-%s\t" % (c['name'],ch['name']))
		fileline+="\n"
		self.outputFile.write(fileline)
		#start timer
		self.createTimer()

	def createTimer(self):
		#timer interval attribute cannot be set
		if (self.__dict__.has_key('timer') and self.timer.IsRunning()):
			self.timer.Stop()
		self.timer = wx.Timer(self)		
		self.Bind(wx.EVT_TIMER, self.pollValues, self.timer)
		self.timer.Start(self.configPanel.timeSlider.GetValue() * 1000)
		




	def pollValues(self, event):
		if (not self.__dict__.has_key("startTime")):
			self.startTime = int(time.time())
			newtimeval = 0
		else:
			newtimeval = int(time.time()) - self.startTime
		timeVal.append(newtimeval)
		fileline = convertSeconds(newtimeval)
		for i,c in enumerate(config['controllers']):
			values = contrdrivers[i].getValues()
			for j in range(len(c['channels'])):
				n = self.configPanel.varSlider.GetValue()
                                #in matplotlib only the last 2 values are needed in order to trace the line        
				if (len(sensorVal[i][j]['mon']) < n):
                                        sensorVal[i][j]['var'] = [0,0]
                                else:
                                        sensorVal[i][j]['var'][0] = sensorVal[i][j]['var'][1]
                                        sensorVal[i][j]['var'][1] = (values[j]['data'] - sensorVal[i][j]['mon'][-n]) / (timeVal[-1] - timeVal[-n-1]) * 3600                                                                                                      
				fileline+=("\t%f" % values[j]['data'] )
				sensorVal[i][j]['mon'].append(values[j]['data'])
				if(values[j].has_key('error')):
        				sensorVal[i][j]['error'] = values[j]['error']
				if(len(timeVal) > MAXNUMBERVAL):
					sensorVal[i][j]['mon'].pop(0)
		fileline+="\n"
		self.outputFile.write(fileline)
		if(len(timeVal) > MAXNUMBERVAL):
			timeVal.pop(0)
		self.page1.repaint()	
		self.page2.repaint()	
		self.page3.repaint()	
		self.page4.repaint()	
		self.page5.repaint()	
		self.page6.repaint()	


	def OnClose(self, event):
		dial = wx.MessageDialog(None, 'Are you sure to quit?', 'Question' , wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
		ret = dial.ShowModal()
		if ret == wx.ID_YES:
			self.Destroy()
		else:
			event.Veto()

	def __del__(self):
		self.outputFile.close()




