#
# Version: too-early-to-get-a-number
# Created by: Andrea Nosler
# Data collected from NASA's MODIS system
#

import os
import sys

import time
import numpy as np
import rasterio as rio
from PIL import Image

debugging = True

# Toggle-able output for Debugging
# Input: String
# Side Effect: Prints
def DEBUG(string):
    if(debugging):
        print("| DB:: ", string, " |")

# Compiles all layers together into resultant image
def collateData(width, height):
    DEBUG("pre-collation --- WIDTH = {}, HEIGHT = {}".format(width,height))
    out_image = Image.new(mode = "RGB", size = (width, height), color = (int(0),int(0),int(255)))
    pixels = out_image.load()
    

    # First Run of Pop
    with rio.open("output/layer0.tif") as dataset:
        layer_data = dataset.read(1)
        max = layer_data.max()
        co = 255 / max
        for i in range(width):
            for j in range(height):
                if (layer_data[j,i] > 0):
                    pixels[i,j] = (int(layer_data[j,i]*co), int(0), int(0))

    # Second run for EVI
    with rio.open("output/layer2.tif") as dataset:
        layer_data = dataset.read(1)
        max = layer_data.max()
        co =  255 / max
        for i in range(width):
            for j in range(height):
                if (layer_data[j,i] > 0):
                    pixels[i,j] = (int(pixels[i,j][0]), int(layer_data[j,i]*co), int(0))

    out_image.save('testoutput.png', format = "PNG")

    for i in range(3):
        os.remove("output/layer{}.tif".format(i))
    return

# TODO : Docstring
def clipLayers(p1, p2, width, height):
    layers = ['layers/pop_2020.tif', 'layers/soil_moisture.tif', 'layers/veg_EVI.tif']
    for i in range(len(layers)):
        # Open the Geotiff
        dataset = rio.open(layers[i])

        # Get the indeces of the geographic points
        y1, x1 = dataset.index(p1[0], p1[1])
        y2, x2 = dataset.index(p2[0], p2[1])

        DEBUG("Point1:  x:{}   y:{}".format(x1, y1))
        DEBUG("Point2:  x:{}   y:{}".format(x2, y2))

        window = rio.windows.Window(x1, y1, x2 - x1, y2 - y1)
        clip = dataset.read(window=window)

        # Define the metadata and save the image
        meta = dataset.meta
        DEBUG("ExportedDataLayers --- WIDTH = {}, HEIGHT = {}".format(width,height))
        meta['width'], meta['height'] = width, height
        meta['transform'] = rio.windows.transform(window, dataset.transform)
        with rio.open("output/layer{}.tif".format(i), 'w', **meta) as dst:
            dst.write(clip)

def main():
    # print("///////////////////////////////////////////////////////////////////")
    # print("/               Animal Habitat Suitability Calculator                 /")
    # print("/                  Authored by Andrea Nosler                      /")
    # print("///////////////////////////////////////////////////////////////////\n")

    # Hawaii
    # corner_point = (-161.378524, 23.148462)
    # corner_point2 = (-153.289470, 18.070883)

    # Maui
    corner_point = (-158.317957, 21.707151)
    corner_point2 = (-157.641939, 21.251767)


    # USA
    # corner_point = (-132.006226, 50.425429)
    # corner_point2 = (-66.717236, 22.862320)

    # New York

    # Korea-Japan
    # corner_point = (120.242558, 47.140085)
    # corner_point2 = (144.665306, 28.960819)

    xdif = corner_point2[0] - corner_point[0]
    ydif = corner_point[1] - corner_point2[1]

    width = int(4000)
    height = int(width * (ydif / xdif))

    clipLayers(corner_point, corner_point2, width, height)
    collateData(width, height)

if __name__ == "__main__":
    main()
