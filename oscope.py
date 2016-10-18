

# """
# Emulate an oscilloscope.  Requires the animation API introduced in
# matplotlib 1.0 SVN.
# """
# import numpy as np
# from matplotlib.lines import Line2D
# import matplotlib.pyplot as plt
# import matplotlib.animation as animation
# from data_stream import DataPiece
# import multiprocessing as mp
# import ran


# ##for troubleshooting
# chans = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]
# chans = [str(x) for x in chans]
# dataQueue = mp.Queue(maxsize=16)

# class Scope(object):
# 	global dataQueue
# 	def __init__(self,ax,channel,maxt=.05,fs=24414.14):
# 		self.ax = ax
# 		self.channel = channel
# 		self.fs = fs
# 		self.maxt = maxt
# 		self.samples = int(np.ceil(self.maxt*fs))
# 		self.tdata = np.linspace(0,self.maxt,self.samples)
# 		self.ydata = np.zeros(self.samples)
# 		self.line = Line2D(self.tdata, self.ydata)
# 		self.ax.add_line(self.line)
# 		self.ax.set_ylim(-1.1, 1.1)
# 		self.ax.set_xlim(0, self.maxt)
# 		self.cursor = 0

# 	def update(self,data_piece):
# 		tag = data_piece.tag
# 		if tag == self.channel:
# 			y = data_piece.data
# 			if y.shape[0] + self.cursor < self.samples:
# 				self.ydata[self.cursor:self.cursor+y.shape[0]] = y
# 				self.cursor+=y.shape[0]
# 			else:
# 				##how much are we overshooting?
# 				diff = self.samples-self.cursor
# 				self.ydata[self.cursor:]=y[0:diff]
# 				self.line.set_ydata(self.ydata)
# 				self.cursor = 0
# 		else:
# 			dataQueue.put(data_piece)
# 		return self.line,


# def emitter():
# 	while True:
# 		yield dataQueue.get()

# def make_data():
# 	while True:
# 		data_len = np.random.randint(60,600)
# 		chan = np.random.choice(chans)
# 		data = np.random.randn(data_len)/10
# 		dataQueue.put(DataPiece(chan,data))


# def run_scope(chan):
# 	fig, ax = plt.subplots()
# 	fig.suptitle(chan)
# 	scope = Scope(ax,chan)
# 	# pass a generator in "emitter" to produce data for the update func
# 	ani = animation.FuncAnimation(fig,scope.update,emitter,interval=0,blit=True)
# 	plt.show()



import matplotlib.pyplot as plt
import multiprocessing as mp
import random
import numpy
import time

def worker(q):
    #plt.ion()
    fig=plt.figure()
    ax=fig.add_subplot(111)
    ln, = ax.plot([], [])
    fig.canvas.draw()   # draw and show it
    plt.show(block=False)

    while True:
        obj = q.get()
        n = obj + 0
        print "sub : got:", n

        ln.set_xdata(numpy.append(ln.get_xdata(), n))
        ln.set_ydata(numpy.append(ln.get_ydata(), n))
        ax.relim()

        ax.autoscale_view(True,True,True)
        fig.canvas.draw()
