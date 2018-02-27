#!/usr/bin/env python3

#Color Sensor Code
#imports
import time

#import Adafruit Module
import Adafruit_TCS34725 
import colorsys
import pprint
import time
import sys
import numpy


#Instance of Adafruit
tcs = Adafruit_TCS34725.TCS34725(integration_time=Adafruit_TCS34725.TCS34725_INTEGRATIONTIME_50MS)
tcs.set_interrupt(False)



#Convert RGB to HLS

pprinter = pprint.PrettyPrinter()

callibrating = True


carpet_values = [0, 0, 0]
carpet_h_values = []
carpet_l_values = []
carpet_s_values = []


h_deviation = 0.0
l_deviation = 0.0
s_deviation = 0.0

recent_samples = []
h_sample_counter = 0
l_sample_counter = 0
s_sample_counter = 0


def get_sample():
    # Read the RGBC color data
    r, g, b, c = tcs.get_raw_data()
    
    red = r / 20480.0
    green = g / 20480.0
    blue = b / 20480.0

    h, l, s = colorsys.rgb_to_hls(red, green, blue)

    return {
        h,
        l,
        s
    }

def write_sample(sample):
    pprinter.pprint(sample)
 

def detect_change_in_values():
    global previous_value
    value = get_sample()
    h,l,s = value
    if (previous_value is not None):
        h_prev, s_prev, l_prev = previous_value
        # Compare h, compare l, and compare s
        # If you see a difference, print something
        if(abs(h - h_prev) > 100):
            print("Hue Change")

       #if(abs(s - s_prev) > s_deviation):
            print("saturation Change")

       #if(abs(l - l_prev) > l_deviation):
            print("Luminosity Change")
        
        
    previous_value = value


def detect_change(v1, v2):
    sample = [h,l,s]
    #if(
    

def write_color_data(network_table):

    #Disable Interrupts
    
    #Read the RGBC color data
    r, g, b, c = tcs.get_raw_data()
    
    red = r
    green = g
    blue = b

    h, l, s = colorsys.rgb_to_hls(red, green, blue)
    
    #print ("red: {}".format(red))
    #print ("green: {}".format(green))
    #print ("blue: {}".format(blue))
    
    
    if(callibrating):
        callibrate_values(h, l, s)
    
    #Determine Change
    if(callibrating != True) and (h_deviation != 0.0):
        check_values(h, s, l, network_table)



    pprinter.pprint([h, l, s])
    if (network_table is not None):
        network_table.putNumber("Hue", h)
        network_table.putNumber("Saturation", s)
        network_table.putNumber("Lightness", l)
    
    #Calculate luminosity
    #lux = Adafruit_TCS34725.calculate_lux(r , g, b)
    
    #Write luminosity to network table
    #network_table.putNumber("Luminosity", lux)

    return 
    
    
def callibrate_values(h, l, s):
    print ("callibrating")
    if(len(carpet_s_values) < 5):
        carpet_h_values.append(h)
        carpet_l_values.append(l)
        carpet_s_values.append(s)
        
    else:
        
        carpet_values[0] = sum(carpet_h_values) / len(carpet_h_values)
        carpet_values[1] = sum(carpet_l_values) / len(carpet_l_values)
        carpet_values[2] = sum(carpet_s_values) / len(carpet_s_values)
                 
        global h_deviation
        global l_deviation
        global s_deviation
        h_deviation = numpy.std(carpet_h_values)
        l_deviation = numpy.std(carpet_l_values)
        s_deviation = numpy.std(carpet_s_values) 



 
        print ("H Value: {}      Deviation: {}".format(carpet_values[0], h_deviation))
        print ("L Value: {}      Deviation: {}".format(carpet_values[1], l_deviation))
        print ("S Value: {}      Deviation: {}".format(carpet_values[2], s_deviation))
        global callibrating
        callibrating = False

    return


def remove_outlier(list):
    #
    #   implement for more accuracy
    #   in rounding error
    #

    return


def check_values(h, s, l, network_table):
    global recent_samples
    if(len(recent_samples) > 5):
        recent_samples.append([h, s, l])
        recent_samples.pop(0)
    else:
        recent_samples.append([h, s, l])

    global h_sample_counter
    global l_sample_counter
    global s_sample_counter
    if(abs(h - carpet_values[0]) > h_deviation * 20): 
        print ("Hue Change")
        if(h_sample_counter > 0):
            put_boolean_to_table(network_table, "Hue Change", True)
        else:
            h_sample_counter += 1
    else:  
        put_boolean_to_table(network_table, "Hue Change", False)
    if(abs(l - carpet_values[1]) > l_deviation * 20):
        print ("Lightness Change")
        if(l_sample_counter > 0):
            put_boolean_to_table(network_table, "Lightness Change", True)
        else:
            l_sample_counter += 1
    else:
        put_boolean_to_table(network_table, "Lightness Change", False)
    if(abs(s - carpet_values[2]) > s_deviation * 20):
        print ("Saturation Change")
        if(s_sample_counter > 0):
            put_boolean_to_table(network_table, "Saturation Change", True)
        else:
            s_sample_counter += 1
    else:
            put_boolean_to_table(network_table, "Saturation Change", False)

    return

def put_boolean_to_table(network_table, title, boolean):
    if(network_table != None):
        network_table.putBoolean(title, boolean)
    return



def run_color_sensor():
   write_color_data(None)
