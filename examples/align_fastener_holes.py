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

# Create the screws that will fasten the plates together
cap_screw = SocketHeadCapScrew(
    size="M2-0.4", length=5, fastener_type="iso4762", simple=False
)

# Two assemblies are required - the top will contain the screws
top_plate_assembly = cq.Assembly(None, name="top_plate_assembly")
base_plate_assembly = cq.Assembly(None, name="base_plate_assembly")

# --- Top Plate ---

# Create the top plate and add clearance holes for the screws
top_plate = (
    cq.Workplane()
    .box(10, 10, 1, centered=(True, True, False))
    .faces(">Z")
    .workplane()
    .pushPoints([(3, 3), (-3, -3)])
    .clearanceHole(
        fastener=cap_screw, counterSunk=False, baseAssembly=top_plate_assembly
    )
)
# Add the top plate to the top assembly so it can be placed with the screws
top_plate_assembly.add(top_plate, name="top_plate")
# Add the top plate and screws to the base assembly
base_plate_assembly.add(
    top_plate_assembly, name="top_plate_assembly", loc=cq.Location(cq.Vector(25, 0, 1))
)

# --- Base Plate ---

# Create the base plate
base_plate = cq.Workplane().box(65, 100, 1, centered=(True, True, False))
# Complete the base plate assembly by adding the base plate
base_plate_assembly.add(base_plate, name="base_plate")
# Add tap holes to the base plate that align with the top plate
base_plate = base_plate.pushFastenerLocations(cap_screw, base_plate_assembly).tapHole(
    fastener=cap_screw, counterSunk=False
)
# Where are the cap screw holes in the base plate?
for loc in base_plate_assembly.fastenerLocations(cap_screw):
    print(loc)

cq.Workplane("XY").pushPoints
if "show_object" in locals():
    show_object(top_plate, name="top_plate")
    show_object(base_plate, name="base_plate")
    show_object(base_plate_assembly, name="plate_assembly")
