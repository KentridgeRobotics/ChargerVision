# import the necessary packages
from collections import deque
from sense_hat import SenseHat
import numpy as np
import time
import argparse
import imutils
import cv2

# initialize the camera and grab a reference to the raw camera capture
cap = cv2.VideoCapture(0)

while(True):
	_, image = cap.read()

	# show the frame
	cv2.imshow("Frame", image)
	key = cv2.waitKey(1) & 0xFF

	# if the `q` key was pressed, break from the loop
	if key == ord("q"):
		sense.clear(0, 0, 0)
		break
cap.release()
cv2.destroyAllWindows()