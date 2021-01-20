# Based on: https://web.archive.org/web/20161202180207/http://williams.best.vwh.net/sunrise_sunset_algorithm.htm
#
# Originally from the Almanac for Computers published in 1978
# https://books.google.com/books?id=JlzvAAAAMAAJ&printsec=frontcover&source=gbs_ge_summary_r&cad=0#v=onepage&q=sunrise&f=false
# In the original, west of GMT was positive, but modern tradition is now negative


import math, sys

def get_sunrise_sunset( in_year, in_month, in_day, is_rise=True, 
    lat_d=38.95, lon_d=-84.35, dst_offset=-5, zenith_d=91):
  # lon_d:
  #   Negative is west of Greenwich Mean Time

  # is_rise:
  #   True = sunrise
  #   False = sunset

  # zenith_d:
  # offical      = 90 degrees 50' = 90 + 50/60
  # civil        = 96 degrees
  # nautical     = 102 degrees
  # astronomical = 108 degrees

  zenith_r = math.radians(zenith_d)
  cos_z_r = math.cos(zenith_r)
  lat_r = math.radians(lat_d)
  lon_r = math.radians(lon_d)
  cos_lat_r = math.cos(lat_r)
  sin_lat_r = math.sin(lat_r)
  print("cos(lat):", cos_lat_r)
  print("sin(lat):", sin_lat_r)
  print("cos(z):", cos_z_r)


  #1. first calculate the day of the year
  n1 = math.floor( 275 * in_month / 9.0 )
  n2 = math.floor( ( in_month + 9 ) / 12.0 )
  n3 = ( 1 + math.floor( in_year - 4 * math.floor( in_year / 4.0 ) + 2 ) / 3.0 )
  doy = n1 - ( n2 * n3 ) + in_day - 30
  print("Day of Year ", doy)

  #2. convert the longitude to hour value and calculate an approximate time
  lon_h = lon_d / 15.0
  print("longitude:", lon_h, "hours")
  if is_rise:
    rise_or_set_time = doy + ( ( 6 - lon_h ) / 24.0 )
    print("approx sunrise at", rise_or_set_time, "days since 01-Jan 00:00 (UTC)")
  else:
    rise_or_set_time = doy + ( ( 18 - lon_h ) / 24.0 )
    print("approx sunset at", rise_or_set_time, "days since 01-Jan 00:00 (UTC)")

  #3. calculate the Sun's mean anomaly
  sun_mean_anomaly_d = ( 0.9856 * rise_or_set_time ) - 3.289  # original was 3.763
  sun_mean_anomaly_r = math.radians(sun_mean_anomaly_d)
  print("sun mean anomaly", sun_mean_anomaly_d, "degrees")

  #4. calculate the Sun's true longitude
  sun_true_lon_d = ( sun_mean_anomaly_d +
              ( 1.916 * math.sin( sun_mean_anomaly_r ) ) +
              ( 0.020 * math.sin( 2 * sun_mean_anomaly_r ) ) +
              282.634 )  # original was 282.605 )

  # make sure sun_true_lon_d is within 0, 360
  if sun_true_lon_d < 0:
    sun_true_lon_d = sun_true_lon_d + 360
  elif sun_true_lon_d > 360:
    sun_true_lon_d = sun_true_lon_d - 360
  sun_true_lon_r = math.radians(sun_true_lon_d)
  print("true longitude", sun_true_lon_d, "degrees")

  #5a. calculate the Sun's right ascension
  sra_r = math.atan( 0.91746 * math.tan( sun_true_lon_r ) )
  sra_d = math.degrees(sra_r)
  print("sun_right_ascension is ", sra_d, "degrees")

  #make sure it's between 0 and 360
  if sra_d < 0:
    sra_d = sra_d + 360
  elif sra_d > 360:
    sra_d = sra_d - 360
  print("sun_right_ascension (modified) is ", sra_d, "degrees")

  #5b. right ascension value needs to be in the same quadrant as L
  sun_true_lon_d_quad = ( math.floor( sun_true_lon_d / 90.0 ) ) * 90
  sra_quad = ( math.floor( sra_d / 90.0 ) ) * 90
  sra_d = sra_d + ( sun_true_lon_d_quad - sra_quad )
  print("sun_right_ascension (quadrant) is ", sra_d, "degrees")

  #5c. right ascension value needs to be converted into hours
  sra_h = sra_d / 15
  print("sun_right_ascension (to hours) is ", sra_h, "hours")


  #6. calculate the Sun's declination
  sin_declination = 0.39782 * math.sin( sun_true_lon_r )
  cos_declination = math.cos( math.asin( sin_declination ) )
  print(" sin/cos declinations ", sin_declination, ", ", cos_declination)

  #7a. calculate the Sun's local hour angle
  cos_hour = ( math.cos( zenith_r ) -
                ( sin_declination * math.sin( lat_r ) ) /
                ( cos_declination * math.cos( lat_r ) ) )
  print("cos of hour ", cos_hour)

  # extreme north / south
  if cos_hour > 1:
    print("Sun Never Rises at this location on this date, exiting")
    # sys.exit()
  elif cos_hour < -1:
    print("Sun Never Sets at this location on this date, exiting")
    # sys.exit()

  #7b. finish calculating H and convert into hours
  if is_rise:
    sun_local_angle_h = ( 360 - math.degrees( math.acos( cos_hour ) ) ) / 15.0
  else:
    sun_local_angle_h = math.degrees( math.acos( cos_hour ) ) / 15.0
  print("sun local angle", sun_local_angle_h, "hours")

  #8. calculate local mean time of rising/setting
  sun_event_time = sun_local_angle_h + sra_h - ( 0.06571 * rise_or_set_time ) - 6.622 # original was 6.589
  print("sun event time ", sun_event_time)

  #9. adjust back to UTC
  ut = sun_event_time - lon_h
  print("ut: ", ut, "hours")

  #10. convert UT value to local time zone of latitude/longitude
  local_time = ut + dst_offset
  if local_time < 0: 
    local_time += 24
  elif local_time > 24:
    local_time -= 24
  print("local time: ", local_time, "hours")
  hours = int(local_time)
  minutes = int(( local_time - hours ) * 60)
  time = "{:>2}".format(hours) + ":" + "{:>2}".format(minutes)
  time = time.replace(" ", "0")
  return time


