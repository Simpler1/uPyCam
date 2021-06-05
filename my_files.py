# my_files.py
"""Custom file methods"""

from uos import listdir

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


def demo():
    count = jpgCount()
    if (count == 1):
        print("There is", count, "jpg file")
    else:
        print("There are", count, "jpg files")

if __name__ == "__main__":
    demo()
