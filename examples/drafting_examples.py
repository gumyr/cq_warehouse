"""

An example of a documented cadquery part with many dimension lines

name: drafting_examples.py
by:   Gumyr
date: June 28th 2021

license:

    Copyright 2021 Gumyr

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

"""
import cadquery as cq
from cq_warehouse.drafting import Draft

MM = 1
INCH = 25.4 * MM

#
# Create the part that will be documented with mixed metric and imperial sizes
center_diameter = 50 * MM
hole_diameter = (37 / 64) * INCH
test_object = (
    cq.Workplane("XY")
    .rect(100 * MM, 3 * INCH, centered=False)
    .circle(center_diameter / 2)
    .translate((25 * MM, 25 * MM, 0))
    .extrude(10 * MM)
    .edges(">Z")
    .chamfer(3 * MM)
    .faces(">Z")
    .workplane()
    .center(85 * MM, 60 * MM)
    .hole(hole_diameter)
)

#
# Extract some key vertices from the part as inputs to drafting methods.
# Circles only have one vertex so the extracted value will be combined
# with the diameter to define the other side of the circle.
# .. note these are type cq.Vertex are located at the bottom of the chamfer
center_pnt1 = (
    test_object.faces(">Z[-1]")
    .edges(cq.selectors.RadiusNthSelector(1))
    .vertices()
    .val()
)
center_pnt0 = center_pnt1 - (center_diameter, 0, 0)

hole_pnt0 = (
    test_object.faces(">Z").edges(cq.selectors.RadiusNthSelector(0)).vertices().val()
)
hole_pnt1 = hole_pnt0 + (hole_diameter, 0, 0)

#
# Create an instance of the Draft class which specifies the text in the tapping instructions
hole_drawing = Draft(label_normal=(0, 0, 1), font_size=5)
#
# Create the tappping instructions (a cq.Assembly) as a callout with a tail composed of two Vertices
# .. note that addition and substraction methods have been added to the cq.Vertex class
hole_instructions = hole_drawing.callout(
    label="tap to 5/8-18 NF",
    tail=[
        hole_pnt0 + (-1 * INCH, 1 * INCH, (1 / 2) * INCH),
        hole_pnt0 + (-(1 / 2) * INCH, 1 * INCH, (1 / 2) * INCH),
        hole_pnt0,
    ],
    justify="right",
)
imperial_fractional_drawing = Draft(
    font_size=2, units="imperial", number_display="fraction"
)
hole_diameter = imperial_fractional_drawing.extension_line(
    object_edge=[hole_pnt0, hole_pnt1], offset=-25.0
)

#
# Create an instance of the Draft class for metric measurements
metric_drawing = Draft(decimal_precision=1)
#
# Extract the vertices from the bottom edge along the x-axis and use them
# to define the object_edge of an extension line. The offset is the distance
# from the part edge to the dimension line. The tolerance is specified as
# a separate + and - values.
length_measure = metric_drawing.extension_line(
    object_edge=test_object.faces("<Z").vertices("<Y").vals(),
    offset=10.0,
    tolerance=(+0.2, -0.1),
)
#
# Use a dimension_line to document an internal dimension
diameter_measure = metric_drawing.dimension_line(path=[center_pnt0, center_pnt1])

#
# Create an instance of the Draft class for imperial measurements precise to a
# thousandths of an inch. The tolerance is specified with a single ± float value.
imperial_drawing = Draft(units="imperial", decimal_precision=3)
width_measure = imperial_drawing.extension_line(
    object_edge=test_object.faces("<Z").vertices(">X").vals(),
    offset=(1 / 2) * INCH,
    tolerance=0.001 * INCH,
)

#
# Title the drawing with a callout where a single point tail defines
# the origin of the callout. Note the callout origin is of type Vertex and
# is specified relative to a corner of the part.
title_drawing = Draft(font_size=10, label_normal=(1, -1, 0))
title = title_drawing.callout(
    label="cq_warehouse.drafting",
    tail=test_object.faces(">Z").vertices(">Y and <X").val() + (0, 0, 25 * MM),
    justify="center",
)

#
# Finalling, create another callout with a description of the chamfer. In this
# case the tail is defined as an cq.Edge object (a spline in this case but any
# Edge or Wire object can be used) which is also supported with all of the
# dimension_line and extension_line paths.
chamfer_drawing = Draft(label_normal=(1, -1, 0))
chamfer_measure = chamfer_drawing.callout(
    label="3mm chamfer",
    tail=cq.Edge.makeSpline(
        listOfVector=[
            (
                test_object.faces(">Z").vertices("<Y and <X").val()
                + (0, 25 * MM, 15 * MM)
            ).toVector(),
            test_object.faces(">Z").vertices("<Y and <X").val().toVector(),
        ],
        tangents=[cq.Vector(0, -1, 0), cq.Vector(0, 0, -1)],
    ),
    justify="left",
)

# If running from within the cq-editor, show the dimension_line lines
if "show_object" in locals():
    show_object(test_object, name="test_object")
    show_object(length_measure, name="length_measure")
    show_object(width_measure, name="width_measure")
    show_object(diameter_measure, name="diameter_measure")
    show_object(hole_diameter, name="hole_diameter")
    show_object(hole_instructions, name="hole_instructions")
    show_object(title, name="title")
    show_object(chamfer_measure, name="chamfer_measure")
