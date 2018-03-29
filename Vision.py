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

color = [0,0,255]

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
	cube_lower_hue = int(pdata[0])
	cube_upper_hue = int(pdata[1])

	cube_lower_sat = int(pdata[2])
	cube_upper_sat = int(pdata[3])

	cube_lower_vib = int(pdata[4])
	cube_upper_vib = int(pdata[5])

	cube_rad = int(pdata[6])
	
	target_lower_hue = int(pdata[8])
	target_upper_hue = int(pdata[9])

	target_lower_sat = int(pdata[10])
	target_upper_sat = int(pdata[11])

	target_lower_vib = int(pdata[12])
	target_upper_vib = int(pdata[13])

	bright = int(pdata[7])
except (IOError, NameError, IndexError, ValueError) as e:
	cube_lower_hue = 0
	cube_upper_hue = 255

	cube_lower_sat = 0
	cube_upper_sat = 255

	cube_lower_vib = 0
	cube_upper_vib = 255

	cube_rad = 10

	bright = 50
	
	target_lower_hue = 0
	target_upper_hue = 255

	target_lower_sat = 0
	target_upper_sat = 255

	target_lower_vib = 0
	target_upper_vib = 255

# push current settings to network tables
nwt.putNumber('cube/lower_hue', cube_lower_hue)
nwt.putNumber('cube/upper_hue', cube_upper_hue)

nwt.putNumber('cube/lower_sat', cube_lower_sat)
nwt.putNumber('cube/upper_sat', cube_upper_sat)

nwt.putNumber('cube/lower_vib', cube_lower_vib)
nwt.putNumber('cube/upper_vib', cube_upper_vib)

nwt.putNumber('radius', cube_rad)

nwt.putNumber('brightness', bright)

nwt.putNumber('target/lower_hue', target_lower_hue)
nwt.putNumber('target/upper_hue', target_upper_hue)

nwt.putNumber('target/lower_sat', target_lower_sat)
nwt.putNumber('target/upper_sat', target_upper_sat)

nwt.putNumber('target/lower_vib', target_lower_vib)
nwt.putNumber('target/upper_vib', target_upper_vib)

# push blank color settings to network tables
nwt.putNumberArray('LED', [0, 0, 0])

# reslution to resize input to
# low resolution used to speed up processing
xres = 160
yres = 128

# finds yellow game cubes in provided hsv image
def findCubeContours(hsv):
	# get settings from network tables
	cube_lower_hue = nwt.getNumber('cube/lower_hue', 0)
	cube_upper_hue = nwt.getNumber('cube/upper_hue', 255)

	cube_lower_sat = nwt.getNumber('cube/lower_sat', 0)
	cube_upper_sat = nwt.getNumber('cube/upper_sat', 255)

	cube_lower_vib = nwt.getNumber('cube/lower_vib', 0)
	cube_upper_vib = nwt.getNumber('cube/upper_vib', 255)

	cube_rad = nwt.getNumber('radius', 10)

	# creates arrays of low and upper bounds of hsv values to test for
	cube_lower_limit = np.array([cube_lower_hue, cube_lower_sat, cube_lower_vib])
	cube_upper_limit = np.array([cube_upper_hue, cube_upper_sat, cube_upper_vib])

	# constructs a mask for the hsv bounds, then performs
	# a series of dilations and erosions to remove any
	# small blobs left in the mask
	mask = cv2.inRange(hsv, cube_lower_limit, cube_upper_limit)
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
			if radius > cube_rad:
				# put data to network tables
				nwt.putNumber('cubeX', cx)
				nwt.putNumber('cubeY', cy)
				nwt.putNumber('cubeR', radius)
	return cnts

# finds vision targets in provided hsv image
def findTargetContours(image, hsv):
	# get settings from network tables
	target_lower_hue = nwt.getNumber('target/lower_hue', 0)
	target_upper_hue = nwt.getNumber('target/upper_hue', 255)

	target_lower_sat = nwt.getNumber('target/lower_sat', 0)
	target_upper_sat = nwt.getNumber('target/upper_sat', 255)

	target_lower_vib = nwt.getNumber('target/lower_vib', 0)
	target_upper_vib = nwt.getNumber('target/upper_vib', 255)

	# creates arrays of low and upper bounds of hsv values to test for
	target_lower_limit = np.array([target_lower_hue, target_lower_sat, target_lower_vib])
	target_upper_limit = np.array([target_upper_hue, target_upper_sat, target_upper_vib])
	
	mask = cv2.inRange(hsv, target_lower_limit, target_upper_limit)
	res = cv2.bitwise_and(image,image,mask=mask)
	
	cv2.imshow('hsv',hsv)
	cv2.imshow('image',res)
	cv2.waitKey(1)
	pass

# capture frames from the camera, converts to hsv
# and pushes to processing functions
def frameUpdate(image):
	hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
	findCubeContours(hsv)
	findTargetContours(image, hsv)

# catch ctrl+c exit and save data to file
@atexit.register
def exithandler():
	with open('VisionData', 'w') as f:
		f.truncate();
		f.write(str(cube_lower_hue) + "," + str(cube_upper_hue) + "," + str(cube_lower_sat) + "," + str(cube_upper_sat) + "," + str(cube_lower_vib) + "," + str(cube_upper_vib) + "," + str(cube_rad) + "," + str(bright) + "," + str(target_lower_hue) + "," + str(target_upper_hue) + "," + str(target_lower_sat) + "," + str(target_upper_sat) + "," + str(target_lower_vib) + "," + str(target_upper_vib))

# initialize the camera and grab a reference to the raw camera capture
cam = cv2.VideoCapture(args["camera"])
# main thread
def main():
	while True:
		# gets LED color and camera brightnessfrom network tables
		# and gets image from camera
		#color = nwt.getNumberArray('LED', (0, 0, 0))
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
