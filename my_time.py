# my_time.py
"""Custom time methods"""

# Conclusion:
# Try ntp.settime() at boot time.
# If successful, time is GMT.
#
# When setting through BLE, use machine.RTC().datetime([Y,M,D,h,m,s,0,0])
#
# time and utime classes will not set the time.

import struct

def nowStringExtended():
    """Returns the current GMT system date in extended ISO8601 format: YY-MM-DDThh:mm:ssZ """
    import machine
    rtc = machine.RTC()
    year, month, day, dayofweek, hour, minute, second, us = rtc.datetime()
    timeISO8601 = "{:4}-{:02}-{:02}T{:02}:{:02}:{:02}Z".format(
        year, month, day, hour, minute, second)
    return timeISO8601


def nowString():
    """Returns the current GMT system date in basic ISO8601 format: YYMMDDThhmmssZ"""
    import machine
    rtc = machine.RTC()
    timestamp = rtc.datetime()
    timeISO8601 = '%4d%02d%02dT%02d%02d%02dZ' % (
        timestamp[0], timestamp[1], timestamp[2], timestamp[4], timestamp[5], timestamp[6])
    return timeISO8601


def nowBytes():
    """Returns the current GMT system date in a format that Bluetooth Low Energy UUID 0x2A08 expects"""
    # b'\xE5\x07\x01\x11\x0F\x05\x00'  is 2021 01 17 15 05 00
    import machine
    rtc = machine.RTC()
    timestamp = rtc.datetime()
    time_bytes = struct.pack("<hbbbbb", timestamp[0], timestamp[1], timestamp[2], timestamp[4], timestamp[5], timestamp[6])
    return time_bytes


def set_time_secs(secs):
    """secs: Seconds since 01-Jan-2000 12:00a GMT"""
    # out_time = utime.localtime(secs)                # Doesn't work
    out_time = utime.gmtime(secs)                   # Doesn't work
    print("+++++++++++++++++++++")
    return out_time


def set_time_tuple(input_tuple):
    """input_tuple: [Y, M, D, dow, h, m, s, us]"""
    # out_time = utime.mktime(input_tuple)            # Doesn't work
    # out_time = machine.RTC().init(input_tuple)      # works
    out_time = machine.RTC().datetime(input_tuple)  # works
    print("---------------------")
    return out_time


def set_time_ntp():
    """Set system time using network time protocol"""
    try:
        import ntptime
        print("ntptime.settime(): ", ntptime.settime(), "------------------")
    except Exception as e:
        print("Couldn't set ntp time: " + str(e))


def print_datetime():
    # MicroPython 1.13 docs say that weekday is
    # weekday is 1-7 for Monday through Sunday
    # but actually,
    # weekday is 0-6 for Monday through Sunday
    print("machine.RTC().datetime():", machine.RTC().datetime())
    # last one is microseconds
    print("                              Y  M  D wd  h  m  s  us")


def print_localtime():
    print("utime.localtime():       ", utime.localtime())
    print("                              Y  M  D  h  m  s wd yd")
    # weekday is 0-6 for Mon-Sun
    # yearday is 1-366


def print_gmtime():
    print("utime.gmtime():          ", utime.gmtime())
    print("                              Y  M  D  h  m  s wd yd")
    # weekday is 0-6 for Mon-Sun
    # yearday is 1-366


def print_time():
    print("utime.time():     ", utime.time())
    print("                   Seconds since 2000-Jan-01 12:00am")


def print_ntp_time():
    try:
        import ntptime
        print("ntptime.time():   ", ntptime.time())
        print("                   Seconds since 2000-Jan-01 12:00am")
    except Exception as e:
        print("Couldn't get ntp time: " + str(e))


def print_all():
    print()
    print("nowString():      ", nowString())          # Prints YYMMDDThhmmssZ
    # Prints YY-MM-DDThh:mm:ssZ
    print("nowStringExtended:", nowStringExtended())
    print_ntp_time()  # Prints seconds
    print_datetime()  # Prints tuple
    # print_localtime() # Prints tuple and is exactly the same as gmtime()
    print_gmtime()    # Prints tuple
    print_time()      # Prints seconds


# Sunrise equation:  https://en.wikipedia.org/wiki/Sunrise_equation
# cos(w0) = -tan(theta) x tan(delta)



def demo():
    Y = 2000
    M = 1
    D = 1
    dow = 0  # Day of week: Ignored on input
    h = 11
    m = 12
    s = 13
    us = 123456  # Microseconds: Generally irrelevant

    print_all()

    print("Setting to [", Y, M, D, dow, h, m, s, us, "]")
    set_time_tuple([Y, M, D, dow, h, m, s, us])

    # print("Setting to 0")
    # set_time_secs(0)

    print_all()
    set_time_ntp()
    print_all()


if __name__ == "__main__":
    demo()
