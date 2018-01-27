# import the necessary packages
from collections import deque
from picamera.array import PiRGBArray
from picamera import PiCamera
from sense_hat import SenseHat
from networktables import NetworkTables
import numpy as np
import time
import argparse
import imutils
import ast
import cv2
import sys
import curses
from curses import wrapper


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--camera", type=int, default=0, help="camera source")
ap.add_argument("-s", "--sense", type=int, default=0, help="enable sensehat")
ap.add_argument("-i", "--serverip", type=str, default="10.37.86.2", help="NetworkTables IP")
ap.add_argument("-a", "--table", type=str, default="SmartDashboard", help="NetworkTables Table")
args = vars(ap.parse_args())

def printst(win, str):
	if not pauseOut:
		win.clear()
		win.addstr(str + "\n")

def nothing(x):
	pass
  
try:
	with open('VisionData', 'r') as f:
		data = f.read()
		pdata = data.split(",")
		f.close()
	lower_hue = int(pdata[0])
	upper_hue = int(pdata[1])

	lower_sat = int(pdata[2])
	upper_sat = int(pdata[3])

	lower_vib = int(pdata[4])
	upper_vib = int(pdata[5])

	rad = int(pdata[6])

	bright = int(pdata[7])
except (IOError, NameError, IndexError, ValueError) as e:
	lower_hue = 0
	Upper_hue = 255

	lower_sat = 0
	upper_sat = 255

	lower_vib = 0
	upper_vib = 255

	rad = 10

	bright = 50

# initialize NetworkTables
print("Connecting to network tables at: " + args["serverip"])
NetworkTables.initialize(server=args["serverip"])
print("Selecting NetworkTable: " + args["table"])
nwt = NetworkTables.getTable(args["table"])

# initialize SenseHat
if args["sense"] == 1:
	sense = SenseHat()
	# enable SenseHat LEDs
	sense.clear(255, 255, 255)
	sense.set_rotation(90)
	sense.set_pixel(2, 1, [0, 0, 0])
	sense.set_pixel(5, 1, [0, 0, 0])
	sense.set_pixel(3, 3, [0, 255, 0])
	sense.set_pixel(4, 3, [0, 255, 0])
	sense.set_pixel(1, 5, [0, 255, 0])
	sense.set_pixel(2, 6, [0, 255, 0])
	sense.set_pixel(3, 6, [0, 255, 0])
	sense.set_pixel(4, 6, [0, 255, 0])
	sense.set_pixel(5, 6, [0, 255, 0])
	sense.set_pixel(6, 5, [0, 255, 0])

# resolution
xres = 160
yres = 128
fps = 40

# capture frames from the camera
def frameUpdate(image, window):

	#for testing
	lower_limit = np.array([lower_hue, lower_sat, lower_vib])
	upper_limit = np.array([upper_hue, upper_sat, upper_vib])

	hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

	# construct a mask for the color "green", then perform
	# a series of dilations and erosions to remove any small
	# blobs left in the mask
	mask = cv2.inRange(hsv, lower_limit, upper_limit)
	mask = cv2.erode(mask, None, iterations=2)
	mask = cv2.dilate(mask, None, iterations=2)

	# find contours in the mask and initialize the current
	# (x, y) center of the ball
	cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
	center = None
	# only proceed if at least one contour was found
	if len(cnts) > 0:
		# find the largest contour in the mask, then use
		# it to compute the minimum enclosing circle and
		# centroid
		c = max(cnts, key=cv2.contourArea)
		((x, y), radius) = cv2.minEnclosingCircle(c)
		M = cv2.moments(c)
		if M["m00"] > 0:
			cx = int(M["m10"] / M["m00"])
			cy = int(M["m01"] / M["m00"])
			center = (cx, cy)
			# only proceed if the radius meets a minimum size
			if radius > rad:
				# add data to NetworkTables
				printst(window, str(center) + "," + str(radius))
				nwt.putNumber('cubeX', cx)
				nwt.putNumber('cubeY', cy)
				nwt.putNumber('cubeR', radius)

def stopRun():
	if args["sense"] == 1:
		sense.clear(0, 0, 0)
	with open('VisionData', 'w') as f:
		f.truncate();
		f.write(str(lower_hue) + "," + str(upper_hue) + "," + str(lower_sat) + "," + str(upper_sat) + "," + str(lower_vib) + "," + str(upper_vib) + "," + str(rad) + "," + str(bright))

def main(window):
	window.nodelay(True)
	global pauseOut
	pauseOut = False
	# initialize the camera and grab a reference to the raw camera capture
	if args["camera"] == -1:
		camera = PiCamera()
		camera.resolution = (xres, yres)
		rawCapture = PiRGBArray(camera, size=(xres, yres))
	 
		# allow the camera to warmup
		time.sleep(0.1)
		while(True):
			camera.capture(rawCapture, format="bgr", use_video_port=True)
			# grab the raw NumPy array representing the image, then initialize the timestamp
			# and occupied/unoccupied text
			image = rawCapture.array
	
			(hc, wc) = image.shape[:2]
			imcenter = (wc/2, hc/2)
			RM = cv2.getRotationMatrix2D(imcenter, 180, 1.0)
			image = cv2.warpAffine(image, RM, (wc,hc))
	
			frameUpdate(image, window)
			# clear the stream in preparation for the next frame
			rawCapture.seek(0)
			rawCapture.truncate(0)
			# if an input was given, break from the loop
			key = window.getch()
			if key == ord('q'):
				stopRun()
				break
			elif key == ord(' '):
				if pauseOut:
					pauseOut = False
				else:
					pauseOut = True
	else:
		cam = cv2.VideoCapture(args["camera"])
		while(True):
			_, image = cam.read()
	
			cam.set(cv2.CAP_PROP_BRIGHTNESS, bright / 100.0)
			image = imutils.resize(image, width=xres)
	
			frameUpdate(image, window)
			# if an input was given, break from the loop
			key = window.getch()
			if key == ord('q'):
				stopRun()
				cam.release()
				break
			elif key == ord(' '):
				if pauseOut:
					pauseOut = False
				else:
					pauseOut = True
wrapper(main)
