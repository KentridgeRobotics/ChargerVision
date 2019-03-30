#!/usr/bin/env python3

from collections import deque
import time
import ast
import sys
import atexit
import math
import argparse
import socket

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
ap.add_argument("-f", "--fps", action='store_true', help="Outputs FPS to console")
ap.add_argument("--image", help="Specify image file path")
args = vars(ap.parse_args())

dataFile = "Data.dat"
def nothing(x):
	pass

# reslution to resize input to
# low resolution used to speed up processing
xres = 320
yres = 256

# blur radius (odd number)
blur_const = 3

# horizontal fov of camera for calculating angle
horizontal_fov = 64.4

# roborio socket
rio_ip = "10.37.86.2"
rio_port = 3000

rio_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# initialize NetworkTables
NetworkTables.initialize(server=args["serverip"])
nwt = NetworkTables.getTable(args["table"])

# push ip to NetworkTables
if not args["environment"]:
	ip = ni.ifaddresses('eth0')[ni.AF_INET][0]['addr']
	nwt.putString("rpi.ip", ip)

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

def translateRotation(rotation, width, height):
	if width < height:
		rotation = -1 * (rotation - 90)
	if rotation > 90:
		rotation = -1 * (rotation - 180)
	rotation *= -1
	return round(rotation, 3)

def getRotation(cnt):
	if len(cnt) >= 5:
		ellipse = cv2.fitEllipse(cnt)
		center = ellipse[0]
		ellipseRotation = ellipse[2]
		ellipseWidth = ellipse[1][0]
		ellipseHeight = ellipse[1][1]
		rotation = translateRotation(ellipseRotation, ellipseWidth, ellipseHeight)
		return rotation, center
	else:
		rect = cv2.minAreaRect(cnt)
		center = rect[0]
		boxRotation = rect[2]
		boxWidth = rect[1][0]
		boxHeight = rect[1][1]
		rotation = translateRotation(boxRotation, boxWidth, boxHeight)
		return rotation, center

xcenter = xres / 2
	
def calculateTarget(cx1, cx2, cy1, cy2):
	center = [np.round((cx1 + cx2) * 0.5).astype("int"), np.round((cy1 + cy2) * 0.5).astype("int")]
	x_dist = center[0] - xcenter
	x_ratio = round(x_dist / xcenter, 3)
	angle = math.degrees(math.atan((center[0] - xcenter) / horizontal_fov))
	return angle, center, x_ratio

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
	#blur = cv2.blur(mask, (blur_const, blur_const))
	blur = cv2.GaussianBlur(mask, (blur_const, blur_const), 0)
	
	if args["gui"]:
		height, width = image.shape[:2]
		res = cv2.bitwise_and(image,image,mask=blur)
		contours = np.zeros((height, width, 3), np.uint8)
		cv2.circle(res, (int(round(width / 2)), int(round(height / 2))), 3, (0, 0, 255), 1)
	
	_, cnts, _ = cv2.findContours(blur, cv2.RETR_TREE, cv2.CHAIN_APPROX_TC89_KCOS)
		
	targets = []
	
	if len(cnts) >= 2:
		sorted_cnts = sorted(cnts, key=lambda cnt: cv2.contourArea(cnt), reverse=True)
		
		bigCnts = []
		for c in sorted_cnts:
			if len(bigCnts) <= 16:
				area = cv2.contourArea(c)
				if area > (xres / 6):
					#peri = cv2.arcLength(c, True)
					#approx = cv2.approxPolyDP(c, 0.01 * peri, True)
					#approx = approx.astype("int")
					rotation, center = getRotation(c)
					if [center[0], center[1], rotation] not in bigCnts:
						bigCnts.append([center[0], center[1], rotation])
						if args["gui"]:
							cv2.drawContours(contours, [c], -1, (0, 255, 0), 1)
					
		bigCnts = sorted(bigCnts, key=lambda cnt: cnt[0])
		
		skipNext = False
		for i in range(len(bigCnts) - 1):
			if skipNext:
				skipNext = False
				continue
			cx1 = bigCnts[i][0]
			cx2 = bigCnts[i + 1][0]
			cy1 = bigCnts[i][1]
			cy2 = bigCnts[i + 1][1]
			angle1 = bigCnts[i][2]
			angle2 = bigCnts[i + 1][2]
			
			if (cx2 - cx1) < (xres / 40):
				continue
			elif abs(cy2 - cy1) > (yres / 2):
				continue
			
			if angle1 > 0:
				continue
			if angle2 < 0:
				continue
			
			angle, center, xdist = calculateTarget(cx1, cx2, cy1, cy2)
			if [angle, center, xdist] not in targets:
				targets.append([angle, center, xdist])
				skipNext = True
				if args["gui"]:
					cv2.circle(res, (center[0], center[1]), 3, (255, 0, 0), 1)
	
	if args["gui"]:
		cv2.imshow('image',image)
		cv2.imshow('mask',res)
		cv2.imshow('contours',contours)
		cv2.waitKey(1)
	
	send_msg = ','.join("{0}_{1}".format(str(round(angle, 3)),str(xdist)) for angle,_,xdist in targets)
	send_msg = send_msg[:1024]
	rio_sock.sendto(send_msg.encode(), (rio_ip, rio_port))
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
	elif not args["environment"]:
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
	cam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
	cam.set(cv2.CAP_PROP_EXPOSURE, 0)
	cam.set(cv2.CAP_PROP_BRIGHTNESS, 0)

fps_shift_reg = deque([], 16)

def getFPS():
	if len(fps_shift_reg) is 0:
		fps = -1
	else:
		fps = sum(fps_shift_reg) / len(fps_shift_reg)
	return fps

# main thread
def main():
	start_time = time.time()
	fps_poll_time = 0.25
	frame_counter = 0
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
			frame_counter += 1
			current_time = time.time()
			if (current_time - start_time) > fps_poll_time:
				fps = frame_counter / (current_time - start_time)
				fps_shift_reg.append(fps)
				frame_counter = 0
				start_time = current_time
			fps = round(getFPS(), 3)
			if not args["environment"]:
				nwt.putNumber("rpi.vision_fps", fps)
			if args["fps"]:
				print("FPS: " + str(fps))
			frameUpdate(image)

# starts main thread
if __name__ == '__main__':
	main()
