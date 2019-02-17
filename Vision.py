#!/usr/bin/env python3

from collections import deque
import time
import ast
import sys
import atexit
import pprint

import netifaces as ni
from networktables import NetworkTables
import argparse

import numpy as np
import cv2
import imutils

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--camera", type=int, default=0, help="camera id")
ap.add_argument("-i", "--serverip", type=str, default="10.37.86.2", help="NetworkTables IP")
ap.add_argument("-a", "--table", type=str, default="SmartDashboard", help="NetworkTables Table")
ap.add_argument("-g", "--gui", action='store_true', help="Enables X GUI")
ap.add_argument("-e", "--environment", action='store_true', help="Disables features for a non-Pi environment")
args = vars(ap.parse_args())

dataFile = "Data"
def nothing(x):
	pass

# initialize NetworkTables
NetworkTables.initialize(server=args["serverip"])
nwt = NetworkTables.getTable(args["table"])

# push ip to NetworkTables
if not args["environment"]:
	ip = ni.ifaddresses('eth0')[ni.AF_INET][0]['addr']
	nwt.putString("rpi_ip", ip)

# Control Window
if args["gui"]:
	cv2.namedWindow('Control', cv2.WINDOW_NORMAL)

# read and parse data file if present - otherwise use default values
try:
	with open(dataFile, 'r') as f:
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

	bright = 15
	
	target_lower_hue = 0
	target_upper_hue = 255

	target_lower_sat = 0
	target_upper_sat = 255

	target_lower_vib = 0
	target_upper_vib = 255

if args["gui"]:
	cv2.createTrackbar('Cube_Lower_Hue', 'Control', cube_lower_hue, 255, nothing)
	cv2.createTrackbar('Cube_Upper_Hue', 'Control', cube_upper_hue, 255, nothing)
	
	cv2.createTrackbar('Cube_Lower_Sat', 'Control', cube_lower_sat, 255, nothing)
	cv2.createTrackbar('Cube_Upper_Sat', 'Control', cube_upper_sat, 255, nothing)
	
	cv2.createTrackbar('Cube_Lower_Vib', 'Control', cube_lower_vib, 255, nothing)
	cv2.createTrackbar('Cube_Upper_Vib', 'Control', cube_upper_vib, 255, nothing)
	
	cv2.createTrackbar('Cube_Rad', 'Control', cube_rad, 100, nothing)
	
	cv2.createTrackbar('Target_Lower_Hue', 'Control', target_lower_hue, 255, nothing)
	cv2.createTrackbar('Target_Upper_Hue', 'Control', target_upper_hue, 255, nothing)
	
	cv2.createTrackbar('Target_Lower_Sat', 'Control', target_lower_sat, 255, nothing)
	cv2.createTrackbar('Target_Upper_Sat', 'Control', target_upper_sat, 255, nothing)
	
	cv2.createTrackbar('Target_Lower_Vib', 'Control', target_lower_vib, 255, nothing)
	cv2.createTrackbar('Target_Upper_Vib', 'Control', target_upper_vib, 255, nothing)
	
	cv2.createTrackbar('Brightness', 'Control', bright, 100, nothing)
else:
	# push current settings to network tables
	nwt.putNumber('cube/lower_hue', cube_lower_hue)
	nwt.putNumber('cube/upper_hue', cube_upper_hue)
	
	nwt.putNumber('cube/lower_sat', cube_lower_sat)
	nwt.putNumber('cube/upper_sat', cube_upper_sat)
	
	nwt.putNumber('cube/lower_vib', cube_lower_vib)
	nwt.putNumber('cube/upper_vib', cube_upper_vib)
	
	nwt.putNumber('cube/radius', cube_rad)
	
	nwt.putNumber('brightness', bright)
	
	nwt.putNumber('target/lower_hue', target_lower_hue)
	nwt.putNumber('target/upper_hue', target_upper_hue)
	
	nwt.putNumber('target/lower_sat', target_lower_sat)
	nwt.putNumber('target/upper_sat', target_upper_sat)
	
	nwt.putNumber('target/lower_vib', target_lower_vib)
	nwt.putNumber('target/upper_vib', target_upper_vib)

# reslution to resize input to
# low resolution used to speed up processing
xres = 160
yres = 128

