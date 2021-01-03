# ###################################################################### #
# Set RTC localTime from UTC and apply DST offset
# Requires import machine, utime, ntptime
# assumes active network, otherwise will raise error whch is not currently dealt with
# Note: dstOffset should be between -12 and +14
# From: https://forum.micropython.org/viewtopic.php?f=16&t=3675&sid=919a628fb8ca22b7dcecb984f5142ef1&start=10
# ###################################################################### #

import utime
import ntptime


def setLocalTime(dstOffset):
    # get the YEAR to use in calculation
    year, month, day, hour, minute, second, ms, dayinyear = utime.localtime()

    # get the time for calculation
    now = ntptime.time()
    # reload current time
    year, month, day, hour, minute, second, ms, dayinyear = utime.localtime()

    # szTime = "{:4}-{:02}-{:02} {:02}:{:02}:{:02}".format( year, month, day, hour, minute, second )
    # print( "Time : " , szTime )

# define DST change dates for this year
    # NZST Starts : 2:00 Last Sunday September  (old)
    # dstST = utime.mktime((year, 9, (30 -(int(5*year/4+4))%7),2,0,0,0,0,0)) #Time of September change to NZDT
    # NZST Starts : 2:00 1st Sunday November
    # Time of November change to NZDT
    dstST = utime.mktime(
        (year, 11, (7 - (int(5*year/4+5)) % 7), 2, 0, 0, 0, 0, 0))
    # NZDT Starts : 3:00 1st Sunday April  (old)
    # dstDT = utime.mktime((year, 4, ( 7 -(int(5*year/4+5))%7),3,0,0,0,0,0)) #Time of April change to NZST
    # NZDT Starts : 2:00 2nd Sunday March
    # Time of March change to NZST
    dstDT = utime.mktime(
        (year, 3, (14 - (int(5*year/4+5)) % 7), 2, 0, 0, 0, 0, 0))

    if dstOffset >= 0:
        # print( "Positive DST timezones" )
        if now > dstDT and now < dstST:
            # print( "Daylight Time")
            ntptime.NTP_DELTA = 3155673600-((dstOffset+1) * 3600)
        else:
            # print( "Standard Time")
            ntptime.NTP_DELTA = 3155673600-(dstOffset * 3600)
    else:
        # print( "Negative DST timezones" )
        if now > dstDT and now < dstST:
            # print( "Daylight Time")
            ntptime.NTP_DELTA = 3155673600-((dstOffset+1) * 3600)
        else:
            # print( "Standard Time")
            ntptime.NTP_DELTA = 3155673600-(dstOffset * 3600)

    # set the RTC to correct time
    ntptime.settime()
    # year, month, day, hour, minute, second, ms, dayinyear = utime.localtime()
    # szTime = "{:4}-{:02}-{:02} {:02}:{:02}:{:02}".format( year, month, day, hour, minute, second )
    # print( "setTime : " , szTime )
