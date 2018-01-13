# import the necessary packages
from collections import deque
from picamera.array import PiRGBArray
from picamera import PiCamera
from sense_hat import SenseHat
import numpy as np
import time
import argparse
import imutils
import cv2

# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (320, 240)
camera.framerate = 20
rawCapture = PiRGBArray(camera, size=(320, 240))

# initialize SenseHat
sense = SenseHat()

# enable SenseHat LEDs
sense.clear(255, 255, 255)
 
# allow the camera to warmup
time.sleep(0.1)

# capture frames from the camera
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
	# grab the raw NumPy array representing the image, then initialize the timestamp
	# and occupied/unoccupied text
	image = frame.array

	(hc, wc) = image.shape[:2]
	imcenter = (wc/2, hc/2)
	RM = cv2.getRotationMatrix2D(imcenter, 180, 1.0)
	image = cv2.warpAffine(image, RM, (wc,hc))

	# show the frame
	cv2.imshow("Frame", image)
	key = cv2.waitKey(1) & 0xFF
 
	# clear the stream in preparation for the next frame
	rawCapture.truncate(0)

	# if the `q` key was pressed, break from the loop
	if key == ord("q"):
		sense.clear(0, 0, 0)
		break