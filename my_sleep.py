import machine
import utime
import ntptime

# ms = 1 * 60 * 60 * 1000

# # Using utime.sleep_ms(ms)
# # ticks() doesn't work when sleeping
# t0 = utime.ticks_us()
# utime.sleep_ms(ms)
# t1 = utime.ticks_us()
# print("utime.sleep_ms(ms)     difference after", ms/1000, "seconds is", t1 - t0 - ms*1000, "microseconds\n")


# # Using machine.lightsleep(ms)
# # ticks() doesn't work when sleeping
# t0 = utime.ticks_us()
# machine.lightsleep(ms)
# t1 = utime.ticks_us()
# print("machine.lightsleep(ms) difference after", ms/1000, "seconds is", t1 - t0 - ms*1000, "microseconds")


# # Using utime.sleep_ms(ms)
# # Not useful for saving energy and inconsistent
# ntptime.settime()
# t0 = utime.mktime(utime.gmtime())
# utime.sleep_ms(ms)
# ntptime.settime()
# t1 = utime.mktime(utime.gmtime())
# print("utime.sleep_ms(ms)     difference after", ms/1000, "seconds is", t1 - t0 - ms/1000, "seconds\n")


# # Using machine.lightsleep(ms)
# # lightsleep loses about 45 seconds every hour (inconsistent)
# boottime_ms = 10000
# sleeptime_ms = ms - boottime_ms
# ntptime.settime()
# t0 = utime.mktime(utime.gmtime())
# machine.lightsleep(sleeptime_ms)
# utime.sleep_ms(boottime_ms)
# ntptime.settime()
# t1 = utime.mktime(utime.gmtime())
# print("machine.lightsleep(ms)     difference after", ms/1000, "seconds is", t1 - t0 - ms/1000, "seconds\n")
