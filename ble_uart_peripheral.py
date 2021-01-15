# From: https://github.com/micropython/micropython/tree/21c293fbcd1f9d5bafac300b5da265b4efd2be52/examples/bluetooth
# This example demonstrates a peripheral implementing the Nordic UART Service (NUS).

import bluetooth
from ble_advertising import advertising_payload
from micropython import const

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)
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


class BLEUART:
    def __init__(self, ble, name="mpy-uart", rxbuf=100):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(self._irq)
        ((self._tx_handle, self._rx_handle),
         ) = self._ble.gatts_register_services((_UART_SERVICE,))
        # Increase the size of the rx buffer and enable append mode.
        self._ble.gatts_set_buffer(self._rx_handle, rxbuf, True)
        self._connections = set()
        self._rx_buffer = bytearray()
        self._handler = None
        # Optionally add services=[_UART_UUID], but this is likely to make the payload too large.
        self._payload = advertising_payload(
            name=name,
            appearance=_ADV_APPEARANCE_GENERIC_COMPUTER
        )
        self._advertise()

    def irq(self, handler):
        self._handler = handler

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
            if conn_handle in self._connections:
                self._connections.remove(conn_handle)
            # Start advertising again to allow a new connection.
            self._advertise()
        elif event == _IRQ_GATTS_WRITE:
            print("_IRQ_GATTS_WRITE")
            conn_handle, value_handle = data
            if conn_handle in self._connections and value_handle == self._rx_handle:
                self._rx_buffer += self._ble.gatts_read(self._rx_handle)
                if self._handler:
                    self._handler()
        elif event == _IRQ_MTU_EXCHANGED:
            # ATT MTU exchange complete (either initiated by us or the remote device).
            conn_handle, mtu = data
            print("_IRQ_MTU_EXCHANGED")
            print("conn_handle:", conn_handle)
            print("mtu:", mtu)

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

    def _advertise(self, interval_us=500000):
        self._ble.gap_advertise(interval_us, adv_data=self._payload)


def demo():
    from utime import sleep
    from my_time import nowStringExtended

    ble = bluetooth.BLE()
    uart = BLEUART(ble)

    def on_rx():
        print("rx: ", uart.read().decode('UTF-8').strip())

    uart.irq(handler=on_rx)

    try:
        while True:
            uart.write(nowStringExtended() + "\n")
            sleep(1)
    except KeyboardInterrupt:
        pass

    uart.close()


if __name__ == "__main__":
    demo()
