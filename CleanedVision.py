#!/usr/bin/env python3
# import the necessary packages
from collections import deque
from networktables import NetworkTables
import numpy as np
import time
import argparse
import imutils
import ast
import cv2
import sys
import ColorSensor

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--camera", type=int, default=0, help="camera source")
ap.add_argument("-i", "--serverip", type=str, default="10.37.86.2", help="NetworkTables IP")
ap.add_argument("-a", "--table", type=str, default="SmartDashboard", help="NetworkTables Table")
args = vars(ap.parse_args())

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
	upper_hue = 255

	lower_sat = 0
	upper_sat = 255

	lower_vib = 0
	upper_vib = 255

	rad = 10

	bright = 50

# reslution
xres = 160
yres = 128

# initialize NetworkTables
NetworkTables.initialize(server=args["serverip"])
nwt = NetworkTables.getTable(args["table"])


def findCubeContours(hsv):
        pass
    lower_limit = np.array([lower_hue, lower_sat, lower_vib])
    upper_limit = np.array([upper_hue, upper_sat, upper_vib])

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)


    mask = cv2.inRange(hsv, lower_limit, upper_limit)
    mask = cv2.erode(mase, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)
    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]

    return cnts

def findTargetContours(hsv):


# capture frames from the camera
def frameUpdate(image):

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
				nwt.putNumber('cubeX', cx)
				nwt.putNumber('cubeY', cy)
				nwt.putNumber('cubeR', radius)
				print(NetworkTables.getTable('/cubeX/'))
				print(NetworkTables.getTable('/cubeY/'))
				print(NetworkTables.getTable('/cubeR/'))

def stopRun():
	with open('VisionData', 'w') as f:
		f.truncate();
		f.write(str(lower_hue) + "," + str(upper_hue) + "," + str(lower_sat) + "," + str(upper_sat) + "," + str(lower_vib) + "," + str(upper_vib) + "," + str(rad) + "," + str(bright))

# initialize the camera and grab a reference to the raw camera capture
# writes color data to the network table
	cam = cv2.VideoCapture(args["camera"])
	while(True):
		image = cam.read()
		image = imutils.resize(image, width=xres)
		cam.set(cv2.CAP_PROP_BRIGHTNESS, bright / 100.0)
		frameUpdate(image)
                write_color_data(nwt)
print('sup')
