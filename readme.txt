readme.txt

readme file for TDT_interface files

TDT Interface is a series of python scripts to interface with
the TDT system.

There are two core files:

-TDT_control_ax.py: 
	This file is designed for use with the 
	RPVdsEx software ONLY; ie if you only want to run RPVdsEx
	circuits directly and handle all of the data storage and data
	visualization manually in Python. It uses the TDT ActiveX controls
	to control the RZ2 processor. If you try to use these functions
	with OpenProject, you'll crash OpenProject.

-TDT_control_tda.py: 
	This series of functions is more or less the same as TDT_control_ax.py,
	but the key difference is that it runs the TDevAcc COM object instead
	of ActiveX. Because of this, it accesses the RZ2 processor via 
	OpenProject/OpenWorkbench server, and therefore is compatible
	with these programs and can be run simultaneously with them. 