"""

Align Fastener Holes Example

name: align_fastener_holes.py
by:   Gumyr
date: December 11th 2021

desc: Example of using the pushFastenerLocations() method to align cq_warehouse.fastener
      holes between to plates in an assembly.

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
from cq_warehouse.fastener import SocketHeadCapScrew
import cq_warehouse.extensions

# Create the screws that will fasten the plates together
cap_screw = SocketHeadCapScrew(
    size="M2-0.4", length=6, fastener_type="iso4762", simple=False
)

# Two assemblies are required - the top will contain the screws
bracket_assembly = cq.Assembly(None, name="top_plate_assembly")
square_tube_assembly = cq.Assembly(None, name="base_plate_assembly")

# --- Angle Bracket ---

# Create an angle bracket and add clearance holes for the screws
angle_bracket = (
    cq.Workplane("YZ")
    .moveTo(-9, 1)
    .hLine(10)
    .vLine(-10)
    .offset2D(1)
    .extrude(10, both=True)
    .faces(">Z")
    .workplane()
    .pushPoints([(5, -5), (-5, -5)])
    .clearanceHole(fastener=cap_screw, counterSunk=False, baseAssembly=bracket_assembly)
    .faces(">Y")
    .workplane()
    .pushPoints([(0, -7)])
    .clearanceHole(fastener=cap_screw, counterSunk=False, baseAssembly=bracket_assembly)
)
# Add the top plate to the top assembly so it can be placed with the screws
bracket_assembly.add(angle_bracket, name="angle_bracket")
# Add the top plate and screws to the base assembly
square_tube_assembly.add(
    bracket_assembly,
    name="top_plate_assembly",
    loc=cq.Location(cq.Vector(20, 10, 10)),
)

# --- Square Tube ---

# Create the square tube
square_tube = (
    cq.Workplane("YZ").rect(18, 18).rect(14, 14).offset2D(1).extrude(30, both=True)
)
# Complete the square tube assembly by adding the square tube
square_tube_assembly.add(square_tube, name="square_tube")
# Add tap holes to the square tube that align with the angle bracket
square_tube = square_tube.pushFastenerLocations(
    cap_screw, square_tube_assembly
).tapHole(fastener=cap_screw, counterSunk=False, depth=10)


# Where are the cap screw holes in the square tube?
for loc in square_tube_assembly.fastenerLocations(cap_screw):
    print(loc)

# How many fasteners are used in the square_tube_assembly and all sub-assemblies
print(square_tube_assembly.fastenerQuantities())

if "show_object" in locals():
    show_object(angle_bracket, name="angle_bracket")
    show_object(square_tube, name="square_tube")
    show_object(square_tube_assembly, name="square_tube_assembly")
