##GUI for controlling TDT data acquisition

import Tkinter as Tk
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import TDT_control_ax as TDT
import data_stream as stream
import time
import os

##GLOBAL VARIABLES##

##a root folder to store the data. Make it if it does not exist.
rootFolder = os.path.normpath("C:/Data/"+time.strftime("%m_%d_%y_%H"))
if not os.path.exists(rootFolder):
	os.makedirs(rootFolder)

##font style
myFont = ("Helvetica", 18)

##path of circuit to load to hardware
circ_path = ""

##size of data chunks to stream, in seconds
chunk_size = 0.1

##TDT activeX object
rz2 = TDT.RZ2(circ_path)
rz2.load_circuit(local = False, start = False)
chunk_size = chunk_size*rz2.get_fs()

##channels to add. TODO: make this an editable GUI thing
channels = range(1,33)


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


##initialize the main window
mainWin = Tk.Tk()
mainWin.wm_title("TDT GUI 1.0")


##create a button class that includes an LED
class controlButton(Tk.Frame):
	def __init__(self, parent, name, function, args = None, add_flag = False):
		self.name = name
		self.function = function
		self.state = False
		self.args = args
		if args is not None and add_flag == True:
			self.args.append(self.state)
		Tk.Frame.__init__(self,parent,width=250,height=150,relief=Tk.SUNKEN,bd=1,padx=5,pady=5)
		self.parent = parent
		self.configure(**kw)
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
			if self.args == None:
				self.function()
			else:
				##call "function" with "args"
				self.function(*self.args)

	def updateLED(self):
		self.led.set(self.state)


##create some control buttons
circuitButton = controlButton(mainWin, "start circuit", rz2.start(), args = None)

recordButton = controlButton(mainWin, "Record", stream.TDT_stream, args = (rz2, channels,
	rootFolder, chunk_size), add_flag = True)

circuitButton.grid(row = 0, column = 0)
recordBbutton.grid(row = 1, column = 0)





