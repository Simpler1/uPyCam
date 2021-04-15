import bluetooth
import struct
import uos
from ble_advertising import advertising_payload
from micropython import const
from my_time import nowStringExtended, nowBytes, set_time_ble
import utime
import my_files
from my_led import setLed

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
# _IRQ_GATTS_READ_REQUEST = const(4)  # Only supported on STM32 (not ESP32-CAM)
_IRQ_SCAN_RESULT = const(5)
_IRQ_SCAN_DONE = const(6)
_IRQ_GATTS_INDICATE_DONE = const(20)
_IRQ_MTU_EXCHANGED = const(21)

_FLAG_DESC_READ = const(1)
_FLAG_DESC_WRITE = const(2)

# https://www.bluetooth.com/specifications/assigned-numbers/
# https://btprodspecificationrefs.blob.core.windows.net/assigned-values/16-bit%20UUID%20Numbers%20Document.pdf
_UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
_UART_RX_CHAR = (
    bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E"),
    bluetooth.FLAG_NOTIFY | bluetooth.FLAG_WRITE,
)
_UART_SERVICE = (
    _UART_UUID,
    (_UART_RX_CHAR,),
)


# org.bluetooth.service.current_time
_CURRENT_TIME_UUID = bluetooth.UUID(0x1805)
_CURRENT_TIME_CHAR = (
    # org.bluetooth.characteristic.current_time
    bluetooth.UUID(0x2A2B),
    bluetooth.FLAG_NOTIFY | bluetooth.FLAG_WRITE,
)
_DATE_TIME_CHAR = (
    # org.bluetooth.characteristic.date_time
    bluetooth.UUID(0x2A08),
    bluetooth.FLAG_NOTIFY | bluetooth.FLAG_WRITE,
)
_CURRENT_TIME_SERVICE = (
    _CURRENT_TIME_UUID,
    (_CURRENT_TIME_CHAR, _DATE_TIME_CHAR,),
)


_FILES_UUID = bluetooth.UUID("7a890001-e96d-4842-8b3d-69ce27889cd6")
_FILE_COUNT_DESC = (
    (
      # org.bluetooth.descriptor.gatt.characteristic_user_description
      bluetooth.UUID(0x2901),
      _FLAG_DESC_READ | _FLAG_DESC_WRITE,
    ),
)
_FILE_COUNT_CHAR = (
    bluetooth.UUID("7a890102-e96d-4842-8b3d-69ce27889cd6"),
    bluetooth.FLAG_NOTIFY | bluetooth.FLAG_WRITE,
    _FILE_COUNT_DESC,
)
_FILES_SERVICE = (
    _FILES_UUID,
    (_FILE_COUNT_CHAR,),
)


