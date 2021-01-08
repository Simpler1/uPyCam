# From https://github.com/micropython/micropython/pull/5171#issuecomment-542878425

# MTU = Maximum Transmission Unit
# UART = Universal Asynchonous Receiver-Transmitter
# L2CAP = Logical Link Control Adaptation Protocol

# Import of modules and classes
import bluetooth

# Configuration
ble = bluetooth.BLE()
ble.active(True)
print(ble.config('mac'))
print(ble.config('gap_name'))

# Event Handling
def ble_irq(event, data):
    # print received data
    print(ble.gatts_read(rx))


ble.irq(ble_irq)

# GATT Server  (Generic Attribute Profile)
UART_UUID = bluetooth.UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')
UART_RX =  (bluetooth.UUID('6E400002-B5A3-F393-E0A9-E50E24DCCA9E'),
            bluetooth.FLAG_WRITE,)
UART_TX =  (bluetooth.UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E'),
            bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY,)
UART_SERVICE = (UART_UUID, (UART_TX, UART_RX,),)
SERVICES = (UART_SERVICE,)
((tx, rx,), ) = ble.gatts_register_services(SERVICES)

# Advertiser
def adv_encode_name(name):
    name = bytes(name, 'ascii')
    return bytearray((len(name) + 1, 0x09)) + name


ble.gap_advertise(100, bytearray('\x02\x01\x02') + adv_encode_name('ESP32'))
