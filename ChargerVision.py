#!/usr/bin/env python

"""
Author: Manpreet Singh 2016
GUI program for Calibration
This Program is meant to run on a computer to find the lower/upper HSV Values for calibration
"""

import numpy as np
import cv2 as cv
from networktables import NetworkTable

def nothing(x):
	pass

nt = NetworkTable.getTable("VISION")

cap = cv.VideoCapture(0)

cv.namedWindow('Control')
cv.createTrackbar('Lower_Hue', 'Control', 0, 255, nothing)
cv.createTrackbar('Upper_Hue', 'Control',0, 255, nothing)

cv.createTrackbar('Lower_Sat', 'Control', 0, 255, nothing)
cv.createTrackbar('Upper_Sat', 'Control',0, 255, nothing)

cv.createTrackbar('Lower_Vib', 'Control', 0, 255, nothing)
cv.createTrackbar('Upper_Vib', 'Control',0, 255, nothing)

cv.createTrackbar('Contour', 'Control',-1, 9, nothing)

switch = 'Track Object \n0 : OFF \n1 : ON'
cv.createTrackbar(switch, 'Control',0,1,nothing)

font = cv.FONT_HERSHEY_SIMPLEX

while(True):
	_, im = cap.read()
	#im = np.array(im, dtype=np.uint8)
	#imgray = cv.cvtColor(im,cv.COLOR_BGR2GRAY)
	
	hsv = cv.cvtColor(im, cv.COLOR_BGR2HSV)
	
	lower_hue = cv.getTrackbarPos('Lower_Hue', 'Control')
	upper_hue = cv.getTrackbarPos('Upper_Hue', 'Control')
	
	lower_sat = cv.getTrackbarPos('Lower_Sat', 'Control')
	upper_sat = cv.getTrackbarPos('Upper_Sat', 'Control')
	
	lower_vib = cv.getTrackbarPos('Lower_Vib', 'Control')
	upper_vib = cv.getTrackbarPos('Upper_Vib', 'Control')
	
	contour_num = cv.getTrackbarPos('Contour', 'Control')
	
	switch_val = cv.getTrackbarPos(switch, 'Control')
	
	#for testing
	lower_limit = np.array([lower_hue, lower_sat, lower_vib])
	upper_limit = np.array([upper_hue, upper_sat, upper_vib])
	
	mask = cv.inRange(hsv, lower_limit, upper_limit)
	
	res = cv.bitwise_and(im, im, mask= mask)	
	
	_,contours, hierarchy = cv.findContours(mask,cv.RETR_TREE,cv.CHAIN_APPROX_SIMPLE)
	
	cv.drawContours(res, contours, -1, (255,0,0), 1)
		
	if switch_val == 1 and len(contours) > 0: 
		
		contour_areas = [cv.contourArea(c) for c in contours]
		max_index = np.argmax(contour_areas)
		cnt = contours[max_index]
		
		# Access object for contour data
		moments = cv.moments(cnt)
		if(moments['m00'] != 0):
			# Get center of contour coordinates
			centroid_x = int(moments['m10'] / moments['m00'])
			centroid_y = int(moments['m01'] / moments['m00'])
			
			nt.putNumber('centerX', centroid_x)
			nt.putNumber('centerY', centroid_y)
			
			# Print the Coordinates onto image
			x_t = 'x:%s' % (centroid_x)
			y_t = 'y:%s' % (centroid_y)
			angle = 'a:%s' % (480 / (68.5 * np.sin(np.arctan(.75))) * centroid_y + 480)
			
			cv.putText(res,x_t,(10,40), font, 1.2,(255,0,255),2)
			cv.putText(res,y_t,(10,90), font, 1.2,(255,255,0),2)
			cv.putText(res,angle, (10, 140), font, 1.2,(255,255,255),2)
			
			# Draw Circle around center of Contour
			cv.circle(res, (centroid_x, centroid_y), 5, (255,0,255), -1)
		
		# Draw Rectangle around center of Contour
		x,y,w,h = cv.boundingRect(cnt)
		cv.rectangle(res,(x,y),(x+w,y+h),(0,255,0),2)
		w_t = 'w:%s' % (w)
		cv.putText(res,w_t,(150,40),font,1.2,(0,255,255),2)
	
	#Display output windows	
	cv.imshow('Output', res)
	cv.imshow('hsv', hsv)
	if cv.waitKey(1) & 0xFF == ord('q'):
		break
        
cap.release()
cv.destroyAllWindows()
