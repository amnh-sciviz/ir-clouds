# IR Clouds

Scripts for generating images sequences for IR cloud data

## Requirements

1. [Python](https://www.python.org/) 2.7.x+
1. [Python Pillow](https://pillow.readthedocs.io/en/5.3.x/) - for image generation
1. [curl](https://curl.haxx.se/) for downloading files
1. An [Earthdata](https://earthdata.nasa.gov/) account for authentication

## Processing the frames

Let's say we want to process all frames between august 2018 and november 2018. You can run the following command:

```
python run.py -start " 2018-08-01" -end " 2018-11-30" -auth "username:password" -ddir "<your path to downloaded data folder>" -fdir "<your path to output frames folder>"
```

You can get your username and password [here](https://ghrcdrive.nsstc.nasa.gov/drive/).

Data files are deleted after frame is finished processing by default. If you'd like to keep the (very large) data files after you are done processing a frame, add `-del 0` to the command.

Also, the script runs multiple threads by default to speed up processing. You can increase/decrease this by passing in `-threads 4` (i.e. 4 threads).  This can be 1 up to however much your CPU allows. Enter -1 for the maximum allowed.
