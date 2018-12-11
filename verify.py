# -*- coding: utf-8 -*-

import argparse
import datetime
import glob
import os
from pprint import pprint
import subprocess
import sys

# input
parser = argparse.ArgumentParser()
parser.add_argument('-start', dest="DATE_START", default="2018-08-01", help="Date start")
parser.add_argument('-end', dest="DATE_END", default="2018-11-01", help="Date end")
parser.add_argument('-fdir', dest="FRAME_DIR", default="frames/", help="Frame directory")
args = parser.parse_args()

DATE_START = tuple([int(p) for p in args.DATE_START.strip().split("-")])
DATE_END = tuple([int(p) for p in args.DATE_END.strip().split("-")])
FRAME_DIR = args.FRAME_DIR

dateStart = datetime.datetime(year=DATE_START[0], month=DATE_START[1], day=DATE_START[2])
dateEnd = datetime.datetime(year=DATE_END[0], month=DATE_END[1], day=DATE_END[2])

date = dateStart
targetFiles = []
while date <= dateEnd:

    # 30-minute increments = 24 x 2
    for t in range(48):
        minutes = t * 30 + 15
        hours = str(minutes / 60).zfill(2)
        minutes = str(minutes % 60).zfill(2)
        timeString = hours + minutes
        filename = date.strftime("globir.%y%j.") + timeString
        imageFile = FRAME_DIR + filename + ".png"
        targetFiles.append(imageFile)

    date += datetime.timedelta(days=1)

existingFiles = glob.glob(FRAME_DIR + "*.png")

targetFiles = set(targetFiles)
existingFiles = set(existingFiles)

missingFiles = sorted(list(targetFiles - existingFiles))
extraFiles = sorted(list(existingFiles - targetFiles))

# print("%s missing files:" % len(missingFiles))
# print("%s extra files:" % len(extraFiles))
# print("delta: %s" % abs(len(missingFiles)-len(extraFiles)))
# sys.exit()

print("%s missing files:" % len(missingFiles))
for fn in missingFiles:
    basename = os.path.basename(fn)
    parts = basename.split(".")
    dateString = parts[-3]
    date = datetime.datetime.strptime(dateString, "%y%j").date()
    dateString = date.strftime("%b %d %Y")
    print("%s\t%s" % (basename, dateString))

print("-------")
print("%s extra files:" % len(extraFiles))
pprint(extraFiles)
