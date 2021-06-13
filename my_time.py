# my_time.py
"""Custom time methods"""

# Conclusion:
# Try ntp.settime() at boot time.
# If successful, time is GMT.
#
# When setting through BLE, use machine.RTC().datetime([Y,M,D,h,m,s,0,0])
#
# time and time classes will not set the time.

import struct
import machine
import config
import ntptime
import time
import my_led
from config import *


def log(*args):
    t = nowStringExtended()
    list_of_strings = [str(v) for v in args]
    text = " ".join(list_of_strings)
    print(text)
    try:
        with open('sd/log.txt', 'a') as f:
            f.write("\n" + t + ":  " + text)
    except Exception as e:
        if (str(e) == '[Errno 2] ENOENT'):
            print('Log file not available: [Errno 2] ENOENT')
        else:
            print("Error writing to log file:", str(e))


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


def nowBytesDateTime():
    """Returns the current GMT system date in a format that Bluetooth Low Energy UUID 0x2A08 (Date Time) expects"""
    # b'\xE5\x07\x01\x11\x0F\x05\x00'  is 2021 01 17 15 05 00
    import machine
    rtc = machine.RTC()
    timestamp = rtc.datetime()
    time_bytes = struct.pack(
        "<hbbbbb", timestamp[0], timestamp[1], timestamp[2], timestamp[4], timestamp[5], timestamp[6])
    return time_bytes


def bytesCurrentTime():
    """
    Returns the current GMT system date in a format that Bluetooth Low Energy UUID 0x2A2B (Current Time) expects

    Exact Time 256 + Adjust Reason(uint8)
    Exact Time 256 = Day Date Time + Fractions256(uint8)

    Day Date Time = Date Time + Day of Week
    Date Time = Year(uint16) + Month(uint8) + Day(uint8) + Hours(uint8) + Minutes(uint8) + Seconds(uint8)
    Day of Week = Day of Week(uint8) [0=unknown, 1=Monday, etc.]

    Octet Meaning  (left to right)
    ----- -------
    0     Year
    1     Year
    2     Month
    3     Day
    4     Hours
    5     Minutes
    6     Seconds
    7     Day of Week (0 = unknown)
    8     Fractions256 (0 = uknown)
    9     Adjust Reason (0x03 = Manual Update => External Reference => No Time Zone Change => No DST Change)
    """
    return nowBytesDateTime() + b'\x00\x00\x03'


def bytesTime(timeTuple):
    time_bytes = struct.pack(
        "<hbbbbb", timeTuple[0], timeTuple[1], timeTuple[2], timeTuple[3], timeTuple[4], timeTuple[5])
    return time_bytes

# sr = Sunrise
# ss = Sunset
# ut = univeral time
# slt = standard local time (no DST)


def getGmtSleepStartStopTimes(off_at_utime, on_at_utime, doy):
    tz = -5  # Timezone ignores Daylight Saving Time
    # doy = 0  # Day of Year
    now_ut = time.gmtime()
    if now_ut[0] > 2000:   # don't deep sleep if the date has not been set
        # Need the local time to know what day it is (which changes with the timezone)
        now_slt = time.gmtime(time.mktime(
            now_ut[0:3] + (now_ut[3]+tz,) + now_ut[4:]))
        if doy != now_slt[7]:
            doy = now_slt[7]
            ss_slt = sunrise_sunset[doy][1]
            sr_slt = sunrise_sunset[doy+1][0]
            off_at_hm = [ss_slt[0], ss_slt[1] + 25]  # 25 minutes after sunset
            on_at_hm = [sr_slt[0], sr_slt[1] - 25]  # 25 minutes before sunrise
            # off_at_time = (2021, 1, doy, off_at_hm[0], off_at_hm[1], 0, 0, 0)
            # on_at_time =  (2021, 1, doy+1, on_at_hm[0], on_at_hm[1], 0, 0, 0)
            off_at_utime = time.gmtime(time.mktime(
                (2021, 1, doy, off_at_hm[0]-tz, off_at_hm[1], 0, 0, 0)))
            on_at_utime = time.gmtime(time.mktime(
                (2021, 1, doy+1, on_at_hm[0]-tz, on_at_hm[1], 0, 0, 0)))
            log("Sunset:", ss_slt, " Sunrise:", sr_slt, " EST",
                "\n  Off at:", off_at_utime, "\n  On at: ", on_at_utime, " GMT")
        off_at_utime_sec = time.mktime(off_at_utime)
        on_at_utime_sec = time.mktime(on_at_utime)
        if off_at_utime_sec < time.mktime(now_ut) and time.mktime(now_ut) < on_at_utime_sec:
            sr_day = doy + 1 if now_slt[3] > 12 else doy
            # sleep_time_s = time.mktime((2021, 1, sr_day, on_at_hm[0], on_at_hm[1], 0, 0, 0)) - time.mktime(now_slt)
            sleep_time_s = time.mktime(on_at_utime) - time.mktime(now_ut)
            deep_sleep_start(sleep_time_s)
        return (off_at_utime, on_at_utime, doy)
    return ((0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0), doy)


def set_time_secs(secs):
    """secs: Seconds since 01-Jan-2000 12:00a GMT"""
    # out_time = time.localtime(secs)                # Doesn't work
    out_time = time.gmtime(secs)                   # Doesn't work
    log("+++++++++++++++++++++")
    return out_time


