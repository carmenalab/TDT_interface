#stream_data.py
##functions to save data from memory-mapped arrays
##using python's multiprocessing module

##Ryan Neely
##ryan_neely@berkeley.edu

import h5py
import multiprocessing as mp


##DUMB: class objects will not pickle! Need to re-do this whole thing.

"""
a class that sets up a set of memory-mapped objects that can be shared
across processes for streaming data to a file
"""
class StreamObj:
	def __init__(self, size, dtype = None, tag = None):
		##default to double
		if self.dtype == None:
			self.dtype = 'd'
		else self.dtype = dtype
		##the name of the dataset
		if tag == None:
			self.tag == "data"
		else self.tag = tag
		##the size of the data pipe array
		self.size = size
		##memory-mapped array object with automatic locking
		self.array = mp.Array(dtype, size, lock = True)
		##memory-mapped Event object to flag new data in the "pipe"
		self.flag = mp.Event()

	##a function to update new data into the pipe
	def write_pipe(self,data):
		if len(data) != self.size:
			raise AssertionError("input data wrong size")
		if self.flag.is_set():
			raise AssertionError("unread data in pipe!")
		##add new data to the array
		self.array[:] = data
		##signal new data is ready to be read
		self.flag.set()

	##a function to check if NEW(!) unread data is available and
	##if so, return it
	def read_pipe(self):
		result = None
		if self.flag.is_set():
			result = array[:]
			##cancel the flag until next write
			self.flag.clear()
		return result



"""
a function to save data from a memory-mapped array.
meant to be implemented by a multiprocessing Process

-start_flag: a mp.Event() object that signals when the saving should terminate
-data_flag: a mp.Event object that signals when new data is present
-array: a mp.Array memory-mapped array containing the data
--array_dtype: the data type that you will be saving
--filename: the address to create or open the data file (str)
"""
def file_stream(start_flag, filename, stream_obj):
	##open an hdf5 file
	f_out = h5py.File(filename, 'a')
	##get the size of the mem-mapped array
	array_len = len(stream_obj.array)
	##create a dataset of size 0 that can be resized.
	##setting chunk size to numPoints should speed up 
	##operations (??)
	try:
		dset = f_out.create_dataset(stream_obj.tag, (0,), dtype = stream_obj.dtype, 
									chunks = (array_len,), maxshape = (None,))
	except RuntimeError: 
		print "A dataset for " + stream_obj.tag + " already exists!"
		break
	##counter for the number of writes to file
	written = 0
	##check for start/stop flag
	while start_flag.is_set():
		##check for new data in the pipe
		data_read = stream_obj.read_pipe()
		if data_read != None:
			##increase the size of the dataset to accomodate new data block
			dset.resize((dset.size+array_len,))
			##append new data to the end of the current dset
			dset[(written*array_len):] = data_read
			written+=1
	f_out.close()
	return 1


"""
The MIMO version of the above file. 

-start_flag is a mem-mapped flag object
-stream_objs: a list of StreamObj objects
"""
def batch_stream(start_flag, stream_objs):
	##how many channels are we working with, 
	##and make sure numbers match
	num_chans = len(stream_objs)
	##create a worker pool to handle the data saving
	pool = mp.Pool(num_chans)
	for i in range(num_chans):
		pool.apply_async(file_stream, args = (start_flag, stream_objs[i]))
	




