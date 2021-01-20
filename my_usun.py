from math import cos,sin,tan,acos,asin,atan,floor
from math import degrees as deg, radians as rad

def get_sunrise_sunset( in_year, in_month, in_day, is_rise=True, 
    lat_d=38.95, lon_d=-84.35, dst_offset=-5, zenith_d=91):
  # lon_d:
  #   Longitude as a degree decimal.  
  #   Negative is west of Greenwich Mean Time

  # is_rise:
  #   True = sunrise
  #   False = sunset

  # zenith_d:
  # offical      = 90 degrees 50' = 90 + 50/60
  # civil        = 96 degrees
  # nautical     = 102 degrees
  # astronomical = 108 degrees

  zenith_r = rad(zenith_d)
  lat_r = rad(lat_d)
  lon_r = rad(lon_d)

  #1. first calculate the day of the year
  n1 = floor( 275 * in_month / 9.0 )
  n2 = floor( ( in_month + 9 ) / 12.0 )
  n3 = ( 1 + floor( in_year - 4 * floor( in_year / 4.0 ) + 2 ) / 3.0 )
  doy = n1 - ( n2 * n3 ) + in_day - 30

  #2. convert the longitude to hour value and calculate an approximate time
  lon_h = lon_d / 15.0
  if is_rise:
    rise_or_set_time = doy + ( ( 6 - lon_h ) / 24.0 )
  else:
    rise_or_set_time = doy + ( ( 18 - lon_h ) / 24.0 )

  #3. calculate the Sun's mean anomaly
  sun_mean_anomaly_d = ( 0.9856 * rise_or_set_time ) - 3.289  # original was 3.763
  sun_mean_anomaly_r = rad(sun_mean_anomaly_d)

  #4. calculate the Sun's true longitude
  sun_true_lon_d = ( sun_mean_anomaly_d +
              ( 1.916 * sin( sun_mean_anomaly_r ) ) +
              ( 0.020 * sin( 2 * sun_mean_anomaly_r ) ) +
              282.634 )  # original was 282.605 )

  # make sure sun_true_lon_d is within 0, 360
  if sun_true_lon_d < 0:
    sun_true_lon_d = sun_true_lon_d + 360
  elif sun_true_lon_d > 360:
    sun_true_lon_d = sun_true_lon_d - 360
  sun_true_lon_r = rad(sun_true_lon_d)

  #5a. calculate the Sun's right ascension
  sra_r = atan( 0.91746 * tan( sun_true_lon_r ) )
  sra_d = deg(sra_r)

  #make sure it's between 0 and 360
  if sra_d < 0:
    sra_d = sra_d + 360
  elif sra_d > 360:
    sra_d = sra_d - 360

  #5b. right ascension value needs to be in the same quadrant as L
  sun_true_lon_d_quad = ( floor( sun_true_lon_d / 90.0 ) ) * 90
  sra_quad = ( floor( sra_d / 90.0 ) ) * 90
  sra_d = sra_d + ( sun_true_lon_d_quad - sra_quad )

  #5c. right ascension value needs to be converted into hours
  sra_h = sra_d / 15

  #6. calculate the Sun's declination
  sin_declination = 0.39782 * sin( sun_true_lon_r )
  cos_declination = cos( asin( sin_declination ) )

  #7a. calculate the Sun's local hour angle
  cos_hour = ( cos( zenith_r ) -
                ( sin_declination * sin( lat_r ) ) /
                ( cos_declination * cos( lat_r ) ) )

  # extreme north / south
  if cos_hour > 1:
    print("Sun never rises at this location on this date.")
  elif cos_hour < -1:
    print("Sun never sets at this location on this date.")

  #7b. finish calculating H and convert into hours
  if is_rise:
    sun_local_angle_h = ( 360 - deg( acos( cos_hour ) ) ) / 15.0
  else:
    sun_local_angle_h = deg( acos( cos_hour ) ) / 15.0

  #8. calculate local mean time of rising/setting
  sun_event_time = sun_local_angle_h + sra_h - ( 0.06571 * rise_or_set_time ) - 6.622 # original was 6.589
  if sun_event_time < 0: 
    sun_event_time += 24
  elif sun_event_time > 24:
    sun_event_time -= 24

  #9. adjust back to UTC
  ut = sun_event_time - lon_h

  #10. convert UT value to local time zone of latitude/longitude
  hours = int(ut) + dst_offset
  minutes = int((ut-int(ut)) * 60)
  time = "{:>2}".format(hours) + ":" + "{:>2}".format(minutes)
  time = time.replace(" ", "0")
  return time


# Test 1 (From original document)
def demo1():
  zenith = 90 + 50/60
  lat_d = 40.9
  lon_d = -74.3
  dst_offset = -4
  y = 1978
  m = 6
  d = 25
  is_rise = True

  print("Local Sunrise at", get_sunrise_sunset(y, m, d, is_rise, lat_d, lon_d, dst_offset, zenith))
  print("Should be:       05:27")


# Test2 (From original document)
def demo2():
  zenith = 102
  lat_d = -6.0
  lon_d = 117.0
  dst_offset = 8
  y = 1978
  m = 10
  d = 1
  is_rise = False

  print("Local Sunset at", get_sunrise_sunset(y, m, d, is_rise, lat_d, lon_d, dst_offset, zenith))
  print("Should be:      18:51")


# Test 3 (My local test)
def demo3():
  zenith = 91
  lat_d = 38.95
  lon_d = -84.35
  dst_offset = -5
  y = 2021
  m = 1
  d = 19

  print("Local Sunrise at", get_sunrise_sunset(y, m, d, True, lat_d, lon_d, dst_offset, zenith))
  print("Should be        07:53\n")
  print("Local Sunset at ", get_sunrise_sunset(y, m, d, False, lat_d, lon_d, dst_offset, zenith))
  print("Should be        17:43\n")
  from utime import gmtime
  now = gmtime()
  print("Today is", now[0:3])
  print("Sunrise today at", get_sunrise_sunset(now[0], now[1], now[2]))
  print("Sunset today at ", get_sunrise_sunset(now[0], now[1], now[2], False))

if __name__ == "__main__":
  demo3()
