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
import struct
import sys

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="data/globir.18305.0015", help="Input data file")
parser.add_argument('-out', dest="OUTPUT_FILE", default="frames/globir.18305.0015.png", help="Output file")
args = parser.parse_args()

INPUT_FILE = args.INPUT_FILE
OUTPUT_FILE = args.OUTPUT_FILE

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

    print("lines: %s, elements: %s, offset: %s" % (lines, elements, dataOffset))
    pixels = np.zeros((lines, elements), dtype=np.int8)

    rowErrors = []
    for line in range(lines):
        infile.seek(dataOffset + elements * line)
        lineString = infile.read(elements)
        lineStringLen = len(lineString)
        try:
            row = struct.unpack(format, lineString)
            pixels[line] = np.array(row).astype(np.int8)
        except struct.error:
            # do nothing
            # print("%s != %s" % (lineStringLen, elements))
            # sys.exit()
            rowErrors.append(line)

        sys.stdout.write('\r')
        sys.stdout.write("%s%%" % round(1.0*(line+1)/lines*100,1))
        sys.stdout.flush()

    print("%s errors." % len(rowErrors))

    for line in range(lines):
        i = lines-line-1
        row = pixels[i]
        all_zeros = not np.any(row)
        if all_zeros:
            pixels = np.delete(pixels, i, 0)

if pixels is not None:
    print("Saving %s..." % OUTPUT_FILE)
    im = Image.fromarray(pixels, mode="L")
    im.save(OUTPUT_FILE)
    print("Saved %s" % OUTPUT_FILE)