class BLE_SERVER:
    def __init__(self, ble, name='C_00'):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        (
            (self._rx_handle,),
            (self._current_time_handle, self._date_time_handle,),
            (self._file_count_handle, self._file_desc_handle,),
        ) = self._ble.gatts_register_services(
            (
              _UART_SERVICE,
              _CURRENT_TIME_SERVICE,
              _FILES_SERVICE,
            )
        )
        
        # Increase the size of the rx buffer and enable append mode.
        self._ble.gatts_set_buffer(self._rx_handle, 100, True)
        self._rx_buffer = bytearray()
        self._connections = set()
        self._payload = advertising_payload(
            name=name,
            services=[
                _UART_UUID,
                # _CURRENT_TIME_UUID,
                # _FILES_UUID,
            ],
        )

        self._ble.gatts_write(self._file_desc_handle, "Number of Files")

        self._advertise()

    def _irq(self, event, data):
        print("\nevent:", event)
        # Track connections so we can send notifications.
        if event == _IRQ_CENTRAL_CONNECT:
            print("_IRQ_CENTRAL_CONNECT")
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
            setLed(1)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            print("_IRQ_CENTRAL_DISCONNECT")
            conn_handle, _, _ = data
            self._ble.gap_scan(None)
            if conn_handle in self._connections:
                self._connections.remove(conn_handle)
            setLed(0)
            # Start advertising again to allow a new connection.
            self._advertise()
        elif event == _IRQ_GATTS_WRITE:
            print("_IRQ_GATTS_WRITE")
            conn_handle, value_handle = data
            if conn_handle in self._connections:
                if value_handle == self._rx_handle:
                    # Since _IRQ_GATTS_READ_REQUEST doesn't work for ESP32-CAM these write operations will actually notify the value.
                    print("  UART write")
                    self._rx_buffer = self._ble.gatts_read(self._rx_handle)
                    rx = self.read(self._rx_buffer).decode('UTF-8').strip()
                    print("rx: ", rx)
                    if rx == "time":
                        now = nowBytes()
                        print("Time as bytes is", now)
                        print("Time is", nowStringExtended())
                        self._ble.gatts_write(self._date_time_handle, now)
                        self._ble.gatts_notify(conn_handle, self._date_time_handle)
                    elif rx == "files":
                        packed = self.getFileCount()
                        self._ble.gatts_write(self._file_count_handle, packed)
                        self._ble.gatts_notify(conn_handle, self._file_count_handle)
                elif value_handle == self._date_time_handle:
                    # Date/time coming in from ble must be "<hbbbbb" (uint16 uint8 uint8 uint8 uint8 uint8)
                    print("Write time")
                    time_in = self._ble.gatts_read(self._date_time_handle)
                    self.set_time(time_in)
                elif value_handle == self._file_count_handle:
                    # Convert from int to a byte literal in order to write to a ble value
                    print("Write file count")
                    packed = self.getFileCount()
                    self._ble.gatts_write(self._file_count_handle, packed)
                    self._ble.gatts_notify(conn_handle, self._file_count_handle)



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

        elif event == _IRQ_SCAN_DONE:
            print("_IRQ_SCAN_DONE")
            pass

    def getFileCount(self):
        count = len(uos.listdir('sd'))-1
        print("File count is", count)
        packed = struct.pack("<h", count)
        return packed

    def any(self):
        return len(self._rx_buffer)

    def read(self, buffer, sz=None):
        if not sz:
            sz = len(buffer)
        result = buffer[0:sz]
        buffer = buffer[sz:]
        return result

    def write(self, data):
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._rx_handle, data)

    def close(self):
        for conn_handle in self._connections:
            self._ble.gap_disconnect(conn_handle)
        self._connections.clear()

    def set_time(self, date_time, notify=True):
        """date_time is input as a bytes string"""
        # 0x2A08 date_time is stored as a bytes string uint16 uint8 uint8 uint8 uint8 uint8
        if not date_time or date_time == b'\x00':  # Just read the time
            now = nowBytes()
            print("Getting date_time:", struct.unpack("<hbbbbb", now))
            self._ble.gatts_write(self._date_time_handle, now)
        else:
            print("Setting date_time:",date_time)
            set_time_ble(date_time)
            self._ble.gatts_write(self._date_time_handle, date_time)
        print("Time is set to", nowStringExtended())
        if notify:
            for conn_handle in self._connections:
                if notify:
                    self._ble.gatts_notify(conn_handle, self._date_time_handle)

    def _advertise(self, interval_us=500000):
        print("Advertising...")
        self._ble.gap_advertise(interval_us, adv_data=self._payload)

    def is_connected(self):
        return True if len(self._connections) > 0 else False        

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
    import random

    try:
        ble = bluetooth.BLE()
        my_device = BLE_SERVER(ble)

        print("\nmac:", my_device.pretty_mac(ble.config('mac')[1]))
        print("gap_name:", ble.config('gap_name').decode('UTF-8'))

    except Exception as e:
        print("BLE Error:", e)
        raise

    try:
        my_device.set_time((2020, 1, 2, 3, 4, 5), notify=True)
    except KeyboardInterrupt:
        pass

    my_device.close()


if __name__ == "__main__":
    demo()
