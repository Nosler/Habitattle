#
# Version: too-early-to-get-a-number
# Created by: Andrea Nosler
# Data collected from NASA's MODIS system
#

import os
import argparse
import time
import numpy as np
import rasterio
from rasterio.enums import Resampling
from PIL import Image

# Toggle-able output for Debugging
# Input: String
# Side Effect: Prints
def DEBUG(string):
    if(debugging):
        print("| DB:: ", string, " |")

# Compiles all layers together into resultant image for testing
def testCollateData(width, height):
    out_image = Image.new(mode = "RGB", size = (width, height), color = (int(0),int(0),int(255)))
    pixels = out_image.load()
    

    # First Run of Pop
    with rasterio.open("output/layer0.tif") as dataset:
        layer_data = dataset.read(1, out_shape = (dataset.count, height, width), resampling = Resampling.bilinear)
        max = layer_data.max()
        co = 255 / max
        for i in range(width):
            for j in range(height):
                if (layer_data[j,i] > 0):
                    pixels[i,j] = (int(layer_data[j,i]*co), int(0), int(0))

    # Second run for EVI
    with rasterio.open("output/layer2.tif") as dataset:
        layer_data = dataset.read(1, out_shape = (dataset.count, height, width), resampling = Resampling.bilinear)
        max = layer_data.max()
        co =  255 / max
        for i in range(width):
            for j in range(height):
                if (layer_data[j,i] > 0):
                    pixels[i,j] = (int(pixels[i,j][0]), int(layer_data[j,i]*co), int(0))

    filename = "{}.png".format(str(time.time()).replace(".",""))
    out_image.save(filename, format = "PNG")

    for i in range(3):
        os.remove("output/layer{}.tif".format(i))
    return

def calcSuitability(width, height):
    out_image = Image.new(mode = "RGB", size = (width, height))
    pixels = out_image.load()
    
    # Calculate Population-related Suitability
    if(pc > 0):
        with rasterio.open("output/layer0.tif") as dataset:
            layer_data = dataset.read(1, out_shape = (dataset.count, height, width), resampling = Resampling.bilinear)
            for i in range(width):
                for j in range(height):
                    if (layer_data[j,i] > 0):
                        if (layer_data[j,i] >= pn):
                            pixels[i,j] =  (0, int(pc * 255) + pixels[i,j][1], 0)
                        else:
                            pixels[i,j] = (0, int((layer_data[j,i]/pn) * pc * 255) + pixels[i,j][1], 0)

    if(sc > 0):
        with rasterio.open("output/layer1.tif") as dataset:
            layer_data = dataset.read(1, out_shape = (dataset.count, height, width), resampling = Resampling.bilinear)
            for i in range(width):
                for j in range(height):
                    if (layer_data[j,i] > 0):
                        if (layer_data[j,i] >= sn):
                            pixels[i,j] =  (0, int(sc * 255) + pixels[i,j][1], 0)
                        else:
                            pixels[i,j] = (0, int((layer_data[j,i]/sn) * sc * 255) + pixels[i,j][1], 0)

    if(vc > 0):
        with rasterio.open("output/layer2.tif") as dataset:
            layer_data = dataset.read(1, out_shape = (dataset.count, height, width), resampling = Resampling.bilinear)
            for i in range(width):
                for j in range(height):
                    if (layer_data[j,i] > 0):
                        if (layer_data[j,i] >= vn):
                            pixels[i,j] =  (0, int(vc * 255) + pixels[i,j][1], 0)
                        else:
                            pixels[i,j] = (0, int((layer_data[j,i]/vn) * vc * 255) + pixels[i,j][1], 0)

    # First Run of Pop
    with rasterio.open("output/layer0.tif") as dataset:
        layer_data = dataset.read(1, out_shape = (dataset.count, height, width), resampling = Resampling.bilinear)
        max = layer_data.max()
        co = 255 / max
        for i in range(width):
            for j in range(height):
                if (layer_data[j,i] > 0):
                    pixels[i,j] = ((int(layer_data[j,i]*co), pixels[i,j][1], 0))

    filename = "{}.png".format(str(time.time()).replace(".",""))
    out_image.save(filename, format = "PNG")

    for i in range(3):
        os.remove("output/layer{}.tif".format(i))
    return


