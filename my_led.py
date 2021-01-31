# my_led.py
"""Custom LED methods"""

from machine import Pin
from utime import sleep_ms

led = Pin(33, Pin.OUT)  # GPIO 33 is the ESP32-CAM on board red LED
flash = Pin(4, Pin.OUT)  # GPIO 4 is the ESP32-CAM on board flash LED


# The actual led is on when the value is 0 and off when the value is 1
# These methods swap that behavior

def setLed(setValue):
    """True=on, False=off"""
    actualValue = 0 if setValue == True else 1
    led.value(actualValue)


def getLed():
    actualValue = led.value()
    getValue = "off" if actualValue == 1 else "on"
    return getValue


def setFlash(setValue):
    """True=on, False=off"""
    actualValue = setValue
    flash.value(actualValue)


def getFlash():
    actualValue = flash.value()
    getValue = "off" if actualValue == 0 else "on"
    return getValue


def cycleLed(x):
    for i in range(x):
        sleep_ms(500)
        setLed(True)
        sleep_ms(500)
        setLed(False)


def demo():
    setLed(0)
    setFlash(0)

    print("LED is", getLed())
    print("Flash is", getFlash())


if __name__ == "__main__":
    demo()
