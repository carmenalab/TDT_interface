"""
TDT_control_3.py
author: Ryan Neely
A series of functions to connect to and
read/write data to TDT bioamp processors using
the TDT TDevAcc controls.

*******************
*******************
NOTE: This set of functions works uses the TDT TDevAcc controls.
These controls are different than those used in TDT_control_ax.py 
because they allow access to the hardware at the same time that 
openProject programs are running. Use THIS control file if you want
to run programs with OpenProject at the same time.
"""
from win32com.client import Dispatch
import numpy as np
import time
import warnings


## a class for interacting with the OpenWorkbench server
##Constructor should be passed the name of the device (str) loaded via
##open workbench. Make sure the string matches exactly
class Server:
	def __init__(self, dev_name):
		self.dev_name = dev_name
		self.dsp = None
		self.fs = None
		self.record = False

	## a function to load a circuit. Local = True loads
	##the circuit to local memory but NOT the processor.
	#start dictates whether to run the circuit on the device. 
	def connect_server(self, start = False):
		##load the activeX controls
		proc = Dispatch('TDevAcc.X')
		##connect to the processor 
		if proc.ConnectServer('Local') == 0:
			raise SystemError, "Cannot connect to server"
		else:
			if start:
				if proc.SetSysMode(2) == 0:
					raise SystemError, "Cannot start Workbench"
			self.dsp = proc
			if self.dsp.GetDeviceName(0) != self.dev_name:
				warnings.warn("Warning: device name not found!")
			self.fs = self.get_fs()

	#to stop the circuit
	def stop(self):
		if self.dsp.SetSysMode(0) == 0:
			raise SystemError, "Cannot stop Workbench"

	#to idle the circuit
	def idle(self):
		if self.dsp.SetSysMode(1) == 0:
			raise SystemError, "Cannot idle Workbench"

	#to set the system to preview
	def preview(self):
		if self.dsp.SetSysMode(2) == 0:
			raise SystemError, "Cannot start preview"

	#to set the system to preview
	def record(self):
		if self.dsp.SetSysMode(3) == 0:
			raise SystemError, "Cannot start recording"

	# to get the sampling frequency 
	def get_fs(self):
		if self.dsp is not None:
			self.fs = self.dsp.GetDeviceSF(self.dev_name)
		else:
			print "No server connected"
		return self.fs

	#to check the processor status
	def get_status(self):
		result = self.dsp.GetSysMode()
		if result == 0:
			print "Workbench stopped"
		if result == 1:
			print "Workbench idle"
		if result == 2:
			print "Workbench in preview"
		if result == 3:
			print "Workbench recording"
		return result

	##helper function to generate a string used to
	##access a particular tag on the loaded device
	def make_tagstring(self,tag_name):
		##just connect the device name and tag name with a period
		return self.dev_name+"."+tag_name

	##a helper function to convert TDT data type values to numpy data values
	##input is a string of a TDT or numpy data type, output is the corresponding
	##TDT or numpy data type
	def dtype_LUT(self, typestring):
		if typestring == "F32":
			result = "float32"
		if typestring == "I32":
			result = "int32"
		if typestring == "I16":
			result = "int16"
		if typestring == "I8":
			result = "int8"
		if typestring == "float32":
			result = "I32"
		if typestring == "int32":
			result = "I32"
		if typestring == "int16":
			result = "I16"
		if typestring == "int8":
			result = "I8"
		else: raise ValueError, "Invalid Dtype"
		return result


	##to set parameter tag values. Requires string tag_name and 
	##value to set parameter to
	def set_tag(self, tag_name, value):
		if self.dsp.SetTargetVal(self.make_tagstring(tag_name), value) == 0:
			raise SystemError, "Cannot set tag"

	##to get a parameter tag
	def get_tag(self, tag_name):
		if self.dsp is not None:
			result = self.dsp.GetTargetVal(self.make_tagstring(tag_name))
		else:
			print "No server connected"
			result = None
		return result

	##to read data from a buffer
	##tag_name is the name of the RPDseX or whatever tag
	##num_samples is the number of samples to read
	##source_type is the data type of the data to be read (as string: F32, I32, I16,etc)
	##dest_type is the destination data type, same as above
	##start_offset is the number of points to offset the buffer before starting read
	def read_target(self, tag_name, num_samples, source_type, 
		dest_type, start_offset = 0):
		##grab the data
		data_read = np.asarray(self.dsp.ReadTargetVEX(self.make_tagstring(tag_name),
			start_offset,num_samples,source_type,dest_type))
		return data_read

	
	##function to continuously acquire data from the server.
	
	##-data_tag: the tag given to the buffer. Note that there needs
	##	to be a corresponding tag, suffix -i, that points to the buffer index.
	##	for example, if the buffer tag is "spike", there should be a tag to the index
	## 	should be "spike_i."

	##-dtype: the data type of the data in the buffer. This is the same data type
	##	that will be stored in the numpy array

	##-start_tag: the tag name of the variable to trigger recording on the circuit

	##-poll_rate: the interval between reads to the buffer in question. This can be
	##	optimized to keep processor load minimal
	def stream_data(self, data_tag, dtype, start_tag, poll_rate = 0.2):
		##get the sample rate
		if self.fs is None:
			get_fs()
		##get the poll rate in samples
		nSamp = int(np.ceil(poll_rate*self.fs))
		##set the recording flags
		self.record = True
		self.set_tag(start_tag,1)
		last_idx = get_tag(data_tag+"_i")
		while self.record = True:
			##get the current buffer index;
			##check if nSamp ahead of last index
			current_idx = get_tag(data_tag+"_i")
			if current_idx > last_idx+nSamp:
				#read data
				data = read_target(data_tag, nSamp, dtype, dtype, 
					start_offset = last_idx)
				last_idx = current_idx
		

		self.set_tag(start_tag,0)









	##to acquire a certain number of samples from the system's buffer.
	##this is NOT an ideal implementation. I tried many ways to make this work
	##with python's multiprocessing functionality, but alas no luck. The main issue
	##is that you don't want to grab the full data buffer all at once, or
	##you overload the processors. 
	#parag- the tag name (str) of the buffer to read from 
	#num_samples- total samples to read from the buffer
	#channels- number of channels being written to the buffer 
	#dtype_o- data type to read out
	#dtype_i- data type to save as 
	#poll_rate: frequency with which to grab data from the hardware buffer (seconds)
	def stream_data(self, partag, num_samples, channels, dtype_o, dtype_i, poll_rate = 0.1):
		#make sure the processor is connected, loaded and running
		if self.dsp.GetStatus() ==0:
			print "trying to reconnect"
			##try to reconnect to the processor 
			if self.dsp.ConnectRZ2('GB', 1) == 0:
				raise SystemError, "Cannot connect to hardware"
			if self.dsp.ReadCOF(self.circ_path) == 0:
				raise SystemError, "Cannot load circuit to local memory"
		#figure out the size of the data chunk to grab every loop
		sr = self.fs
		chunk_size = np.ceil(sr*poll_rate)
		##figure out the number of chunks
		num_chunks = np.ceil(num_samples/chunk_size)
		##allocate memory for the data to be read (might be larger than
		##num_samples; we'll deal with this later)
		data_stream = np.zeros((channels, num_chunks*chunk_size))
		##start saving the data
		for i in np.arange(0, num_chunks*chunk_size, chunk_size):
			time.sleep(poll_rate)
			data_stream[:,i:i+chunk_size] = np.asarray(self.dsp.ReadTagVEX(partag, i, 
				chunk_size, dtype_o, dtype_i, channels))
		##throw out any extra array pieces
		data_stream = data_stream[:,0:num_samples]
		return data_stream


