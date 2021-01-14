# From https://github.com/micropython/micropython/pull/5171#issuecomment-542878425

import bluetooth

ble = bluetooth.BLE()
ble.active(True)
print("mac:", ble.config('mac')[1])
print("gap_name:", ble.config('gap_name').decode('UTF-8'))

def ble_irq(event, data):
    print("")
    print("event:", event)
    if event == 1:
        # A central has connected to this peripheral.
        conn_handle, addr_type, addr = data
        print("_IRQ_CENTRAL_CONNECT")
        print("conn_handle:", conn_handle)
        print("addr_type:", addr_type)
        print("addr:", addr)
    elif event == 2:
        # A central has disconnected from this peripheral.
        conn_handle, addr_type, addr = data
        print("_IRQ_CENTRAL_DISCONNECT")
        print("conn_handle:", conn_handle)
        print("addr_type:", addr_type)
        print("addr:", addr)
    elif event == 3:
        # A client has written to this characteristic or descriptor.
        conn_handle, attr_handle = data
        print("_IRQ_GATTS_WRITE")
        print("conn_handle:", conn_handle)
        print("attr_handle:", attr_handle)
        print("ble.gatts_read(rx):", ble.gatts_read(rx).decode('UTF-8'))
    elif event == 21:
        # ATT MTU exchange complete (either initiated by us or the remote device).
        conn_handle, mtu = data    # print received data
        print("_IRQ_MTU_EXCHANGED")
        print("conn_handle:", conn_handle)
        print("mtu:", mtu)


def write(data):
    data = bytes(data, 'utf-8')  # Convert the input string to bytes
    print("type(data):", type(data))
    ble.gatts_notify(0, tx, data)


ble.irq(ble_irq)

# GATT Server  (Generic Attribute Profile)
UART_UUID = bluetooth.UUID('6E400001-B5A3-F393-E0A9-E50E24DCCA9E')
UART_RX = (bluetooth.UUID('6E400002-B5A3-F393-E0A9-E50E24DCCA9E'), bluetooth.FLAG_WRITE,)
UART_TX = (bluetooth.UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E'), bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY,)
UART_SERVICE = (UART_UUID, (UART_TX, UART_RX,),)
SERVICES = (UART_SERVICE,)
((tx, rx,), ) = ble.gatts_register_services(SERVICES)

# Advertiser
def adv_encode_name(name):
    name = bytes(name, 'ascii')
    return bytearray((len(name) + 1, 0x09)) + name


ble.gap_advertise(100, bytearray('\x02\x01\x02') + adv_encode_name('ESP32'))
