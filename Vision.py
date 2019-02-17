#!/usr/bin/env python3

from collections import deque
import time
import ast
import sys
import atexit
import math
import argparse

import pprint
import netifaces as ni
from networktables import NetworkTables

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
ap.add_argument("--image", help="Specify image file path")
args = vars(ap.parse_args())

dataFile = "Data.dat"
def nothing(x):
	pass

# reslution to resize input to
# low resolution used to speed up processing
xres = 160
yres = 128

# horizontal fov of camera for calculating angle
horizontal_fov = 64.4

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
	
	bright = int(pdata[0])
	
	target_lower_hue = int(pdata[1])
	target_upper_hue = int(pdata[2])

	target_lower_sat = int(pdata[3])
	target_upper_sat = int(pdata[4])

	target_lower_vib = int(pdata[5])
	target_upper_vib = int(pdata[6])
except (IOError, NameError, IndexError, ValueError) as e:
	bright = 15
	
	target_lower_hue = 0
	target_upper_hue = 255

	target_lower_sat = 0
	target_upper_sat = 255

	target_lower_vib = 0
	target_upper_vib = 255

if args["gui"]:
	cv2.createTrackbar('Brightness', 'Control', bright, 100, nothing)
	
	cv2.createTrackbar('Target_Lower_Hue', 'Control', target_lower_hue, 255, nothing)
	cv2.createTrackbar('Target_Upper_Hue', 'Control', target_upper_hue, 255, nothing)
	
	cv2.createTrackbar('Target_Lower_Sat', 'Control', target_lower_sat, 255, nothing)
	cv2.createTrackbar('Target_Upper_Sat', 'Control', target_upper_sat, 255, nothing)
	
	cv2.createTrackbar('Target_Lower_Vib', 'Control', target_lower_vib, 255, nothing)
	cv2.createTrackbar('Target_Upper_Vib', 'Control', target_upper_vib, 255, nothing)
else:
	# push current settings to network tables
	nwt.putNumber('brightness', bright)
	
	nwt.putNumber('target/lower_hue', target_lower_hue)
	nwt.putNumber('target/upper_hue', target_upper_hue)
	
	nwt.putNumber('target/lower_sat', target_lower_sat)
	nwt.putNumber('target/upper_sat', target_upper_sat)
	
	nwt.putNumber('target/lower_vib', target_lower_vib)
	nwt.putNumber('target/upper_vib', target_upper_vib)

angle_per_pixel = horizontal_fov / xres

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
	if args["gui"]:
		res = cv2.bitwise_and(image,image,mask=mask)
	
	cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
	cnts = imutils.grab_contours(cnts)
	
	height, width = image.shape[:2]
	if args["gui"]:
		contours = np.zeros((height, width, 3), np.uint8)
	
	sorted_rects = []
	
	for c in cnts:
		peri = cv2.arcLength(c, True)
		approx = cv2.approxPolyDP(c, 0.03 * peri, True)
		if 3 <= len(approx) <= 5:
			c = c.astype("int")
			rect = cv2.minAreaRect(c)
			sorted_rects.append(rect)
			if args["gui"]:
				cv2.drawContours(contours, [c], -1, (0, 255, 0), 1)
	
	sorted_rects = sorted(sorted_rects, key=lambda cnt: cnt[0][0])
	
	center_pnts = []
	
	left = False
	
	if args["gui"]:
		cv2.circle(res, (np.round(width / 2).astype("int"), np.round(height / 2).astype("int")), 3, (0, 0, 255), 1)
	
	for rect in sorted_rects:
		angle = rect[2]
		if angle < -45:
			left = True
			leftMid = rect[0]
		elif angle >= -45:
			if left:
				rightMid = rect[0]
				mid = (np.round((leftMid[0] + rightMid[0]) * 0.5).astype("int"), np.round((leftMid[1] + rightMid[1]) * 0.5).astype("int"))
				center_pnts.append(mid)
				if args["gui"]:
					cv2.circle(res, mid, 3, (255, 0, 0), 1)
				left = False
				
	angles = []
	
	center = width / 2
	
	for pnt in center_pnts:
		x_dist = pnt[0] - center
		angle = x_dist * angle_per_pixel
		angles.append(angle)
	
	if args["gui"]:
		cv2.imshow('hsv',hsv)
		cv2.imshow('image',image)
		cv2.imshow('mask',res)
		cv2.imshow('contours',contours)
		cv2.waitKey(1)
	pass

# capture frames from the camera, converts to hsv
# and pushes to processing functions
def frameUpdate(image):
	hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
	findTargetContours(image, hsv)

# catch ctrl+c exit and save data to file
@atexit.register
def exithandler():
	if args["gui"]:
		bright = cv2.getTrackbarPos('Brightness', 'Control')
		
		target_lower_hue = cv2.getTrackbarPos('Target_Lower_Hue', 'Control')
		target_upper_hue = cv2.getTrackbarPos('Target_Upper_Hue', 'Control')
		
		target_lower_sat = cv2.getTrackbarPos('Target_Lower_Sat', 'Control')
		target_upper_sat = cv2.getTrackbarPos('Target_Upper_Sat', 'Control')
		
		target_lower_vib = cv2.getTrackbarPos('Target_Lower_Vib', 'Control')
		target_upper_vib = cv2.getTrackbarPos('Target_Upper_Vib', 'Control')
		
		cv2.destroyAllWindows()
	else:
		bright = nwt.getNumber('brightness', 15.0)
		
		target_lower_hue = nwt.getNumber('target/lower_hue', 0)
		target_upper_hue = nwt.getNumber('target/upper_hue', 255)

		target_lower_sat = nwt.getNumber('target/lower_sat', 0)
		target_upper_sat = nwt.getNumber('target/upper_sat', 255)

		target_lower_vib = nwt.getNumber('target/lower_vib', 0)
		target_upper_vib = nwt.getNumber('target/upper_vib', 255)
	
	with open(dataFile, 'w') as f:
		f.truncate();
		f.write(str(bright) + "," + str(target_lower_hue) + "," + str(target_upper_hue) + "," + str(target_lower_sat) + "," + str(target_upper_sat) + "," + str(target_lower_vib) + "," + str(target_upper_vib))

# initialize the camera and grab a reference to the raw camera capture
if args["image"] is None:
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
		if args["image"] is not None:
			check = True;
			image = cv2.imread(args["image"], cv2.COLOR_BGR2HSV);
		else:
			check, image = cam.read()
		if check:
			# if image exists, resize to resolution specified above,
			# sets camera brightness and processes image
			image = imutils.resize(image, width=xres, height=yres)
			if args["image"] is None:
				cam.set(cv2.CAP_PROP_BRIGHTNESS, bright / 100.0)
			frameUpdate(image)

# starts main thread
if __name__ == '__main__':
	main()
