#!/usr/bin/python

"""pixel2svg - Convert pixel art to SVG

   Copyright 2011 Florian Berger <fberger@florian-berger.de>
   Copyright 2015 Cyrille Chopelet
   Copyright 2020 Ale Rimoldi <ale@graphicslab.org>
   Copyright 2021 Dirk Jagdmann <doj@cubic.org>
"""

# pixel2svg is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# pixel2svg is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pixel2svg.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import sys
import os.path
import re

from PIL import Image

import svgwrite
from svgwrite.extensions import Inkscape

import numpy as np
from python_tsp.distances import great_circle_distance_matrix
from python_tsp.heuristics import solve_tsp_simulated_annealing

VERSION = "0.6.0"

# some constants
RED = 0
GREEN = 1
BLUE = 2
ALPHA = 3

class BreakEx(Exception): pass

# compare two RGB colors @p a and @p b for similarity.
# the @p sensitivity parameter configures how sensitive the color comparison is.
# larger values for @p sensitivity will make the comparison less sensitive.
def similar_color(a, b, sensitivity):
    if a == b:
        return True
    r = (a[RED]   - b[RED])   ** 2
    g = (a[GREEN] - b[GREEN]) ** 2
    b = (a[BLUE]  - b[BLUE])  ** 2
    return r+g+b < sensitivity

