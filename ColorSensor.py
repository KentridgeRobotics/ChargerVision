#Color Sensor Code
#imports
import time

#import Adafruit Module
import Adafruit_TCS34725 

#Instance of Adafruit
import smbus
tcs = Adafruit_TCS34725.TCS34725()


def write_color_data(network_table):

    #Disable Interups
    tcs.set_interrupt(false)

    #Read the RGBC color data
    r, g, b, c = tcs.get_raw_data()

    network_table.putNumber("red", r)
    network_table.putNumber("green",g)
    newtork_table.putNumber("blue",b)
    
    #Calculate luminosity
    lux = Adafruit_TCS34725.calculate_lux(r,g,b)
    
    #Write luminosity to network table
    network_table.putNumber("lum",lux)
    return 




