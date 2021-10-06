"""

Fastener Diagrams

name: fastener_diagrams.py
by:   Gumyr
date: August 14th 2021

desc: Create a disc with countersunk holes around the perimeter with
      every type of screw in it.


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
from math import pi
import cadquery as cq
from cq_warehouse.fastener import (
    Screw,
    ButtonHeadScrew,
    ButtonHeadWithCollarScrew,
    CheeseHeadScrew,
    CounterSunkScrew,
    HexHeadScrew,
    HexHeadWithFlangeScrew,
    PanHeadScrew,
    PanHeadWithCollarScrew,
    RaisedCheeseHeadScrew,
    RaisedCounterSunkOvalHeadScrew,
    SocketHeadCapScrew,
    Nut,
    DomedCapNut,
    HexNut,
    HexNutWithFlange,
    UnchamferedHexagonNut,
    SquareNut,
    Washer,
    PlainWasher,
    ChamferedWasher,
    CheeseHeadWasher,
)
from cq_warehouse.drafting import Draft

MM = 1

fastener_title_callout = Draft(font_size=10, label_normal=(1, -1, 0))
title_callout = fastener_title_callout.callout(
    label="cq_warehouse.fastener", origin=(0, 0, 75 * MM), justify="center",
)
# ------------------------ Screws ------------------------

#
# Create a list of all the "target_size" screws in all the screw classes and types
target_size = "M6-1"
screw_type_dict = Screw.select_by_size(target_size)
screw_type_list = [
    (screw_class, screw_type)
    for screw_class, screw_types in screw_type_dict.items()
    for screw_type in screw_types
]
number_of_screws = len(screw_type_list)
print(
    f"The disc contains {number_of_screws} {target_size} screws of the following types:"
)
#
# Display the list of screws which will populate the holes in the disk
for screw_class, screw_types in screw_type_dict.items():
    screws = ", ".join(screw_types)
    print(f"- {screw_class.__name__} : {screws}")
#
# Instantiate all of the screws, use simple=True to dramatically lessen the elapsed time
screw_list = [
    screw_type[0](screw_type=screw_type[1], size=target_size, length=20, simple=True)
    for screw_type in screw_type_list
]

#
# Calculate the size of the disk such that there is room for all the screws in the perimeter
screw_diameters = [screw.head_diameter for screw in screw_list]
total_diameters = sum(screw_diameters) + 5 * MM * number_of_screws
disk_radius = total_diameters / (2 * pi)

#
# Create the cadquery objects
disk_assembly = cq.Assembly(name="figure")

# As all of the screws are unique, cycle over the disk creating clearance holes
# and accumulating the screws in the disk_assembly
disk = cq.Workplane("XY").circle(disk_radius).extrude(30)
for i, screw in enumerate(screw_list):
    depth = None if i % 2 == 0 else screw.min_hole_depth(True)
    disk = (
        disk.toPending()
        .faces(">Z")
        .workplane()
        .polarArray(disk_radius, i * (360 / number_of_screws), 360, 1)
        .clearanceHole(
            fastener=screw,
            fit="Close",
            depth=depth,
            counterSunk=True,
            baseAssembly=disk_assembly,
            clean=False,
        )
    )

# ------------------------ Washers ------------------------
# Create a list of all the "target_size" washers in all the washer classes and types
washer_classes = Washer.__subclasses__()
target_size = "M6"
washer_type_dict = Washer.select_by_size(target_size)
print(washer_type_dict)
washer_type_list = [
    (washer_class, washer_type)
    for washer_class, washer_types in washer_type_dict.items()
    for washer_type in washer_types
]
number_of_washers = len(washer_type_list)
print(
    f"The disc contains {number_of_washers} {target_size} washers of the following types:"
)
#
# Display the list of washers which will populate the holes in the disk
for washer_class, washer_types in washer_type_dict.items():
    washers = ", ".join(washer_types)
    print(f"- {washer_class.__name__} : {washers}")
#
# Instantiate all of the washers, use simple=True to dramatically lessen the elapsed time
washer_list = [
    washer_type[0](washer_type=washer_type[1], size=target_size)
    for washer_type in washer_type_list
]

# ------------------------ Nuts ------------------------
#
# Create a list of all the "target_size" nuts in all the nut classes and types
nut_classes = Nut.__subclasses__()
target_size = "M6-1"
nut_type_dict = Nut.select_by_size(target_size)
nut_type_list = [
    (nut_class, nut_type)
    for nut_class, nut_types in nut_type_dict.items()
    for nut_type in nut_types
]
number_of_nuts = len(nut_type_list)
print(f"The disc contains {number_of_nuts} {target_size} nuts of the following types:")
#
# Display the list of nuts which will populate the holes in the disk
for nut_class, nut_types in nut_type_dict.items():
    nuts = ", ".join(nut_types)
    print(f"- {nut_class.__name__} : {nuts}")
#
# Instantiate all of the nuts, use simple=True to dramatically lessen the elapsed time
nut_list = [
    nut_type[0](nut_type=nut_type[1], size=target_size, simple=True)
    for nut_type in nut_type_list
]
#
# Calculate the size of the disk such that there is room for all the nuts in the perimeter
nut_diameters = [nut.nut_diameter for nut in nut_list]
total_diameters = sum(nut_diameters) + 5 * MM * number_of_nuts
disk_radius = 1.5 * total_diameters / (2 * pi)

#
# Create the cadquery objects
# As all of the nuts are unique, cycle over the disk creating clearance holes
# and accumulating the nuts in the disk_assembly
for i, nut in enumerate(nut_list):
    washers = [washer_list[j % number_of_washers] for j in range(i, i + 2)]
    disk = (
        disk.toPending()
        .faces(">Z")
        .workplane()
        .polarArray(disk_radius, i * (360 / number_of_nuts), 360, 1)
        .tapHole(
            fastener=nut,
            washers=washers,
            material="Soft",
            counterSunk=False,
            fit="Close",
            baseAssembly=disk_assembly,
            clean=False,
        )
    )

#
# ------------------------ Threaded Hole ------------------------
#
disk = (
    disk.toPending()
    .faces(">Z")
    .pushPoints([(0, 0)])
    .threadedHole(fastener=screw_list[0], depth=20, simple=True, counterSunk=False,)
)

# Finally, add the finished disk to the assembly
disk_assembly.add(disk, name="plate", color=cq.Color(162 / 255, 138 / 255, 255 / 255))

if "show_object" in locals():
    show_object(disk, name="disk")
    show_object(disk_assembly, name="disk_assembly")
    show_object(title_callout, name="title")
