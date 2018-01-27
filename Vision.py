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

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-c", "--camera", type=int, default=-1, help="camera source")
ap.add_argument("-b", "--buffer", type=int, default=64, help="max buffer size")
ap.add_argument("-s", "--sense", type=int, default=0, help="enable sensehat")
ap.add_argument("-t", "--team", type=str, default="3786", help="FRC team number")
ap.add_argument("-a", "--table", type=str, default="SmartDashboard", help="NetworkTables Table")
args = vars(ap.parse_args())

def nothing(x):
	pass

# Control Window
cv2.namedWindow('Control', )
try:
	with open('VisionData', 'r') as f:
		data = f.read()
		pdata = data.split(",")
		f.close()
	cv2.createTrackbar('Lower_Hue', 'Control', int(pdata[0]), 255, nothing)
	cv2.createTrackbar('Upper_Hue', 'Control', int(pdata[1]), 255, nothing)

	cv2.createTrackbar('Lower_Sat', 'Control', int(pdata[2]), 255, nothing)
	cv2.createTrackbar('Upper_Sat', 'Control', int(pdata[3]), 255, nothing)

	cv2.createTrackbar('Lower_Vib', 'Control', int(pdata[4]), 255, nothing)
	cv2.createTrackbar('Upper_Vib', 'Control', int(pdata[5]), 255, nothing)

	cv2.createTrackbar('Rad', 'Control', int(pdata[6]), 100, nothing)

	cv2.createTrackbar('Brightness', 'Control', int(pdata[7]), 100, nothing)
except (IOError, NameError, IndexError, ValueError) as e:
	cv2.createTrackbar('Lower_Hue', 'Control', 0, 255, nothing)
	cv2.createTrackbar('Upper_Hue', 'Control', 255, 255, nothing)

	cv2.createTrackbar('Lower_Sat', 'Control', 0, 255, nothing)
	cv2.createTrackbar('Upper_Sat', 'Control', 255, 255, nothing)

	cv2.createTrackbar('Lower_Vib', 'Control', 0, 255, nothing)
	cv2.createTrackbar('Upper_Vib', 'Control', 255, 255, nothing)

	cv2.createTrackbar('Rad', 'Control', 10, 100, nothing)

	cv2.createTrackbar('Brightness', 'Control', 50, 100, nothing)

# initialize NetworkTables
teamSplit = [args["team"][i:i+2] for i in range(0, len(args["team"]), 2)]
print("Connecting to network tables at: 10." + teamSplit[0] + "." + teamSplit[1] + ".2")
NetworkTables.initialize(server='10.' + teamSplit[0] + '.' + teamSplit[1] + '.2')
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

# list of tracked points
pts = deque(maxlen=args["buffer"])

# capture frames from the camera
def frameUpdate(image):
	# color trackbars
	lower_hue = cv2.getTrackbarPos('Lower_Hue', 'Control')
	upper_hue = cv2.getTrackbarPos('Upper_Hue', 'Control')
	
	lower_sat = cv2.getTrackbarPos('Lower_Sat', 'Control')
	upper_sat = cv2.getTrackbarPos('Upper_Sat', 'Control')
	
	lower_vib = cv2.getTrackbarPos('Lower_Vib', 'Control')
	upper_vib = cv2.getTrackbarPos('Upper_Vib', 'Control')

	rad = cv2.getTrackbarPos('Rad', 'Control')

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
				# draw the circle and centroid on the frame,
				# then update the list of tracked points
				cv2.circle(image, (int(x), int(y)), int(radius), (0, 255, 255), 2)
				cv2.circle(image, center, 5, (0, 0, 255), -1)

				# update the points queue
				pts.appendleft(center)

	# loop over the set of tracked points
	for i in xrange(1, len(pts)):
		# if either of the tracked points are None, ignore
		# them
		if pts[i - 1] is None or pts[i] is None:
			continue
		# otherwise, compute the thickness of the line and
		# draw the connecting lines
		thickness = int(np.sqrt(args["buffer"] / float(i + 1)) * 2.5)
		cv2.line(image, pts[i - 1], pts[i], (0, 0, 255), thickness)

	# show the frame
	imagem = cv2.bitwise_and(image,image,mask = mask)
	hsvm = cv2.bitwise_and(hsv,hsv,mask = mask)
	cv2.imshow("Track", image)
	cv2.imshow("Mask", imagem)
	cv2.imshow("HSV", hsv)
	cv2.imshow("HSV Mask", hsvm)

def stopRun():
	lower_hue = cv2.getTrackbarPos('Lower_Hue', 'Control')
	upper_hue = cv2.getTrackbarPos('Upper_Hue', 'Control')
	
	lower_sat = cv2.getTrackbarPos('Lower_Sat', 'Control')
	upper_sat = cv2.getTrackbarPos('Upper_Sat', 'Control')
	
	lower_vib = cv2.getTrackbarPos('Lower_Vib', 'Control')
	upper_vib = cv2.getTrackbarPos('Upper_Vib', 'Control')

	rad = cv2.getTrackbarPos('Rad', 'Control')

	bright = cv2.getTrackbarPos('Brightness', 'Control')

	if args["sense"] == 1:
		sense.clear(0, 0, 0)
	with open('VisionData', 'w') as f:
		f.truncate();
		f.write(str(lower_hue) + "," + str(upper_hue) + "," + str(lower_sat) + "," + str(upper_sat) + "," + str(lower_vib) + "," + str(upper_vib) + "," + str(rad) + "," + str(bright))

# initialize the camera and grab a reference to the raw camera capture
if args["camera"] == -1:
	camera = PiCamera()
	camera.resolution = (xres, yres)
	camera.framerate = fps
	rawCapture = PiRGBArray(camera, size=(xres, yres))
 
	# allow the camera to warmup
	time.sleep(0.1)
	for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
		# grab the raw NumPy array representing the image, then initialize the timestamp
		# and occupied/unoccupied text
		image = frame.array

		(hc, wc) = image.shape[:2]
		imcenter = (wc/2, hc/2)
		RM = cv2.getRotationMatrix2D(imcenter, 180, 1.0)
		image = cv2.warpAffine(image, RM, (wc,hc))

		frameUpdate(image)
		# clear the stream in preparation for the next frame
		rawCapture.truncate(0)
		# if the `q` key was pressed, break from the loop
		key = cv2.waitKey(1) & 0xFF
		if key == ord("q"):
			stopRun()
			break
		# if an input was given, break from the loop
		elif sys.stdin.readline():
			stopRun()
			break
else:
	cam = cv2.VideoCapture(args["camera"])
	while(True):
		print("test")
		_, image = cam.read()

		bright = cv2.getTrackbarPos('Brightness', 'Control')

		cam.set(cv2.CAP_PROP_BRIGHTNESS, bright / 100.0)
		image = imutils.resize(image, width=xres)

		frameUpdate(image)
		# if the `q` key was pressed, break from the loop
		key = cv2.waitKey(1) & 0xFF
		if key == ord("q"):
			stopRun()
			cam.release()
			break
		# if an input was given, break from the loop
		elif sys.stdin.readline():
			stopRun()
			cam.release()
			break
cv2.destroyAllWindows()
