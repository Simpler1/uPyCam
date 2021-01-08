# Conclusion:
# Try ntp.settime() at boot time.  
# If successful, time is local and daylight saving time is accounted for.
# 
# When setting through BLE, use machine.RTC().datetime([Y,M,D,h,m,s,0,0])
#
# time and utime classes will not set the time.



def set_time_secs(secs):  # Seconds since 01-Jan-2000 12:00am
    # out_time = utime.localtime(secs)                # Doesn't work
    out_time = utime.gmtime(secs)                   # Doesn't work
    print("+++++++++++++++++++++")
    return out_time


def set_time_tuple(input_tuple):  # [Y, M, D, dow, h, m, s, us]
    # out_time = utime.mktime(input_tuple)            # Doesn't work
    # out_time = machine.RTC().init(input_tuple)      # works
    out_time = machine.RTC().datetime(input_tuple)  # works
    print("---------------------")
    return out_time


def set_time_ntp():
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
    print("                              Y  M  D wd  h  m  s  us") # last one is microseconds


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
    print_ntp_time()  # Prints seconds
    print_datetime()  # Prints tuple
    print_localtime() # Prints tuple
    # print_gmtime()    # Prints tuple and is exactly the same as localtime()
    print_time()      # Prints seconds


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