def set_time_tuple(input_tuple):
    """input_tuple: [Y, M, D, h, m, s]"""
    import machine
    import time
    time_in = list(input_tuple)
    time_in.insert(3, 0)
    time_in.append(0)
    time_in = tuple(time_in)
    log("time_in:", time_in)
    # out_time = time.mktime(input_tuple)            # Doesn't work
    # out_time = machine.RTC().init(input_tuple)      # works
    out_time = machine.RTC().datetime(time_in)  # works
    # log("time.gmtime is now:          ", time.gmtime())
    # log("machine.RTC().datetime is now:", machine.RTC().datetime())
    log("---------------------")
    return out_time


def set_time_ble(byte_string):
    """byte_string: b'\xe1\x07\x03\x04\x05\x06\x07' is 2017-03-04 05:06:07"""
    import machine
    import time
    time_in = struct.unpack("<hbbbbb", byte_string)
    time_in = list(time_in)
    time_in.insert(3, 0)
    time_in.append(0)
    time_in = tuple(time_in)
    # log("time_in:", time_in)
    # out_time = time.mktime(input_tuple)            # Doesn't work
    # out_time = machine.RTC().init(input_tuple)      # works
    out_time = machine.RTC().datetime(time_in)  # works
    # log("time.gmtime is now:          ", time.gmtime(), "Y M D h m s wd yd")
    # log("machine.RTC().datetime is now:", machine.RTC().datetime(), "Y M D wd h m s us")
    log("********************")
    return out_time


def set_time_ntp(error_count=0):
    """Set system time using network time protocol"""
    import time
    import ntptime
    try:
        ntptime.settime()
        log("ntptime.settime(): ", nowStringExtended(), "\n++++++++++++++++++++")
    except Exception as e:
        if error_count < 5:
            log(error_count, "seconds")
            error_count += 1
            time.sleep(1)
            set_time_ntp(error_count)
        else:
            log("Couldn't set ntp time after", str(
                error_count), "seconds\n", str(e))


def print_datetime():
    # MicroPython 1.13 docs say that weekday is
    # weekday is 1-7 for Monday through Sunday
    # but actually,
    # weekday is 0-6 for Monday through Sunday
    log("machine.RTC().datetime():", machine.RTC().datetime())
    # last one is microseconds
    log("                              Y  M  D wd  h  m  s  us")


def print_localtime():
    log("time.localtime():        ", time.localtime())
    log("                              Y  M  D  h  m  s wd yd")
    # weekday is 0-6 for Mon-Sun
    # yearday is 1-366


def print_gmtime():
    log("time.gmtime():           ", time.gmtime())
    log("                              Y  M  D  h  m  s wd yd")
    # weekday is 0-6 for Mon-Sun
    # yearday is 1-366


def print_time():
    log("time.time():      ", time.time())
    log("                   Seconds since 2000-Jan-01 12:00am")


def print_ntp_time():
    try:
        import ntptime
        log("ntptime.time():   ", ntptime.time())
        log("                   Seconds since 2000-Jan-01 12:00am")
    except Exception as e:
        log("Couldn't get ntp time: " + str(e))


def print_all():
    log()
    log("nowString():        ", nowString())          # Prints YYMMDDThhmmssZ
    # Prints YY-MM-DDThh:mm:ssZ
    log("nowStringExtended():", nowStringExtended())
    log("nowBytesDateTime():         ", nowBytesDateTime())
    print_ntp_time()  # Prints seconds
    print_datetime()  # Prints tuple
    # print_localtime() # Prints tuple and is exactly the same as gmtime()
    print_gmtime()    # Prints tuple
    print_time()      # Prints seconds


# Sunrise equation:  https://en.wikipedia.org/wiki/Sunrise_equation
# cos(w0) = -tan(theta) x tan(delta)


def deep_sleep_start(seconds):
    import time
    log("Sleeping for " + str(time.gmtime(seconds)[3:6]))
    try:
        set_time_ntp()
    except Exception as e:
        log("NTP Time Error ocurred on sleep: " + str(e))
    t0 = machine.RTC().datetime()
    line = str(t0) + "\t" + str(seconds)
    # "with open()" handles the close() automatically
    with open('sleep.txt', 'w') as f:
        f.write(line)
    log("machine.deepsleep(ms): starting to deep sleep for " + str(seconds) +
        " seconds until " + str(time.gmtime(time.time()+seconds)))
    my_led.setLed(False)
    my_led.setFlash(False)
    machine.deepsleep((seconds) * 1000)
    # deep_sleep_end()  # TODO: This is temporary while testing lightsleep


def deep_sleep_end():
    with open('sleep.txt', 'r') as f:
        line = f.read()
    parts = line.split("\t")
    _time = eval(parts[0])
    seconds = int(parts[1])
    _was = time.time()
    log("At wake            " + nowStringExtended())
    machine.RTC().datetime(
        (_time[0:6] + (_time[6] + seconds + config.app_config["deepSleepBootTime_s"] + config.app_config["deepSleepOvernightCorrection_s"],) + (0,)))
    _is = time.time()
    log("Manually set to    " + nowStringExtended())
    log(" Adjustment of", _is - _was, "seconds")
    # set_time_ntp() # TODO: Temporary while testing lightsleep


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

    log("Setting to [", Y, M, D, h, m, s, "]")
    set_time_tuple([Y, M, D, h, m, s])
    print_all()

    # log("Setting to 0")
    # set_time_secs(0)

    log("Setting to xE5 x07 x01 x11 x0F x05 x00")
    set_time_ble(b'\xE5\x07\x01\x11\x0F\x05\x00')
    print_all()

    log("Setting to ntp")
    set_time_ntp()
    print_all()

    deep_sleep_start(10)


def demo1():
    deep_sleep_start(5*60*60)


if __name__ == "__main__":
    demo()
