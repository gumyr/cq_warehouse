"""

Extensions Examples

name: extensions_examples.py
by:   Gumyr
date: January 10th 2022

desc: Emboss examples.

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
from enum import Enum, auto
import cadquery as cq
import cq_warehouse.extensions

# The emboss examples
class Testcase(Enum):
    EMBOSS_TEXT = auto()
    EMBOSS_WIRE = auto()


# A sphere used as a projection target
sphere = cq.Solid.makeSphere(50, angleDegrees1=-90)

for example in list(Testcase):

    # if example != Testcase.EMBOSS_WIRE:
    #     continue

    if example == Testcase.EMBOSS_TEXT:
        """Emboss a text string onto a shape"""

        starttime = timeit.default_timer()

        arch_path = (
            cq.Workplane(sphere)
            .cut(
                cq.Solid.makeCylinder(
                    80, 100, pnt=cq.Vector(-50, 0, -70), dir=cq.Vector(1, 0, 0)
                )
            )
            .edges("<Z")
            .val()
        )
        projected_text = sphere.embossText(
            txt="emboss - 'the quick brown fox jumped over the lazy dog'",
            fontsize=14,
            font="Serif",
            fontPath="/usr/share/fonts/truetype/freefont",
            depth=3,
            path=arch_path,
        )

        print(f"Example #{example} time: {timeit.default_timer() - starttime:0.2f}s")

        if "show_object" in locals():
            show_object(sphere, name="sphere_solid", options={"alpha": 0.8})
            show_object(arch_path, name="arch_path", options={"alpha": 0.8})
            show_object(projected_text, name="embossed_text")

    elif example == Testcase.EMBOSS_WIRE:
        """Emboss a wire and use it to create a feature"""

        starttime = timeit.default_timer()
        target_object = cq.Solid.makeCylinder(
            50, 100, pnt=cq.Vector(0, 0, -50), dir=cq.Vector(0, 0, 1)
        )
        path = cq.Workplane(target_object).section().edges().val()
        # to_emboss_wire = cq.Wire.makeRect(
        #     80, 40, cq.Vector(), cq.Vector(0, 0, 1), cq.Vector(1, 0, 0)
        # )
        to_emboss_wire = cq.Workplane("XY").slot2D(80, 40).wires().val()
        embossed_wire = to_emboss_wire.embossToShape(
            targetObject=target_object,
            surfacePoint=path.positionAt(0),
            surfaceXDirection=path.tangentAt(0),
            tolerance=0.1,
        )
        embossed_edges = embossed_wire.sortedEdges()
        for i, e in enumerate(to_emboss_wire.sortedEdges()):
            target = e.Length()
            actual = embossed_edges[i].Length()
            print(
                f"Edge lengths: target {target}, actual {actual}, difference {abs(target-actual)}"
            )
        sweep_profile = cq.Wire.makeCircle(
            3, center=embossed_wire.positionAt(0), normal=embossed_wire.tangentAt(0)
        )
        swept_wire = cq.Solid.sweep(sweep_profile, [], path=embossed_wire)
        print(f"Example #{example} time: {timeit.default_timer() - starttime:0.2f}s")

        if "show_object" in locals():
            show_object(target_object, name="target_object", options={"alpha": 0.8})
            show_object(path, name="path")
            show_object(to_emboss_wire, name="to_emboss_wire")
            show_object(embossed_wire, name="embossed_wire")
            show_object(swept_wire, name="swept_wire")
