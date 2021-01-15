# From https://github.com/micropython/micropython/pull/5171#issuecomment-542878425

import bluetooth
from ble_uart_peripheral import BLEUART
from ble_temperature import BLETemperature


class ble_device:
    def __init__(self):
        ble = bluetooth.BLE()
        uart = BLEUART(ble, name="my_universal")
        # temp = BLETemperature(ble, name="my_temp")

        def on_rx():
            print("rx: ", uart.read().decode('UTF-8').strip())

        uart.irq(handler=on_rx)

        print("\nmac:", self.pretty_mac(ble.config('mac')[1]))
        print("gap_name:", ble.config('gap_name').decode('UTF-8'))

    def pretty_mac(self, hex_mac):             # hex_mac = b'<a\x05\x15\x9d\xfe'
        s = []
        for i in hex_mac:                      # i = list(hex_mac)[0]   =>  60
            value = hex(i)[2:4]                # value = hex(i)  =>  '0x3c'  =>  '3c'
            padded = "{:>2}".format(value)     # padded => '3c'   ('5'  => ' 5')
            upper = padded.upper()             # upper => '3C'
            s.append(upper.replace(' ', '0'))  # ['3C', '61', '05', ...]
        s = ':'.join(s)                        # '3C:61:05...
        return s


def demo():
    try:
        my_device = ble_device()
    except Exception as e:
        print("BLE Error:", e)


if __name__ == "__main__":
    demo()