# finds yellow game cubes in provided hsv image
def findCubeContours(hsv):
	# get settings from network tables or trackbars
	if args["gui"]:
		cube_lower_hue = cv2.getTrackbarPos('Cube_Lower_Hue', 'Control')
		cube_upper_hue = cv2.getTrackbarPos('Cube_Upper_Hue', 'Control')
		
		cube_lower_sat = cv2.getTrackbarPos('Cube_Lower_Sat', 'Control')
		cube_upper_sat = cv2.getTrackbarPos('Cube_Upper_Sat', 'Control')
		
		cube_lower_vib = cv2.getTrackbarPos('Cube_Lower_Vib', 'Control')
		cube_upper_vib = cv2.getTrackbarPos('Cube_Upper_Vib', 'Control')
		
		cube_rad = cv2.getTrackbarPos('Cube_Rad', 'Control')
	else:
		cube_lower_hue = nwt.getNumber('cube/lower_hue', 0)
		cube_upper_hue = nwt.getNumber('cube/upper_hue', 255)

		cube_lower_sat = nwt.getNumber('cube/lower_sat', 0)
		cube_upper_sat = nwt.getNumber('cube/upper_sat', 255)

		cube_lower_vib = nwt.getNumber('cube/lower_vib', 0)
		cube_upper_vib = nwt.getNumber('cube/upper_vib', 255)

		cube_rad = nwt.getNumber('cube/radius', 10)

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
	# get settings from network tables or trackbars
	if args["gui"]:
		target_lower_hue = cv2.getTrackbarPos('Target_Lower_Hue', 'Control')
		target_upper_hue = cv2.getTrackbarPos('Target_Upper_Hue', 'Control')
		
		target_lower_sat = cv2.getTrackbarPos('Target_Lower_Sat', 'Control')
		target_upper_sat = cv2.getTrackbarPos('Target_Upper_Sat', 'Control')
		
		target_lower_vib = cv2.getTrackbarPos('Target_Lower_Vib', 'Control')
		target_upper_vib = cv2.getTrackbarPos('Target_Upper_Vib', 'Control')
	else:
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
	
	if args["gui"]:
		cv2.imshow('hsv',hsv)
		cv2.imshow('image',image)
		cv2.imshow('mask',res)
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
	if args["gui"]:
		cube_lower_hue = cv2.getTrackbarPos('Cube_Lower_Hue', 'Control')
		cube_upper_hue = cv2.getTrackbarPos('Cube_Upper_Hue', 'Control')
		
		cube_lower_sat = cv2.getTrackbarPos('Cube_Lower_Sat', 'Control')
		cube_upper_sat = cv2.getTrackbarPos('Cube_Upper_Sat', 'Control')
		
		cube_lower_vib = cv2.getTrackbarPos('Cube_Lower_Vib', 'Control')
		cube_upper_vib = cv2.getTrackbarPos('Cube_Upper_Vib', 'Control')
		
		cube_rad = cv2.getTrackbarPos('Cube_Rad', 'Control')
		
		target_lower_hue = cv2.getTrackbarPos('Target_Lower_Hue', 'Control')
		target_upper_hue = cv2.getTrackbarPos('Target_Upper_Hue', 'Control')
		
		target_lower_sat = cv2.getTrackbarPos('Target_Lower_Sat', 'Control')
		target_upper_sat = cv2.getTrackbarPos('Target_Upper_Sat', 'Control')
		
		target_lower_vib = cv2.getTrackbarPos('Target_Lower_Vib', 'Control')
		target_upper_vib = cv2.getTrackbarPos('Target_Upper_Vib', 'Control')
		
		bright = cv2.getTrackbarPos('Brightness', 'Control')
		
		cv2.destroyAllWindows()
	else:
		cube_lower_hue = nwt.getNumber('cube/lower_hue', 0)
		cube_upper_hue = nwt.getNumber('cube/upper_hue', 255)

		cube_lower_sat = nwt.getNumber('cube/lower_sat', 0)
		cube_upper_sat = nwt.getNumber('cube/upper_sat', 255)

		cube_lower_vib = nwt.getNumber('cube/lower_vib', 0)
		cube_upper_vib = nwt.getNumber('cube/upper_vib', 255)

		cube_rad = nwt.getNumber('cube/radius', 10)
		
		target_lower_hue = nwt.getNumber('target/lower_hue', 0)
		target_upper_hue = nwt.getNumber('target/upper_hue', 255)

		target_lower_sat = nwt.getNumber('target/lower_sat', 0)
		target_upper_sat = nwt.getNumber('target/upper_sat', 255)

		target_lower_vib = nwt.getNumber('target/lower_vib', 0)
		target_upper_vib = nwt.getNumber('target/upper_vib', 255)

		bright = nwt.getNumber('brightness', 15.0)
	
	with open(dataFile, 'w') as f:
		f.truncate();
		f.write(str(cube_lower_hue) + "," + str(cube_upper_hue) + "," + str(cube_lower_sat) + "," + str(cube_upper_sat) + "," + str(cube_lower_vib) + "," + str(cube_upper_vib) + "," + str(cube_rad) + "," + str(bright) + "," + str(target_lower_hue) + "," + str(target_upper_hue) + "," + str(target_lower_sat) + "," + str(target_upper_sat) + "," + str(target_lower_vib) + "," + str(target_upper_vib))

# initialize the camera and grab a reference to the raw camera capture
cam = cv2.VideoCapture(args["camera"])
cam.set(cv2.CAP_PROP_AUTOFOCUS, 0)
cam.set(cv2.CAP_PROP_SATURATION, 0.20)
cam.set(cv2.CAP_PROP_CONTRAST, 0.1)
cam.set(cv2.CAP_PROP_GAIN, 0.15)

# main thread
def main():
	while True:
		# gets image from camera
		if args["gui"]:
			bright = cv2.getTrackbarPos('Brightness', 'Control')
		else:
			bright = nwt.getNumber('brightness', 15.0)
		check, image = cam.read()
		if check:
			# if image exists, resize to resolution specified above,
			# sets camera brightness and processes image
			image = imutils.resize(image, width=xres, height=yres)
			cam.set(cv2.CAP_PROP_BRIGHTNESS, bright / 100.0)
			frameUpdate(image)

# starts main thread
if __name__ == '__main__':
	main()
