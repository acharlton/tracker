#!/usr/bin/python
# script to log cpu_temp, RAM info, Disk info to a rrd database
try:
	from Adafruit_PWM_Servo_Driver import PWM
	import os 
	import re
	import time
	import spidev
	import RPi.GPIO as GPIO

	# GPIO references actual pin numbers (top left is 3.3v pin 2 is 5v)
	GPIO.setmode(GPIO.BOARD)

	# pin 12 is the base of the transistor->relay
	GPIO.setup(12,GPIO.OUT)
	GPIO.output(12,0) # pin, low or high
	GPIO.output(12,1) # pin, low or high
	
	# pin 15 is the base of the transistor->FET
	GPIO.setup(15,GPIO.OUT)
	GPIO.output(15,0)
	GPIO.output(15,1) # FET on for batt monitor

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
	print "Tolerance: " + str(tolerance)
	#saveenergy = 3600
	snooze = 10
	print "Snooze Period: " + str(snooze)

	# need to read last position
	pos = 500
	max = 540
	min = 100

	# initialize servo
	print "panning servo - max left: " + str(max)
	#pwm.setPWM(0,0,min)
	#time.sleep(1)
	print "panning servo - max right: " + str(min)
	#pwm.setPWM(0,0,max)
	#time.sleep(2)
	print "starting...." + str(pos)

	def pause(t):
		localtime = time.asctime( time.localtime(time.time()) )
		print "Local current time:\t", localtime
        	print "sleeping.." + str(t) + "\n\n"
        	time.sleep(t)
        
	def readadc(adcnum):
    		if adcnum > 7 or adcnum < 0:
        		return -1
    		r = spi.xfer2([1, 8 + adcnum << 4, 0])
    		adcout = ((r[1] & 3) << 8) + r[2]
    		return adcout

	while move:
        	GPIO.output(12,1) # transistor on to saturate 5v relay for servo power enable
        	move = True
        	left = readadc(0)
        	right = readadc(1)
		batt = readadc(3)
        	battvolts = (batt * 10.47) / 1024
        	lvolts = (left * 3.3) / 1024
        	rvolts = (right * 3.3) / 1024
        	print ("\n\nBattery: \t\t%5.3fv \nSensors: \t\t[left] %5.3fv \n\t\t\t[right] %5.3fv" % (battvolts, lvolts, rvolts))
        	difference = lvolts - rvolts
        	if((-1*tolerance > difference) or (difference > tolerance)):
                	if(left > right):
                        	pos = pos - 20
                        	print "moving < " + str(pos)
                        	pwm.setPWM(0,0,pos)
                        	if(pos < min):
                                	pos = min
                                	pause(snooze)
                	elif(left < right):
                        	pos = pos + 20 
                        	print "moving > " + str(pos)        
                        	pwm.setPWM(0,0,pos)
                        	if(pos > max):
                                	pos = max
                                	pause(snooze)
       	 	else:
                	GPIO.output(12,0)
                	pause(snooze)

        	time.sleep(0.1)
except KeyboardInterrupt:
	GPIO.cleanup()

