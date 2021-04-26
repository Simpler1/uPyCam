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

import uos
import machine
import time
import camera
from ftp import ftpserver
from config import *
import bluetooth
import my_files
from my_time import nowString, nowStringExtended, deep_sleep_start, getGmtSleepStartStopTimes
from my_bluetooth import BLE_SERVER

if app_config['mode'] == 'MQTT':
    from umqtt.simple2 import MQTTClient

try:
    # camera init
    led = machine.Pin(app_config['led'], machine.Pin.OUT)

    if app_config['camera'] == 'ESP32-CAM':
        camera.init(0, format=camera.JPEG)  # ESP32-CAM
    elif app_config['camera'] == 'M5CAMERA':
        camera.init(0, d0=32, d1=35, d2=34, d3=5, d4=39, d5=18, d6=36, d7=19,
                    href=26, vsync=25, reset=15, sioc=23, siod=22, xclk=27, pclk=21)  # M5CAMERA

    if app_config['mode'] == 'microSD':
        # sd mount
        sd = machine.SDCard(slot=3, width=1,
                            sck=machine.Pin(microsd_config['sck']),
                            mosi=machine.Pin(microsd_config['mosi']),
                            miso=machine.Pin(microsd_config['miso']),
                            cs=machine.Pin(microsd_config['ss']))
        uos.mount(sd, '/sd')
        # uos.listdir('/')
    elif app_config['mode'] == 'MQTT':
        c = MQTTClient(mqtt_config['client_id'], mqtt_config['server'])
        c.connect()

    rtc = machine.RTC()

    if app_config['ftp']:
        # ftp for checking
        u = ftpserver()
        u.start_thread()

except Exception as e:
    print("Startup Error:", str(e))
    time.sleep_ms(5000)
    machine.reset()
try:
    ble = bluetooth.BLE()
    my_device = BLE_SERVER(ble)
except Exception as e:
    print("BLE Error:", e)

proc_time_ms = 0
this_time = time.ticks_ms() - app_config['sleep_ms']
error_counter = 0
loop = True
while loop:
    try:
        getGmtSleepStartStopTimes()

        # prepare for photo
        if app_config['flash']:
            led.value(1)

        # take photo
        buf = camera.capture()
        led.value(0)

        # save photo
        if app_config['mode'] == 'microSD':
            count = my_files.jpgCount('sd/')
            filename = 'sd/{:05d}-%s.jpg'.format(count + 1) % (nowString())
            f = open(filename, 'w')
            f.write(buf)
            time.sleep_ms(200)
            f.close()
        elif app_config['mode'] == 'MQTT':
            c.publish(mqtt_config['topic'], buf)

        print("Picture", filename, "taken at:", nowStringExtended())

        # sleep
        last_time = this_time
        this_time = time.ticks_ms()
        last_proc_time_ms = proc_time_ms
        proc_time_ms = this_time - last_time - app_config['sleep_ms'] + last_proc_time_ms
        time.sleep_ms(app_config['sleep_ms'] - proc_time_ms)

    except KeyboardInterrupt:
        print("debugging stopped")
        loop = False

    except Exception as e:
        print("Error in main loop:", str(e))
        error_counter = error_counter + 1
        if error_counter > app_config['max-error']:
            machine.reset()
