import uos


def filterJPG(filename):
    if(".jpg" in filename):
        return True
    else:
        return False


def jpgCount():
    files = uos.listdir('/sd/')
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
