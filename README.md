# ChargerVision

Computer vision program in Python with OpenCV to identify FIRST Robotics 2019 vision targets

## Requirements
* Python 3.6
* OpenCV 3.4.0
* Numpy 1.14.2
* PyNetworkTables 2018.1.0
* Imutils 0.5.2
* Netifaces 0.10.6
* Pprint 0.1

## Usage
Run with Python

Default Raspberry Pi: `python3 Vision.py`

Argument | Usage
--- | ---
-c | Camera ID
-i | NetworkTables IP
-a | NetworkTables Table
-g | Output to X
-e | Disables unnecessary RaspberryPi code for testing vision on other devices
-f | Outputs the FPS to the console
--image | Specifies test image for experimentation without a camera