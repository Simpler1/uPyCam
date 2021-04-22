Timelapse
=========


TODO:
-----
Power switch (to swap SD Card)
Build / 3D Print a case
BLE
  Mobile app to connect
    Check voltage ??
    Download photos ??
  Voltage Service
    Battery voltage
Voltage Meter
Solar Panel
Motion Sensor
Light Sensor
  Wake/Sleep based on light sensor value
Temperature Sensor


Flow
----
Boot
  Attempt to update time using ntp
    If successful
      update time
      Cycle red LED 3 times, 
    else
      Cycle red LED 1 time.
  Enable BLE (Bluetooth Low Energy)
    If connected
      LED on
      Send (notify?)
        Old date/time
        Number of photos
        Battery voltage
      Receive (write?)
        Updated date/time from mobile
    If disconnected
      LED off


Main
  Start loop
    If sun is up
      Check battery voltage and use as suffix for filename (i.e. "_3.3v.jpg")
      Check number of photos, increment, and use as prefix for filename (i.e. "00001")
      Take photo
        Save photo as 00001_3.3v.jpg
      Sleep for 1 minute
    else
      Sleep until sunrise


Bluetooth Low Energy
====================
Attribute Table
---------------
ESP32-CAM
  GAP Role:  Peripheral
  GATT:  Server
    Service:  "Current Time Service"  (Profile Specification: CTS)
      Characteristic:  Date Time
        Descriptor:  
          Name:
          Requirement:  **Mandatory**
          Type:
          UUID:
          Read:  **Mandatory**
          Write:  **Mandatory**
          Disclaimer:  
          Summary:  
        Operations (Properties?):
          Read:  **Mandatory**
          Write:  **Mandatory**
          Write without response:  Excluded
          Signed write:  Excluded
          Notify:  **Mandatory**
          Indicate:  Excluded
          Writeable Auxiliaries:  Excluded
          Broadcast:  Excluded
          Extended Properties:  Excluded
          Reliable Write:  Excluded
        Value:
          Name:
          Repeated:  Yes
          Requirement:  **Mandatory**
          Description:  
          Minimum:  
          Maximum:  
          Unit:
          Multiplier:
          Decimal Exponent:
          Binary Exponent:
          Format:  uint8  (Unsigned 8 bits)
          Characteristic Reference: 

    Service:  "File Service" (Custom)
      Characteristic:  Number of image files
        Descriptor:  
    Service:  
      Characteristic:  Battery voltage
        Descriptor:  
    Service:  
      Characteristic:  Light sensor
        Descriptor:  
    Service:  
      Characteristic:  Enable Flash
        Descriptor:  
    Service:  
      Characteristic:  Reset button
        Descriptor:  

Cell phone with Flutter app (or maybe just "nRF Connect")
  GAP Role:  Central
  GATT:  Client


Glossary
========
UART:   Universal Asynchonous Receiver-Transmitter
GATT:   Generic Attribute Profile
GAP:    Generic Access Profile
MTU:    Maximum Transmission Unit
ATT:    Attribute Protocol
RSSI:   Received Signal Strength Indicator
PXP:    Proximity Profile
L2CAP:  Logical Link Control Adaptation Protocol
