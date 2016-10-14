## a GUI to record and visualize data while testing V1 tuning

import numpy as np
import Tkinter as Tk
import time
import os
import multiprocessing as mp
import data_stream as stream
import TDT_control_ax as tdt
from psychopy import visual
from psychopy import core
from psychopy import info
import matplotlib.pyplot as plt
from scipy.signal import butter, lfilter

##some necessary globals
rz2 = None
dataQueue = None
startFlag = mp.Event()
startFlag.clear()

##font style
myFont = ("Helvetica", 18)

##a root folder to store the data. Make it if it does not exist.
rootFolder = os.path.normpath("D:/"+time.strftime("%m_%d_%y"))
# if not os.path.exists(rootFolder):
# 	os.makedirs(rootFolder)
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
	if rz2.is_running():
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
	chans = [int(i) for i in chosenLB.unitList] ##channel numbers are str; convert to int
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
	if rz2 is not None:
		rz2.stop()
	##grating variables
	#directions of movement (list). -1 is the baseline gray screen
	##***NOTE: for plotting to be correct, the gray screen value should be last in the array!!!***
	DIRECTIONS = np.array([0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, -1])
	#the spatial frequency of the grating in cycles/degree
	SPATIAL_FREQ = 0.08
	##amount of time to display the gray screen in seconds
	GRAY_TIME = 2.0
	##amount of time to display the drifting grating in seconds
	DRIFT_TIME = 2.0
	#the number of times to repeat the full set of gratings
	NUM_SETS = 20
	##NUM_CHANNELS = number of channels
	NUM_CHANNELS = 64
	##the location of the TDT circuit file to load
	CIRCUIT_LOC = circEntry.entryString.get()
	data_filepath = saveEntry.entryString.get()
	##create an HDF5 file in which to save the data
	dataFile = h5py.File(data_filepath, 'w')
	##load the spcified circuit file and connect to the processor;
	#use a different instance than the GUI's connection
	"""
	NOTE: Loading the wrong file isn't immediately obvious and can cause
	a lot of headaches!!
	"""
	RZ2 = tdt.RZ2(CIRCUIT_LOC)
	##load the RPvdsEx circuit locally
	RZ2.load_circuit(local = True, start = True)
	##get the processor sampling rate
	fs = RZ2.get_fs()
	#print 'sample rate is: ' + str(fs)
	##the number of samples to take from the TDT (duration of each stim rep)
	num_samples = int(np.ceil(fs*(DRIFT_TIME+2*GRAY_TIME)))
	x_axis = np.linspace(0,1000*(GRAY_TIME+DRIFT_TIME+GRAY_TIME), num_samples)

	visual = mp.Process(target=run_orientations)
	visual.start()
	tuningStatus.toggleState(True)
	visual.join()
	tuningStatus.toggleState(False)

		##define filter functions
	def butter_bandpass(lowcut, highcut, fs, order=5):
		nyq = 0.5 * fs
		low = lowcut / nyq
		high = highcut / nyq
		b, a = butter(order, [low, high], btype='band')
		return b, a


	def butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
		b, a = butter_bandpass(lowcut, highcut, fs, order=order)
		y = lfilter(b, a, data)
		return y

	##a function to stream data from the TDT hardware. 
	##args are obvious except for pause- this value, if not None,
	##intentionally slows down the data rate by pausing in between
	##reads. This is because you can overload the TDT bus by asking for 
	##to much data at once. Value is seconds.
	def get_data(n_chan, n_samp, dtype="F32", pause = None):
		##allocate memory; channels x samples 
		data = np.zeros((n_chan, n_samp))
		##we are assuming the channels are distributed across
		#multiple processors, and we don't want to grab all channes
		##from once processor at once and overload it, so randomize the order
		chans = np.arange(1,n_chan+1) ##TDT channels start at 1
		np.random.shuffle(chans)
		##go through each channel and grab however many samples
		for c in chans:
			data[c-1,:] = RZ2.read_target(str(c), 0, n_samp, 1, dtype, dtype).squeeze()
			if pause is not None:
				time.sleep(pause)
		return data


	def run_orientations(plot = True, savefigs = False):
		##double check that the TDT processors are connected and the circuit is running
		if RZ2.get_status() != 7:
			raise SystemError, "Check RZ2 status!"
		print "Running orientation presentation."
		if plot:
			fig1 = plt.figure(figsize = (20,10))
			ax1 = fig1.add_subplot(221)
			ax2 = fig1.add_subplot(223)
			ax3 = fig1.add_subplot(222)
			ax4 = fig1.add_subplot(224)
			#full data
			p_data, = ax1.plot(x_axis, np.zeros(num_samples),'k')
			#zoomed data
			z_data, = ax2.plot(x_axis, np.zeros(num_samples),'k')
			##spikband data
			s_data, = ax3.plot(x_axis, np.zeros(num_samples),'r')
			#lfpband data
			l_data, = ax4.plot(x_axis, np.zeros(num_samples),'g')
			ax1.axvspan(GRAY_TIME*1000, GRAY_TIME*1000+DRIFT_TIME*1000, 
				alpha = 0.5, color = 'royalblue')
			ax2.axvspan(GRAY_TIME*1000, GRAY_TIME*1000+DRIFT_TIME*1000, 
				alpha = 0.5, color = 'royalblue')
			ax3.axvspan(GRAY_TIME*1000, GRAY_TIME*1000+DRIFT_TIME*1000, 
				alpha = 0.5, color = 'royalblue')
			ax4.axvspan(GRAY_TIME*1000, GRAY_TIME*1000+DRIFT_TIME*1000, 
				alpha = 0.5, color = 'royalblue')		
			ax1.set_title("Full trace", fontsize = 12)
			ax2.set_title("Onset", fontsize = 12)
			ax2.set_xlim(GRAY_TIME*1000-100, GRAY_TIME*1000+400)
			ax2.set_xlabel("time, ms")
			ax2.set_ylabel("mV")
			ax1.set_ylabel("mV")
			ax4.set_xlabel("time, ms")
			ax3.set_title("Spike band", fontsize = 12)
			ax4.set_title("LFP band", fontsize = 12)
			fig1.set_size_inches((12,8))
		##create a window for the stimuli
		myWin = visual.Window([800,480] ,monitor="RPi_5in", units="deg", fullscr = True, screen = 1)
		# ##get the system/monitor info (interested in the refresh rate)
		# print "Testing monitor refresh rate..."
		# sysinfo = info.RunTimeInfo(author = 'Ryan', version = '1.0', win = myWin, 
		# 	refreshTest = 'grating', userProcsDetailed = False, verbose = False)
		# ##get the length in ms of one frame
		# frame_dur = float(sysinfo['windowRefreshTimeMedian_ms'])
		frame_dur = 15.22749 #calculated beforehand

		##create a grating object
		grating = visual.GratingStim(win=myWin, mask = None, size=40,
		                             pos=[0,0], sf=SPATIAL_FREQ, ori = 0, units = 'deg')
		##calculate the number of frames needed to produce the correct display time
		num_frames = int(np.ceil((DRIFT_TIME*1000.0)/frame_dur))
		##set RZ2 recording time parameters
		RZ2.set_tag("samples", num_samples)
		##generate the stimuli
		for setN in range(NUM_SETS):
			print "Beginning set " + str(setN+1) + " of " + str(NUM_SETS)
			##shuffle the orientations
			np.random.shuffle(DIRECTIONS)
			##create a file group for this set
			set_group = dataFile.create_group("set_" + str(setN+1))
			for repN in range(DIRECTIONS.size):
				##make sure you are still connected to the RZ2
				if RZ2.get_status == 0:
					raise SystemError, "Hardware connection lost"
				##create a dataset for this orientation
				dset = set_group.create_dataset(str(DIRECTIONS[repN]), (NUM_CHANNELS,num_samples), dtype = 'f')
				##initialize thread pool to stream data
				#dpool = ThreadPool(processes = 3)
				##set the contrast to zero:
				grating.contrast = 0.0
				grating.draw()
				myWin.flip()
				##trigger the RZ2 to begin recording
				RZ2.send_trig(1)
				##start threads
				#sort_thread = dpool.apply_async(RZ2.stream_data, ("sorted", num_samples, 16, "I32", "int"))
				#spk_thread = dpool.apply_async(RZ2.stream_data, ("spkR", num_samples, 16, "F32", "float"))
				#lfp_thread = dpool.apply_async(RZ2.stream_data, ("lfpR", num_samples, 16, "F32", "float"))
				##pause for the Gray time
				core.wait(GRAY_TIME)
				##make sure this isn't a gray trial
				if DIRECTIONS[repN] != -1:
					##adjust the orientation
					grating.ori = DIRECTIONS[repN]
					##bring the contrast back to 100%
					grating.contrast = 1.0
					##draw the stimuli and update the window
					print "Showing orientation " + str(DIRECTIONS[repN])
					for frameN in range(num_frames):
						grating.phase = (0.026*frameN, 0.0)
						grating.draw()
						myWin.flip()
				else:
					##continue to display gray screen
					print "Showing zero contrast control"
					core.wait(DRIFT_TIME)
				##set the contrast to zero:
				grating.contrast = 0.0
				grating.draw()
				myWin.flip()
				##pause for the specified time
				core.wait(GRAY_TIME)
				##now save the data to the hdf5 file
				#raw trace
				trace_data = get_data(NUM_CHANNELS, num_samples, pause = .005)
				dset[:,:] = trace_data
				if plot:
					lfp = butter_bandpass_filter(trace_data[4,:], 0.5, 300, fs, 1)
					spike = butter_bandpass_filter(trace_data[4,:], 300, 5000, fs, 5)
					p_data.set_ydata(trace_data[4,:])
					z_data.set_ydata(trace_data[4,:])
					s_data.set_ydata(spike)
					l_data.set_ydata(lfp)
					ax1.set_ylim(trace_data[4,:].min(), trace_data[4,:].max())
					ax2.set_ylim(trace_data[4,:].min(), trace_data[4,:].max())
					ax3.set_ylim(spike.min(), spike.max())
					ax4.set_ylim(lfp.min(), lfp.max())
					fig1.suptitle(str(DIRECTIONS[repN])+" Degrees", fontsize = 18)
					fig1.canvas.draw()
					if savefigs:
						fig1.savefig(fig_filepath+str(DIRECTIONS[repN])+".png", format = 'png')
				##clean up
				#dpool.close()
				#dpool.join()

		print "Orientation test complete."
		myWin.close()
		dataFile.close()
		RZ2.stop()






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






