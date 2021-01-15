# boot.py
import config
import network
import utime
import ntptime
from my_time import nowStringExtended
from my_led import cycleLed


def do_connect():
    sta_if = network.WLAN(network.STA_IF)
    start = utime.time()
    timed_out = False

    if not sta_if.isconnected():
        print('\nConnecting to network...')
        print("Before Connecting:", nowStringExtended())
        sta_if.active(True)
        sta_if.connect(config.wifi_config["ssid"],
                       config.wifi_config["password"])
        while not sta_if.isconnected() and \
                not timed_out:
            if utime.time() - start >= 20:
                timed_out = True
            else:
                pass

    if sta_if.isconnected():
        try:
            ntptime.settime()
            cycleLed(3)
        except Exception as e:
            print("NTP Time Error ocurred: " + str(e))
            cycleLed(1)
        print("After Connecting: ", nowStringExtended())
        print('Network config:', sta_if.ifconfig())
    else:
        print('Internet not available')


do_connect()
