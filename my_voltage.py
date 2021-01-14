# my_voltage.py
"""Custom voltage methods"""

from machine import Pin
from machine import ADC


def readVoltage():
    voltagePin = Pin(13, Pin.IN)

    value = voltagePin.value()
    print("value: ", value)

    adcv = ADC(Pin(voltagePin))
    print("ADC Voltage: ", adcv)


def demo():
    readVoltage()


if __name__ == "__main__":
    demo()
