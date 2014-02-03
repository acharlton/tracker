#!/usr/bin/python
# script to log cpu_temp, RAM info, Disk info to a rrd database
from Adafruit_PWM_Servo_Driver import PWM
import os 
import re
import time
import spidev
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)

# pin 8 is the base of the transistor
GPIO.setup(8,GPIO.OUT)
GPIO.output(8,0)

# pin 16 is the first LDR sensor
GPIO.setup(16,GPIO.OUT)
GPIO.output(16,0)
GPIO.output(16,1)

# pin 18 is the second LDR sensor
GPIO.setup(18,GPIO.OUT)
GPIO.output(18,0)
GPIO.output(18,1)

pwm = PWM(0x40, debug=True)
pwm.setPWMFreq(60)   

spi = spidev.SpiDev()
spi.open(0, 0)
move = True
difference = 0
tolerance = 0.15

# need to read last position
pos = 500
max = 500
min = 100

# initialize servo
print "initializing - max left: " + str(max)
GPIO.output(8,1)
#time.sleep(1)
pwm.setPWM(0,0,min)
time.sleep(1)
print "initializing - max right: " + str(min)
pwm.setPWM(0,0,max)
time.sleep(2)
print "starting...." + str(pos)

def pause(t):
	localtime = time.asctime( time.localtime(time.time()) )
	print "Local current time :", localtime
        print "sleeping.." + str(t)
        time.sleep(t)
        
def readadc(adcnum):
    if adcnum > 7 or adcnum < 0:
        return -1
    r = spi.xfer2([1, 8 + adcnum << 4, 0])
    adcout = ((r[1] & 3) << 8) + r[2]
    return adcout

while move:
        GPIO.output(8,1)
        move = True
        right = readadc(1)
        left = readadc(0)
	batt = readadc(2)
        battvolts = (batt * 9.98) / 1024
        lvolts = (left * 3.3) / 1024
        rvolts = (right * 3.3) / 1024
        print ("batt: %4d/1023 => %5.3fV [L%4d/1023 => %5.3fV] [R%4d/1023 => %5.3fV]" % (batt, battvolts, left, lvolts, right, rvolts))
        difference = lvolts - rvolts
        if((-1*tolerance > difference) or (difference > tolerance)):
                if(left > right):
                        pos = pos - 20
                        print "< " + str(pos)
                        pwm.setPWM(0,0,pos)
                        if(pos < min):
                                pos = min
                                pause(3600)
                elif(left < right):
                        pos = pos + 20 
                        print "> " + str(pos)        
                        pwm.setPWM(0,0,pos)
                        if(pos > max):
                                pos = max
                                pause(3600)
        else:
                print "|..centered..|"
        	print ("batt: %4d/1023 => %5.3f" % (batt, battvolts))
                GPIO.output(8,0)
                pause(3600)

        time.sleep(0.1)
GPIO.cleanup()