# TODO : Docstring
def clipLayers(p1, p2, width, height):
    layers = ['layers/pop_2020.tif', 'layers/soil_moisture.tif', 'layers/veg_EVI.tif']
    for i in range(len(layers)):
        # Open the Geotiff
        dataset = rasterio.open(layers[i])

        # Get the indeces of the geographic points
        y1, x1 = dataset.index(p1[0], p1[1])
        y2, x2 = dataset.index(p2[0], p2[1])

        window = rasterio.windows.Window(x1, y1, x2 - x1, y2 - y1)
        clip = dataset.read(window=window)

        # Define the metadata and save the image
        meta = dataset.meta
        DEBUG("ExportedDataLayers --- WIDTH = {}, HEIGHT = {}".format(window.width,window.height))
        meta['width'], meta['height'] = window.width, window.height
        meta['transform'] = rasterio.windows.transform(window, dataset.transform)
        with rasterio.open("output/layer{}.tif".format(i), 'w', **meta) as dst:
            dst.write(clip)

# Parses the command-line arguments for the coordinates
def parseCoords():
    c1string = c1.replace("(","").replace(")","").split(",")
    c2string = c2.replace("(","").replace(")","").split(",")
    lat1 = float(c1string[0])
    lon1 = float(c1string[1])
    lat2 = float(c2string[0])
    lon2 = float(c2string[1])

    # Lat,Lon input becomes Lon,Lat as it more closely resembles (x,y)
    if(lat1 > lat2):
        if(lon1 < lon2):
            tl_corner = (lon1, lat1)
            br_corner = (lon2, lat2)
        else:
            tl_corner = (lon2, lat1)
            br_corner = (lon1, lat1)
    else:
        if(lon2 < lon1):
            br_corner = (lon2, lat2)
            tl_corner = (lon1, lat1)
        else:
            tl_corner = (lon1, lat2)
            br_corner = (lon2, lat1)

    return (tl_corner, br_corner)

def main():
    print("///////////////////////////////////////////////////////////////////")
    print("/               Animal Habitat Suitability Calculator                 /")
    print("/                  Authored by Andrea Nosler                      /")
    print("///////////////////////////////////////////////////////////////////\n")

    corners = parseCoords()
    corner_point1, corner_point2 = corners[0], corners[1]
    xdif = corner_point2[0] - corner_point1[0]
    ydif = corner_point1[1] - corner_point2[1]

    height = int(width * (ydif / xdif))

    clipLayers(corner_point1, corner_point2, width, height)
    calcSuitability(width, height)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c1", "--corner_one", type = str, required = True)
    parser.add_argument("-c2", "--corner_two", type = str,required = True)
    parser.add_argument("-pn", "--population_need", type = float, required = True)
    parser.add_argument("-pc", "--population_contribution", type = float, required = True)
    parser.add_argument("-sn", "--soil_moisture_need", type = float, required = True)
    parser.add_argument("-sc", "--soil_moisture_contribution", type = float, required = True)
    parser.add_argument("-vn", "--vegetation_need", type = float, required = True)
    parser.add_argument("-vc", "--vegetation_contribution", type = float, required = True)
    parser.add_argument("-w", "--image_width", type = int, default = 500, required = False)
    parser.add_argument("-d", "--debugging", type = bool, default = False, required = False)
    args = parser.parse_args()
    c1 = args.corner_one
    c2 = args.corner_two
    pn = args.population_need
    pc = args.population_contribution
    sn = args.soil_moisture_need
    sc = args.soil_moisture_contribution
    vn = args.vegetation_need
    vc = args.vegetation_contribution
    width = args.image_width
    debugging = args.debugging
    main()
