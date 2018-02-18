#!/usr/bin/env python3

#Color Sensor Code
#imports
import time

#import Adafruit Module
import Adafruit_TCS34725 
import colorsys
import pprint
import time

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




h_rounding_error_list = []
l_rounding_error_list = []
s_rounding_error_list = []

h_rounding_error = 0.0
l_rounding_error = 0.0
s_rounding_error = 0.0


def write_color_data(network_table):

    #Disable Interrupts
    
    #Read the RGBC color data
    r, g, b, c = tcs.get_raw_data()
    
    red = r / 20480.0
    green = g / 20480.0
    blue = b / 20480.0

    h, l, s = colorsys.rgb_to_hls(red, green, blue)
    
    #print ("red: {}".format(red))
    #print ("green: {}".format(green))
    #print ("blue: {}".format(blue))
    
    
    if(callibrating):
        callibrate_values(h, l, s)
    
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
    if(len(carpet_s_values) < 5):
        carpet_h_values.append(h)
        carpet_l_values.append(l)
        carpet_s_values.append(s)
        
    elif(len(h_rounding_error_list) < 5):
        carpet_values[0] = sum(carpet_h_values) / len(carpet_h_values)
        carpet_values[1] = sum(carpet_l_values) / len(carpet_l_values)
        carpet_values[2] = sum(carpet_s_values) / len(carpet_s_values)
        temp_h_round = abs(h - carpet_values[0])
        temp_l_round = abs(l - carpet_values[1])
        temp_s_round = abs(s - carpet_values[2])
        h_rounding_error_list.append(temp_h_round)
        l_rounding_error_list.append(temp_l_round)
        s_rounding_error_list.append(temp_s_round)
    else:
        sorted(h_rounding_error_list)
        h_rounding_error = h_rounding_error_list[len(h_rounding_error_list) - 1]
        l_rounding_error = l_rounding_error_list[len(l_rounding_error_list) - 1]
        s_rounding_error = s_rounding_error_list[len(s_rounding_error_list) - 1]
        
         
        print ("H Value: {}      Rounding Error: {}".format(carpet_values[0], h_rounding_error))
        print ("L Value: {}      Rounding Error: {}".format(carpet_values[1], l_rounding_error))
        print ("S Value: {}      Rounding Error: {}".format(carpet_values[2], s_rounding_error))
        callibrating = False

    return


def remove_outlier(list):
    #
    #   implement for more accuracy
    #   in rounding error
    #

    return










while True:
    write_color_data(None)


