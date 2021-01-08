# ###################################################################### #
# Set RTC localTime from UTC and apply DST offset
# Requires import machine, utime, ntptime
# assumes active network, otherwise will raise error whch is not currently dealt with
# Note: dstOffset should be between -12 and +14
# From: https://forum.micropython.org/viewtopic.php?f=16&t=3675&sid=919a628fb8ca22b7dcecb984f5142ef1&start=10
#
# RTC: Real Time Clock
# NTP: Network Time Protocol
#
# (date(2000, 1, 1) - date(1900, 1, 1)).days * 24*60*60 = 3155673600
# ###################################################################### #

import utime
import ntptime


def setLocalTime(dstOffset):
    try:
        # get the YEAR to use in calculation
        year, month, day, hour, minute, second, ms, dayinyear = utime.localtime()

        # define Daylight Saving Time start date and Standard Time start date for this year
        # Eastern Daylight Time (EDT) Starts at 2:00 2nd Sunday March
        dstDT = utime.mktime(
            (year, 3, (14 - (int(5*year/4+5)) % 7), 2, 0, 0, 0, 0, 0))
        # Eastern Standard Time (EST) Starts at 2:00 1st Sunday November
        dstST = utime.mktime(
            (year, 11, (7 - (int(5*year/4+5)) % 7), 2, 0, 0, 0, 0, 0))

        # get the time for calculation
        now = ntptime.time()
        if dstOffset >= 0:
            # print( "Positive timezone" )
            if dstDT < now and now < dstST:
                # print( "Daylight Time")
                ntptime.NTP_DELTA = 3155673600-((dstOffset+1) * 3600)
            else:
                # print( "Standard Time")
                ntptime.NTP_DELTA = 3155673600-(dstOffset * 3600)
        else:
            # print( "Negative timezone" )
            if dstDT < now and now < dstST:
                # print( "Daylight Time")
                ntptime.NTP_DELTA = 3155673600-((dstOffset+1) * 3600)
            else:
                # print( "Standard Time")
                ntptime.NTP_DELTA = 3155673600-(dstOffset * 3600)

        # set the RTC to correct time
        ntptime.settime()

    except Exception as e:
        print("Time error ocurred: " + str(e))


def getTime():
    year, month, day, hour, minute, second, ms, dayinyear = utime.localtime()
    szTime = "{:4}-{:02}-{:02} {:02}:{:02}:{:02}".format(
        year, month, day, hour, minute, second)
    return(szTime)


def demo():
    import uos
    print("getTime():", getTime())  # Formatted
    print("utime.localtime():", utime.localtime())
    try:
        print("ntptime.time():    ", ntptime.time())
    except:
        print("Not connected to the network yet")
    st_mode, st_ino, st_dev, st_nlink, st_uid, st_gid, st_size, st_atime, st_mtime, st_ctime = uos.stat(
        '/netLocalTime.py')
    print("st_mtime from uos.stat()", st_mtime)


if __name__ == "__main__":
    demo()
