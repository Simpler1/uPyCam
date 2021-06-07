from math import cos, sin, tan, acos, asin, atan, floor
from math import degrees as deg, radians as rad


def get_sunrise_sunset(year, month, day, is_rise=True,
                       tz_offset=0, dst=False, lat_d=38.95, lon_d=-84.35, zenith_d=91):
    """
    year:
      4 digit int
    month:
      Jan-Dec as 1 to 12
    day:
      Day of the month (1 to 31)
    is_rise:
      True = sunrise
      False = sunset
    tz_offset:
      Time Zone Offset
    dst:
      Daylight Saving Time
    lat_d:
      Lattitude as a degree decimal (-90 to 90)
      Negative is the southern hemisphere
    lon_d:
      Longitude as a degree decimal (-180 to 180)
      Negative is west of Greenwich Mean Time
    zenith_d:
      offical      = 90 degrees 50' = 90 + 50/60
      civil        = 96 degrees
      nautical     = 102 degrees
      astronomical = 108 degrees
    """
    tz_offset = tz_offset + 1 if dst else tz_offset
    zenith_r = rad(zenith_d)
    lat_r = rad(lat_d)
    lon_r = rad(lon_d)

    # 1. first calculate the day of the year
    n1 = floor(275 * month / 9.0)
    n2 = floor((month + 9) / 12.0)
    n3 = (1 + floor(year - 4 * floor(year / 4.0) + 2) / 3.0)
    d_o_y = n1 - (n2 * n3) + day - 30

    # 2. convert the longitude to hour value and calculate an approximate time
    lon_h = lon_d / 15.0
    if is_rise:
        rise_or_set_time = d_o_y + ((6 - lon_h) / 24.0)
    else:
        rise_or_set_time = d_o_y + ((18 - lon_h) / 24.0)

    # 3. calculate the Sun's mean anomaly
    sun_mean_anomaly_d = (0.9856 * rise_or_set_time) - \
        3.289  # original was 3.763
    sun_mean_anomaly_r = rad(sun_mean_anomaly_d)

    # 4. calculate the Sun's true longitude
    sun_true_lon_d = (sun_mean_anomaly_d +
                      (1.916 * sin(sun_mean_anomaly_r)) +
                      (0.020 * sin(2 * sun_mean_anomaly_r)) +
                      282.634)  # original was 282.605 )

    # make sure sun_true_lon_d is within 0, 360
    if sun_true_lon_d < 0:
        sun_true_lon_d = sun_true_lon_d + 360
    elif sun_true_lon_d > 360:
        sun_true_lon_d = sun_true_lon_d - 360
    sun_true_lon_r = rad(sun_true_lon_d)

    # 5a. calculate the Sun's right ascension
    sra_r = atan(0.91746 * tan(sun_true_lon_r))
    sra_d = deg(sra_r)

    # make sure it's between 0 and 360
    if sra_d < 0:
        sra_d = sra_d + 360
    elif sra_d > 360:
        sra_d = sra_d - 360

    # 5b. right ascension value needs to be in the same quadrant as L
    sun_true_lon_d_quad = (floor(sun_true_lon_d / 90.0)) * 90
    sra_quad = (floor(sra_d / 90.0)) * 90
    sra_d = sra_d + (sun_true_lon_d_quad - sra_quad)

    # 5c. right ascension value needs to be converted into hours
    sra_h = sra_d / 15

    # 6. calculate the Sun's declination
    sin_declination = 0.39782 * sin(sun_true_lon_r)
    cos_declination = cos(asin(sin_declination))

    # 7a. calculate the Sun's local hour angle
    cos_hour = (cos(zenith_r) -
                (sin_declination * sin(lat_r)) /
                (cos_declination * cos(lat_r)))

    # extreme north / south
    if cos_hour > 1:
        print("Sun never rises at this location on this date.")
    elif cos_hour < -1:
        print("Sun never sets at this location on this date.")

    # 7b. finish calculating H and convert into hours
    if is_rise:
        sun_local_angle_h = (360 - deg(acos(cos_hour))) / 15.0
    else:
        sun_local_angle_h = deg(acos(cos_hour)) / 15.0

    # 8. calculate local mean time of rising/setting
    sun_event_time = sun_local_angle_h + sra_h - \
        (0.06571 * rise_or_set_time) - 6.622  # original was 6.589

    # 9. adjust back to UTC
    ut = sun_event_time - lon_h

    # 10. convert UT value to local time zone of latitude/longitude
    local_time = ut + tz_offset
    if local_time < 0:
        local_time += 24
    elif local_time > 24:
        local_time -= 24
    hours = int(local_time)
    minutes = int((local_time - hours) * 60)
    # time = "{:>2}".format(hours) + ":" + "{:>2}".format(minutes)
    # time = time.replace(" ", "0")
    return (year, month, day, hours, minutes, 0)


