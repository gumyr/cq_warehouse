"""

An example of a documented a cadquery part with diagonal lines

name: drafting_dimension_diagonal.py
by:   Gumyr
date: July 20th 2022

license:

    Copyright 2022 Gumyr

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

# Create an object with two diagonal edges and extract them
target = (
    cq.Workplane("XY").sketch().trapezoid(80, 60, 120, angle=180).finalize().extrude(-1)
)
top_left_edge = target.faces(">Z").edges("<X").val()
top_right_edge = target.faces(">Z").edges(">X").val()

# Initialize the Drafting class - with a new custom extension_gap
metric_drawing = Draft(decimal_precision=1, extension_gap=2)

# Create a diagonal extension line
left_extension_line = metric_drawing.extension_line(
    object_edge=top_left_edge, offset=10
)

# Create two perpendicular extension lines
right_horizontal_extension_line = metric_drawing.extension_line(
    object_edge=top_right_edge,
    offset=40,
    project_line=(1, 0),
)
right_vertical_extension_line = metric_drawing.extension_line(
    object_edge=top_right_edge,
    offset=25,
    project_line=(0, 1),
)

# If running from within the cq-editor, show the extension lines
if "show_object" in locals():
    show_object(target, name="target")
    show_object(top_left_edge, name="bottom_left_edge")
    show_object(top_right_edge, name="bottom_right_edge")
    show_object(left_extension_line, name="left_extension_line")
    show_object(right_horizontal_extension_line, name="right_horizontal_extension_line")
    show_object(right_vertical_extension_line, name="right_vertical_extension_line")
