# IR Clouds

Scripts for generating images sequences for IR cloud data

## Requirements

1. [Python](https://www.python.org/) 2.7.x+
1. [Python Pillow](https://pillow.readthedocs.io/en/5.3.x/) - for image generation
1. An [Earthdata](https://earthdata.nasa.gov/) account

## Retrieving data files

You can download these files manually via the [web](https://ghrc.nsstc.nasa.gov/pub/globalir/data/). Or using [Earthdata Drive](https://ghrcdrive.nsstc.nasa.gov/drive/help).

## Processing the frames

Let's say we want to process all frames between august 2018 and november 2018. You can run the following command:

```
python run.py -start " 2018-08-01" -end " 2018-11-30" -ddir "<your path to data folder>" -fdir "<your path to frames folder>"
```

This assumes you already manually downloaded all the necessary files.  If you want to automate this, you must follow [these directions]((https://ghrcdrive.nsstc.nasa.gov/drive/help)) to setup a network drive to the data.  Let's say you set up a drive `Z:/`. You can then run this command:

```
python run.py -start " 2018-08-01" -end " 2018-11-30" -drive "Z:/" -ddir "<your path to data folder>" -fdir "<your path to frames folder>"
```
