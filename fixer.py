#

import os
import argparse
import time
import numpy as np
import rasterio as rio
from rasterio.enums import Resampling

def main():
    with rio.open(filename) as src:
        data_raster = src.read()
        data_meta = src.meta
        shape = data_raster.shape

        for i in range(shape[0]):
            for j in range(shape[1]):
                if data_raster[i][j] == 253:
                    data_raster[i][j] == 0
        
        with rio.open("tmp/{}".format(filename), 'w', **data_meta) as dst:
            dst.write(data_raster)

if __name__ == "__main__":
    filename = "nothing"
    main()
