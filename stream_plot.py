#stream_plot.py

##uses multiprocessing framework to visualize data streams

from data_stream import DataPiece
import math
import Tkinter as Tk
import Tkconstants
import matplotlib
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pprint, inspect
import numpy as np
import random
import oscope
import multiprocessing as mp

##for troubleshooting
chans = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]

"""
we might have a lot of channels to plot, so it's necessary to get 
complicated with this app. The following script will add a
scrollable figure to a tkinter frame:
"""
def addScrollingFigure(figure, frame,ax_dict):
	global canvas, mplCanvas, interior, interior_id, cwid
	# set up a canvas with scrollbars
	canvas = Tk.Canvas(frame)
	canvas.grid(row=1, column=1, sticky=Tkconstants.NSEW)

	xScrollbar = Tk.Scrollbar(frame, orient=Tkconstants.HORIZONTAL)
	yScrollbar = Tk.Scrollbar(frame)

	xScrollbar.grid(row=2, column=1, sticky=Tkconstants.EW)
	yScrollbar.grid(row=1, column=2, sticky=Tkconstants.NS)

	canvas.config(xscrollcommand=xScrollbar.set)
	xScrollbar.config(command=canvas.xview)
	canvas.config(yscrollcommand=yScrollbar.set)
	yScrollbar.config(command=canvas.yview)

	# plug in the figure
	figAgg = FigureCanvasTkAgg(figure, canvas)
	mplCanvas = figAgg.get_tk_widget()

	# and connect figure with scrolling region
	cwid = canvas.create_window(0, 0, window=mplCanvas, anchor=Tkconstants.NW)
	changeSize(figure, 1,ax_dict)


"""
a function that will let us scale the size of the plots/subplots
"""
def changeSize(figure, factor,ax_dict):
	global canvas, mplCanvas, interior, interior_id, frame, cwid
	oldSize = figure.get_size_inches()
	figure.set_size_inches([factor * s for s in oldSize])
	wi,hi = [i*figure.dpi for i in figure.get_size_inches()]
	mplCanvas.config(width=wi, height=hi)
	canvas.itemconfigure(cwid, width=wi, height=hi)
	canvas.config(scrollregion=canvas.bbox(Tkconstants.ALL),width=1500,height=1000)
	tz.set_fontsize(tz.get_fontsize()*factor)
	for key in ax_dict.keys():
		ax = ax_dict[key]
		for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
				ax.get_xticklabels() + ax.get_yticklabels()):
			item.set_fontsize(item.get_fontsize()*factor)
		ax.xaxis.labelpad = ax.xaxis.labelpad*factor
		ax.yaxis.labelpad = ax.yaxis.labelpad*factor
	figure.tight_layout() # matplotlib > 1.1.1
	#figure.subplots_adjust(left=0.2, bottom=0.15, top=0.86)
	figure.canvas.draw()

def read_data(queue,chans):
	pass

"""
run_plots plots the incoming data from a given queue.
Queue should be populated with DataPiece objects (see data_strean.py)
chans is a list of channels that will have data passed via the queue.
***NOTE: make sure the chans list argument matches what will be in the queue***
"""
#def run_plots(queue,chans):
if __name__ == "__main__":
	global root, figure
	frame = None
	canvas = None
	ax = None
	##set up the root window and attach a frame
	root = Tk.Tk()
	root.rowconfigure(1,weight=1)
	root.columnconfigure(1, weight=1)
	frame = Tk.Frame(root)
	frame.grid(column=1, row=1, sticky=Tkconstants.NSEW)
	frame.rowconfigure(1, weight=1)
	frame.columnconfigure(1, weight=1)

	##****create the animated figures here****
	figure = plt.figure(dpi=150,figsize=(10,6))
	##the number of rows (of 4 columns)
	rows = np.ceil(len(chans)/4.0)
	##a dictionary to store the axes handles
	ax_dict = {}
	for n,chan in enumerate(chans):
		ax = figure.add_subplot(rows,4,n+1)
		ax.set_title(str(chan),fontsize=5)
		for tick in ax.xaxis.get_major_ticks():
			tick.label.set_fontsize(4)
		for tick in ax.yaxis.get_major_ticks():
			tick.label.set_fontsize(4)
		ax_dict[str(chan)] = ax
	tz = figure.suptitle("Live")
	addScrollingFigure(figure,frame,ax_dict)
	buttonFrame = Tk.Frame(root)
	buttonFrame.grid(row=1, column=2, sticky=Tkconstants.NS)
	biggerButton = Tk.Button(buttonFrame, text="larger",
						command=lambda : changeSize(figure, 1.2,ax_dict))
	biggerButton.grid(column=1, row=1)
	smallerButton = Tk.Button(buttonFrame, text="smaller",
						 command=lambda : changeSize(figure, 0.833,ax_dict))
	smallerButton.grid(column=1, row=2)
	qButton = Tk.Button(buttonFrame, text="quit",
						 command=lambda :  root.destroy())
	qButton.grid(column=1, row=3)

	##a dictionary of the oscilliscopes
	scope_dict = {}
	for chan in chans:
		scope_dict[str(chan)] = oscope.Scope(ax_dict[str(chan)])
	

	ani_dict = {}
	for chan in chans:
		ani_dict[str(chan)] = animation.FuncAnimation(figure,
			scope_dict[str(chan)].update,oscope.emitter,interval=0,blit=True)

	root.mainloop()

