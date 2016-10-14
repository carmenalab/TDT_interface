## a GUI to record and visualize data while testing V1 tuning

import numpy as np
import Tkinter as Tk
import time
import os
import multiprocessing as mp
import data_stream as stream
import TDT_control_ax as tdt
import h5py
import V1_test

##some necessary globals
rz2 = None
dataQueue = None
startFlag = mp.Event()
startFlag.clear()

##font style
myFont = ("Helvetica", 18)

##a root folder to store the data. Make it if it does not exist.
rootFolder = os.path.normpath("D:/"+time.strftime("%m_%d_%y"))
if not os.path.exists(rootFolder):
	os.makedirs(rootFolder)
"""
*****CLASS DEFINITIONS******
"""

class entryBox(object):
	"""Tkinter object that contains some editable text"""
	def __init__(self, homeFrame, labelText, preset, grid_row, grid_col):
		self.homeFrame = homeFrame
		self.labelText = labelText
		self.preset = preset
		self.entryString = Tk.StringVar()
		self.entryObj = Tk.Entry(homeFrame, textvariable = self.entryString, font = myFont)
		self.title = Tk.Label(self.homeFrame, text = self.labelText, font = myFont)
		self.entryString.set(self.preset)
		self.title.grid(row = grid_row, column = grid_col)
		self.entryObj.grid(row = grid_row+1, column = grid_col)

#class to create a new Tkinter Frame with all the needed listbox functionality
class UnitListBox(object):
	##take as arguments the master list and master unit list box to work from
	##and the frame that everything will become part of (should be initialized and 
	##packed before creating this object), text for the label,
    ##and whether or not to make an entry box
	def __init__(self, masterList, masterListBox, homeFrame, labelText, 
		grid_row=0,grid_col=0):
		self.masterList = masterList
		self.masterListBox = masterListBox
		#list to store current contents of listbox
		self.unitList = []
		##make the label
		self.title = Tk.Label(homeFrame,text=labelText,font=myFont).grid(row=grid_row,column=grid_col)
		##make the listbox
		self.LB = Tk.Listbox(homeFrame, height = 10, selectmode = 'extended')
		self.LB.grid(row=grid_row+1,column=grid_col)
		##make the buttons
		self.RmvBUT = Tk.Button(homeFrame,text="Remove selected",font=myFont)
		self.RmvBUT.grid(row=grid_row+2,column=grid_col)
		self.AddBUT = Tk.Button(homeFrame, text="Add selected",font=myFont)
		self.AddBUT.grid(row=grid_row+3,column=grid_col)
		self.config_buttons()
	
	#add a unit from the master list, and remove it from the master list
	def Add(self):
		idx = self.masterListBox.curselection()
		for i in idx:
			self.LB.insert('end', self.masterList[i])
			self.unitList.append(self.masterList[i])
		##need to reverse the order of the index list 
		##so we can delete things (long story...)
		idx = sorted(idx,reverse=True)
		for i in idx:
			self.masterListBox.delete(i)
			del self.masterList[i]
	
	#remove a unit and add it back to the master list
	def Rmv(self):
		idx = self.LB.curselection()
		for i in idx:
			self.masterListBox.insert('end', self.unitList[i])
			self.masterList.append(self.unitList[i])
		idx = sorted(idx,reverse=True)
		for i in idx:
			del self.unitList[i]
			self.LB.delete(i)

	##function to set up button functionality
	def config_buttons(self):
		self.RmvBUT.config(command = self.Rmv)
		self.AddBUT.config(command = self.Add)


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
		self.cmdState = Tk.IntVar()
		self.label = Tk.Label(self, text = self.name, font = myFont)
		self.led = LED(self, 40)
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
		self.cmdState = Tk.IntVar()
		self.label = Tk.Label(self, text = self.name, font = myFont)
		self.set_state = Tk.Checkbutton(self, text = "On/Off", font = myFont, 
			variable = self.cmdState, command = self.toggleCmdState)
		self.led = LED(self, 40)
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
				self.function(*self.args)
		elif self.state == False and self.flag != None:
			self.flag.clear()

	def updateLED(self):
		if self.state:
			self.led.set(True)
		elif self.state == False:
			self.led.set(False)

"""
*******Actual recording/streaming/hardware interface functions*******
"""
def init():
	global rz2
	circ_path = circEntry.entryString.get()
	rz2 = tdt.RZ2(circ_path)
	rz2.load_circuit(local=False,start=True)
	rz2.get_status()
	if rz2.is_running:
		systemStatus.toggleState(True)
		startFlag.clear()
	else: 
		print "System connection error..."

def set_DAC():
	global rz2
	if rz2 is not None:
		rz2.get_status()
		if rz2.is_running():
			new_chan = int(DACEntry.entryString.get())
			rz2.set_tag("AD_out",AD_chan)
	else:
		print "Can't set A/D channel..."

