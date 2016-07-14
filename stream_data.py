#stream_data.py
##functions to save data from memory-mapped arrays
##using python's multiprocessing module

##Ryan Neely
##ryan_neely@berkeley.edu

import h5py
import multiprocessing as mp

"""
a function to save data from a memory-mapped array.
meant to be implemented by a multiprocessing Process

-start_flag: a mp.Event() object that signals when the saving should terminate
-data_flag: a mp.Event object that signals when new data is present
-array: a mp.Array memory-mapped array containing the data
--array_dtype: the data type that you will be saving
--lock: a threading.Lock object to control access to the Array and Event objects
--fileroot: the address to create or open the data file (str)
-channel: the channel number (will be used to name the dataset)
"""
def file_stream(start_flag, data_flag, shared_array, 
	dtype, fileroot, channel):
	##open an hdf5 file
	f_out = h5py.File(fileroot, 'a')
	##get the size of the mem-mapped array
	array_len = len(array)
	##create a dataset of size 0 that can be resized.
	##setting chunk size to numPoints should speed up 
	##operations (??)
	try:
		dset = f_out.create_dataset(channel, (0,), dtype = "float32", 
									chunks = (array_len,), maxshape = (None,))
	except RuntimeError:
		print "A dataset for " + channel + " already exists!"
		break
	##counter for the number of writes to file
	written = 0
	##check for start/stop flag
	while run_flag.is_set():
		##check for new data in the pipe
		if data_flag.is_set():
			##increase the size of the dataset to accomodate new data block
			dset.resize((dset.size+array_len,))
			##append new data to the end of the current dset
			dset[(written*array_len):] = array[:]
			##signal that data has been written
			new_flag.clear()
			written+=1
	f_out.close()
	return 1


"""
The MIMO version of the above file. 
"""
def batch_stream(start_flag, fileroot, dtype, 
	channel_names, data_flags, arrays):
	pass



