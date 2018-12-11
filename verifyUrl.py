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
parser.add_argument('-auth', dest="AUTH", default="username:password", help="Earthdata drive username and password")
parser.add_argument('-start', dest="DATE_START", default="2018-08-01", help="Date start")
parser.add_argument('-end', dest="DATE_END", default="2018-11-01", help="Date end")
args = parser.parse_args()

AUTH = args.AUTH
DATE_START = tuple([int(p) for p in args.DATE_START.strip().split("-")])
DATE_END = tuple([int(p) for p in args.DATE_END.strip().split("-")])
BASE_URL = "https://ghrcdrive.nsstc.nasa.gov/pub/globalir/data/"

dateStart = datetime.datetime(year=DATE_START[0], month=DATE_START[1], day=DATE_START[2])
dateEnd = datetime.datetime(year=DATE_END[0], month=DATE_END[1], day=DATE_END[2])

total = (dateEnd-dateEnd).days * 48

date = dateStart
invalidUrls = []
i = 0
while date <= dateEnd:

    # 30-minute increments = 24 x 2
    for t in range(48):
        minutes = t * 30 + 15
        hours = str(minutes / 60).zfill(2)
        minutes = str(minutes % 60).zfill(2)
        timeString = hours + minutes
        filename = date.strftime("globir.%y%j.") + timeString
        url = BASE_URL + date.strftime("%Y/%m%d/") + filename
        command = ['curl', '-I', '-u', AUTH, url]
        print(" ".join(command))
        result = subprocess.check_output(command).splitlines()
        if result and len(result):
            if "404" in result[0]:
                invalidUrls.append(("missing", url, date.strftime("%b %d %Y")))

            else:
                for r in result:
                    if r.startswith("Content-length:"):
                        parts = r.split(":")
                        length = int(parts[-1].strip())
                        if length < 10000000:
                            invalidUrls.append(("empty", url, date.strftime("%b %d %Y")))


        i += 1

        if total > 0:
            sys.stdout.write('\r')
            sys.stdout.write("%s%%" % round(1.0*i/total*100,1))
            sys.stdout.flush()

    date += datetime.timedelta(days=1)

print("%s invalid urls:" % len(invalidUrls))
for u in invalidUrls:
    print("%s\t%s\t%s" % u)
