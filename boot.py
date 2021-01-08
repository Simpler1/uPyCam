# boot.py
import config
import network
import utime
import ntptime
import netLocalTime

# ftp access
#from ftp import ftpserver


def do_connect():
    sta_if = network.WLAN(network.STA_IF)
    start = utime.time()
    timed_out = False

    if not sta_if.isconnected():
        print('connecting to network...')
        print("Before Connecting:", netLocalTime.getTime())
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
            # Eastern Standard Time is 5 hours earlier than GMT
            netLocalTime.setLocalTime(-5)
        except Exception as e:
            print("Local Time Error ocurred: " + str(e))
        print("After Connecting: ", netLocalTime.getTime())
        print('network config:', sta_if.ifconfig())
    else:
        print('internet not available')


do_connect()
