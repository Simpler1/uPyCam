import bluetooth
import struct
import uos
from ble_advertising import advertising_payload
from micropython import const
from my_time import *
from my_led import setLed
import network
import gc
import json

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
_CURRENT_TIME_SERVICE = (
    _CURRENT_TIME_UUID,
    (_CURRENT_TIME_CHAR,),
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
_FILE_LOG_DESC = (
    (
        # org.bluetooth.descriptor.gatt.characteristic_user_description
        bluetooth.UUID(0x2901),
        _FLAG_DESC_READ | _FLAG_DESC_WRITE,
    ),
)
_FILE_LOG_CHAR = (
    bluetooth.UUID("7a890103-e96d-4842-8b3d-69ce27889cd6"),
    bluetooth.FLAG_NOTIFY | bluetooth.FLAG_WRITE,
    _FILE_LOG_DESC,
)
_FILES_SERVICE = (
    _FILES_UUID,
    (_FILE_COUNT_CHAR, _FILE_LOG_CHAR,),
)


_WIFI_UUID = bluetooth.UUID("8e0e0001-0a70-4b3c-b314-dd5b9cd7bdc7")
_WIFI_DESC = (
    (
        # org.bluetooth.descriptor.gatt.characteristic_user_description
        bluetooth.UUID(0x2901),
        _FLAG_DESC_READ | _FLAG_DESC_WRITE,
    ),
)
_WIFI_CHAR = (
    bluetooth.UUID("8e0e0002-0a70-4b3c-b314-dd5b9cd7bdc7"),
    bluetooth.FLAG_NOTIFY | bluetooth.FLAG_WRITE,
    _WIFI_DESC,
)
_WIFI_SERVICE = (
    _WIFI_UUID,
    (_WIFI_CHAR,),
)


_SLEEP_UUID = bluetooth.UUID("908b0001-cf3d-4405-8759-a28c4ae64c53")
_SLEEP_START_DESC = (
    (
        # org.bluetooth.descriptor.gatt.characteristic_user_description
        bluetooth.UUID(0x2901),
        _FLAG_DESC_READ | _FLAG_DESC_WRITE,
    ),
)
_SLEEP_STOP_DESC = (
    (
        # org.bluetooth.descriptor.gatt.characteristic_user_description
        bluetooth.UUID(0x2901),
        _FLAG_DESC_READ | _FLAG_DESC_WRITE,
    ),
)
_SLEEP_START_CHAR = (
    bluetooth.UUID("908b0002-cf3d-4405-8759-a28c4ae64c53"),
    bluetooth.FLAG_NOTIFY | bluetooth.FLAG_WRITE,
    _SLEEP_START_DESC,
)
_SLEEP_STOP_CHAR = (
    bluetooth.UUID("908b0003-cf3d-4405-8759-a28c4ae64c53"),
    bluetooth.FLAG_NOTIFY | bluetooth.FLAG_WRITE,
    _SLEEP_STOP_DESC,
)
_SLEEP_SERVICE = (
    _SLEEP_UUID,
    (_SLEEP_START_CHAR, _SLEEP_STOP_CHAR,),
)


class BLE_SERVER:
    def __init__(self, ble):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        (
            (self._rx_handle,),
            (self._current_time_handle,),
            (self._file_count_handle, self._file_count_desc_handle,
             self._file_log_handle, self._file_log_desc_handle,),
            (self._wifi_handle, self._wifi_desc_handle,),
            (self._sleep_start_handle, self._sleep_start_desc_handle,
             self._sleep_stop_handle, self._sleep_stop_desc_handle,),
        ) = self._ble.gatts_register_services(
            (
                _UART_SERVICE,
                _CURRENT_TIME_SERVICE,
                _FILES_SERVICE,
                _WIFI_SERVICE,
                _SLEEP_SERVICE,
            )
        )

        _mac = self.pretty_mac(self._ble.config('mac')[1])
        name = self.getName(_mac)

        # Increase the size of the rx buffer and enable append mode.
        self._ble.gatts_set_buffer(self._rx_handle, 100, True)
        self._rx_buffer = bytearray()
        self._connections = set()
        self._payload = advertising_payload(
            name=name,
            services=[
                # _UART_UUID,
                # _CURRENT_TIME_UUID,
                # _FILES_UUID,
                _WIFI_UUID,
            ],
        )

        self._ble.gatts_write(self._file_count_desc_handle, "Number of Files")
        self._ble.gatts_write(self._file_log_desc_handle, "Log File")
        self._ble.gatts_write(self._wifi_desc_handle, "WiFi State")
        self._ble.gatts_write(self._sleep_start_desc_handle, "Sleep Start")
        self._ble.gatts_write(self._sleep_stop_desc_handle, "Sleep Stop")

        self._advertise()

    def _irq(self, event, data):
        # log("event:", event)
        # Track connections so we can send notifications.
        if event == _IRQ_CENTRAL_CONNECT:
            log("_IRQ_CENTRAL_CONNECT")
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
            setLed(1)
            self.checkingConnection()
        elif event == _IRQ_CENTRAL_DISCONNECT:
            log("_IRQ_CENTRAL_DISCONNECT")
            conn_handle, _, _ = data
            self._ble.gap_scan(None)
            if conn_handle in self._connections:
                self._connections.remove(conn_handle)
            setLed(0)
            # Start advertising again to allow a new connection.
            self._advertise()
        elif event == _IRQ_GATTS_WRITE:
            # log("_IRQ_GATTS_WRITE")
            conn_handle, value_handle = data
            if conn_handle in self._connections:
                if value_handle == self._rx_handle:
                    # Since _IRQ_GATTS_READ_REQUEST doesn't work for ESP32-CAM these write operations will actually notify the value.
                    log("  UART write")
                    self._rx_buffer = self._ble.gatts_read(self._rx_handle)
                    rx = self.read(self._rx_buffer).decode('UTF-8').strip()
                    log("rx: ", rx)
                    if rx == "time":
                        now = bytesCurrentTime()
                        log("Time as bytes is", now)
                        log("Time is", nowStringExtended())
                        self._ble.gatts_write(self._current_time_handle, now)
                        self._ble.gatts_notify(
                            conn_handle, self._current_time_handle)
                    elif rx == "files":
                        packed = self.getFileCount()
                        self._ble.gatts_write(self._file_count_handle, packed)
                        self._ble.gatts_notify(
                            conn_handle, self._file_count_handle)
                elif value_handle == self._current_time_handle:
                    # Date/time coming in from ble must be "<hbbbbb" (uint16 uint8 uint8 uint8 uint8 uint8)
                    # log("Write time")
                    time_in = self._ble.gatts_read(self._current_time_handle)
                    self.set_time(time_in)
                elif value_handle == self._file_count_handle:
                    # Convert from int to a byte literal in order to write to a ble value
                    log("  Get file count")
                    packed = self.getFileCount()
                    self._ble.gatts_write(self._file_count_handle, packed)
                    self._ble.gatts_notify(
                        conn_handle, self._file_count_handle)
                elif value_handle == self._file_log_handle:
                    # print("Write file log")
                    packed = self.getFileLog()
                    for chunk in packed:
                        try:
                            # print(chunk)
                            # self._ble.gatts_write(self._file_log_handle, chunk)
                            self._ble.gatts_notify(
                                conn_handle, self._file_log_handle, chunk)
                            gc.collect()  # Memory error occurs if this is not called
                        except Exception as e:
                            print("Error writing log file:", e)
                elif value_handle == self._wifi_handle:
                    # Convert from int to a byte literal in order to write to a ble value
                    log("  Get WiFi state")
                    wifi_in = self._ble.gatts_read(self._wifi_handle)
                    wifi_int = struct.unpack('b', wifi_in)[0]
                    sta_if = network.WLAN(network.STA_IF)
                    if wifi_int == 1 or wifi_int == 0:
                        if wifi_int == 1:
                            wifi_bool = True
                        elif wifi_int == 0:
                            wifi_bool = False

                        log("WiFi set to", wifi_bool)
                        sta_if.active(wifi_bool)
                        self._ble.gatts_write(self._wifi_handle, wifi_in)
                    else:
                        wifi_bool = sta_if.active()
                        log("WiFi is", wifi_bool)
                        wifi_out = struct.pack('<h', wifi_bool)
                        self._ble.gatts_write(self._wifi_handle, wifi_out)
                    self._ble.gatts_notify(conn_handle, self._wifi_handle)
                elif value_handle == self._sleep_start_handle:
                    log("  Get Sleep Start & Stop Times")
                    (sleep_start_time, sleep_stop_time, _) = getGmtSleepStartStopTimes(
                        (0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0), 0)
                    # log("Sleep start_time:", sleep_start_time)
                    # log("Sleep stop time: ", sleep_stop_time)
                    sleep_start_bytes = bytesTime(sleep_start_time)
                    sleep_stop_bytes = bytesTime(sleep_stop_time)
                    self._ble.gatts_write(
                        self._sleep_start_handle, sleep_start_bytes)
                    self._ble.gatts_write(
                        self._sleep_stop_handle, sleep_stop_bytes)
                    for conn_handle in self._connections:
                        self._ble.gatts_notify(
                            conn_handle, self._sleep_start_handle)
                        self._ble.gatts_notify(
                            conn_handle, self._sleep_stop_handle)

        elif event == _IRQ_MTU_EXCHANGED:
            # ATT MTU exchange complete (either initiated by us or the remote device).
            conn_handle, mtu = data
            log("_IRQ_MTU_EXCHANGED")
            log("conn_handle:", conn_handle)
            log("mtu:", mtu)

        elif event == _IRQ_GATTS_INDICATE_DONE:
            log("_IRQ_GATTS_INDICATE_DONE")
            conn_handle, value_handle, status = data

        elif event == _IRQ_SCAN_RESULT:
            log("_IRQ_SCAN_RESULT")

        elif event == _IRQ_SCAN_DONE:
            log("_IRQ_SCAN_DONE")
            pass

    def checkingConnection(self):
        # while (self.is_connected()):
        #   log("Checking connection...")
        #   time.sleep(60)
        return

    def getName(self, mac):
        # Use the my_macs json file to determine the camera name
        _macs = self.getMacs()
        if mac in _macs:
            return _macs[mac]
        else:
            return 'C_00'

    def getFileCount(self):
        count = len(uos.listdir('sd'))-1
        log("File count is", count)
        packed = struct.pack("<h", count)
        return packed

    def getFileLog(self):
        with open('sd/log.txt', 'r') as f:
            logFile = f.read()
        log("File log character length is", len(logFile))
        packed = logFile.encode('utf8')
        # Break into a list of 20 byte chunks
        splitLogFile = [packed[i:i+20] for i in range(0, len(packed), 20)]
        return splitLogFile

    def getMacs(self):
        with open('my_macs.json', 'r') as macsJson:
            data = macsJson.read()
        return json.loads(data)

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
        """date_time is input as a bytes string (for BLE UUID 0x2A08) uint16 uint8 uint8 uint8 uint8 uint8"""
        if not date_time or date_time == b'\x00':  # Just read the time
            now = bytesCurrentTime()
            log("  Get date_time:", struct.unpack("<hbbbbbbbb", now))
            self._ble.gatts_write(self._current_time_handle, now)
        else:
            _was = time.time()
            log("  Set date_time:", struct.unpack("<hbbbbb", date_time))
            set_time_ble(date_time)
            _is = time.time()
            log(" Difference of", _was - _is, "seconds")
            self._ble.gatts_write(self._current_time_handle,
                                  date_time + b'\x00\x00\x03')
        # log("Time is ", nowStringExtended())
        if notify:
            for conn_handle in self._connections:
                if notify:
                    self._ble.gatts_notify(
                        conn_handle, self._current_time_handle)

    def _advertise(self, interval_us=500000):
        log("Advertising...")
        self._ble.gap_advertise(interval_us, adv_data=self._payload)

    def is_connected(self):
        return True if len(self._connections) > 0 else False

    def pretty_mac(self, hex_mac):             # hex_mac = b'<a\x05\x15\x9d\xfe'
        s = []
        for i in hex_mac:                      # i = list(hex_mac)[0]   =>  60
            # value = hex(i)  =>  '0x3c'  =>  '3c'
            value = hex(i)[2:4]
            # padded => '3c'   ('5'  => ' 5')
            padded = "{:>2}".format(value)
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

        log("\nmac:", my_device.pretty_mac(ble.config('mac')[1]))
        log("gap_name:", ble.config('gap_name').decode('UTF-8'))

    except Exception as e:
        log("BLE Error:", e)
        raise

    try:
        my_device.set_time((b'\xE5\x07\x01\x11\x0F\x05\x00'), notify=True)
    except KeyboardInterrupt:
        pass

    my_device.close()


if __name__ == "__main__":
    demo()
