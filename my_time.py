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
import machine
import config
import ntptime

def nowStringExtended():
    """Returns the current GMT system date in extended ISO8601 format: YYYY-MM-DDThh:mm:ssZ """
    import machine
    rtc = machine.RTC()
    year, month, day, dayofweek, hour, minute, second, us = rtc.datetime()
    timeISO8601 = "{:4}-{:02}-{:02}T{:02}:{:02}:{:02}Z".format(
        year, month, day, hour, minute, second)
    return timeISO8601


def nowString():
    """Returns the current GMT system date in basic ISO8601 format: YYYYMMDDThhmmssZ"""
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
    """input_tuple: [Y, M, D, h, m, s]"""
    import machine
    import utime
    time_in = list(input_tuple)
    time_in.insert(3, 0)
    time_in.append(0)
    time_in = tuple(time_in)
    print("time_in:", time_in)
    # out_time = utime.mktime(input_tuple)            # Doesn't work
    # out_time = machine.RTC().init(input_tuple)      # works
    out_time = machine.RTC().datetime(time_in)  # works
    # print("utime.gmtime is now:          ", utime.gmtime())
    # print("machine.RTC().datetime is now:", machine.RTC().datetime())
    print("---------------------")
    return out_time


def set_time_ble(byte_string):
    """byte_string: b'\xe1\x07\x03\x04\x05\x06\x07'"""
    import machine
    import utime
    time_in = struct.unpack("<hbbbbb", byte_string)
    time_in = list(time_in)
    time_in.insert(3, 0)
    time_in.append(0)
    time_in = tuple(time_in)
    # print("time_in:", time_in)
    # out_time = utime.mktime(input_tuple)            # Doesn't work
    # out_time = machine.RTC().init(input_tuple)      # works
    out_time = machine.RTC().datetime(time_in)  # works
    # print("utime.gmtime is now:          ", utime.gmtime(), "Y M D h m s wd yd")
    # print("machine.RTC().datetime is now:", machine.RTC().datetime(), "Y M D wd h m s us")
    print("********************")
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


def deep_sleep_start(seconds):
    clock_correction_24hr_s = 0
    try:
        ntptime.settime()
    except Exception as e:
        print("NTP Time Error ocurred on sleep: " + str(e))
    t0 = str(machine.RTC().datetime())
    line = t0 + "\t" + str(seconds)
    # "with open()" handles the close() automatically
    with open('sleep.txt', 'w') as f:
        f.write(line)
    print("machine.deepsleep(ms): starting to deep sleep for", seconds, "seconds at", nowStringExtended(), "\n")
    machine.deepsleep((seconds + clock_correction_24hr_s) * 1000)


def deep_sleep_end():
    with open('sleep.txt', 'r') as f:
        line = f.read()
    parts = line.split("\t")
    time = eval(parts[0])
    seconds = int(parts[1])
    print("Time was   ", nowStringExtended())
    machine.RTC().datetime((time[0:6] + (time[6] + seconds + config.app_config["deepSleepBootTime_s"],) + (0,)))
    print("Time is now", nowStringExtended())



def demo():
    Y = 2000
    M = 1
    D = 1
    # dow = 0  # Day of week: Ignored on input
    h = 11
    m = 12
    s = 13
    # us = 123456  # Microseconds: Generally irrelevant

    print_all()

    print("Setting to [", Y, M, D, h, m, s, "]")
    set_time_tuple([Y, M, D, h, m, s])

    # print("Setting to 0")
    # set_time_secs(0)

    print_all()
    set_time_ntp()
    print_all()


def demo1():
  deep_sleep_start(3600)


if __name__ == "__main__":
    demo1()
