# -*- coding: utf-8 -*-

# Details: https://ghrc.nsstc.nasa.gov/home/data-recipes/infrared-global-geostationary-composite-quick-view
# Data source: https://ghrc.nsstc.nasa.gov/pub/globalir/data/
# Doc: https://ghrc.nsstc.nasa.gov/pub/globalir/doc/globalir_dataset.pdf

import argparse
import math
import os
import numpy as np
from PIL import Image
from pprint import pprint
from projection import mercatorToEquirectangular
import struct
import sys

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="data/globir.18319.2345", help="Input data file")
parser.add_argument('-out', dest="OUTPUT_FILE", default="frames/%s.png", help="Output file")
parser.add_argument('-width', dest="WIDTH", default=9896, type=int, help="Width of output image")
parser.add_argument('-proj', dest="PROJECTION", default=1, type=int, help="Do projection?")
args = parser.parse_args()

INPUT_FILE = args.INPUT_FILE
OUTPUT_FILE = args.OUTPUT_FILE
PROJECTION = args.PROJECTION
WIDTH = args.WIDTH

if "%" in OUTPUT_FILE:
    OUTPUT_FILE = OUTPUT_FILE % INPUT_FILE.split("/")[-1]

NORTH, SOUTH = (70.0, -69.0)
WEST = 75.2 # https://en.wikipedia.org/wiki/GOES-16
LON_OFFSET = (180.0 - WEST) / 360.0 # lon will be converted to -180.0 -> 180.0
HEIGHT = int(round(((NORTH - SOUTH) / 180.0) * (WIDTH / 2.0)))
print("%s x %s" % (WIDTH, HEIGHT))

header = []
pixels = None
print("Reading file: %s" % INPUT_FILE)
with open(INPUT_FILE) as infile:
    # Read the first 768 bytes of the file containing the header and navigation information
    header = struct.unpack('<192I', infile.read(768))

    # Extract the data parameters
    lines = header[8]
    elements = header[9]
    format = "%4dB" % (elements)
    dataOffset = header[33]   # offset to data array (bytes)

    offsetLeft = int(round(elements * LON_OFFSET))
    offsetRight = elements - offsetLeft

    print("lines: %s, elements: %s, offset: %s" % (lines, elements, dataOffset))
    pixels = np.zeros((lines, elements), dtype=np.int8)

    rowErrors = []
    for line in range(lines):
        infile.seek(dataOffset + elements * line)
        lineString = infile.read(elements)
        lineStringLen = len(lineString)
        try:
            row = struct.unpack(format, lineString)
            row = np.array(row).astype(np.int8)
            if LON_OFFSET < 1.0:
                row = np.concatenate((row[offsetLeft:], row[:offsetLeft]), axis=0)
            pixels[line] = row
        except struct.error:
            # do nothing
            # print("%s != %s" % (lineStringLen, elements))
            # sys.exit()
            rowErrors.append(line)

        sys.stdout.write('\r')
        sys.stdout.write("%s%%" % round(1.0*(line+1)/lines*100,1))
        sys.stdout.flush()

    print("%s errors." % len(rowErrors))

    # for line in range(lines):
    #     i = lines-line-1
    #     row = pixels[i]
    #     all_zeros = not np.any(row)
    #     if all_zeros:
    #         pixels = np.delete(pixels, i, 0)

# Do projection
if PROJECTION:
    print("Projecting...")
    dest = np.zeros((HEIGHT, WIDTH), dtype=np.int8)
    pixels = mercatorToEquirectangular(pixels, dest, north=NORTH, south=SOUTH)

    # remove rows of black
    # pixels = pixels[~np.all(pixels <= 0, axis=1)]

if pixels is not None:
    print("Saving %s..." % OUTPUT_FILE)
    im = Image.fromarray(pixels, mode="L")
    im.save(OUTPUT_FILE)
    print("Saved %s" % OUTPUT_FILE)
