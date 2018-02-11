#Color Sensor Code
#imports
import time

#import Adafruit Module
import Adafruit_TCS34725 

#Instance of Adafruit
tcs = Adafruit_TCS34725.TCS34725(integration_time = Adafruit_TCS34725.TCS34725_INTEGRATIONTIME_50MS)

#Convert RGB to HLS
import colorsys

def write_color_data(network_table):

    #Disable Interups
    tcs.set_interrupt(false)

    #Read the RGBC color data
    r, g, b, c = tcs.get_raw_data()

    h, l, s = colorsys.rgb_to_hls(r, g, b)

    network_table.putNumber("Hue", h)
    network_table.putNumber("Saturation", s)
    newtork_table.putNumber("Lightness", l)
    
    #Calculate luminosity
    lux = Adafruit_TCS34725.calculate_lux(r , g, b)
    
    #Write luminosity to network table
    network_table.putNumber("Luminosity", lux)
    return 




