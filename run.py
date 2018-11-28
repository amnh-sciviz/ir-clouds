# -*- coding: utf-8 -*-

import argparse
import datetime
import multiprocessing
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
import os
from pprint import pprint
from shutil import copyfile
import subprocess
import sys

# input
parser = argparse.ArgumentParser()
parser.add_argument('-start', dest="DATE_START", default="2018-08-01", help="Date start")
parser.add_argument('-end', dest="DATE_END", default="2018-11-01", help="Date end")
parser.add_argument('-drive', dest="INPUT_DRIVE", default="Z:/", help="Data directory")
parser.add_argument('-ddir', dest="DATA_DIR", default="data/", help="Data directory")
parser.add_argument('-fdir', dest="FRAME_DIR", default="frames/", help="Frame directory")
parser.add_argument('-log', dest="LOG_FILE", default="logs/errors.txt", help="Frame directory")
parser.add_argument('-threads', dest="THREADS", default=3, type=int, help="Amount of parallel frames to process; -1 for maximum allowed by cpu")
parser.add_argument('-overwrite', dest="OVERWRITE", default=0, type=int, help="Overwrite existing frames?")
parser.add_argument('-del', dest="DELETE_DATA", default=0, type=int, help="Delete data after processing frame?")
args = parser.parse_args()

DATE_START = tuple([int(p) for p in args.DATE_START.strip()split("-")])
DATE_END = tuple([int(p) for p in args.DATE_END.strip().split("-")])
INPUT_DRIVE = args.INPUT_DRIVE
INPUT_DIR = INPUT_DRIVE + "globalir/data/"
DATA_DIR = args.DATA_DIR
FRAME_DIR = args.FRAME_DIR
THREADS = min(args.THREADS, multiprocessing.cpu_count()) if args.THREADS > 0 else multiprocessing.cpu_count()
OVERWRITE = (args.OVERWRITE > 0)
DELETE_DATA = (args.DELETE_DATA > 0)
LOG_FILE = args.LOG_FILE

dateStart = datetime.datetime(year=DATE_START[0], month=DATE_START[1], day=DATE_START[2])
dateEnd = datetime.datetime(year=DATE_END[0], month=DATE_END[1], day=DATE_END[2])

# ensure directories exist
def makeDirectories(filenames):
    if not isinstance(filenames, list):
        filenames = [filenames]
    for filename in filenames:
        dirname = os.path.dirname(filename)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
makeDirectories([DATA_DIR, FRAME_DIR])

params = []
date = dateStart
while date <= dateEnd:

    # 30-minute increments = 24 x 2
    for t in range(48):
        minutes = t * 30 + 15
        hours = str(minutes / 60).zfill(2)
        minutes = str(minutes % 60).zfill(2)
        timeString = hours + minutes

        filename = date.strftime("globir.%y%j.") + timeString
        # e.g. https://ghrc.nsstc.nasa.gov/pub/globalir/data/2018/0806/globir.18218.0015
        infile = INPUT_DIR + date.strftime("%Y/%m%d/") + filename

        params.append({
            "infile": infile,
            "datafile": DATA_DIR + filename,
            "imagefile": FRAME_DIR + filename + ".png"
        })

    date += datetime.timedelta(days=1)

def logMessage(filename, message):
    print(message)
    with open(filename, "a") as f:
        f.write(message+"\n")

def downloadAndProcessFrame(p):
    resp = {}
    infile = p["infile"]
    datafile = p["datafile"]
    imagefile = p["imagefile"]

    if not os.path.isfile(datafile):
        # command = ['curl', '-O', '-L', url] # We need -L because the URL redirects
        # print(" ".join(command))
        # finished = subprocess.check_call(command)
        # os.rename(os.path.basename(datafile), datafile)

        # Copy the file to the target location
        # Requires Earthdata Drive: https://ghrcdrive.nsstc.nasa.gov/drive/help
        copyfile(infile, datafile)

    size = os.path.getsize(datafile)

    # Remove file if not downloaded properly
    if size < 100000:
        error = "Error: could not properly download %s" % infile
        os.remove(datafile)
        logMessage(LOG_FILE, error)
        resp["error"] = error

    # Otherwise, process frame
    elif not os.path.isfile(imagefile) or OVERWRITE:
        command = ['python', '-W', 'ignore', 'data_to_frame.py', '-in', datafile, '-out', imagefile]
        finished = subprocess.check_call(command)

        if os.path.isfile(imagefile):
            if DELETE_DATA:
                os.remove(datafile)
        else:
            error = "Error: could not properly process %s" % datafile
            logMessage(LOG_FILE, error)
            resp["error"] = error

    return resp

print("Processing %s files" % len(params))

if (THREADS > 1):
    pool = ThreadPool(THREADS)
    results = pool.map(downloadAndProcessFrame, params)
    pool.close()
    pool.join()

else:
    results = []
    for i, p in enumerate(params):
        results.append(downloadAndProcessFrame(p))
