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

# Completes the suitability calcualations and exports the resultant image.
# Side Effects: cleans the tmp/ folder
# TODO: Utilize a buffer as opposed to constantly re-reading data and doing it in place
def calcSuitability(width, height):
    r_buf = np.zeros((width, height))
    g_buf = np.zeros((width, height))

    # Add population to red channel
    if(draw_pop):
        print("Applying population to red buffer...", end = "")
        with rasterio.open("tmp/popdensity.tif") as dataset:
            layer_data = dataset.read(1, out_shape = (dataset.count, height, width), resampling = Resampling.bilinear)
            max = layer_data.max()
            co = 255 / max
            for i in range(width):
                for j in range(height):
                    if (layer_data[j,i] > 0):
                        r_buf[i][j] = (layer_data[j,i]*co)
        print("Done.")

    # Calculate suitability and accumulate on green channel
    for key in layers.keys():
        print("Applying suitability for {} to green buffer...".format(key), end = "")
        with rasterio.open("tmp/{}".format(key)) as dataset:
            need, contribution = layers[key]
            layer_data = dataset.read(1, out_shape = (dataset.count, height, width), resampling = Resampling.bilinear)
            for i in range(width):
                for j in range(height):
                    if (layer_data[j,i] > 0):
                        if (layer_data[j,i] >= need):
                            g_buf[i][j] += contribution
                        else:
                            g_buf[i][j] += (layer_data[j,i]/need) * contribution
        print("Done.")
    
    out_image = Image.new(mode = "RGB", size = (width, height))
    pixels = out_image.load()

    # Apply values to the out_image pixel map
    # If draw_water is True, values are clipped to that mask
    if(draw_water):
        print("Applying water mask & writing to pixels...", end = "")
        with rasterio.open("tmp/water_mask.tif") as dataset:
            layer_data = dataset.read(1, out_shape = (dataset.count, height, width), resampling = Resampling.nearest)
            for i in range(width):
                for j in range(height):
                    if (layer_data[j,i] == 1):
                        pixels[i,j] = (0, 0, 255)
                    else:
                        pixels[i,j] = (int(r_buf[i][j]), int(g_buf[i][j] * 255), 0)
        print("Done.")
    else:
        for i in range(width):
            for j in range(height):
                pixels[i,j] = (int(r_buf[i][j]), int(g_buf[i][j] * 255), 0)

    filename = "output/{}.png".format(str(time.time()).replace(".",""))
    print("Saving file {}...".format(filename), end = "")
    out_image.save(filename, format = "PNG")
    print("Done.")

    # Clean up temp files
    print("Cleaning up...", end = "")
    for key in layers.keys():
        os.remove("tmp/{}".format(key))
    print("Done.")

    return

# TODO : Docstring
def clipLayer(key, p1, p2, width, height):
    # Open the Geotiff
    dataset = rasterio.open("layers/{}".format(key))
    # Get the indeces of the geographic points
    y1, x1 = dataset.index(p1[0], p1[1])
    y2, x2 = dataset.index(p2[0], p2[1])
    window = rasterio.windows.Window(x1, y1, x2 - x1, y2 - y1)
    clip = dataset.read(window=window)
    # Define the metadata and save the image
    meta = dataset.meta
    print("({}, {}) ".format(window.width, window.height), end="")
    meta['width'], meta['height'] = window.width, window.height
    meta['transform'] = rasterio.windows.transform(window, dataset.transform)
    with rasterio.open("tmp/{}".format(key), 'w', **meta) as dst:
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
    print("| Animal Habitat Suitability Calculator  - Andrea Nosler |\n")
    print("Selected Layers: ")
    for key in layers.keys():
        print("   -{}".format(key))
    print("")
    corners = parseCoords()
    corner_point1, corner_point2 = corners[0], corners[1]
    xdif = corner_point2[0] - corner_point1[0]
    ydif = corner_point1[1] - corner_point2[1]
    height = int(width * (ydif / xdif))
    
    print("Clipping layers...")
    # Clip user-specified layers
    for key in layers.keys():
        print("   - Clipping {}...".format(key), end="")
        clipLayer(key, corner_point1, corner_point2, width, height)
        print("Done.")
    print("")

    # Clip the water mask
    #clipLayer("water_mask.tif", corner_point1, corner_point2, width, height)
    
    # If population layer not already clipped, clip to ensure it's availible
    if "pop_2020.tif" not in layers.keys():
        print("   - Clipping popdensity.tif...", end="")
        clipLayer("popdensity.tif", corner_point1, corner_point2, width, height)
        print("Done.")

    calcSuitability(width, height)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c1", "--corner_one", type = str, required = True)
    parser.add_argument("-c2", "--corner_two", type = str, required = True)
    parser.add_argument("-pn", "--population_need", type = float, required = False)
    parser.add_argument("-pc", "--population_contribution", type = float, required = False)
    parser.add_argument("-sn", "--soil_moisture_need", type = float, required = False)
    parser.add_argument("-sc", "--soil_moisture_contribution", type = float, required = False)
    parser.add_argument("-vn", "--vegetation_need", type = float, required = False)
    parser.add_argument("-vc", "--vegetation_contribution", type = float, required = False)
    parser.add_argument("-tn", "--temperature_need", type = int, required = False)
    parser.add_argument("-tc", "--temperature_contribution", type = int, required = False)
    parser.add_argument("-w", "--image_width", type = int, default = 4000, required = False)
    parser.add_argument("-d", "--debugging", type = bool, default = False, required = False)
    parser.add_argument("-dwm", "--draw_water_mask", type = bool, default = False, required = False)
    parser.add_argument("-dpl", "--draw_pop_layer", type = bool, default = True, required = False)
    
    args = parser.parse_args()
    c1 = args.corner_one
    c2 = args.corner_two
    width = args.image_width
    debugging = args.debugging
    draw_water = args.draw_water_mask
    draw_pop = args.draw_pop_layer

    # Determine which layers are to be analyzed
    layers = {}
    if args.population_need is not None and args.population_contribution is not None:
        layers["popdensity.tif"] = (args.population_need, args.population_contribution)
    if args.soil_moisture_need is not None and args.soil_moisture_contribution is not None:
        layers["soil_moisture.tif"] = (args.soil_moisture_need, args.soil_moisture_contribution)
    if args.vegetation_need is not None and args.vegetation_contribution is not None:
        layers["veg_EVI.tif"] = (args.vegetation_need, args.vegetation_contribution)
    if args.temperature_need is not None and args.temperature_contribution is not None:
        layers["day_LST.tif"] = (args.temperature_need, args.temperature_contribution)

    if not layers:
        print("No valid Need/Contribution pair submitted!")
        quit
    
    main()
