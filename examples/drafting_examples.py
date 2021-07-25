"""

An example of a documented cadquery part with dimension lines

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


def building_a_mystery() -> cq.Workplane:
    """
    Create the mystery part that will be documented with mixed metric and imperial sizes
    emulating an object being imported from a STEP file.
    """
    mystery_object = (
        cq.Workplane("XY")
        .hLineTo(100 * MM)
        .vLineTo(3 * INCH)
        .sagittaArc((0, 3 * INCH), -1 * INCH)
        .close()
        .extrude(10 * MM)
        .edges(">Z")
        .chamfer(3 * MM)
        .faces(">Z")
        .workplane()
        .center(50 * MM, 1.5 * INCH)
        .hole(50 * MM)
        .center(0, 45 * MM)
        .hole((37 / 64) * INCH)
    )
    return mystery_object


#
# Create an instance of the mystery object
mystery_object = building_a_mystery()

#
# Start by adding a title to the drawing with a callout where a single Vertex
# (relative to a corner of the part) defines the origin of the callout.
drawing_title_callout = Draft(font_size=10, label_normal=(1, -1, 0))
title_callout = drawing_title_callout.callout(
    label="cq_warehouse.drafting",
    origin=mystery_object.faces(">Z").vertices("<Y and <X").val()
    + (0, 3 * INCH, 25 * MM),
    justify="center",
)

#
# When documenting dimension_lines in the drawing, set the number of decimal
# points in metric dimensions to one - use the options for the other inputs.
metric_drawing = Draft(decimal_precision=1)

#
# Extract the vertices from the bottom edge along the x-axis and use them
# to define the object_edge of an extension line. The offset is the distance
# from the part edge to the dimension line. A tolerance is specified as
# a separate + and - values.
length_dimension_line = metric_drawing.extension_line(
    object_edge=mystery_object.faces("<Z").vertices("<Y").vals(),
    offset=10.0,
    tolerance=(+0.2, -0.1),
)

#
# After some experimentation, the width was determined to be an imperial dimension_line
# so create an instance of the Draft class for imperial dimension_lines precise to a
# thousandths of an inch. The tolerance is specified with a single ± float value.
imperial_drawing = Draft(units="imperial", decimal_precision=3)
width_dimension_line = imperial_drawing.extension_line(
    object_edge=mystery_object.faces("<Z").vertices(">X").vals(),
    offset=(1 / 2) * INCH,
    tolerance=0.001 * INCH,
)

#
# To document the two holes the sizes need to be extracted as a circle has only one
# vertex and can only be used to locate the hole. The `circle` edge selector is
# used to extract the circles from the mystery object and with the help of a sorted set
# the four unique radii of the object are exacted.
(bolt_radius, bearing_radius, upper_edge_radius, lower_edge_radius) = sorted(
    {round(circle.radius(), 7) for circle in mystery_object.edges("%circle").vals()}
)


#
# To locate a dimension line for the central hole, a hole vertex needs to
# found. The RadiusNthSelector(1) selector is looking for circles from the ordered
# list of radii (as was created above) so the `1` input refers to the bearing_radius.
# Note that `vertices().val()` is returning a single cq.Vertex object.
bearing_point0 = (
    mystery_object.faces(">Z").edges(cq.selectors.RadiusNthSelector(1)).vertices().val()
)
# Knowing the size of the hole, the second vertex is easily determined
bearing_point1 = bearing_point0 + (bearing_radius * 2, 0, 0)

#
# Use a dimension_line to document an internal dimension
bearing_dimension_line = metric_drawing.dimension_line(
    path=[bearing_point0, bearing_point1]
)

#
# Use the same procedure to determine the location of the bolt hole
bolt_hole_point0 = (
    mystery_object.faces(">Z").edges(cq.selectors.RadiusNthSelector(0)).vertices().val()
)
bolt_hole_point1 = bolt_hole_point0 + (bolt_radius * 2, 0, 0)
#
# The bolt hole is an imperial size so the fractional display is needed
bolt_dimension_line = Draft(
    font_size=4, units="imperial", number_display="fraction"
).extension_line(
    object_edge=[bolt_hole_point0, bolt_hole_point1], offset=(1 / 2) * INCH
)

#
# Create the tapping instructions as a callout with a tail composed of two Vertices
# .. note that addition and substraction methods have been added to the cq.Vertex class
tap_instructions = Draft(label_normal=(0, 0, 1), font_size=5).callout(
    label="tap to 5/8-18 NF",
    tail=[
        bolt_hole_point0 + (-(1 / 2) * INCH, -(3 / 4) * INCH, (1 / 4) * INCH),
        bolt_hole_point0 + (-(1 / 4) * INCH, -(3 / 4) * INCH, (1 / 4) * INCH),
        bolt_hole_point0,
    ],
    justify="right",
)

#
# Create another callout with a description of the chamfer. In this
# case the tail is defined as an cq.Edge object (a spline in this case but any
# Edge or Wire object can be used) which is also supported with all of the
# dimension_line and extension_line paths.
chamfer_size = lower_edge_radius - upper_edge_radius
chamfer_drawing = Draft(label_normal=(1, 0, 0))
chamfer_callout = chamfer_drawing.callout(
    label=str(chamfer_size) + "mm chamfer",
    tail=cq.Edge.makeSpline(
        listOfVector=[
            (
                mystery_object.faces(">Z").vertices("<Y and <X").val()
                + (0, 15 * MM, 15 * MM)
            ).toVector(),
            mystery_object.faces(">Z").vertices("<Y and <X").val().toVector(),
        ],
        tangents=[cq.Vector(0, -1, 0), cq.Vector(0, 0, -1)],
    ),
    justify="left",
)

#
# Finally, dimension the arc that the part's edge sweeps in degrees
curved_edge = mystery_object.faces(">Z").edges(cq.selectors.RadiusNthSelector(2)).val()
arc_extension_line = metric_drawing.extension_line(
    object_edge=curved_edge, offset=10, label_angle=True
)

# If running from within the cq-editor, show the dimension_line lines
if "show_object" in locals():
    show_object(mystery_object, name="mystery_object")
    show_object(title_callout, name="title_callout")
    show_object(length_dimension_line, name="length_dimension_line")
    show_object(width_dimension_line, name="width_dimension_line")
    show_object(bearing_dimension_line, name="bearing_dimension_line")
    show_object(bolt_dimension_line, name="bolt_diameter")
    show_object(tap_instructions, name="tap_instructions")
    show_object(chamfer_callout, name="chamfer_callout")
    show_object(arc_extension_line, name="arc_extension_line")
