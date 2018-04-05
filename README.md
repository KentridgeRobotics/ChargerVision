# ChargerVision

Vision program written to run on a raspberry pi. The purpose of this program is to mask out a target in a camera feed and return the X and Y Position of the center of the object in the image

## Requirements
* Python 3.6
* OpenCV 3.4.0
* Numpy 1.14.2
* PyNetworkTables 2018.1.0
* Imutils 0.4.6
* Netifaces 0.10.6
* pprint 0.1

## Usage
Run with Python

Default Raspberry Pi: `python3 Vision.py`

Argument | Usage
--- | ---
-c | Camera ID
-i | NetworkTables IP
-a | NetworkTables Table
-g | Output to X
-l | Forcefully Enable LEDs
-e | Disables unnecessary RaspberryPi code for testing vision on other devices
