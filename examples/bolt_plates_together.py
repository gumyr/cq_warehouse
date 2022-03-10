"""

Bolt Plates Together Example

name: bolt_plates_together.py
by:   Gumyr
date: March 7th 2022

desc: Example of using pushFastenerLocations to align fasteners.

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
from cq_warehouse.fastener import HexHeadScrew, PlainWasher, HexNutWithFlange
import cq_warehouse.extensions

MM = 1

# Create the fasteners used in this example
hex_bolt = HexHeadScrew(
    size="M6-1", length=20 * MM, fastener_type="iso4014", simple=False
)
flanged_nut = HexNutWithFlange(size="M6-1", fastener_type="din1665")
large_washer = PlainWasher(size="M6", fastener_type="iso7093")

# Create an empty Assembly to hold all of the fasteners
fastener_assembly = cq.Assembly(None, name="top")

# Create the top and bottom plates with holes
top_plate_size = (50 * MM, 100 * MM, 5 * MM)
bottom_plate_size = (100 * MM, 50 * MM, 5 * MM)
top_plate = (
    cq.Workplane("XY", origin=(0, 0, bottom_plate_size[2]))
    .box(*top_plate_size, centered=(True, True, False))
    .faces(">Z")
    .workplane()
    .clearanceHole(
        fastener=hex_bolt,
        washers=[large_washer],
        baseAssembly=fastener_assembly,
        counterSunk=False,
    )
)
bottom_plate = (
    cq.Workplane("XY")
    .box(*bottom_plate_size, centered=(True, True, False))
    .pushFastenerLocations(
        fastener=large_washer,
        baseAssembly=fastener_assembly,
        offset=-(top_plate_size[2] + bottom_plate_size[2]),
        flip=True,
    )
    .clearanceHole(
        fastener=flanged_nut,
        baseAssembly=fastener_assembly,
        counterSunk=False,
    )
)
print(fastener_assembly.fastenerQuantities())

if "show_object" in locals():
    show_object(
        top_plate, name="top_plate", options={"alpha": 0.8, "color": (170, 0, 255)}
    )
    show_object(
        bottom_plate, name="bottom_plate", options={"alpha": 0.8, "color": (255, 85, 0)}
    )
    show_object(fastener_assembly, name="fastener_assembly")