# Test 1 (From original document)
def demo1():
  zenith = 90 + 50/60
  lat_d = 40.9
  lon_d = -74.3
  dst_offset = -4
  d = 25
  m = 6
  y = 1978
  is_rise = True

  print("Local Sunrise at", get_sunrise_sunset(y, m, d, is_rise, lat_d, lon_d, dst_offset, zenith))
  print("Should be:       05:27")

# Test2 (From original document)  Nautical evening twilight
def demo2():
  zenith = 102
  lat_d = -6.0
  lon_d = 117.0
  dst_offset = 8 # This is not accounted for in the original document and time is listed as UT
  d = 1
  m = 10
  y = 1978
  is_rise = False

  print("Local Sunset at", get_sunrise_sunset(y, m, d, is_rise, lat_d, lon_d, dst_offset, zenith))
  print("Should be:      18:51")

# Test 3 (My local test)
def demo3():
  zenith = 91
  lat_d = 38.95
  lon_d = -84.35
  dst_offset = -5
  d = 19
  m = 1
  y = 2021

  print("Local Sunrise at", get_sunrise_sunset(y, m, d, True, lat_d, lon_d, dst_offset, zenith))
  print("Should be        07:53\n")
  print("Local Sunset at ", get_sunrise_sunset(y, m, d, False, lat_d, lon_d, dst_offset, zenith))
  print("Should be        17:43\n")

if __name__ == "__main__":
  demo3()
