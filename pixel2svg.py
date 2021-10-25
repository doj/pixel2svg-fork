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

from PIL import Image

import svgwrite
from svgwrite.extensions import Inkscape

VERSION = "0.6.0"

# TODO: better similarity comparison
def similar_pixel(a, b):
    return a == b

if __name__ == "__main__":

    argument_parser = argparse.ArgumentParser(description="Convert pixel art to SVG")

    argument_parser.add_argument("imagefile",
                                 help="The image file to convert")

    argument_parser.add_argument("--overlap",
                                 action="store_true",
                                 help="If given, overlap vector squares by 1px")

    argument_parser.add_argument("--version",
                                 action="version",
                                 version=VERSION,
                                 help="Display the program version")

    argument_parser.add_argument("--squaresize",
                                 type=int,
                                 default=40,
                                 help="Width and height of vector squares in pixels, default: 40")

    argument_parser.add_argument("--combineh",
                                 action="store_true",
                                 help="If given, combine similar pixels horizontally")

    arguments = argument_parser.parse_args()

    print("pixel2svg {0}".format(VERSION))
    print("Reading image file '{0}'".format(arguments.imagefile))

    image = Image.open(arguments.imagefile)

    print("Converting image to RGBA")

    image = image.convert("RGBA")

    (width, height) = image.size

    print("Image is {0}x{1}".format(width, height))

    rgb_values = list(image.getdata())

    print("Read {0} pixels".format(len(rgb_values)))

    svgdoc = svgwrite.Drawing(filename=os.path.splitext(arguments.imagefile)[0] + ".svg",
                              size=("{0}px".format(width * arguments.squaresize),
                                    "{0}px".format(height * arguments.squaresize)))
    inkscape = Inkscape(svgdoc)
    top_layer = inkscape.layer(label="Top Layer", locked=True)
    svgdoc.add(top_layer)

    # If --overlap is given, use a slight overlap to prevent inaccurate SVG rendering
    overlap = arguments.overlap
    if overlap:
        overlap = 1
    else:
        overlap = 0
    print("Will use an square overlap of {0}px".format(overlap))

    rectangle_num = 0
    Y = 0
    while Y < height:

        #print("Processing pixel row {0} of {1}".format(Y + 1, height))

        X = 0
        while X < width:

            #rgba_tuple = rgb_values.pop(0)
            rgba_tuple = rgb_values[Y * width + X]

            # Omit transparent pixels
            x = 1
            alpha = rgba_tuple[3]
            if alpha > 0:

                # combine horizontal pixels?
                if arguments.combineh:
                    while X+x < width:
                        px = rgb_values[Y * width + X + x]
                        if not similar_pixel(px, rgba_tuple):
                            break
                        x += 1
                    if x > 1:
                        print("combine {0},{1} {2},{3}".format(X,Y,x,1))

                rectangle_num += 1
                rectangle_posn = ("{0}px".format(X * arguments.squaresize),
                                  "{0}px".format(Y * arguments.squaresize))
                rectangle_size = ("{0}px".format(x * arguments.squaresize + overlap),
                                  "{0}px".format(arguments.squaresize + overlap))
                rectangle_fill = svgwrite.rgb(rgba_tuple[0], rgba_tuple[1], rgba_tuple[2])

                if alpha == 255:
                    top_layer.add(svgdoc.rect(insert=rectangle_posn,
                                           size=rectangle_size,
                                           fill=rectangle_fill))
                else:
                    top_layer.add(svgdoc.rect(insert=rectangle_posn,
                                           size=rectangle_size,
                                           fill=rectangle_fill,
                                           opacity=alpha/float(255)))

            X += x

        Y += 1

    print("used {0} rectangles".format(rectangle_num))
    print("Saving SVG to '{0}'".format(svgdoc.filename))

    svgdoc.save()
    sys.exit(0)
