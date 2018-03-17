
import cv2
import numpy  



# Pipeline to find Targets

class ObjectDetector:
    lower_hue
    upper_hue
    
    #Instantiate ObjectDector for Specific color

    def __init__(self, lower_hue, upper_hue):
        self.lower_hue = lower_hue
        upper_hue = upper_hue


    #Filter Color
      def filter_colors(img):
        hsv = cv2.cvtColor(img, cvt.Color_BGR2HSV)

        mask = cv2.inRange(hsv, lower_hue, upper_hue)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        return; 
    
    

    #Find Contours

    def find_contours(img):
        
        
        return;
    




    #Find Specific Rectangles


    #Find Two Rectangles of Similar Shapes

    #Get Positions

    #Calculate Relative Distance


