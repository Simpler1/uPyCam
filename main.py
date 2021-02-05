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
import utime
import camera
from ftp import ftpserver
from config import *
import bluetooth
import my_files
from my_time import nowStringExtended, deep_sleep_start
from my_bluetooth import BLE_SERVER
from my_usun import get_sunrise_sunset

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
    utime.sleep_ms(5000)
    machine.reset()
try:
    ble = bluetooth.BLE()
    my_device = BLE_SERVER(ble)
except Exception as e:
    print("BLE Error:", e)

proc_time_ms = 0
this_time = utime.ticks_ms() - app_config['sleep_ms']
tz = -5
doy = 0
error_counter = 0
loop = True
while loop:
    try:
        now_ut = utime.gmtime()
        # Need the local time to know what day it is (which changes with the timezone)
        now_lt = utime.gmtime(utime.mktime(now_ut[0:3] + (now_ut[3]+tz,) + now_ut[4:]))
        if doy != now_lt[7]:
            doy = now_lt[7]
            ss_lt = sunrise_sunset[doy][1]
            sr_lt = sunrise_sunset[doy+1][0]
            print("\nSunset:", ss_lt, " Sunrise:", sr_lt, "\n")
        sr_day = doy + 1 if now_lt[3] > 12 else doy
        sleep_time_s = utime.mktime(
            (2021, 1, sr_day, sr_lt[0], sr_lt[1], 0, 0, 0)) - utime.mktime(now_lt)
        if utime.mktime((2021, 1, doy, ss_lt[0], ss_lt[1], 0, 0, 0)) < utime.mktime(now_lt) or \
           utime.mktime(now_lt) < utime.mktime((2021, 1, doy, sr_lt[0], sr_lt[1], 0, 0, 0)):
            print("Sleeping for", utime.localtime(sleep_time_s)[3:6])
            deep_sleep_start(sleep_time_s)

        # prepare for photo
        if app_config['flash']:
            led.value(1)

        # take photo
        buf = camera.capture()
        led.value(0)

        # save photo
        if app_config['mode'] == 'microSD':
            count = my_files.jpgCount('sd/')
            filename = 'sd/{:05d}.jpg'.format(count + 1)
            f = open(filename, 'w')
            f.write(buf)
            utime.sleep_ms(200)
            f.close()
        elif app_config['mode'] == 'MQTT':
            c.publish(mqtt_config['topic'], buf)

        print("Picture", filename, "taken at:", nowStringExtended())

        # sleep
        last_time = this_time
        this_time = utime.ticks_ms()
        last_proc_time_ms = proc_time_ms
        proc_time_ms = this_time - last_time - app_config['sleep_ms'] + last_proc_time_ms
        utime.sleep_ms(app_config['sleep_ms'] - proc_time_ms)

    except KeyboardInterrupt:
        print("debugging stopped")
        loop = False

    except Exception as e:
        print("Error in main loop:", str(e))
        error_counter = error_counter + 1
        if error_counter > app_config['max-error']:
            machine.reset()
