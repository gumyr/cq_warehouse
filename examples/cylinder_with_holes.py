"""
Cylinder with Hex holes

name: cylinder_with_holes.py
by:   Gumyr
date: March 6th 2022

desc: Use projection and makeHoles to efficiently create a cylinder with hexagon
      holes around it.

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
from math import pi
import cadquery as cq
import cq_warehouse.extensions

radius = 10
circumference = 2 * pi * radius
hex_diagonal = 4 * (circumference / 10) / 3

# Create the cylinder and extract just the curved Face
cylinder = cq.Workplane("XY").cylinder(
    hex_diagonal * 5, radius, centered=(True, True, False)
)
cylinder_wall = cylinder.faces("not %Plane").val()

# Create a hexagon and position it on the surface of the cylinder
hex_wire_vertical = (
    cq.Workplane("XZ", origin=(0, radius, hex_diagonal / 2))
    .polygon(6, hex_diagonal * 0.8)
    .wires()
    .val()
)

# Project the hexagon onto the cylinder (note that emboss isn't accurate enough for this)
projected_wire = hex_wire_vertical.projectToShape(
    targetObject=cylinder.val(), center=(0, 0, hex_diagonal / 2)
)[0]

# Create a list of the projected wires positioned around the cylinder
# Note: The makeHoles() method will fail on the holes on the "back" of
#       the cylinder so only the "front" has holes.
projected_wires = [
    projected_wire.rotate((0, 0, 0), (0, 0, 1), i * 360 / 10).translate(
        (0, 0, (j + (i % 2) / 2) * hex_diagonal)
    )
    for i in range(6)
    for j in range(4)
]
# Cut holes in the cylinder wall (a Face) which is more efficient than doing this
# with a Solid object
cylinder_walls_with_holes = cylinder_wall.makeHoles(projected_wires)

# Build a pipe object by thickening the cylinder walls with holes
half_hollow_cylinder_with_holes = cylinder_walls_with_holes.thicken(1)

# Build the complete pipe by extracting just the "front", mirroring and fusing
half_hollow_cylinder_with_holes = half_hollow_cylinder_with_holes.cut(
    cq.Solid.makeBox(100, 100, 100, pnt=cq.Vector(0, -50, 0))
)
hollow_cylinder_with_holes = half_hollow_cylinder_with_holes.fuse(
    half_hollow_cylinder_with_holes.mirror("YZ")
)

# Is the resulting object valid?
print(hollow_cylinder_with_holes.isValid())

if "show_object" in locals():
    show_object(projected_wires, name="projected_wires")
    show_object(cylinder_walls_with_holes, name="cylinder_walls_with_holes")
    show_object(hollow_cylinder_with_holes, name="hollow_cylinder_with_holes")
