#!/usr/bin/env python3
from time import time
from serial import Serial 

serialDevice = "/dev/ttyS0"


def measure(portName):
    ser = Serial(portName, 9600, 8, 'N', 1, timeout=1)
    timeStart = time()
    valueCount = 0

    while time() < timeStart + 3:
        if ser.inWaiting():
            bytesToRead = ser.inWaiting()
            valueCount += 1
            if valueCount < 2: 
                continue
            testData = ser.read(bytesToRead)
            if not testData.startswith(b'R'):
                continue
            try:
                sensorData = testData.decode('utf-8').lstrip('R')
            except UnicodeDecodeError:
                continue
            try:
                mm = int(sensorData)
            except ValueError:
                continue
            ser.close
            return(mm)
    ser.close()
    raise RuntimeError("Expected serial data not received")

if __name__ == '__main__':
    measure = measure(serialDevice)
    print("distance =". measurement)