# SVG color keywords
# https://www.w3.org/TR/SVG11/types.html#ColorKeywords
svgcolors = {
'aliceblue': (240, 248, 255),
'antiquewhite': (250, 235, 215),
'aqua': ( 0, 255, 255),
'aquamarine': (127, 255, 212),
'azure': (240, 255, 255),
'beige': (245, 245, 220),
'bisque': (255, 228, 196),
'black': ( 0, 0, 0),
'blanchedalmond': (255, 235, 205),
'blue': ( 0, 0, 255),
'blueviolet': (138, 43, 226),
'brown': (165, 42, 42),
'burlywood': (222, 184, 135),
'cadetblue': ( 95, 158, 160),
'chartreuse': (127, 255, 0),
'chocolate': (210, 105, 30),
'coral': (255, 127, 80),
'cornflowerblue': (100, 149, 237),
'cornsilk': (255, 248, 220),
'crimson': (220, 20, 60),
'cyan': ( 0, 255, 255),
'darkblue': ( 0, 0, 139),
'darkcyan': ( 0, 139, 139),
'darkgoldenrod': (184, 134, 11),
'darkgray': (169, 169, 169),
'darkgreen': ( 0, 100, 0),
'darkgrey': (169, 169, 169),
'darkkhaki': (189, 183, 107),
'darkmagenta': (139, 0, 139),
'darkolivegreen': ( 85, 107, 47),
'darkorange': (255, 140, 0),
'darkorchid': (153, 50, 204),
'darkred': (139, 0, 0),
'darksalmon': (233, 150, 122),
'darkseagreen': (143, 188, 143),
'darkslateblue': ( 72, 61, 139),
'darkslategray': ( 47, 79, 79),
'darkslategrey': ( 47, 79, 79),
'darkturquoise': ( 0, 206, 209),
'darkviolet': (148, 0, 211),
'deeppink': (255, 20, 147),
'deepskyblue': ( 0, 191, 255),
'dimgray': (105, 105, 105),
'dimgrey': (105, 105, 105),
'dodgerblue': ( 30, 144, 255),
'firebrick': (178, 34, 34),
'floralwhite': (255, 250, 240),
'forestgreen': ( 34, 139, 34),
'fuchsia': (255, 0, 255),
'gainsboro': (220, 220, 220),
'ghostwhite': (248, 248, 255),
'gold': (255, 215, 0),
'goldenrod': (218, 165, 32),
'gray': (128, 128, 128),
'grey': (128, 128, 128),
'green': ( 0, 128, 0),
'greenyellow': (173, 255, 47),
'honeydew': (240, 255, 240),
'hotpink': (255, 105, 180),
'indianred': (205, 92, 92),
'indigo': ( 75, 0, 130),
'ivory': (255, 255, 240),
'khaki': (240, 230, 140),
'lavender': (230, 230, 250),
'lavenderblush': (255, 240, 245),
'lawngreen': (124, 252, 0),
'lemonchiffon': (255, 250, 205),
'lightblue': (173, 216, 230),
'lightcoral': (240, 128, 128),
'lightcyan': (224, 255, 255),
'lightgoldenrodyellow': (250, 250, 210),
'lightgray': (211, 211, 211),
'lightgreen': (144, 238, 144),
'lightgrey': (211, 211, 211),
'lightpink': (255, 182, 193),
'lightsalmon': (255, 160, 122),
'lightseagreen': ( 32, 178, 170),
'lightskyblue': (135, 206, 250),
'lightslategray': (119, 136, 153),
'lightslategrey': (119, 136, 153),
'lightsteelblue': (176, 196, 222),
'lightyellow': (255, 255, 224),
'lime': ( 0, 255, 0),
'limegreen': ( 50, 205, 50),
'linen': (250, 240, 230),
'magenta': (255, 0, 255),
'maroon': (128, 0, 0),
'mediumaquamarine': (102, 205, 170),
'mediumblue': ( 0, 0, 205),
'mediumorchid': (186, 85, 211),
'mediumpurple': (147, 112, 219),
'mediumseagreen': ( 60, 179, 113),
'mediumslateblue': (123, 104, 238),
'mediumspringgreen': ( 0, 250, 154),
'mediumturquoise': ( 72, 209, 204),
'mediumvioletred': (199, 21, 133),
'midnightblue': ( 25, 25, 112),
'mintcream': (245, 255, 250),
'mistyrose': (255, 228, 225),
'moccasin': (255, 228, 181),
'navajowhite': (255, 222, 173),
'navy': ( 0, 0, 128),
'oldlace': (253, 245, 230),
'olive': (128, 128, 0),
'olivedrab': (107, 142, 35),
'orange': (255, 165, 0),
'orangered': (255, 69, 0),
'orchid': (218, 112, 214),
'palegoldenrod': (238, 232, 170),
'palegreen': (152, 251, 152),
'paleturquoise': (175, 238, 238),
'palevioletred': (219, 112, 147),
'papayawhip': (255, 239, 213),
'peachpuff': (255, 218, 185),
'peru': (205, 133, 63),
'pink': (255, 192, 203),
'plum': (221, 160, 221),
'powderblue': (176, 224, 230),
'purple': (128, 0, 128),
'red': (255, 0, 0),
'rosybrown': (188, 143, 143),
'royalblue': ( 65, 105, 225),
'saddlebrown': (139, 69, 19),
'salmon': (250, 128, 114),
'sandybrown': (244, 164, 96),
'seagreen': ( 46, 139, 87),
'seashell': (255, 245, 238),
'sienna': (160, 82, 45),
'silver': (192, 192, 192),
'skyblue': (135, 206, 235),
'slateblue': (106, 90, 205),
'slategray': (112, 128, 144),
'slategrey': (112, 128, 144),
'snow': (255, 250, 250),
'springgreen': ( 0, 255, 127),
'steelblue': ( 70, 130, 180),
'tan': (210, 180, 140),
'teal': ( 0, 128, 128),
'thistle': (216, 191, 216),
'tomato': (255, 99, 71),
'turquoise': ( 64, 224, 208),
'violet': (238, 130, 238),
'wheat': (245, 222, 179),
'white': (255, 255, 255),
'whitesmoke': (245, 245, 245),
'yellow': (255, 255, 0),
'yellowgreen': (154, 205, 50),
}

