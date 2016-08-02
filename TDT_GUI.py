##GUI for controlling TDT data acquisition

import Tkinter as Tk
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import data_stream as stream
import time
import os
import multiprocessing as mp

##GLOBAL VARIABLES##

##a root folder to store the data. Make it if it does not exist.
rootFolder = os.path.normpath("C:/Data/"+time.strftime("%m_%d_%y"))
if not os.path.exists(rootFolder):
	os.makedirs(rootFolder)

##the name of the file to save ##TODO: make this a GUI option
fname = "animalx.hdf5"

##the full file path
filepath = os.path.join(rootFolder, fname)

##font style
myFont = ("Helvetica", 18)

##path of circuit to load to hardware
circ_path = r"C:\Users\TDT\Documents\tdt_circuits\recording_circuit_basic.rcx"

##channels to add. TODO: make this an editable GUI thing
channels = range(1,33)

##max length of recording in mins
max_duration = 120 ##TODO: add to editable GUI

##create shared objects to synchronize processes
dataQueue = mp.Queue()
startFlag = mp.Event()
startFlag.clear()

##initialize the main window
mainWin = Tk.Tk()
mainWin.wm_title("TDT GUI 1.0")

##GUI functions and widgets##
class LED(Tk.Frame):
	"""A Tkinter LED Widget.
	a = LED(root,10)
	a.set(True)
	current_state = a.get()"""
	OFF_STATE = 0
	ON_STATE = 1
	
	def __init__(self,master,size=10,**kw):
		self.size = size
		Tk.Frame.__init__(self,master,width=size,height=size)
		self.configure(**kw)
		self.state = LED.OFF_STATE
		self.c = Tk.Canvas(self,width=self['width'],height=self['height'])
		self.c.grid()
		self.led = self._drawcircle((self.size/2)+1,(self.size/2)+1,(self.size-1)/2)
	def _drawcircle(self,x,y,rad):
		"""Draws the circle initially"""
		color="red"
		return self.c.create_oval(x-rad,y-rad,x+rad,y+rad,width=rad/5,fill=color,outline='black')
	def _change_color(self):
		"""Updates the LED colour"""
		if self.state == LED.ON_STATE:
			color="green"
		else:
			color="red"
		self.c.itemconfig(self.led, fill=color)
	def set(self,state):
		"""Set the state of the LED to be True or False"""
		self.state = state
		self._change_color()
	def get(self):
		"""Returns the current state of the LED"""
		return self.state


##create a label class that includes an LED
class statusLabel(Tk.Frame):
	def __init__(self, parent, name):
		self.name = name
		self.state = False
		Tk.Frame.__init__(self,parent,width=250,height=150,bd=1,padx=5,pady=5)
		self.parent = parent
#		self.configure(**kw)
		self.cmdState = Tk.IntVar()
		self.label = Tk.Label(self, text = self.name, font = myFont)
		self.led = LED(self, 50)
		self.label.grid(column = 0, row = 0)
		self.led.grid(column = 2, row = 0)

	def toggleState(self, status):
		"""updates state and LED
		"""
		self.state = status
		self.updateLED()

	def updateLED(self):
		if self.state:
			self.led.set(True)
		else:
			self.led.set(False)

initialized = statusLabel(mainWin, "Ready")
initialized.grid(row = 0, column = 0)

##create a button class that includes an LED
class controlButton(Tk.Frame):
	def __init__(self, parent, name, function, args = None, flag = None):
		self.name = name
		self.function = function
		self.state = False
		self.args = args
		self.flag = flag
		Tk.Frame.__init__(self,parent,width=250,height=150,bd=1,padx=5,pady=5)
		self.parent = parent
#		self.configure(**kw)
		self.cmdState = Tk.IntVar()
		self.label = Tk.Label(self, text = self.name, font = myFont)
		self.set_state = Tk.Checkbutton(self, text = "On/Off", font = myFont, 
			variable = self.cmdState, command = self.toggleCmdState)
		self.led = LED(self, 50)
		self.label.grid(column = 0, row = 0)
		self.set_state.grid(column = 1, row = 0)
		self.led.grid(column = 2, row = 0)

	def toggleCmdState(self):
		"""reads the current state of the checkbox,
		updates LED widget, calls function and sets variable
		"""
		self.state = self.cmdState.get()
		self.updateLED()
		if self.state:
			if self.flag != None:
				self.flag.set()
			if self.args == None:
				self.function()
			else:
				##call "function" with "args"
#				print "about to call with state = " + str(self.args[-1].is_set())
				self.function(*self.args)
#				print "call complete; state = " + str(self.args[-1].is_set())
		elif self.state == False and self.flag != None:
			self.flag.clear()

	def updateLED(self):
		if self.state:
			self.led.set(True)
		elif self.state == False:
			self.led.set(False)

##some functions to spawn processes to run the recording/streaming functions
def init():
	##create the file to save
	stream.setup_file(filepath, channels, max_duration)
	##spawn processes to handle the data
	writer = mp.Process(target = stream.write_to_file, args = (dataQueue,filepath))
	streamer = mp.Process(target = stream.hardware_streamer, args = (
		circ_path, channels, dataQueue, startFlag))
	writer.start()
	streamer.start()
	initialized.toggleState(True)

def record():
	print "Recording started"
	##TODO: generate some IO pulse to trigger the pi box logger
 
initButton = Tk.Button(mainWin, text = "Init", command = init, font = myFont)
initButton.grid(column = 0, row = 1)

recordButton = controlButton(mainWin, "Record", record, args = None, flag = startFlag)
recordButton.grid(row = 0, column = 1)

Tk.mainloop()





