"""
TDT_control_ax.py
author: Ryan Neely
A series of functions to connect to and
read/write data to TDT bioamp processors 
*****using the TDT ActiveX controls*******.

*******************
*******************
NOTE: This set of functions works ONLY with RPvdsEx circuits and NOT(!)
with OpenEx (workbench, openController, etc). It will cause workbench to crash.
To allow access to parameter tags when using OpenEx, you need to use TDevAccX.
"""
from win32com.client import Dispatch
import numpy as np
import time


## a class for interacting with the RZ2 processor on an
##optical gigabit interface. Constructor should be passed a
##string path to the circuit that should be loaded. 
class RZ2:
	def __init__(self, circ_path):
		self.circ_path = circ_path
		self.dsp = None
		self.fs = None
		self.is_running = False

	## a function to load a circuit. Local = True loads
	##the circuit to local memory but NOT the processor.
	#start dictates whether to run the circuit on the device. 
	def load_circuit(self, local = True, start = False):
		##load the activeX controls
		proc = Dispatch('RPco.X')
		##connect to the processor 
		if proc.ConnectRZ2('GB', 1) == 0:
			raise SystemError, "Cannot connect to hardware"
		if local:
			#just load the circuit into memory but not the RZ2
			if proc.ReadCOF(self.circ_path) == 0:
				raise SystemError, "Cannot load circuit to local memory"
		else:
			#clear whatever might be loaded on the RZ2
			if proc.ClearCOF() == 0:
				raise SystemError, "Cannot clear device"
			#load circuit onto device
			if proc.LoadCOF(self.circ_path) == 0:
				raise SystemError, "Cannot load circuit to device"
		if start:
			if proc.Run() == 0:
				raise SystemError, "Cannot start circuit"
		self.dsp = proc

	##to start the circuit
	def start(self):
		if self.dsp.Run() == 0:
			raise SystemError, "Cannot start device"
		else:
			self.is_running = True

	#to stop the circuit
	def stop(self):
		if self.dsp.Halt() == 0:
			raise SystemError, "Cannot stop device"
		else:
			self.is_running = False

	# to get the sampling frequency 
	def get_fs(self):
		if self.dsp is not None:
			self.fs = self.dsp.GetSFreq()
		else:
			print "No circuit loaded"
		return self.fs

	#to check the processor status (7 = loaded and running)
	def get_status(self):
		result = self.dsp.GetStatus()
		if result == 7:
			self.is_running = True
		else:
			self.is_running = False
		return result

	#to check the size of a buffer
	def get_size(self, tag_name):
		result = self.dsp.GetTagSize(tag_name)
		if result == 0:
			raise TypeError("Invalid Tag")
		return result

	##to set parameter tag values. Requires string tag_name and 
	##value to set parameter to
	def set_tag(self, tag_name, value):
		if self.dsp.SetTagVal(tag_name, value) == 0:
			raise SystemError, "Cannot set tag"

	##to get a parameter tag
	def get_tag(self, tag_name):
		if self.dsp is not None:
			result = self.dsp.GetTagVal(tag_name)
		else:
			print "No circuit loaded"
			result = None
		return result

	##to send a software trigger
	def send_trig(self, trig_num):
		if self.dsp.SoftTrg(trig_num) == 0:
			raise SystemError, "Cannot connect to hardware"

	##to get the dataype of a target tag
	def get_dtype(self, tag_name):
		t = self.dsp.GetTagType(tag_name)
		if t == 0:
			raise NameError, "Can't get tag type"
		else:
			return t

	##to read data from a buffer
	##-tag_name is the name of the RPDseX or whatever tag
	##-start_idx is the buffer index to start the read from
	##-num_samples is the number of samples to read, starting at start_idx
	##-num_channels is the number of channels; ****note that this needs to match the 
	##	number of channels set to the buffer in the circuit****
	##-source_type is the data type of the data to be read (as string: F32, I32, I16,etc)
	##-dest_type is the destination data type, same as above
	def read_target(self, tag_name, start_idx, num_samples, num_channels, source_type, 
		dest_type):
		##grab the data
		data_read = np.asarray(self.dsp.ReadTagVEX(tag_name, start_idx, num_samples,
			source_type, dest_type, num_channels)).squeeze()
		return data_read
