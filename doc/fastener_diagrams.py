"""

Fastener Diagrams

name: fastener_diagrams.py
by:   Gumyr
date: August 14th 2021

desc:


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
    ChamferedHexHeadScrew,
    ChamferedHexHeadWithFlangeScrew,
    CheeseHeadScrew,
    CounterSunkScrew,
    PanHeadScrew,
    PanHeadWithCollarScrew,
    RaisedCheeseHeadScrew,
    RaisedCounterSunkOvalHeadScrew,
    SocketHeadCapScrew,
)

MM = 1
IN = 25.4 * MM


screw_classes = Screw.__subclasses__()
target_size = "M6-1"
screw_type_list = [
    (screw_class, screw_type)
    for screw_class in screw_classes
    for screw_type in screw_class.types()
    if target_size in screw_class.sizes(screw_type)
]
screw_list = [
    screw_type[0](screw_type=screw_type[1], size=target_size, length=20, simple=True)
    for screw_type in screw_type_list
]
number_of_screws = len(screw_list)
screw_diameters = [screw.head_diameter for screw in screw_list]
total_diameters = sum(screw_diameters) + 5 * MM * number_of_screws
disk_radius = total_diameters / (2 * pi)

disk_assembly = cq.Assembly(name="figure")
disk = cq.Workplane("XY").circle(disk_radius).extrude(20)
for i, screw in enumerate(screw_list):
    disk = (
        cq.Workplane("XY")
        .add(disk.val())
        .toPending()
        .faces(">Z")
        .workplane()
        .polarArray(disk_radius, i * (360 / number_of_screws), 360, 1)
        .clearanceHole(
            screw=screw,
            fit="Close",
            counterSunk=True,
            baseAssembly=disk_assembly,
            clean=False,
        )
    )
disk_assembly.add(disk, name="plate", color=cq.Color(162 / 255, 138 / 255, 255 / 255))

if "show_object" in locals():
    show_object(disk, name="disk")
    show_object(disk_assembly, name="disk_assembly")


# exit()
# socket_head_cap_screw = SocketHeadCapScrew(size="M4-0.7", length=10 * MM)
# print(socket_head_cap_screw.__dict__.items())

# exit()
# # hex_nut = HexNut(size="#10-32").cq_object
# # square_nut = SquareNut(size="M8-1.25").cq_object
# button_head_cap_screw = ButtonHeadCapScrew(size="M3-0.5", length=10 * MM).cq_object
# setscrew = SetScrew(size="#6-32", length=(1 / 4) * IN).cq_object
# hex_bolt = HexBolt(size="M5-0.8", length=10 * MM).cq_object
# external_thread = ExternalThread(
#     major_diameter=(1 / 4) * IN, pitch=IN / 20, length=(1 / 4) * IN
# ).cq_object
# internal_thread = InternalThread(
#     major_diameter=3 * MM, pitch=0.5, length=3 * MM
# ).cq_object

# if "show_object" in locals():
#     show_object(hex_nut, name="HexNut")
#     show_object(square_nut, name="SquareNut")
#     show_object(
#         socket_head_cap_screw, name="SocketHeadCapScrew",
#     )
#     show_object(
#         button_head_cap_screw, name="ButtonHeadCapScrew",
#     )
#     show_object(setscrew, name="SetScrew")
#     show_object(hex_bolt, name="HexBolt")
#     show_object(
#         external_thread, name="ExternalThread",
#     )
#     show_object(
#         internal_thread, name="InternalThread",
#     )
