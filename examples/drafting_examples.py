"""

Dimension lines for documentation of cadquery designs

name: drafting.py
by:   Gumyr
date: June 28th 2021

desc: A class used to document cadquery designs by providing several methods
      that create objects that can be included into the design illustrating
      marked dimension_lines.

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
from math import sqrt, cos, sin, pi, floor, log2, gcd
from typing import overload, Union, Tuple, Literal
from numpy import arange, show_config
import cadquery as cq
from cq_warehouse.drafting import Draft

MM = 1
INCH = 25.4 * MM


center_diameter = 50 * MM
hole_measure = (5 / 8) * INCH
test_object = (
    cq.Workplane("XY")
    .rect(100 * MM, 3 * INCH, centered=False)
    .circle(center_diameter / 2)
    .translate((25, 25, 0))
    .extrude(10)
    .edges(">Z")
    .chamfer(3 * MM)
    .faces(">Z")
    .workplane()
    .center(85 * MM, 60 * MM)
    .hole(hole_measure)
)
center_pnt1 = cq.Vector(
    test_object.faces("<Z")
    .edges(cq.selectors.RadiusNthSelector(1))
    .vertices()
    .val()
    .toTuple()
)
center_pnt0 = center_pnt1 - cq.Vector(center_diameter, 0, 0)

hole_pnt0 = cq.Vector(
    test_object.faces(">Z")
    .edges(cq.selectors.RadiusNthSelector(0))
    .vertices()
    .val()
    .toTuple()
)
hole_pnt1 = hole_pnt0 + cq.Vector(hole_measure, 0, 0)

metric_drawing = Draft(decimal_precision=1)
imperial_drawing = Draft(units="imperial", decimal_precision=3)
imperial_fractional_drawing = Draft(
    font_size=4, units="imperial", unit_display="fraction"
)
diameter_measure = metric_drawing.dimension_line(path=(center_pnt0, center_pnt1))
length_measure = metric_drawing.extension_line(
    object_edge=test_object.faces("<Z").vertices("<Y").vals(), offset=10.0
)
width_measure = imperial_drawing.extension_line(
    object_edge=test_object.faces("<Z").vertices(">X").vals(), offset=10.0
)
hole_measure = imperial_fractional_drawing.extension_line(
    object_edge=(hole_pnt0, hole_pnt1), offset=-25.0
)
title_drawing = Draft(font_size=10, label_normal=(1, -1, 0))
title = title_drawing.text_box(
    label="cq_warehouse.drafting",
    location=cq.Vector(test_object.faces(">Z").vertices(">Y and <X").val().toTuple())
    + cq.Vector(0, 0, 25 * MM),
    justify="center",
)
chamfer_drawing = Draft(label_normal=(1, -1, 0))

chamfer_measure = chamfer_drawing.text_box(
    label="3mm Chamfer",
    location=cq.Vector(test_object.faces(">Z").vertices("<Y and <X").val().toTuple())
    + cq.Vector(0, 0, 15 * MM),
    point_at=test_object.faces(">Z").vertices("<Y and <X").val().toTuple(),
    justify="right",
)
# imperial_drawing = Draft(units="imperial")
# draft_obj = Draft(font_size=5, color=cq.Color(0.75, 0.25, 0.25))
# draft_obj_y = Draft(
#     font_size=8, color=cq.Color(0.75, 0.25, 0.25), label_normal=cq.Vector(0, -1, 0),
# )
# test0 = draft_obj.dimension_line(
#     path=((0, 0, 0), (40 * cos(pi / 6), -40 * sin(pi / 6), 0))
# )
# test1 = imperial_fractional_drawing.dimension_line(path=((-40, 0, 0), (40, 0, 0)))
# test2 = draft_obj_y.dimension_line(
#     label="test2",
#     path=cq.Edge.makeThreePointArc(
#         cq.Vector(-40, 0, 0),
#         cq.Vector(-40 * sqrt(2) / 2, 0, 40 * sqrt(2) / 2),
#         cq.Vector(0, 0, 40),
#     ),
# )
# test3 = draft_obj_y.dimension_line(
#     label="test3",
#     path=cq.Edge.makeThreePointArc(
#         cq.Vector(0, 0, 40),
#         cq.Vector(40 * sqrt(2) / 2, 0, 40 * sqrt(2) / 2),
#         cq.Vector(40, 0, 0),
#     ),
# )
# test4 = draft_obj.dimension_line(
#     label="test4",
#     path=cq.Edge.makeThreePointArc(
#         cq.Vector(-40, 0, 0), cq.Vector(0, -40, 0), cq.Vector(40, 0, 0)
#     ),
# )
# draft_obj_oblique = Draft(
#     font_size=8,
#     color=cq.Color(0.75, 0.25, 0.25),
#     label_normal=cq.Vector(0, -0.5, 1),
# )
# test5 = draft_obj_oblique.dimension_line(
#     label="test5",
#     path=cq.Edge.makeSpline(
#         [cq.Vector(-40, 0, 0), cq.Vector(35, 20, 10), cq.Vector(40, 0, 0)]
#     ),
# )
# test6 = draft_obj.dimension_line(
#     label="test6", arrow_heads=[False, True], path=(cq.Vector(40, 0, 0), (80, 0, 0))
# )
# test7 = draft_obj.dimension_line(
#     label="test7",
#     arrow_heads=[True, False],
#     path=((-80, 0, 0), cq.Vector(-40, 0, 0)),
# )
# test8 = draft_obj.dimension_line(
#     label="test8",
#     arrow_heads=[True, False],
#     path=(cq.Vertex.makeVertex(0, -80, 0), cq.Vertex.makeVertex(0, -40, 0)),
# )
# test9 = draft_obj.extension_line(
#     label="test9",
#     object_edge=(cq.Vertex.makeVertex(0, -80, 0), cq.Vertex.makeVertex(0, -40, 0)),
#     offset=10 * MM,
# )
# test10 = draft_obj.extension_line(
#     label="80mm", object_edge=((-40, 0, 0), (40, 0, 0)), offset=30 * MM,
# )
# test11 = draft_obj.text_box(label="two\nlines", location=(40, 40, 0))
# test12 = draft_obj.text_box(
#     label="look\nhere", location=(40, -40, 0), point_at=(0, -40, 0)
# )
# with cProfile.Profile() as pr:
#     test3 = dimension_line("test3",
#         path=cq.Edge.makeThreePointArc(
#             cq.Vector(0,0,40),
#             cq.Vector(40*sqrt(2)/2,0,40*sqrt(2)/2),
#             cq.Vector(40,0,0)
#         )
#     )
# stats = pstats.Stats(pr)
# stats.sort_stats(pstats.SortKey.TIME)
# stats.print_stats()


# If running from within the cq-editor, show the dimension_line lines
if "show_object" in locals():
    show_object(test_object, name="test_object")
    show_object(diameter_measure, name="diameter_measure")
    # show_object(dim_line1, name="dim_line1")
    # show_object(dim_line2, name="dim_line2")
    # show_object(dim_line3, name="dim_line3")
    show_object(length_measure, name="length_measure")
    show_object(width_measure, name="width_measure")
    show_object(hole_measure, name="hole_measure")
    show_object(title, name="title")
    show_object(chamfer_measure, name="chamfer_measure")
    # show_object(test0, name="test0")
    # show_object(test1, name="test1")
    # show_object(test2, name="test2")
    # show_object(test3, name="test3")
    # show_object(test4, name="test4")
    # show_object(test5, name="test5")
    # show_object(test6, name="test6")
    # show_object(test7, name="test7")
    # show_object(test8, name="test8")
    # show_object(test9, name="test9")
    # show_object(test10, name="test10")
    # show_object(test11, name="test11")
    # show_object(test12, name="test12")
