"""

Parametric Threaded Fasteners

name: fastener.py
by:   Gumyr
date: August 14th 2021

desc:

    This python/cadquery code is a parameterized threaded fastener generator.
    Currently the following classes are defined:
    - Thread
    - HexNut
    - SquareNut
    - Screw
    - SocketHeadCapScrew
    - ButtonHeadCapScrew
    - HexBolt
    - SetScrew

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
from cq_warehouse.fastener import (
    HexNut,
    SquareNut,
    SocketHeadCapScrew,
    ButtonHeadCapScrew,
    HexBolt,
    SetScrew,
    ExternalThread,
    InternalThread,
)

MM = 1
IN = 25.4 * MM

hex_nut = HexNut(size="#10-32").cq_object
square_nut = SquareNut(size="M8-1.25").cq_object
socket_head_cap_screw = SocketHeadCapScrew(size="M4-0.7", length=10 * MM).cq_object
button_head_cap_screw = ButtonHeadCapScrew(size="M3-0.5", length=10 * MM).cq_object
setscrew = SetScrew(size="#6-32", length=(1 / 4) * IN).cq_object
hex_bolt = HexBolt(size="M5-0.8", length=10 * MM).cq_object
external_thread = ExternalThread(
    major_diameter=(1 / 4) * IN, pitch=IN / 20, length=(1 / 4) * IN
).cq_object
internal_thread = InternalThread(
    major_diameter=3 * MM, pitch=0.5, length=3 * MM
).cq_object

if "show_object" in locals():
    show_object(hex_nut, name="HexNut")
    show_object(square_nut, name="SquareNut")
    show_object(
        socket_head_cap_screw, name="SocketHeadCapScrew",
    )
    show_object(
        button_head_cap_screw, name="ButtonHeadCapScrew",
    )
    show_object(setscrew, name="SetScrew")
    show_object(hex_bolt, name="HexBolt")
    show_object(
        external_thread, name="ExternalThread",
    )
    show_object(
        internal_thread, name="InternalThread",
    )
