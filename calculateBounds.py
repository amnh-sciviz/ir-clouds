# -*- coding: utf-8 -*-

# Given an image with mercator projection, try to determine its bounds based on its aspect ratio

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
parser.add_argument('-in', dest="INPUT_FILE", default="data/globir.18319.2345.png", help="Input data file")
args = parser.parse_args()

INPUT_FILE = args.INPUT_FILE

im = Image.open(INPUT_FILE)
im = im.convert("L")
imW, imH = im.size

# imH/2.0 = imW / (2.0 * math.pi) * math.log(math.tan(math.pi / 4.0 + math.radians(NORTH) / 2.0))
# (imH / 2.0) / (imW / (2.0 * math.pi)) = math.log(math.tan(math.pi / 4.0 + math.radians(NORTH) / 2.0))
# math.exp((imH / 2.0) / (imW / (2.0 * math.pi))) = math.tan(math.pi / 4.0 + math.radians(NORTH) / 2.0)
# math.atan(math.exp((imH / 2.0) / (imW / (2.0 * math.pi)))) = math.pi / 4.0 + math.radians(NORTH) / 2.0
# math.atan(math.exp((imH / 2.0) / (imW / (2.0 * math.pi)))) - (math.pi / 4.0) = math.radians(NORTH) / 2.0
# (math.atan(math.exp((imH / 2.0) / (imW / (2.0 * math.pi)))) - (math.pi / 4.0)) * 2.0 = math.radians(NORTH)
north = math.degrees((math.atan(math.exp((imH / 2.0) / (imW / (2.0 * math.pi)))) - (math.pi / 4.0)) * 2.0)
south = -north
print("%s -> %s (total = %s)" % (north, south, north*2))
