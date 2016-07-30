##mp_test.py
import h5py
import multiprocessing as mp

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
def stream_to_file(queue, fname, tag, dtype, chunk):
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

"""
creates a dectionary of nchan queues keyed by channel name
chans is a LIST of channels (int)
"""
def queue_creator(chans):
	result = {}
	for n in chans:
		result[n] = mp.Queue()
	return result


"""
TODO: FIGURE OUT WHAT "FLAG" is going to be (mp.Event? some kind of IO trigger?)
This function takes a TDT activeX object
and streams the data from n channels to file.
There are some assumtions about the structure of the RZ2 circuit:
1)
Args
TDT_obj: an RZ2 (or similar) class object from TDT_control_ax.py
nchan: channels to stream. This is a LIST of channels.
save_folder: the folder location to save the data files.
"""
def TDT_stream(TDT_obj, chans, save_folder, chunk, flag):
	##TODO: add these to the arglist somehow and make it still compatible with the GUI
	tag = "raw_voltage"
	dtype = "d"
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
		arg_lists.append([queue_dict[chan], save_folder+"/"+chan+".hdf5", 
			tag, dtype, chunk])
	pool.imap_unordered(stream_to_file, arg_lists)
	##workers should now be waiting to stream data to disc...
	##start streaming data from the RZ2 to the waiting queues
	##create a dictionary to store the index values of each channel
	idx_dict = {}
	for chan in chans:
		idx_dict[chan] = TDT_obj.get_tag(chan+"_i")
	while flag.is_set():
		for chan in chans:
			##see if buffer has advanced beyond 1 chunk size of last check
			current_idx = TDT_obj.get_tag(chan+"_i")
			last_idx = idx_dict[chan]
			if current_idx >= last_idx+chunk:
				##grab the data
				data = TDT_obj.read_target(chan, last_idx, chunk, 1, 'd', 'd') ##*******TODO**********: check on the last two params- source type and dest type
				##add new data to the appropriate queue (we will use the blocking call
				##so we don't overwrite any unprocessed data there)
				queue_dict[chan].put(data)
				##update the index dictionary
				idx_dict[chan] = last_idx+chunk
	##send the poison pill to kill the processess
	##(which will also close out the files)
	for chan in chans:
		queue_dict[chan].put(None)

			





	


