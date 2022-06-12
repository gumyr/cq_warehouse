"""

Extensions Examples

name: txt_on_path.py
by:   Gumyr
date: January 10th 2022

desc: Create 3D txt on a path on many planes.

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
import timeit
import random
import cadquery as cq
import cq_warehouse.extensions

starttime = timeit.default_timer()

for base_plane in [
    "XY",
    "YZ",
    "ZX",
    "XZ",
    "YX",
    "ZY",
    "front",
    "back",
    "left",
    "right",
    "top",
    "bottom",
]:
    text_on_path = (
        cq.Workplane(base_plane)
        .threePointArc((50, 30), (100, 0))
        .textOnPath(
            txt=base_plane + " The quick brown fox jumped over the lazy dog",
            fontsize=5,
            distance=1,
            positionOnPath=0.05,
        )
    )
    if "show_object" in locals():
        show_object(text_on_path, name=base_plane)

random_plane = cq.Plane(
    origin=(0, 0, 0), normal=(random.random(), random.random(), random.random())
)
clover = (
    cq.Workplane(random_plane)
    .moveTo(0, 10)
    .radiusArc((10, 0), 7.5)
    .radiusArc((0, -10), 7.5)
    .radiusArc((-10, 0), 7.5)
    .radiusArc((0, 10), 7.5)
    .consolidateWires()
    .textOnPath(
        txt=".x" * 102,
        fontsize=1,
        distance=1,
    )
)
order = (
    cq.Workplane(random_plane)
    .lineTo(100, 0)  # Not used for path
    .circle(15)
    .textOnPath(
        txt=".o" * 140,
        fontsize=1,
        distance=1,
    )
)
print(f"Test time: {timeit.default_timer() - starttime:0.2f}s")

if "show_object" in locals():
    show_object(clover, name="clover")
    show_object(order, name="order")
