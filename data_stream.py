##mp_test.py
import h5py
import TDT_control_ax as tdt
import time
import numpy as np
import os

"""
Defines a DataPiece class which is essentially a
snippet of data with some metadata attached that
signals where it came from and  thus where
it belongs in the file
"""
class DataPiece:
	def __init__(self, tag, data):
		self.tag = tag
		self.data = data
		self.size = len(data)


"""
function that watches a queue for new data, then writes that
data to an hdf5 file.

args: 
queue: a multiprocessing.Queue() object to watch
fname: str containing the path of the file to write to
	"""
def write_to_file(queue, fname):
	##set up a dictionary to keep track of the write indexes
	last_written = {}
	#create hdf5 file
	with h5py.File(fname, 'r+') as f_out:
		##poll the queue
		data = queue.get()
		##"data" is a class object
		##sending None into the queue will kill the process
		while data != None:
			##see if there is an entry in the index dictionary;
			##if not create it
			if data.tag not in last_written.keys():
				last_written[data.tag] = 0
			##the index of the END of last write
			idx = last_written[data.tag]
			##append the data to the correct dataset. If the dset
			##isn't big enough, exit the loop and close out the file
			try:
				f_out[str(data.tag)][idx:idx+data.size] = data.data
			except TypeError:
				print "Reached the file limit- recording stopped!"
				break
			##update the index dictionary
			last_written[data.tag]+=data.size
			##re-poll the queue. This is a blocking call, ie the process will wait 
			#for new data
			data = queue.get()
		##if recording has ended, trim the unwritten ends off of the end 
		##of the datasets
		print "resizing now"
		for chan in last_written.keys():
			idx = last_written[chan]
			f_out[str(chan)].resize((idx,))
		f_out.close()
		print("Done resizing")
	return 1

"""
This is a function that sets up an HDF5 file dictionary
with the correct dataset settings and dset names
given a list of channel numbers (as int), a filename (str)
and the max duration of the recording (in mins). ***NOTE*** Program will
stop saving when recording time exceeds this variable!!!
fs is the sample rate in samples/sec.
"""
def setup_file(f_root, chans, max_duration, fs = 25000):
	max_samples = int(fs*60*max_duration)
	##createe the file
	f = h5py.File(f_root, 'w')
	##create the datasets
	for chan in chans:
		f.create_dataset(str(chan), (max_samples,), 
			maxshape=(max_samples,), dtype = 'f', compression = 'gzip', 
			compression_opts=9)
	f.close()


"""
This function connects the RZ2 and loads the specified
circuit. "Chans" is a list of (int) channel numbers to stream.
Data is then stored in a DataPiece class and passed to the queue,
where it can be written to file. Flag is a mp.Event to signal
start/stop recording.
Note that this assumes a certain convention when building RPVdsEx
circuits: buffers storing data are named as a number corresponding to the 
channel they get data from, and the buffer indices are named as the channel
number + "_i", as in "5_i."
""" 
def hardware_streamer(circ_path, chans, queue, flag):
	##connect to the processor 
	rz2 = tdt.RZ2(circ_path)
	rz2.load_circuit(local = False, start = False)
	rz2.get_status()
	if rz2.is_running:
		rz2.stop()
	#check that the buffer sizes are equal, and
	##check that the channels specified are actually available
	##on the processor
	buf_sizes = []
	for chan in chans:
		try:
			buf_sizes.append(rz2.get_size(str(chan)))
		except TypeError:
			print "Check channel numbers"
			break
	assert len(set(buf_sizes)) == 1, "Check buffer sizes"
	##thanks to the above assertion, we can assume all buffers
	##have the same size:
	buf_size = buf_sizes[0]
	##set up a dictionary to store the last read index for each channel
	last_read = {}
	for chan in chans:
		last_read[chan] = 0
	##wait for the signal to start
	while not flag.is_set():
		time.sleep(0.1) ##TODO: better way of blocking here?
	##when triggered, start the circuit and start streaming to the queue
	rz2.start()
	while flag.is_set():
		for chan in chans:
			##see where the buffer index is at currently
			next_index = rz2.get_tag(str(chan)+"_i")
			##case where buffer has not yet wrapped back to zero
			if next_index > last_read[chan]:
				length = next_index - last_read[chan]
				data = np.asarray(rz2.read_target(str(chan), last_read[chan], 
					length, 1, "F32", "F32")).squeeze()
			##case where buffer has wrapped back to zero
			elif next_index < last_read[chan]:
				length_a = buf_size - last_read[chan]
				data_a = np.asarray(rz2.read_target(str(chan), last_read[chan], 
					length_a, 1, "F32", "F32")).squeeze()
				data_b = np.asarray(rz2.read_target(str(chan), 0, next_index,
					1, "F32", "F32")).squeeze()
				try:
					data = np.concatenate((data_a, data_b))
				except ValueError:
					if data_a.shape[0] == 0 and data_b.shape[0] != 0:
						data = data_b
					elif data_b.shape[0] == 0: and data_a.shape[0] != 0:
						data = data_a
					else:
						print "Error: data pieces have sizes "+str(data_a.shape)+" and "+str(data_b.shape)
						data = np.zeros((length_a+next_index))
			queue.put(DataPiece(chan, data))
			last_read[chan] = next_index
	##when the flag goes off, signal the writer process
	queue.put(None)
	# except SystemError, e:
	# 	print("Error acquiring data: {}".format(e))
	rz2.stop()
	print "Recording ended"


