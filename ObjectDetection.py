
import cv2
import numpy  



# Pipeline to find Targets

class ObjectDetector:
    lower_hue
    upper_hue
    
    #Instantiate ObjectDector for Specific color

    def __init__(self, lower_hue, upper_hue):
        self.lower_hue = lower_hue
        self.upper_hue = upper_hue


    #Filter Color
    def filter_colors(img):
        hsv = cv2.cvtColor(img, cvt.COLOR_BGR2HSV)

        mask = cv2.inRange(hsv, lower_hue, upper_hue)
        mask = cv2.cvtColor(mask, cvt.COLOR_HSV2BGR)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        return mask; 
    
    

    #Find Contours

    def find_contours(img):
        img = cv2.cvtColor(img, cvt.COLOR_BGR2GRAY)
        ret, thresh = cv2.threshold(img, 127, 255, 0)
        contours, hierarchy = cv2.findContours(thresh, 1, 2)

        for x in range(0, len(contours)):
            contours.
        return;
    




    #Find Specific Rectangles


    #Find Two Rectangles of Similar Shapes

    #Get Positions

    #Calculate Relative Distance