##a function to parse the sort code data generated by the PC Sort macro in RPvdsEx
def parse_sorted(arr_in):
	##lookup table for unit letters to be compatible with Plexon naming convention
	unit_letters = ['a', 'b', 'c', 'd']
	##generate an output dictionary
	results_dict = {}
	##how many channels are we dealing wtih?
	num_chans = arr_in.shape[0]
	##run through each channel and parse individual sort codes
	for c in range(int(num_chans)):
		#how many units sorted on this channel?
		num_sorted = arr_in[c,:].max()
		##if the max is > 4, outlier sort codes are present- get rid of them
		while num_sorted > 4:
			#print "Removing outlier sort code ("+str(num_sorted)+")"
			np.place(arr_in[c,:], arr_in[c,:]==num_sorted, [0])
			num_sorted = arr_in[c,:].max()
		if num_sorted > 0:
			for unit in range(1,int(num_sorted+1)):
				spiketrain = (arr_in[c,:] == unit).astype(int)
				if c < 9:
					pad = '00'
				elif c < 99:
					pad = '0'
				else:
					pad = ''
				name = 'sig'+pad+str(c+1)+unit_letters[unit-1]
				results_dict[name] = spiketrain
	return results_dict


## a helper function to get the names of all the sorted units in a file set
def get_sorted_names(fIn):
	##get the names from one set as a start
	unit_names = parse_sorted(np.asarray(fIn['orientation']['set_1']['0'][0,:,:])).keys()
	##check all instances, and if there is a new addition, add it to the master list
	for setN in range(NUM_SETS):
		for oriN in DIRECTIONS:
			units_present = parse_sorted(np.asarray(fIn['orientation']['set_'+str(setN+1)][str(oriN)][0,:,:])).keys()
			for unit in units_present:
				if unit not in unit_names:
					#print "adding a unit - " + unit
					unit_names.append(unit)
	return unit_names

