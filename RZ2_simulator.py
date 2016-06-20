##this is a function to simulate the data buffers on the RZ2.
##designed to be used to test code without having to fire up the 
##whole system. The program uses the plexon test data to generate
##data points.

#!/usr/bin/env python
import numpy as np
import wave
import h5py
import multiprocessing as mp
import time

##the location of the sample .wav file
#data_wav = r"C:\Users\Ryan\Google Drive\carmena_lab\bmi_code\TestSpike&FPdata-1min.wav"
data_wav = r"/Users/Ryan/Google Drive/carmena_lab/bmi_code/TestSpike&FPdata-1min.wav"
#testfile = r"C:\Users\Ryan\Google Drive\carmena_lab\bmi_code\TestWFS.hdf5"
testfile = r"/Users/Ryan/Google Drive/carmena_lab/bmi_code/TestWFS.hdf5"


buffer_size = 100000

##generate a data array from the wav file (this will be the raw analog trace)
spf = wave.open(data_wav,'r')
analog_data = spf.readframes(-1)
analog_data = np.fromstring(analog_data, 'Int16')
spf.close()

##get some sample waveforms
f = h5py.File(testfile,'r')
wf_data = np.asarray(f['wfs'])
f.close()
wf_len = wf_data.shape[1]

##memory-mapped buffers to operate on
timestamp = mp.Value('i', 0)
raw_data = mp.Array('i', np.zeros(buffer_size).astype(int))
wfs = mp.Array('f', np.zeros(buffer_size))
##shared Value objects for indexing
raw_data_i = mp.Value('i', 0)
wfs_i = mp.Value('i', 0)

##create a shared signal
run = mp.Event()

##a function to stop the process script
def Halt():
	run.clear()
	return 1

##a function that can be passed to the process to do the whole thing
def record(run, timestamp, raw_data, raw_data_i, wfs, wfs_i):
	##create a raw data generator
	raw = get_raw_data(analog_data)
	while run.is_set():
		##add data to the data buffers:
		#increment timestamp by one
		timestamp.value += 1
		##add the next data point to raw_data
		raw_data[raw_data_i.value] = next(raw)
		##make sure you haven't reached the end of the buffer
		if raw_data_i.value+1 < buffer_size:
			raw_data_i.value +=1
		##if you have, wrap the index back to one
		else:
			raw_data_i.value = 0
		##see if you have a "spike" on this ms
		is_wf = get_waveform(wf_data)
		if is_wf is not None:
			##concatenate timestamp and wf data like in TDT
			is_wf = np.hstack((timestamp.value,is_wf))
			##add data to the buffer, taking into account circularity
			x = convert_idx(buffer_size, wfs_i.value, wf_len+1)
			#can't fancy index mem-mapped arrays like in python so do it c-style
			#well, kind of :)
			for n,val in enumerate(x):
				wfs[val] = is_wf[n]
			##set the index to the next unwritten point
			wfs_i.value = x[-1]+1
		##sleep for a bit
		time.sleep(.01)

def Run():
	run.set()
	p = mp.Process(target = record, args = (run, timestamp, raw_data, raw_data_i, wfs, wfs_i))
	p.start()
	return 1

##functions that mimic TDT ActiveX controls


##a generator to yield raw data
def get_raw_data(data):
	max_len = data.shape[0]
	idx = 0
	while True:
		while idx < max_len:
			yield data[idx]
			idx +=1
		idx = 0

## a pseudo-generator to yield a random waveform
def get_waveform(wfs):
	result = None
	##determine if you are going to yield a "spike"
	##built-in 10% chance
	if flip(0.3):
		##randomly pick a waveform from the arguments
		result = wfs[np.random.randint(0,3),:]
	return result

##a function to get the indexes for a "circular" buffer
def convert_idx(max_len, start, n_samp):
	##if the ramge is within the size of the buffer, just 
	##return the range
	if start+n_samp <= max_len:
		result = np.arange(start, start+n_samp)
	else:
		##figure out how many samples over the end of the
		##buffer you are
		over = (start+n_samp) - max_len
		result = np.hstack((np.arange(start,max_len), np.arange(over)))
	return result

##bias coin flip function
def flip(p):
	return True if np.random.random() < p else False

 ##other functions to mimic RZ2
def ConnectRZ2(x,y):
	return 1

def ReadCOF(x):
 	return 1

def ClearCOF():
	return 1

def LoadCOF(x):
	return 1

def GetSFreq():
	return 100.0

def GetStaus():
	if run.is_set():
		return 7
	else:
		return 0

def GetTagVal(tag_name):
	result = None
	if tag_name == "timestamp":
		result = timestamp.value
	elif tag_name == "raw_data_i":
		result = raw_data_i.value
	elif tag_name == "wfs_i":
		result = wfs_i.value
	return result

def GetTagType(tag_name):
	result = None
	if tag_name == "raw_data":
		result = 'I16'
	elif tag_name == "wfs":
		result = "F32"
	return result

def ReadTagVEX(tag_name, start_idx, num_samples, x,y,z):
	result = None
	if tag_name == "raw_data":
		x = convert_idx(buffer_size, start_idx, num_samples)
		result = np.zeros(num_samples)
		for i, val in enumerate(x):
			result[i] = raw_data[val]
	elif tag_name == "wfs":
		x = convert_idx(buffer_size, start_idx, num_samples)
		result = np.zeros(num_samples)
		for i, val in enumerate(x):
			result[i] = wfs[val]
	return result
