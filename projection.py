import math
import numpy as np
import os
from pprint import pprint
import pyopencl as cl

os.environ['PYOPENCL_COMPILER_OUTPUT'] = '1'

def mercatorToEquirectangular(src, dest, north, south):
    sh, sw = src.shape
    dh, dw = dest.shape

    src = src.reshape(-1)
    dest = dest.reshape(-1)

    northY = math.log(math.tan(math.pi / 4.0 + math.radians(north) / 2.0))
    southY = math.log(math.tan(math.pi / 4.0 + math.radians(south) / 2.0))

    # the kernel function
    srcCode = """
    static float lerp(float a, float b, float mu) {
        return (b - a) * mu + a;
    }

    static float norm(float value, float a, float b) {
        float n = (value - a) / (b - a);
        if (n > 1.0) {
            n = 1.0;
        }
        if (n < 0.0) {
            n = 0.0;
        }
        return n;
    }

    __kernel void doProjection(__global uchar *source, __global uchar *dest){
        int sw = %d;
        int sh = %d;
        int dw = %d;
        int dh = %d;
        float north = %f;
        float south = %f;
        float northY = %f;
        float southY = %f;
        float piq = %f;

        // get dest position
        int x = get_global_id(1);
        int y = get_global_id(0);
        int i = y * dw + x;

        // get normalized position
        float nx = (float) x / (float) (dw-1);
        float ny = (float) y / (float) (dh-1);

        // get lat
        float lat = lerp(north, south, ny);

        // convert lon lat from mercator to equirectangular
        float nmy = ny;
        float my = (float) tan(piq + (float) radians(lat) / (float) 2.0);
        if (my > 0) {
            my = log(my);
            nmy = norm(my, northY, southY);
        }

        // get source position
        int sx = (int) round(nx * (float) (sw-1));
        int sy = (int) round(nmy * (float) (sh-1));
        int j = sy * sw + sx;

        // assign pixel
        dest[i] = source[j];
    }
    """ % (sw, sh, dw, dh, north, south, northY, southY, math.pi / 4.0)

    # Get platforms, both CPU and GPU
    plat = cl.get_platforms()
    GPUs = plat[0].get_devices(device_type=cl.device_type.GPU)
    CPU = plat[0].get_devices()
    # prefer GPUs
    if GPUs and len(GPUs) > 0:
        ctx = cl.Context(devices=GPUs)
    else:
        print "Warning: using CPU instead of GPU"
        ctx = cl.Context(CPU)
    # Create queue for each kernel execution
    queue = cl.CommandQueue(ctx)
    mf = cl.mem_flags
    # Kernel function instantiation
    prg = cl.Program(ctx, srcCode).build()

    bufIn =  cl.Buffer(ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=src)
    bufOut = cl.Buffer(ctx, mf.WRITE_ONLY, dest.nbytes)
    prg.doProjection(queue, [dh, dw], None , bufIn, bufOut)

    # Copy result
    cl.enqueue_copy(queue, dest, bufOut)

    dest = dest.reshape(dh, dw)
    return dest
