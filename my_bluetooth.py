import bluetooth
import struct
from ble_advertising import advertising_payload
from micropython import const
from my_time import nowBytes
import utime
import my_files

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)
_IRQ_GATTS_INDICATE_DONE = const(20)
_IRQ_MTU_EXCHANGED = const(21)

# https://specificationrefs.bluetooth.com/assigned-values/Appearance%20Values.pdf
_ADV_APPEARANCE_GENERIC_COMPUTER = const(128)

# https://www.bluetooth.com/specifications/assigned-numbers/
# https://btprodspecificationrefs.blob.core.windows.net/assigned-values/16-bit%20UUID%20Numbers%20Document.pdf
_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_RX = (
    bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"),
    bluetooth.FLAG_WRITE,
)
_UART_TX = (
    bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"),
    bluetooth.FLAG_NOTIFY,
)
_UART_SERVICE = (
    _UART_UUID,
    (_UART_TX, _UART_RX),
)


# org.bluetooth.service.environmental_sensing
_ENV_SENSE_UUID = bluetooth.UUID(0x181A)
# org.bluetooth.characteristic.temperature
_TEMP_CHAR = (
    bluetooth.UUID(0x2A6E),
    # TODO: Why can't I just swap 0x2A6E for 0x2A1C ?
    #       0x2A6E is just a temperature in Celcius
    #       0x2A1C is a variable length structure containing:
    #          Flags
    #          Temperature Measurement Value
    #          Time Stamp (optional based on Flags value)
    #          Temperature Type (optional based on Flags value)
    bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY | bluetooth.FLAG_INDICATE,
)
_ENV_SENSE_SERVICE = (
    _ENV_SENSE_UUID,
    (_TEMP_CHAR,),
)


_PROX_SENSE_UUID = bluetooth.UUID("3E099910-293F-11E4-93BD-AFD0FE6D1DFD")
_PROX_CHAR = (
    bluetooth.UUID("3E099911-293F-11E4-93BDA-FD0FE6D1DFD"),
    bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY | bluetooth.FLAG_WRITE,
    (
      (
        bluetooth.UUID(0x2901),
        bluetooth.FLAG_READ | bluetooth.FLAG_WRITE
      ),
    )
)
_PROX_TIME_CHAR = (
    bluetooth.UUID(0x2A08),
    # 0x2A08  format is YYYYMMDDhhmmss as a hex byte string
    #    b'\xE5\x07\x01\x11\x0F\x05\x00'  is 2021 01 17 15 05 00
    # 0x2A2B  CurrentTime  =>  ExactTime256, Timezone, DST, Method of update  ??
    # https://speakerdeck.com/ephread/bluetooth-low-energy?slide=21
    bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY,
)
_PROX_SERVICE = (
    _PROX_SENSE_UUID,
    (_PROX_CHAR, _PROX_TIME_CHAR),
)


