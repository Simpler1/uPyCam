# my_files.py
"""Custom file methods"""

from uos import listdir
from my_time import nowStringExtended


def filterJPG(filename):
    if(".jpg" in filename):
        return True
    else:
        return False


def jpgCount(directory):
    """Returns the number of .jpg files in the directory"""
    files = listdir(directory)
    jpgFiles = list(filter(filterJPG, files))
    count = len(jpgFiles)
    return count


def log(text):
    t = nowStringExtended()
    print(text)
    with open('sd/log.txt', 'w') as f:
        f.write(t + ": " + text)


def demo():
    count = jpgCount()
    if (count == 1):
        print("There is", count, "jpg file")
    else:
        print("There are", count, "jpg files")

if __name__ == "__main__":
    demo()
