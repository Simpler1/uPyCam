Overview
========
MicroPython does not support timezones or daylight saving time.


Considerations
==============
When files are created in MicroPython, they will alway be created based on GMT.
When these files are viewed on a machine that supports timezone, they will be displayed with
a create/modify time in the current timezone.

NPT_DELTA represents the number of seconds in 100 years (from 01-Jan-1900 to 01-Jan-2000)
Changing this value changes the GMT time on the board with messes up the times that the files were created/modified.  
**Conclusion:  Don't Change the NTP_DELTA value.**


exiftool
========
jpg images created with the ESP32-CAM do not have a CreateDate tag in the exif data.
The *FileModifyDate* (case insensitive) can be used to rename the files on the desktop system that
supports timezone and DST.

exiftool \
-v \
-r \
-P \
-ext jpg \
-d "./%f-%Y%m%d_%H%M%S.%%le" \
"-filename<FileModifyDate" \
"./"

test with:

exiftool \
-v \
-r \
-P \
-ext jpg \
-d "./%f-%Y%m%d_%H%M%S.%%le" \
"-testname<FileModifyDate" \
"./"


Example exif data from jpg file taken on ESP32-CAM after npttime.settime() was used
-----------------------------------------------------------------------------------
$ exiftool 20210111_144950.jpg
ExifTool Version Number         : 10.80
File Name                       : 20210111_144950.jpg
Directory                       : .
File Size                       : 143 kB
File Modification Date/Time     : 2021:01:11 09:49:50-05:00
File Access Date/Time           : 2021:01:10 19:00:00-05:00
File Inode Change Date/Time     : 2021:01:11 09:49:50-05:00
File Permissions                : rw-r--r--
File Type                       : JPEG
File Type Extension             : jpg
MIME Type                       : image/jpeg
JFIF Version                    : 1.01
Resolution Unit                 : inches
X Resolution                    : 0
Y Resolution                    : 0
Image Width                     : 1600
Image Height                    : 1200
Encoding Process                : Baseline DCT, Huffman coding
Bits Per Sample                 : 8
Color Components                : 3
Y Cb Cr Sub Sampling            : YCbCr4:2:2 (2 1)
Image Size                      : 1600x1200
Megapixels                      : 1.9