class BLE_SERVER:
    def __init__(self, ble, name='my_server'):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        (
            (self._tx_handle, self._rx_handle),
            (self._temp_handle,),
            (self._prox_handle, self._prox_desc_handle, self._prox_time_handle),
        ) = self._ble.gatts_register_services(
            (
              _UART_SERVICE,
              _ENV_SENSE_SERVICE,
              _PROX_SERVICE,
            )
        )
        self._ble.gatts_write(self._prox_desc_handle, "RSSI (0-127)")
        
        # Increase the size of the rx buffer and enable append mode.
        self._ble.gatts_set_buffer(self._rx_handle, 100, True)
        self._rx_buffer = bytearray()
        self._connections = set()
        self._payload = advertising_payload(
            name=name,
            services=[
                # _UART_UUID,
                _ENV_SENSE_UUID,
                # _PROX_SENSE_UUID,
            ],
            appearance=_ADV_APPEARANCE_GENERIC_COMPUTER
        )
        self._advertise()

    def _irq(self, event, data):
        print("\nevent:", event)
        # Track connections so we can send notifications.
        if event == _IRQ_CENTRAL_CONNECT:
            print("_IRQ_CENTRAL_CONNECT")
            conn_handle, _, _ = data
            self._connections.add(conn_handle)

        elif event == _IRQ_CENTRAL_DISCONNECT:
            print("_IRQ_CENTRAL_DISCONNECT")
            conn_handle, _, _ = data
            self._ble.gap_scan(None)
            if conn_handle in self._connections:
                self._connections.remove(conn_handle)
            # Start advertising again to allow a new connection.
            self._advertise()
        elif event == _IRQ_GATTS_WRITE:
            print("_IRQ_GATTS_WRITE")
            conn_handle, value_handle = data
            if conn_handle in self._connections and value_handle == self._rx_handle:
                self._rx_buffer += self._ble.gatts_read(self._rx_handle)
                rx = self.read().decode('UTF-8').strip()
                print("rx: ", rx)
                if rx == "scan":
                    print("starting scan")
                    self._ble.gap_scan()
                elif rx == "stop":
                    print("stopping scan")
                    self._ble.gap_scan(None)
                elif rx == "files":
                    print("files")



        elif event == _IRQ_MTU_EXCHANGED:
            # ATT MTU exchange complete (either initiated by us or the remote device).
            conn_handle, mtu = data
            print("_IRQ_MTU_EXCHANGED")
            print("conn_handle:", conn_handle)
            print("mtu:", mtu)

        elif event == _IRQ_GATTS_INDICATE_DONE:
            print("_IRQ_GATTS_INDICATE_DONE")
            conn_handle, value_handle, status = data

        elif event == _IRQ_SCAN_RESULT:
            print("_IRQ_SCAN_RESULT")
            addr_type, addr, adv_type, rssi, adv_data = data
            positive_rssi = 127 + rssi
            # now = nowString() # TODO:  WHAT IS THIS FORMAT SUPPOSED TO BE ?????
            # b'\xE5\x07\x01\x11\x0F\x05\x00'  is 2021 01 17 15 05 00
            now = nowBytes()
            print('positive_rssi:', positive_rssi, '   now:', now)
            self._ble.gatts_write(self._prox_handle, struct.pack(
            "<h", positive_rssi))
            self._ble.gatts_write(self._prox_time_handle, now)
            for conn_handle in self._connections:
                self._ble.gatts_notify(conn_handle, self._prox_handle)
                self._ble.gatts_notify(conn_handle, self._prox_time_handle)

        elif event == _IRQ_SCAN_DONE:
            print("_IRQ_SCAN_DONE")
            pass


    def any(self):
        return len(self._rx_buffer)

    def read(self, sz=None):
        if not sz:
            sz = len(self._rx_buffer)
        result = self._rx_buffer[0:sz]
        self._rx_buffer = self._rx_buffer[sz:]
        return result

    def write(self, data):
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._tx_handle, data)

    def close(self):
        for conn_handle in self._connections:
            self._ble.gap_disconnect(conn_handle)
        self._connections.clear()

    def set_temperature(self, temp_deg_c, notify=False, indicate=False):
        # 0x2A6E data is sint16 in degrees Celsius with a resolution of 0.01 degrees Celsius.
        # Write the local value, ready for a central to read.
        self._ble.gatts_write(self._temp_handle, struct.pack(
            "<h", int(temp_deg_c * 100)))
        if notify or indicate:
            for conn_handle in self._connections:
                if notify:
                    self._ble.gatts_notify(conn_handle, self._temp_handle)
                if indicate:
                    self._ble.gatts_indicate(conn_handle, self._temp_handle)

    def _advertise(self, interval_us=500000):
        self._ble.gap_advertise(interval_us, adv_data=self._payload)

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
    from utime import sleep
    from my_time import nowStringExtended
    import random

    t = 25
    i = 0

    try:
        ble = bluetooth.BLE()
        my_device = BLE_SERVER(ble)

        print("\nmac:", my_device.pretty_mac(ble.config('mac')[1]))
        print("gap_name:", ble.config('gap_name').decode('UTF-8'))

    except Exception as e:
        print("BLE Error:", e)

    try:
        # Scan to get the RSSI (Received Signal Strength Indication aka Proximity)
        ble.gap_scan()

        while True:
            # Notify the time
            my_device.write(nowStringExtended() + "\n")

            # Write every second, notify every 10 seconds.
            i = (i + 1) % 10
            my_device.set_temperature(t, notify=i == 0, indicate=False)
            # Random walk the temperature.
            t += random.uniform(-0.5, 0.5)

            sleep(1)
    except KeyboardInterrupt:
        ble.gap_scan(None)
        pass

    my_device.close()


if __name__ == "__main__":
    demo()