# find a SVG color name for a RGB tuple @p c.
# based on https://stackoverflow.com/questions/9694165/convert-rgb-color-to-english-color-name-like-green-with-python
def color_name(c):
    min_colors = {}
    for name, col in svgcolors.items():
        r = (c[RED]   - col[RED])   ** 2
        g = (c[GREEN] - col[GREEN]) ** 2
        b = (c[BLUE]  - col[BLUE])  ** 2
        min_colors[r + g + b] = name
    return min_colors[min(min_colors.keys())]

# convert a SVG coordinate to a float number
def svg2float(c):
    return float(re.sub('[^.\-\d]', '', str(c)))

if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser(description="Convert pixel art to SVG")

    argument_parser.add_argument("imagefile",
                                 help="The image file to convert")

    argument_parser.add_argument("--version",
                                 action="version",
                                 version=VERSION,
                                 help="Display the program version")

    argument_parser.add_argument("--overlap",
                                 action="store_true",
                                 help="If given, overlap vector squares by 1 unit")

    argument_parser.add_argument("--squaresize",
                                 type=int,
                                 default=40,
                                 help="Width and height of vector squares in pixels, default: 40")

    # https://www.w3.org/TR/SVG2/coords.html#Units
    # https://www.w3.org/TR/css-values-3/#length-value
    argument_parser.add_argument("--unit",
                                 default='px',
                                 choices=['em','ex','cm','mm','Q','in','pc','pt','px'],
                                 help="set SVG unit used with --squaresize, default: px")

    argument_parser.add_argument("--combine",
                                 action="store_true",
                                 help="If given, combine similar pixels into larger rectangles")

    argument_parser.add_argument("--similar",
                                 type=int,
                                 default=0,
                                 help="Configure a numeric value to find a similar color. Larger values make the comparison less sensitive.")

    argument_parser.add_argument("--optimize",
                                 action="store_true",
                                 help="Optimize the order of SVG rectangles to minimize the path.")

    argument_parser.add_argument("--reverse",
                                 action="store_true",
                                 help="Reverse the order of SVG rectangles.")

    arguments = argument_parser.parse_args()
    unit = arguments.unit

    print("pixel2svg {0}".format(VERSION))
    print("read: {0}".format(arguments.imagefile))

    image = Image.open(arguments.imagefile)
    image = image.convert("RGBA")

    # width and height of the image in pixels
    (image_width, image_height) = image.size

    print("input image size: {0}x{1} px".format(image_width, image_height))
    print("  SVG image size: {0}x{1} {2}".format(image_width * arguments.squaresize, image_height * arguments.squaresize, unit))

    rgb_values = list(image.getdata())

    svg_filename = os.path.splitext(arguments.imagefile)[0] + ".svg"
    svgdoc = svgwrite.Drawing(filename=svg_filename,
                              size=(str(image_width * arguments.squaresize)+unit,
                                    str(image_height * arguments.squaresize)+unit))
    inkscape = Inkscape(svgdoc)

    # If --overlap is given, use a slight overlap to prevent inaccurate SVG rendering
    overlap = arguments.overlap
    if overlap:
        overlap = 1
    else:
        overlap = 0
    print("overlap: {0} {1}".format(overlap, unit))

    # a dictionary of rectangles
    # key: rgba tuple
    # value: list of SVG rectangle objects
    rectangles = {}

    # iterate over all pixels and create SVG rectangles mapped by the pixel's color
    rectangle_num = 0
    Y = 0 # Y coordinate of current pixel
    while Y < image_height:

        #print("Processing pixel row {0} of {1}".format(Y + 1, image_height))

        X = 0 # X coordinate of current pixel
        while X < image_width:

            rgba_tuple = rgb_values[Y * image_width + X]

            # Omit transparent pixels
            w = 1 # width of rectangle
            alpha = rgba_tuple[ALPHA]
            if alpha > 0:
                h = 1 # height of rectangle

                # combine pixels?
                if arguments.combine:
                    # find pixels with same color horizontally
                    while X+w < image_width:
                        px = rgb_values[Y * image_width + X + w]
                        if not similar_color(px, rgba_tuple, arguments.similar):
                            break
                        w += 1
                    # check if pixels below have the same color and can be combined?
                    try:
                        while Y+h < image_height:
                            # check if the next row of pixels has a similar color
                            i = 0
                            while i < w:
                                px = rgb_values[(Y+h) * image_width + X + i]
                                if not similar_color(px, rgba_tuple, arguments.similar):
                                    raise BreakEx
                                i += 1
                                # the color is similar.
                                # set the alpha value of all these pixels to 0, so they will not be processed any more.
                            i = 0
                            while i < w:
                                # the pixel is a python tuple and constant.
                                # create a new tuple with alpha=0 and assign to the pixel array.
                                px = rgb_values[(Y+h) * image_width + X + i]
                                rgb_values[(Y+h) * image_width + X + i] = (px[RED], px[GREEN], px[BLUE], 0)
                                i += 1

                            h += 1

                    except BreakEx:
                        pass
                    #print("combine: {0},{1} {2},{3}".format(X,Y,w,h))

                rectangle_num += 1
                rectangle_posn = (str(X * arguments.squaresize)+unit,
                                  str(Y * arguments.squaresize)+unit)
                rectangle_size = (str(w * arguments.squaresize + overlap)+unit,
                                  str(h * arguments.squaresize + overlap)+unit)
                rectangle_fill = svgwrite.rgb(rgba_tuple[0], rgba_tuple[1], rgba_tuple[2])
                rect = 1

                if alpha == 255:
                    rect = svgdoc.rect(insert=rectangle_posn,
                                       size=rectangle_size,
                                       fill=rectangle_fill)
                else:
                    rect = svgdoc.rect(insert=rectangle_posn,
                                       size=rectangle_size,
                                       fill=rectangle_fill,
                                       opacity=alpha/float(255))

                rectangles.setdefault(rgba_tuple, []).append(rect)

            X += w

        Y += 1

    print("used {0} rectangles".format(rectangle_num))
    print("found {0} colors".format(len(rectangles)))

    # output rectangles on a separate layer for each color
    layer_num = 0
    for rgba_tuple in rectangles:
        name = color_name(rgba_tuple)
        rectangles_num = len(rectangles[rgba_tuple])
        print("  "+name+" for "+str(rgba_tuple)+" with "+str(rectangles_num)+" rectangles")
        layer = inkscape.layer(label=name, locked=True)
        svgdoc.add(layer)

        # use travelling salesman algorithm to calculate a good path between the rectangles?
        # the command line option to optimize the rectangle order needs to be enabled,
        # and there need to be at least 3 rectangles.
        if arguments.optimize and rectangles_num > 2:

            # 1st step: create a list with rectangle coordinates
            coord = []
            for rect in rectangles[rgba_tuple]:
                coord.append([svg2float(rect.attribs['x']), svg2float(rect.attribs['y'])])
            # 2nd step: create a distance matrix from the coordinates
            distance_matrix = great_circle_distance_matrix(np.array(coord))
            distance_matrix[:, 0] = 0 # set first column to 0, this will not require a closed path
            # 3rd step: find a good path
            permutation, distance = solve_tsp_simulated_annealing(distance_matrix)
            # 4th step: add SVG rectangles to the layer
            if arguments.reverse:
                permutation.reverse()
            for idx in permutation:
                layer.add(rectangles[rgba_tuple][idx])
        else:
            rect_list = rectangles[rgba_tuple]
            if arguments.reverse:
                rect_list.reverse()
            for rect in rect_list:
                layer.add(rect)

    print("write: {0}".format(svgdoc.filename))
    svgdoc.save(pretty=True)

    f = open(svg_filename, 'a')
    f.writelines([
        "<!-- created by pixel2svg.py -->\n",
        "<!-- https://github.com/doj/pixel2svg-fork -->\n",
        ])
    f.close()
    sys.exit(0)
