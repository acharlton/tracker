#!/usr/bin/python
# script to log cpu_temp, RAM info, Disk info to a rrd database
from Adafruit_PWM_Servo_Driver import PWM
import os 
import re
import time
import spidev
import RPi.GPIO as GPIO
import rrdtool

DEBUG = 1

RRD_BASE = '/home/pi'
RRD = '%s/rpi_stats.rrd' % RRD_BASE
if DEBUG:
        print RRD_BASE
        print RRD

if not os.path.exists(RRD):
        print "creating rrd...\n"
        ret = rrdtool.create(RRD, "--step", "60", "--start", '0',
        "DS:battery:GAUGE:300:0:200",
        "DS:cpu_temp:GAUGE:300:0:200",
        "DS:ram_used:GAUGE:300:0:512",
        "RRA:AVERAGE:0.5:1:10080")

# Return CPU temperature as a character string
def getCPUtemperature():
    res = os.popen('vcgencmd measure_temp').readline()
    return(str(res.replace("temp=","").replace("'C\n","")))


# Return RAM information (unit=kb) in a list                                                                                                        
def getRAMinfo():
    p = os.popen('free')
    i = 0
    while 1:
        i = i + 1
        line = p.readline()
        if i==2:
            return(line.split()[1:4])

try:

	# GPIO references actual pin numbers (top left is 3.3v pin 2 is 5v)
	GPIO.setmode(GPIO.BOARD)

	# pin 12 is the base of the transistor->relay
	GPIO.setup(12,GPIO.OUT)
	GPIO.output(12,0) # pin, low or high
	GPIO.output(12,1) # pin, low or high
	
	# pin 15 is the base of the transistor->FET
	GPIO.setup(15,GPIO.OUT)
	GPIO.output(15,0)

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
	tolerance = 0.50 # 0.15
	print "Tolerance: " + str(tolerance)
	#saveenergy = 3600
	snooze = 60
	print "Snooze Period: " + str(snooze)

	# need to read last position
	pos = 500
	max = 540
	min = 100


	def init(): 
		# initialize servo
		print "panning servo - max left: " + str(max)
		pwm.setPWM(0,0,min)
		time.sleep(1)
		print "panning servo - max right: " + str(min)
		pwm.setPWM(0,0,max)
		time.sleep(2)
		print "starting...." + str(pos)

	def pause(t):
		print "logging stats..."
		# Battery informatiom
		batt = readadc(3)
        	battv = (batt * 10.47) / 1024
		# CPUinformatiom
        	CPU_temp = getCPUtemperature()
		# RAM informatiom
		RAM_stats = getRAMinfo()
		RAM_used = round(int(RAM_stats[1]) / 1000,1)
		rrddata = str(round(battv,4)) + ":" + str(CPU_temp) + ":" + str(RAM_used)
        	cmdstring = '/usr/bin/rrdtool update ' + RRD + ' N:' + str(rrddata)
        	os.system(cmdstring)
        	if DEBUG: print cmdstring;
		localtime = time.asctime( time.localtime(time.time()) )
		print "Local current time:\t", localtime
        	print "sleeping.." + str(t) + "\n\n"
                GPIO.output(12,0)
                GPIO.output(15,0)
        	time.sleep(t)
        
	def readadc(adcnum):
    		if adcnum > 7 or adcnum < 0:
        		return -1
    		r = spi.xfer2([1, 8 + adcnum << 4, 0])
    		adcout = ((r[1] & 3) << 8) + r[2]
    		return adcout

	#init()
	while move:
        	GPIO.output(12,1) # transistor on to saturate 5v relay for servo power enable
        	GPIO.output(15,1) # transistor on to FET
        	#move = True
        	left = readadc(0)
        	right = readadc(1)
		#batt = readadc(3)
        	#battvolts = (batt * 10.47) / 1024
        	lvolts = (left * 2.8) / 1024
        	rvolts = (right * 3.3) / 1024
        	print ("\n\nCurrent Pos: \t\t" + str(pos) + " \nSensors: \t\t[left] %5.3fv \n\t\t\t[right] %5.3fv" % (lvolts, rvolts))
        	difference = lvolts - rvolts
        	if((-1*tolerance > difference) or (difference > tolerance)):
                	if(left > right):
                        	pos = pos - 5
                        	print "moving < " + str(pos)
                        	pwm.setPWM(0,0,pos)
                        	if(pos < min):
                                	pos = min
                                	pause(snooze)
                	elif(left < right):
                        	pos = pos + 5 
                        	print "moving > " + str(pos)        
                        	pwm.setPWM(0,0,pos)
                        	if(pos > max):
                                	pos = max
                                	pause(snooze)
       	 	else:
                	pause(snooze)

        	time.sleep(0.1)
except KeyboardInterrupt:
	GPIO.cleanup()

