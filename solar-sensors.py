#!/usr/bin/env python
 
# Adapted from:
# https://learn.adafruit.com/reading-a-analog-in-and-controlling-audio-volume-with-the-raspberry-pi

# sudo apt-get install python-setuptools
# sudo easy_install rpi.gpio

import time
import os
import RPi.GPIO as GPIO
import requests
 
GPIO.setmode(GPIO.BCM)
 
# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
    if ((adcnum > 7) or (adcnum < 0)):
        return -1

    GPIO.output(cspin, True)

    GPIO.output(clockpin, False)  # start clock low
    GPIO.output(cspin, False)     # bring CS low

    commandout = adcnum
    commandout |= 0x18  # start bit + single-ended bit
    commandout <<= 3    # we only need to send 5 bits here
    for i in range(5):
        if (commandout & 0x80):
            GPIO.output(mosipin, True)
        else:
            GPIO.output(mosipin, False)
        commandout <<= 1
        GPIO.output(clockpin, True)
        GPIO.output(clockpin, False)

    adcout = 0
    # read in one empty bit, one null bit and 10 ADC bits
    for i in range(12):
        GPIO.output(clockpin, True)
        GPIO.output(clockpin, False)
        adcout <<= 1
        if (GPIO.input(misopin)):
            adcout |= 0x1

    GPIO.output(cspin, True)
    
    adcout >>= 1       # first bit is 'null' so drop it
    return adcout
 
# change these as desired - they're the pins connected from the
# SPI port on the ADC to the Cobbler
SPICLK = 18
SPIMISO = 23
SPIMOSI = 24
SPICS = 25

PHOTORESISTOR_CHANNEL = 0
SOLAR_PANEL_CHANNEL = 1
 
# set up the SPI interface pins
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)
 
while True:
    scale = 3.3 / 1023
    photo_v = round(scale * readadc(PHOTORESISTOR_CHANNEL, SPICLK, SPIMOSI, SPIMISO, SPICS), 3)
    solar_v = round(scale * readadc(SOLAR_PANEL_CHANNEL, SPICLK, SPIMOSI, SPIMISO, SPICS), 3)

    solar_resistor_ohms = 1000 # TODO: measure
    solar_power_mw = round(solar_v**2/solar_resistor_ohms, 3)

    http_keystore_url = "http://10.0.1.125:11000/solar-sensors"
    post_data = {"photo_v":photo_v, "solar_v":solar_v, "solar_power_mw":solar_power_mw}
    requests.post(http_keystore_url, data=post_data)

    print "photoresistor: ", photo_v, 3, "V"
    print "  solar power: ", solar_power_mw, 3, "mW"
    print "solar voltage: ", solar_v, 3, "V"

    time.sleep(5)