def record():
	global startFlag
	global dataQueue
	save_file = saveEntry.entryString.get()
	
	dur = int(maxTimeEntry.entryString.get())
	if len(chans) > 0:
		##create file to save the data
		stream.setup_file(save_file,chans,dur)
		##spawn processes to handle the data
		writer = mp.Process(target = stream.write_to_file, args = (dataQueue,filepath))
		streamer = mp.Process(target = stream.hardware_streamer, args = (
			circ_path, channels, dataQueue, startFlag))
		writer.start()
		streamer.start()
		##give everything a pause to get started
		time.sleep(1)
		startFlag.set()
		recordStatus.toggleState(True)
	else:
		print "No channels selected!"

def stop():
	global startFlag
	global rz2
	startFlag.clear()
	if rz2 is not None and recordStatus.state is False:
		rz2.stop()
	elif recordStatus.state is True:
		recordStatus.toggleState(False)

def run_tuning():
	global rz2
	save_file = saveEntry.entryString.get()
	circ_path = circEntry.entryString.get()
	chans = [int(i) for i in chosenLB.unitList] ##channel numbers are str; convert to int
	if rz2 is not None:
		rz2.stop()
	visual = mp.Process(target=V1_test.run_orientations,args=(save_file,circ_path,chans))
	visual.start()


"""
********GUI SETUP*********
"""

##initialize the main window
mainWin = Tk.Tk()
mainWin.wm_title("TDT_GUI version 2.0")

"""Channel selection"""
chansFrame = Tk.Frame(mainWin)
chansFrame.grid(row=1,column=0)
##a listbox with all potential channels
chansLB = Tk.Listbox(chansFrame,height=10,selectmode='extended')
chansScroll=Tk.Scrollbar(chansFrame,orient='vertical')
chansScroll.config(command=chansLB.yview)
chansLB.config(yscrollcommand=chansScroll.set)
##an array of all possible channels (64 total)
chans = list(np.arange(1,65).astype(str))
for chan in chans:
	chansLB.insert('end',chan)
chansLabel = Tk.Label(chansFrame,text="Available Channels",font=myFont).grid(row=0,column=0)
chansLB.grid(row=1,column=0)
chansLB.columnconfigure(0,weight=1)
chansScroll.grid(row=1,column=1,sticky='n'+'s')
##the frame to store selected channels
selectedFrame = Tk.Frame(mainWin)
selectedFrame.grid(row=1,column=1)
##the interactive listbox to choose channels from
chosenLB = UnitListBox(chans,chansLB,selectedFrame,"Selected Channels")
##create a frame for buttons that control experiument params
buttonFrame = Tk.Frame(mainWin)
buttonFrame.grid(row=2,column=0)
##entry box to pick a channel for analog out
DACEntry = entryBox(buttonFrame,"DAC out channel","1",0,0)
##button to change DAC channel
DACButton = Tk.Button(buttonFrame,text="Change DAC channel",font=myFont,command=set_DAC)
DACButton.grid(row=2,column=0)
#DACButton.configure()*******************
buttonFrame2 = Tk.Frame(mainWin)
buttonFrame2.grid(row=2,column=1)
##entry box for the circuit to load
circEntry = entryBox(buttonFrame2,"RCX location",
	r"C:\Users\Carmena\Documents\tdt_circuits\recording_circuit_basic2.rcx",1,0)
##entry box for save location
saveEntry = entryBox(buttonFrame2,"Save location",os.path.join(rootFolder,"test_1"),4,0)
##a frame to show the system status
statusFrame = Tk.Frame(mainWin)
statusFrame.grid(row=0,column=0)
statusFrame2 = Tk.Frame(mainWin)
statusFrame2.grid(row=0,column=1)
##a statusLabel to indicate if streaming has started
streamStatus = statusLabel(statusFrame,"Streaming")
streamStatus.grid(row=0,column=1)
##a status label to indicate that the TDT system is connected and ready
systemStatus = statusLabel(statusFrame,"System ready")
systemStatus.grid(row=0,column=0)
##recording status
recordStatus = statusLabel(statusFrame2,"Recording")
recordStatus.grid(row=0,column=0)
##testing tuning status
tuningStatus = statusLabel(statusFrame2,"Running visuals")
tuningStatus.grid(row=0,column=1)
##a frame for the control buttons
ctrlFrame = Tk.Frame(mainWin)
ctrlFrame.grid(row=1,column=2)
##some control buttons
streamButton = Tk.Button(ctrlFrame,text="Stream",font=myFont)
streamButton.grid(row=1,column=0)
##to load params to TDT and check status
initButton = Tk.Button(ctrlFrame,text="Initialize",font=myFont,command=init)
initButton.grid(row=0,column=0)
##to run the visual tuning test
tuningButton = Tk.Button(ctrlFrame,text="Tuning test",font=myFont,command=run_tuning)
tuningButton.grid(row=2,column=0)
#to record streaming data
recordButton = Tk.Button(ctrlFrame,text="Record",font=myFont,command=record)
recordButton.grid(row = 3, column = 0)
##to kill the streaming/recording threads
stopButton = Tk.Button(ctrlFrame,text="STOP",font=myFont,command=stop)
stopButton.grid(row=4,column=0)
##another frame cause I need more space!
paramsFrame = Tk.Frame(mainWin)
paramsFrame.grid(row=2,column=2)
##the maximum duration of the recording
maxTimeEntry = entryBox(paramsFrame,"Max rec time (mins)","120",0,0)

Tk.mainloop()






