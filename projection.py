import numpy as np
import os
from pprint import pprint
import pyopencl as cl

os.environ['PYOPENCL_COMPILER_OUTPUT'] = '1'

# From /data/idl/cross/remap/apian_arago/amnh_apianus_info
#
# This is the projected version of the sphere that we use for our Earth Wall. The projection is called "Apianus", and no one uses it except us as far as I can tell. Here are the formulas for image coordinates in X and Y:
#
# X = {((sqrt(1-(latitude/90)^2))/180)+ 1}(image_width/2)+x0
# Y = {1-(latitude/90)}(Height/2)+y0
# (x0,y0) is uppler left corner of projection
# image_width should be 2 * image_height

def projectApian(src, dest, north, south):
    sh, sw = src.shape
    dh, dw = dest.shape

    src = src.reshape(-1)
    dest = dest.reshape(-1)

    visibleHeight = (north - south) / 180.0 * dh
    offsetY = (dh - visibleHeight) / 2.0

    # the kernel function
    srcCode = """
    static float lerp(float a, float b, float mu) {
        return (b - a) * mu + a;
    }

    __kernel void doProjection(__global uchar *source, __global uchar *dest){
        int sw = %d;
        int sh = %d;
        int dw = %d;
        int dh = %d;
        float north = %f;
        float south = %f;
        float vh = %f;
        float y0 = %f;

        // get dest position
        int x = get_global_id(1);
        int y = get_global_id(0);

        // get normalized position
        float nx = (float) x / (float) (dw-1);
        float ny = (float) y / (float) (dh-1);

        // get source position
        int sx = (int) round(nx * (float) (sw-1));
        int sy = (int) round(ny * (float) (sh-1));
        int j = sy * sw + sx;

        // get lon and lat
        // float lon = lerp(west, east, nx);
        float lat = lerp(north, south, ny);

        // get source position
        float z = sqrt((float) 1.0) / 180.0;
        float multiplier = 0.0;
        float a = 1.0 - (lat/90.0) * (lat/90.0);
        if (a > 0.0) {
            multiplier = sqrt(a) / 180.0;
        }
        multiplier = multiplier / z;
        float latWidth = (float) dw * multiplier;
        float offsetX = ((float) dw - latWidth) * 0.5;
        int dx = (int) round(offsetX + nx * latWidth);
        int dy = (int) round(ny * (float) (vh-1.0) + y0);
        dx = clamp(dx, 0, dw-1);
        dy = clamp(dy, 0, dh-1);
        int i = dy * dw + dx;

        // assign pixel
        dest[i] = source[j];
    }
    """ % (sw, sh, dw, dh, north, south, visibleHeight, offsetY)

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
