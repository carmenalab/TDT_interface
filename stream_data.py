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
--filename: the address to create or open the data file (str)
"""
def file_stream(start_flag, data_flag, shared_array, 
	array_dtype, filename):
	##open an hdf5 file
	f_out = h5py.File(filename, 'a')
	##get the size of the mem-mapped array
	array_len = len(array)
	##create a dataset of size 0 that can be resized.
	##setting chunk size to numPoints should speed up 
	##operations (??)
	try:
		dset = f_out.create_dataset("data", (0,), dtype = "array_dtype", 
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

-start_flag is a mem-mapped flag object
-data_flags: list of mp flags for each array object
-array_dtype: data type to save data as 
-filenames: list of filenames to save data as
"""
def batch_stream(start_flag, data_flags, arrays, array_dtype, filenames):
	##how many channels are we working with, 
	##and make sure numbers match
	num_chans = len(arrays)
	if num_chans != len(filenames) or num_chans != len(data_flags):
		raise ValueError("Mismatched channel names/flags/numbers")
	##create a worker pool to handle the data saving
	pool = mp.Pool(num_chans)
	for i in range(num_chans):
		pool.apply_async(file_stream, args = (start_flag, data_flags[i], arrays[i],
			array_dtype, filenames[i]))
	




