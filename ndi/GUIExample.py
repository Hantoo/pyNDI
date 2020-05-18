# pyNDI Made by CarlosFdez
# Example by Joel Luther-Braun / Github(@Hantoo)

# TKInter GUI example showing NDI Sources
# When the list is updated/refreshed, every 30 seconds, the frame refresh will stop for 5 seconds
# If the source being used is closed then the program will crash


#pyNDI Import
import finder
import receiver
import lib
#Other Import
import imutils
import tkinter as tk
import time
import numpy as np
import PIL
from PIL import Image, ImageTk
import time, threading
from queue import Queue


recieveSource = None; 
NDIsources = None;
NDISourceList = None;
frameimage = None;
NDIList_out = Queue()
NDIImage_out = Queue()
refreshList = True;


# FUNCTIONS

# Set NDI Source user is viewing, create reciever
def setNDISource(value):
	global recieveSource
	global frameimage 
	global currentStatus
	currentStatus.set("Retreving NDI Source")
	frameimage = None
	recieveSource = receiver.create_receiver(NDIsources[value])

# Tell program User has requested NDI Source List Refresh
def refreshNDIList():
	global refreshList
	refreshList = True

# Generate button list for NDI Sources
def generateSourceListGUI():
	global currentStatus
	global NDIsources
	global NDISourceList
	
	if NDIsources is not None:
		if NDISourceList is not None:
			NDISourceList.destroy()
		NDISourceList = tk.Frame()
		# buttonframe = tk.Frame(master=NDISourceList,relief=tk.RAISED,borderwidth=1)
		buttona = tk.Button(master=NDISourceList, text="Refresh List", command=refreshNDIList)
		buttona.pack()
		# buttonframe.pack()
		if(len(NDIsources) > 0):
			print(str(len(NDIsources)) + " NDI Sources Detected")
			frame = tk.Frame(master=NDISourceList,relief=tk.RAISED,borderwidth=1)
			for x in range(len(NDIsources)):
				
				#frame.grid(row=x, column=0)
				button = (tk.Button(master=frame,text=NDIsources[x].name,width=100,height=1,command=lambda idx = x: setNDISource(idx)))
				button.pack()
			frame.pack()


		else:
			label = tk.Label(master=NDISourceList, text="No Sources Detected")
			label.pack()
		NDISourceList.pack()

# Load image for program on main thread
def refreshFrame(image):
	global frameimage
	frame = image
	if frame is None:
		return
	frameimage = ImageTk.PhotoImage(image=Image.fromarray(frame, mode="RGBA"))
	if(frameimage != None):
		canvas.create_image(0,0, anchor="nw", image=frameimage)


# Get NDI List 
def workerThread_generateSourceList():
	NDIsources = find.get_sources()
	if NDIsources is not None:
		NDIList_out.put(NDIsources)

# Get image from NDI Stream
def workerThread_GetNDIImage(rec):
	recieveSource = rec
	
	frameimage = None;
	if(recieveSource != None):
		try:
			frame = recieveSource.read()
		except:
			recieveSource = None
			print("Lost source")
			#currentStatus.set("Current NDI Source Lost")
			return
		frame = imutils.resize(frame, width=500)
		b, g, r, a = frame.T
		frame = np.array([r, g, b, a])
		frame = frame.transpose()
	NDIImage_out.put(frame)

# FUNCTIONs END

# Main Program

find = finder.create_ndi_finder()


window = tk.Tk()
window.title("NDI Monitor")
canvas = tk.Canvas(width=500,height=300)
canvas.pack()
currentStatus = tk.StringVar()
currentStatus.set("Awaiting NDI Source")
tk.Label(textvariable=currentStatus).pack()

#generateSourceListGUI()

Process = threading.Thread(target=workerThread_GetNDIImage, args=(recieveSource, ))
generateSourceList = threading.Thread(target=workerThread_generateSourceList)


while(1):

	# ==================================================================
	# Get NDI Source Frame

	# If frame grabber now alive, then make new thread for it
	if recieveSource is not None:
		if not Process.is_alive():
			currentStatus.set("Grabbing Image")
			Process = threading.Thread(target=workerThread_GetNDIImage, args=(recieveSource, ))
			Process.start()

	# If NDI Image Queue is not empty then show NDI Image on GUI
	if not NDIImage_out.empty():
		currentStatus.set("Displaying Image")
		refreshFrame(NDIImage_out.get())
		with NDIImage_out.mutex:
			NDIImage_out.queue.clear()

	# =================================================================
	# List NDI Sources

	# Every 10 Seconds Refresh NDI List on thread.
	if refreshList:
		if generateSourceList.is_alive() is not True:
			currentStatus.set("Refreshing NDI Sources")
			generateSourceList = threading.Thread(target=workerThread_generateSourceList)
			generateSourceList.start()
		refreshList = False
		

	# If NDI list refreshed and stored in queue, generate new GUI for it
	if not NDIList_out.empty():
		currentStatus.set("Regenerating List")
		NDIsources = NDIList_out.get()
		generateSourceListGUI()
	
	# =================================================================
	window.update()
	
	
# Main Program End
