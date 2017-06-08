# Introduction
Measures the output of a solar panel and a small photoresistor, and relays it via http-keystore.

# Motivation
I wanted to know how well a solar panel would do where I live. Also, I wanted to round out my weather data with a measure of how much sunlight we were getting.

# Environment

* Sensors: Solar panel connected to GPIO pins of raspberry pi
* Raspberry Pi: Pi 2 Model B running Raspbian 7.8.

I followed the example of https://learn.adafruit.com/reading-a-analog-in-and-controlling-audio-volume-with-the-raspberry-pi/overview to wire the ADC in.

ADC Pin | GPIO Pin
------- | ---------------
VDD     | +3.3V
VREF    | +3.3V
AGND    | GND
CLK     | #18
DOUT    | #23
DIN     | #24
CS      | #25
DGND    | GND

# How it works
The panel has a 1K resistor on it as a load, and is connected to a MCP3008 ADC, which is in turn connected to the GPIO pins of a raspberry pi. Since the MCP3008 has 8 channels of input and I had a spare photoresistor laying around, I put that in too, with a 10K pull-down resistor.

`solar-sensors.py` scans the sensors every 5 seconds and makes a request to http-keystore, where something else can snag the data.

`solar-sensors.service` goes in /etc/systemd/system:

# Setup

## Sensor unit
As root on a raspberry pi running Raspbian:

```
apt-get update
apt-get install python-dev python-setuptools
easy_install rpi.gpio
pip install requests

cd
git clone https://github.com/jonasacres/solar-sensors
echo http://http.keystore.url/solar-sensors > ~/solar-sensors/sensor-unit/http-keystore-url
cp ~/solar-sensors/sensor-unit/solar-sensors.service /etc/systemd/system
systemctl start solar-sensors
systemctl enable solar-sensors.service
```

## Log unit

```
adduser solar
su - solar

sudo gem install websocket-client-simple sqlite3
cd
git clone https://github.com/jonasacres/solar-sensors
echo http://http.keystore.url/solar-sensors > ~/solar-sensors/log-unit/http-keystore-url
cp ~/solar-sensors/log-unit/solar-log.service /etc/systemd/system
systemctl start solar-log
systemctl enable solar-log.service
```

# http-keystore data

Posted to `/solar-sensors`:

key            | value
-------------- | -----
photo_v        | photoresistor voltage
solar_v        | solar panel voltage
solar_power_mw | solar panel power, milliwatts

