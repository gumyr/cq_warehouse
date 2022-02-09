"""

Plastic Bottle Funnel

name: plastic_bottle_funnel.py
by:   Gumyr
date: February 9th 2022

desc: This python/cadquery code is a parameterized plastic bottle funnel.

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
from cq_warehouse.thread import PlasticBottleThread
import cq_warehouse.extensions  # need projectText()

MM = 1


class BottleFunnel:
    """A Funnel with integral Plastic Bottle threads

    A funnel that screws onto the top of a plastic bottle to minimize any spillage during use.
    The funnel has an internal drip edge that keeps capillary action from causing the liquid
    to flow over the lip of the bottle. The intended usage is for 3D printing resin bottles
    where excess resin needs to be filtered and returned to the storage bottle but the resin
    printer trays are difficult to handle with one hand.

    The provided thread size string e.g. 'M38SP444' is embossed to the cap of the funnel to
    help with selecting the appropriate funnel if one has multiple sizes to fit different bottles.

    Args:
        thread_size (str, optional): ASTM D2911 Standard Plastic Bottle Thread size.
            Defaults to "M38SP444".
        funnel_height (float, optional): height. Defaults to 95*MM.
        funnel_top_diameter (float, optional): top diameter. Defaults to 140*MM.
        cap_length (float, optional): cap size. Defaults to 25*MM.
        num_ribs (int, optional): number external ribs. Defaults to 6.
        wall_thickness (float, optional): funnel and cap wall thickness.
            Defaults to 1.5*MM.
        compensation (float, optional): used to compensate for over-extrusion
            of 3D printers. A value of 0.2mm will reduce the radius of an external thread
            by 0.2mm (and increase the radius of an internal thread) such that the resulting
            3D printed part matches the target dimensions. Defaults to 0.2*MM.

    Attributes:
        cq_object (Compound): The funnel

    """

    @property
    def cq_object(self):
        """The funnel CAD / Compound object"""
        return self._cq_object

    def __init__(
        self,
        thread_size: str = "M38SP444",
        funnel_height: float = 95 * MM,
        funnel_top_diameter: float = 140 * MM,
        cap_length: float = 25 * MM,
        num_ribs: int = 6,
        wall_thickness: float = 1.5 * MM,
        compensation: float = 0.2 * MM,
    ):
        self.thread_size = thread_size
        self.funnel_height = funnel_height
        self.funnel_top_diameter = funnel_top_diameter
        self.cap_length = cap_length
        self.num_ribs = num_ribs
        self.wall_thickness = wall_thickness
        self.compensation = compensation

        # Create the thread which controls the dimensions of the cap section
        self.thread = PlasticBottleThread(
            size=thread_size,
            external=False,
            manufacturingCompensation=self.compensation,
        )
        self.bottle_internal_diameter = self.thread.diameter - 12 * MM

        # Create the profile of the funnel as a cadquery Wire
        self.funnel_side_wire = self.make_funnel_side_wire()

        # Create the ribs
        # Note: without the +5 for the angle the union operation with the funnel
        #       will drop one of the ribs.
        _funnel_rib = self.make_funnel_rib()
        self.funnel_ribs = cq.Compound.makeCompound(
            [
                _funnel_rib.rotate((0, 0, 0), (0, 0, 1), i * 360 / self.num_ribs + 5)
                for i in range(self.num_ribs)
            ]
        )
        # Create the drip edge
        self.drip_edge = self.make_drip_edge()

        # Create the funnel and add ribs and drip edge
        self._cq_object = self.make_funnel().val()

    def make_funnel(self):
        """Create the funnel by revolving the shape and adding features"""
        funnel = (
            cq.Workplane("XZ")
            .add(self.funnel_side_wire)
            .toPending()
            .offset2D(self.wall_thickness / 2)
            .revolve()
        )
        label_path = cq.Edge.makeCircle(
            radius=self.thread.root_radius + self.wall_thickness,
            pnt=(0, 0, self.cap_length / 2),
        )
        label = funnel.val().projectText(
            txt=self.thread_size,
            fontsize=self.cap_length / 2,
            depth=1 * MM,
            path=label_path,
        )
        funnel = (
            funnel.union(label)
            .union(self.drip_edge)
            .union(self.funnel_ribs)
            .union(self.thread.cq_object)
        )

        return funnel

    def make_drip_edge(self):
        """Create the drip edge as a chamferred pipe"""
        drip_edge = (
            cq.Workplane("XY", origin=(0, 0, self.cap_length - 5 * MM))
            .circle(self.bottle_internal_diameter / 2 - self.wall_thickness)
            .circle(self.bottle_internal_diameter / 2 - 2 * self.wall_thickness)
            .extrude(5 * MM)
            .faces("<Z")
            .edges(cq.selectors.RadiusNthSelector(1))
            .chamfer(3 * self.wall_thickness / 4)
        )
        return drip_edge

    def make_funnel_rib(self):
        """Create a support rib from splines"""
        funnel_rib = (
            cq.Workplane("XZ")
            .moveTo(
                self.bottle_internal_diameter / 2 - 3 * self.wall_thickness / 2,
                self.cap_length,
            )
            .spline(
                [(self.funnel_top_diameter / 2, self.funnel_height)],
                [(0, 0.5), (1, 1)],
                scale=False,
                includeCurrent=True,
            )
            .spline(
                [(self.thread.root_radius + self.wall_thickness / 2, self.cap_length)],
                [(-1, -1), (0, -0.5)],
                scale=False,
                includeCurrent=True,
            )
            .close()
            .offset2D(self.wall_thickness / 2)
            .extrude(3 * self.wall_thickness / 4, both=True)
            .edges()
            .fillet(self.wall_thickness / 2)
            .val()
        )
        return funnel_rib

    def make_funnel_side_wire(self):
        """Define the profile of the funnel with a spline"""
        funnel_side_wire = (
            cq.Workplane("XZ")
            .moveTo(self.thread.root_radius + self.wall_thickness / 2)
            .vLineTo(self.cap_length)
            .hLineTo(self.bottle_internal_diameter / 2 - 3 * self.wall_thickness / 2)
            .spline(
                [(self.funnel_top_diameter / 2, self.funnel_height)],
                [(0, 0.5), (1, 1)],
                scale=False,
                includeCurrent=True,
            )
            .consolidateWires()
        )
        return funnel_side_wire


if __name__ == "__main__" or "show_object" in locals():
    bottle_funnel = BottleFunnel().cq_object
    # To save the funnel as an STL file ready for printing uncomment one of these exports:

    # Small version with noticeable flat sections in the cone
    # cq.exporters.export(bottle_funnel, fname="funnel.stl")

    # Very large version with very few mesh artifacts
    # cq.exporters.export(bottle_funnel, fname="funnel.stl", angularTolerance=0.05)

if "show_object" in locals():
    show_object(bottle_funnel, name="funnel")
