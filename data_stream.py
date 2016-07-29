##mp_test.py
import h5py
import multiprocessing as mp

def stream_to_file(queue, fname, tag, dtype, chunk):
"""
function that watches a queue for new data, then writes that
data to an hdf5 file.

args: 
queue: a multiprocessing.Queue() object to watch
fname: str containing the path of the file to write to
tag: str that will be used to name the dataset
dtype: datatype that will be written. Suggested: 'd' (double)
chunk: chunksize of data that will be written to the queue. Also used
	to parameterize the hdf5 file chunk size
"""
	#create hdf5 file
	f_out = h5py.File(fname, 'w-')
	#create the dataset
	dset = f_out.create_dataset(tag, (0,), dtype = dtype, chunks = (chunk,),
		maxshape = (None,))
	##poll the queue
	data = queue.get()
	##sending None into the queue will kill the process
	while data != None:
		idx = dset.size
		##increase the size of the dataset to accomodate new data block
		dset.resize((idx+chunk,))
		##append new data to the end of the current dset
		dset[idx:] = data
		##re-poll the queue. This is a blocking call, ie the process will wait 
		#for new data
		data = queue.get()
	f_out.close()
	return 1

def queue_creator(chans):
"""
creates a dectionary of nchan queues keyed by channel name
chans is a LIST of channels (int)
"""
	result = {}
	for n in chans:
		result[n] = mp.Queue()
	return result


def TDT_stream(TDT_obj, chans, save_folder):
	"""
	This function takes a TDT activeX object
	and streams the data from n channels to file.
	There are some assumtions about the structure of the RZ2 circuit:
	1)
	Args
	TDT_obj: an RZ2 (or similar) class object from TDT_control_ax.py
	nchan: channels to stream. This is a LIST of channels.
	save_folder: the folder location to save the data files.
	"""
	##check that the circuit is running (start if not running)
	if not TDT_obj.is_running:
		TDT_obj.start()
	##create a dictionary of queues for each active channel
	queue_dict = queue_creator(chans)
	##spawn processes to stream the data
	pool = mp.Pool(len(chans))
	##generate a list of argument lists
	arg_lists = []
	for chan in chans:
		arg_lists.append([queue_dict[chan], save_folder+"/"+chan+".hdf5", ])
	pool.apply_async(stream_to_file, )

	


