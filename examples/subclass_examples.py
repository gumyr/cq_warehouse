"""

Sub-Class Examples

name: subclass_examples.py
by:   Gumyr
date: August 31st 2022

desc: This python/cadquery code is an example of how to use and create
      custom CAD object classes that are a sub-class of the base Shape class.

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
from cadquery import Solid, Location, Vector
from cadquery.occ_impl.shapes import VectorLike
from cq_warehouse.fastener import DomedCapNut, CounterSunkScrew
import cq_warehouse.extensions

# Use a pre-defined sub-classed object
nut = DomedCapNut(size="M6-1", fastener_type="din1587")

# Observe how normal cadquery methods apply to the sub-classed object
print(f"{nut.Center()=}")
nut_moved = nut.translate(Vector(20, 20, 10))

screw = CounterSunkScrew(size="M6-1", fastener_type="iso2009", length=30)
screw_rotated = screw.rotate((0, 0, 0), (0, 1, 0), 90)


class FilletBox(Solid):
    """A filleted box

    A box of the given dimensions with all of the edges filleted.

    Args:
        length (float): box length
        width (float): box width
        height (float): box height
        radius (float): edge radius
        pnt (VectorLike, optional): minimum x,y,z point. Defaults to (0, 0, 0).
        dir (VectorLike, optional): direction of height. Defaults to (0, 0, 1).
    """

    def __init__(
        self,
        length: float,
        width: float,
        height: float,
        radius: float,
        pnt: VectorLike = (0, 0, 0),
        dir: VectorLike = (0, 0, 1),
    ):
        # Store the attributes so the object can be copied
        self.length = length
        self.width = width
        self.height = height
        self.radius = radius
        self.pnt = pnt
        self.dir = dir

        # Create the object
        obj = Solid.makeBox(length, width, height, pnt, dir)
        obj = obj.fillet(radius, obj.Edges())
        # Initialize the Solid class with the new OCCT object
        super().__init__(obj.wrapped)


# Create an instance of the FilletBox
fillet_box = FilletBox(length=10, width=8, height=5, radius=1).locate(
    Location(Vector(20, -15, 0))
)
print(f"{fillet_box.Center()=}")

if "show_object" in locals():
    show_object(nut, name="nut")
    show_object(nut_moved, name="nut_moved")
    show_object(fillet_box, name="fillet_box")
