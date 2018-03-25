#!/usr/bin/env python3

from collections import deque
import time
import ast
import sys
import atexit
import pprint

from networktables import NetworkTables
import argparse

import numpy as np
import cv2
import imutils

import LED

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--camera", type=int, default=0, help="camera id")
ap.add_argument("-i", "--serverip", type=str, default="10.37.86.2", help="NetworkTables IP")
ap.add_argument("-a", "--table", type=str, default="SmartDashboard", help="NetworkTables Table")
args = vars(ap.parse_args())

def nothing(x):
	pass

# initialize NetworkTables
NetworkTables.initialize(server=args["serverip"])
nwt = NetworkTables.getTable(args["table"])

# read and parse data file if present - otherwise use default values
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

# push current settings to network tables
nwt.putNumber('lower_hue', lower_hue)
nwt.putNumber('upper_hue', upper_hue)

nwt.putNumber('lower_sat', lower_sat)
nwt.putNumber('upper_sat', upper_sat)

nwt.putNumber('lower_vib', lower_vib)
nwt.putNumber('upper_vib', upper_vib)

nwt.putNumber('radius', rad)

nwt.putNumber('brightness', bright)

# push blank color settings to network tables
nwt.putNumberArray('LED', [0, 0, 0])

# reslution to resize input to
# low resolution used to speed up processing
xres = 160
yres = 128

# finds yellow game cubes in provided hsv image
def findCubeContours(hsv):
	# get settings from network tables
	lower_hue = nwt.getNumber('lower_hue', 0)
	upper_hue = nwt.getNumber('upper_hue', 255)

	lower_sat = nwt.getNumber('lower_sat', 0)
	upper_sat = nwt.getNumber('upper_sat', 255)

	lower_vib = nwt.getNumber('lower_vib', 0)
	upper_vib = nwt.getNumber('upper_vib', 255)

	rad = nwt.getNumber('radius', 10)

	# creates arrays of low and upper bounds of hsv values to test for
	lower_limit = np.array([lower_hue, lower_sat, lower_vib])
	upper_limit = np.array([upper_hue, upper_sat, upper_vib])

	# constructs a mask for the hsv bounds, then performs
	# a series of dilations and erosions to remove any
	# small blobs left in the mask
	mask = cv2.inRange(hsv, lower_limit, upper_limit)
	mask = cv2.erode(mask, None, iterations=2)
	mask = cv2.dilate(mask, None, iterations=2)

	# find contours in the mask and initialize the
	# current (x, y) center of the cube
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
				# put data to network tables
				nwt.putNumber('cubeX', cx)
				nwt.putNumber('cubeY', cy)
				nwt.putNumber('cubeR', radius)
	return cnts

# finds vision targets in provided hsv image
def findTargetContours(hsv):
	pass

# capture frames from the camera, converts to hsv
# and pushes to processing functions
def frameUpdate(image):
	hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
	findCubeContours(hsv)
	findTargetContours(hsv)

# catch ctrl+c exit and save data to file
@atexit.register
def exithandler():
	with open('VisionData', 'w') as f:
		f.truncate();
		f.write(str(lower_hue) + "," + str(upper_hue) + "," + str(lower_sat) + "," + str(upper_sat) + "," + str(lower_vib) + "," + str(upper_vib) + "," + str(rad) + "," + str(bright))

# initialize the camera and grab a reference to the raw camera capture
# writes color data to the network table
cam = cv2.VideoCapture(args["camera"])

# main thread
def main():
	while True:
		# gets LED color and camera brightnessfrom network tables
		# and gets image from camera
		color = nwt.getNumberArray('LED', (0, 0, 0))
		LED.setColor(color)
		bright = nwt.getNumber('brightness', 100.0)
		_, image = cam.read()
		if image is not None:
			# if image exists, resize to resolution specified above,
			# sets camera brightness and processes image
			image = imutils.resize(image, width=xres, height=yres)
			cam.set(cv2.CAP_PROP_BRIGHTNESS, bright / 100.0)
			frameUpdate(image)

# starts main thread
if __name__ == '__main__':
	main()