# Test 1 (From original document)
def demo1():
    zenith = 90 + 50/60
    lat_d = 40.9
    lon_d = -74.3
    tz_offset = -4
    dst = False
    y = 1978
    m = 6
    d = 25
    is_rise = True

    print("Local Sunrise at", get_sunrise_sunset(
        y, m, d, is_rise, tz_offset, dst, lat_d, lon_d, zenith))
    print("Should be:       (1978, 6, 25, 5, 27, 0)")


# Test2 (From original document)
def demo2():
    zenith = 102
    lat_d = -6.0
    lon_d = 117.0
    tz_offset = 8
    dst = False
    y = 1978
    m = 10
    d = 1
    is_rise = False

    print("Local Sunset at", get_sunrise_sunset(
        y, m, d, _rise, tz_offset, dst, islat_d, lon_d, zenith))
    print("Should be:      (1978, 10, 1, 18, 51, 0)")


# Test 3 (My local test)
def demo3():
    zenith = 91
    lat_d = 38.95
    lon_d = -84.35
    tz_offset = -5
    dst = False
    y = 2021
    m = 1
    d = 19

    print("\n")
    print("Local Sunrise at", get_sunrise_sunset(
        y, m, d, True, tz_offset, dst, lat_d, lon_d, zenith))
    print("Should be        (2021, 1, 19, 7, 53, 0)\n")
    print("Local Sunset at", get_sunrise_sunset(
        y, m, d, False, tz_offset, dst, lat_d, lon_d, zenith))
    print("Should be       (2021, 1, 19, 17, 43, 0)\n")
    from utime import gmtime
    now = gmtime()
    print("Sunrise today at", get_sunrise_sunset(
        now[0], now[1], now[2], True, -5, False))
    print("Sunset today at ", get_sunrise_sunset(
        now[0], now[1], now[2], False, -5, False))


# Test 4 (Full year test)
def demo4():
    import utime
    import json
    zenith = 91
    lat_d = 38.95
    lon_d = -84.35
    tz_offset = -5
    dst = False
    y = 2021
    m = 1
    d = 1
    sec = utime.mktime((y, m, d, 0, 0, 0, 0, 0))
    out = []

    while y == 2021:
        r = get_sunrise_sunset(y, m, d, True, tz_offset,
                               dst, lat_d, lon_d, zenith)
        s = get_sunrise_sunset(y, m, d, False, tz_offset,
                               dst, lat_d, lon_d, zenith)
        ss = {
            "Off At": "{:04}-{:02}-{:02} {:02}:{:02}{}".format(s[0], s[1], s[2], s[3] if s[3] < 12 else s[3] - 12, s[4], "pm" if s[3] > 12 else "am"),
            "On At": "{:04}-{:02}-{:02} {:02}:{:02}{}".format(r[0], r[1], r[2], r[3] if r[3] < 12 else r[3] - 12, r[4], "pm" if r[3] > 12 else "am"),
        }
        key = "{:04}-{:01}-{:01}".format(y, m, d)
        out.append({key: ss})

        sec += 86400
        y, m, d, _, _, _, _, _ = utime.localtime(sec)

    print(json.dumps(out))


# Test 5 (Output list for year test)
def demo5():
    import utime
    import json
    zenith = 91
    lat_d = 38.95
    lon_d = -84.35
    tz_offset = -5
    dst = False
    y = 2021
    m = 1
    d = 1
    sec = utime.mktime((y, m, d, 0, 0, 0, 0, 0))
    out = []

    while y == 2021:
        r = get_sunrise_sunset(y, m, d, True, tz_offset,
                               dst, lat_d, lon_d, zenith)
        s = get_sunrise_sunset(y, m, d, False, tz_offset,
                               dst, lat_d, lon_d, zenith)
        ss = [
            (r[3], r[4]),
            (s[3], s[4])
        ]
        out.append(ss)

        sec += 86400
        y, m, d, _, _, _, _, _ = utime.localtime(sec)

    print(json.dumps(out))


if __name__ == "__main__":
    demo5()
