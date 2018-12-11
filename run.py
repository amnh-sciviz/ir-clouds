# -*- coding: utf-8 -*-

import argparse
import datetime
import multiprocessing
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
import os
from pprint import pprint
import subprocess
import sys

# input
parser = argparse.ArgumentParser()
parser.add_argument('-auth', dest="AUTH", default="username:password", help="Earthdata drive username and password")
parser.add_argument('-start', dest="DATE_START", default="2018-08-01", help="Date start")
parser.add_argument('-end', dest="DATE_END", default="2018-11-01", help="Date end")
parser.add_argument('-ddir', dest="DATA_DIR", default="data/", help="Data directory")
parser.add_argument('-fdir', dest="FRAME_DIR", default="frames/", help="Frame directory")
parser.add_argument('-custom', dest="CUSTOM_FILES", default="", help="Path to a list of filenames separated by new lines")
parser.add_argument('-log', dest="LOG_FILE", default="logs/errors.txt", help="Frame directory")
parser.add_argument('-threads', dest="THREADS", default=3, type=int, help="Amount of parallel frames to process; -1 for maximum allowed by cpu")
parser.add_argument('-overwrite', dest="OVERWRITE", default=0, type=int, help="Overwrite existing frames?")
parser.add_argument('-del', dest="DELETE_DATA", default=1, type=int, help="Delete data after processing frame?")
args = parser.parse_args()

DATE_START = tuple([int(p) for p in args.DATE_START.strip().split("-")])
DATE_END = tuple([int(p) for p in args.DATE_END.strip().split("-")])
AUTH = args.AUTH
DATA_DIR = args.DATA_DIR
FRAME_DIR = args.FRAME_DIR
THREADS = min(args.THREADS, multiprocessing.cpu_count()) if args.THREADS > 0 else multiprocessing.cpu_count()
OVERWRITE = (args.OVERWRITE > 0)
DELETE_DATA = (args.DELETE_DATA > 0)
LOG_FILE = args.LOG_FILE
CUSTOM_FILES = args.CUSTOM_FILES

BASE_URL = "https://ghrcdrive.nsstc.nasa.gov/pub/globalir/data/"

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

if len(CUSTOM_FILES) > 0:
    filenames = []
    with open(CUSTOM_FILES) as f:
        filenames = f.read().splitlines()
    for fn in filenames:
        filename = fn.strip()
        dateString = filename.split(".")[-2]
        date = datetime.datetime.strptime(dateString, "%y%j").date()
        url = BASE_URL + date.strftime("%Y/%m%d/") + filename
        params.append({
            "url": url,
            "datafile": DATA_DIR + filename,
            "imagefile": FRAME_DIR + filename + ".png"
        })

else:
    date = dateStart
    while date <= dateEnd:

        # 30-minute increments = 24 x 2
        for t in range(48):
            minutes = t * 30 + 15
            hours = str(minutes / 60).zfill(2)
            minutes = str(minutes % 60).zfill(2)
            timeString = hours + minutes

            filename = date.strftime("globir.%y%j.") + timeString
            # e.g. https://ghrcdrive.nsstc.nasa.gov/pub/globalir/data/2018/0806/globir.18218.0015
            url = BASE_URL + date.strftime("%Y/%m%d/") + filename

            params.append({
                "url": url,
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
    url = p["url"]
    datafile = p["datafile"]
    imagefile = p["imagefile"]

    imageFileExists = os.path.isfile(imagefile)
    dataFileExists = os.path.isfile(datafile)

    # already completed frame
    if imageFileExists and not OVERWRITE:
        return resp

    if not dataFileExists:
        command = ['curl', '-O', '-L', '-u', AUTH, url] # We need -L because the URL redirects
        print(" ".join(command))
        finished = subprocess.check_call(command)
        os.rename(os.path.basename(datafile), datafile)

    size = os.path.getsize(datafile)

    # Remove file if not downloaded properly
    if size < 100000:
        error = "Error: could not properly download %s" % url
        os.remove(datafile)
        logMessage(LOG_FILE, error)
        resp["error"] = error

    # Otherwise, process frame
    else:
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
