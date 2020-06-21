# Copyright 2020 LeMaRiva|tech lemariva.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import machine 
import sdcard
import ntptime
import time
import camera
from ftp import ftpserver
from config import *


try:
    # camera init
    led = machine.Pin(4, machine.Pin.OUT)
    camera.init(0, format=camera.JPEG)  # ESP32-CAM

    #camera.init(0, d0=32, d1=35, d2=34, d3=5, d4=39, d5=18, d6=36, d7=19, 
    #            href=26, vsync=25, reset=15, sioc=23, siod=22, xclk=27, pclk=21)   #M5CAMERA
                
    # sd mount
    spi = machine.SPI(2, baudrate=100000, 
                    phase=0, polarity=0, 
                    sck=machine.Pin(device_config['sck']), 
                    mosi=machine.Pin(device_config['mosi']), 
                    miso=machine.Pin(device_config['miso'])) 

    sd = sdcard.SDCard(spi, machine.Pin(device_config['ss']))
    os.mount(sd, '/sd')
    os.listdir('/')
    
    # ntp sync for date
    ntptime.settime()
    rtc = machine.RTC()

    if app_config['ftp']:
        # ftp for checking
        u = ftpserver()
        u.start_thread()

except Exception as e:
    print("Error ocurred: " + str(e))
    time.sleep_ms(5000)
    machine.reset()

error_counter = 0
loop = True
while loop:
    try:
        # prepare for photo
        led.value(1)
        led.value(0)
        time.sleep_ms(100)

        # take photo
        buf = camera.capture()
        time.sleep_ms(100)
        # save photo
        timestamp = rtc.datetime()
        time_str = '%4d%02d%02d%02d%02d%02d' %(timestamp[0], timestamp[1], timestamp[2], timestamp[4], timestamp[5], timestamp[6])
        f = open('sd/'+time_str+'.jpg', 'w')
        f.write(buf)
        time.sleep_ms(100)
        f.close()

        # sleep
        time.sleep_ms(app_config['sleep-ms'])
    
    except KeyboardInterrupt:
        print("debugging stopped")
        loop = False

    except Exception as e:
        print("Error ocurred: " + str(e))
        error_counter = error_counter + 1
        if error_counter > app_config['max-error']:
            machine.reset()