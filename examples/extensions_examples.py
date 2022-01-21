"""

Extensions Examples

name: extensions_examples.py
by:   Gumyr
date: January 10th 2022

desc: Projection, emboss and textOnPath examples.

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
from cq_warehouse.map_texture import *

FLAT_PROJECTION = 1
CONICAL_PROJECTION = 2
FACE_ON_SPHERE = 3
CANADIAN_FLAG = 4
TEXT_ON_PATH = 5
EMBOSS_TEXT = 6
PROJECT_TEXT = 7
EMBOSS_WIRE = 8

example = EMBOSS_WIRE

# A sphere used as a projection target
sphere = cq.Solid.makeSphere(50, angleDegrees1=-90)


if example == FLAT_PROJECTION:
    """Example 1 - Flat Projection of Text on Sphere"""
    starttime = timeit.default_timer()

    projection_direction = cq.Vector(0, -1, 0)
    planar_text_faces = (
        cq.Workplane("XZ")
        .text(
            "Flat #" + str(example),
            fontsize=30,
            distance=1,
            font="Serif",
            fontPath="/usr/share/fonts/truetype/freefont",
            halign="center",
        )
        .faces(">Y")
        .vals()
    )
    projected_text_faces = [
        f.projectToShape(sphere, projection_direction)[0] for f in planar_text_faces
    ]
    projection_beams = [
        cq.Solid.extrudeLinear(f, cq.Vector(projection_direction * 80))
        for f in planar_text_faces
    ]
    print(f"Example #{example} time: {timeit.default_timer() - starttime:0.2f}s")
    if "show_object" in locals():
        show_object(sphere, name="sphere_solid", options={"alpha": 0.8})
        show_object(planar_text_faces, name="planar_text_faces")
        show_object(projected_text_faces, name="projected_text_faces")
        show_object(
            projection_beams,
            name="projection_beams",
            options={"alpha": 0.9, "color": (170 / 255, 170 / 255, 255 / 255)},
        )


elif example == CONICAL_PROJECTION:
    """Example 2 - Conical Projection of Text on Sphere"""
    starttime = timeit.default_timer()

    # projection_center = cq.Vector(0, 700, 0)
    projection_center = cq.Vector(0, 0, 0)
    planar_text_faces = (
        cq.Workplane("XZ")
        .text(
            "Conical #" + str(example),
            fontsize=25,
            distance=1,
            font="Serif",
            fontPath="/usr/share/fonts/truetype/freefont",
            halign="center",
        )
        .faces(">Y")
        .vals()
    )
    planar_text_faces = [f.translate((0, -60, 0)) for f in planar_text_faces]

    projected_text_faces = [
        f.projectToShape(sphere, center=projection_center)[0] for f in planar_text_faces
    ]
    projection_source = cq.Solid.makeBox(1, 1, 1, pnt=cq.Vector(-0.5, -0.5, -0.5))
    projected_text_source_faces = [
        f.projectToShape(projection_source, center=projection_center)[0]
        for f in planar_text_faces
    ]
    projection_beams = [
        cq.Solid.makeLoft(
            [
                projected_text_source_faces[i].outerWire(),
                planar_text_faces[i].outerWire(),
            ]
        )
        for i in range(len(planar_text_faces))
    ]
    print(f"Example #{example} time: {timeit.default_timer() - starttime:0.2f}s")
    if "show_object" in locals():
        show_object(sphere, name="sphere_solid", options={"alpha": 0.8})
        show_object(planar_text_faces, name="planar_text_faces", options={"alpha": 0.5})
        show_object(projected_text_faces, name="projected_text_faces")
        show_object(projected_text_source_faces, name="projected_text_source_faces")
        show_object(
            cq.Vertex.makeVertex(*projection_center.toTuple()), name="projection center"
        )
        show_object(
            projection_beams,
            name="projection_beams",
            options={"alpha": 0.9, "color": (170 / 255, 170 / 255, 255 / 255)},
        )

elif example == FACE_ON_SPHERE:
    """Example 4 - Mapping A Face on Sphere"""
    starttime = timeit.default_timer()
    projection_direction = cq.Vector(0, 0, 1)

    square = (
        cq.Workplane("XY", origin=(0, 0, -60)).rect(20, 20).extrude(1).faces("<Z").val()
    )
    square_projected = square.projectToShape(sphere, projection_direction)
    square_solids = cq.Compound.makeCompound([f.thicken(2) for f in square_projected])
    projection_beams = [
        cq.Solid.makeLoft(
            [
                square.outerWire(),
                square.outerWire().translate(cq.Vector(0, 0, 120)),
            ]
        )
    ]
    print(f"Example #{example} time: {timeit.default_timer() - starttime:0.2f}s")
    if "show_object" in locals():
        show_object(sphere, name="sphere_solid", options={"alpha": 0.8})
        show_object(square, name="square")
        show_object(square_solids, name="square_solids")
        show_object(
            projection_beams,
            name="projection_beams",
            options={"alpha": 0.9, "color": (170 / 255, 170 / 255, 255 / 255)},
        )

elif example == CANADIAN_FLAG:
    """Create a Canadian Flag blowing in the wind"""

    starttime = timeit.default_timer()

    # Canadian Flags have a 2:1 aspect ratio
    height = 50
    width = 2 * height
    wave_amplitude = 3

    def surface(amplitude, u, v):
        """Calculate the surface displacement of the flag at a given position"""
        return v * amplitude / 20 * cos(3.5 * pi * u) + amplitude / 10 * v * sin(
            1.1 * pi * v
        )

    # Note that the surface to project on must be a little larger than the faces
    # being projected onto it to create valid projected faces
    the_wind = (
        cq.Workplane("XY")
        .parametricSurface(
            lambda u, v: cq.Vector(
                width * (v * 1.1 - 0.05),
                height * (u * 1.2 - 0.1),
                height * surface(wave_amplitude, u, v) / 2,
            ),
            N=40,
        )
        .thicken(0.5)
        .val()
    )
    west_field = (
        cq.Workplane("XY")
        .center(-1, 0)
        .rect(0.5, 1, centered=False)
        .wires()
        .val()
        .scale(height)
    )
    east_field = west_field.mirror("YZ")
    center_field = (
        cq.Workplane("XY")
        .center(-0.5, 0)
        .rect(1, 1, centered=False)
        .wires()
        .val()
        .scale(height)
    )
    maple_leaf = (
        cq.Workplane("XY")
        .moveTo(0.0000, 0.0771)
        .lineTo(0.0187, 0.0771)
        .lineTo(0.0094, 0.2569)
        .radiusArc((0.0325, 0.2773), 0.0271)
        .lineTo(0.2115, 0.2458)
        .lineTo(0.1873, 0.3125)
        .radiusArc((0.1915, 0.3277), 0.0271)
        .lineTo(0.3875, 0.4865)
        .lineTo(0.3433, 0.5071)
        .radiusArc((0.3362, 0.5235), 0.0271)
        .lineTo(0.375, 0.6427)
        .lineTo(0.2621, 0.6188)
        .radiusArc((0.2469, 0.6267), 0.0271)
        .lineTo(0.225, 0.6781)
        .lineTo(0.1369, 0.5835)
        .radiusArc((0.1138, 0.5954), 0.0271)
        .lineTo(0.1562, 0.8146)
        .lineTo(0.0881, 0.7752)
        .radiusArc((0.0692, 0.7808), 0.0271)
        .lineTo(0.0000, 0.9167)
        .mirrorY()
        .wires()
        .val()
        .scale(height)
    )
    # To help build a good face, provide a couple points in the face
    west_vertices = cq.Edge.makeLine(
        cq.Vector(27 * width / 32, height / 2, 30),
        cq.Vector(29 * width / 32, height / 2, 30),
    ).Vertices()
    west_points = [cq.Vector(*v.toTuple()) for v in west_vertices]

    # Create planar faces for all of the flag components
    flag_faces = [
        cq.Face.makeFromWires(w, []).translate(cq.Vector(width / 2, 0, 30))
        for w in [west_field, maple_leaf, east_field]
    ]
    flag_faces.append(
        cq.Face.makeFromWires(center_field, [maple_leaf]).translate(
            cq.Vector(width / 2, 0, 30)
        )
    )
    # Are all of the faces valid?
    for i, f in enumerate(flag_faces):
        print(f"Face #{i} is valid: {f.isValid()}")

    # Create non-planar faces on the surface for all of the flag components
    projected_flag_faces = [
        flag_faces[2].projectToShape(
            the_wind, direction=cq.Vector(0, 0, -1), internalFacePoints=west_points
        )[0]
    ]
    projected_flag_faces.extend(
        [
            f.projectToShape(
                the_wind,
                direction=cq.Vector(0, 0, -1),
            )[0]
            for f in [flag_faces[0], flag_faces[1], flag_faces[3]]
        ]
    )
    flag_parts = [f.thicken(1, cq.Vector(0, 0, 1)) for f in projected_flag_faces]
    print(f"Example #{example} time: {timeit.default_timer() - starttime:0.2f}s")

    if "show_object" in locals():
        show_object(flag_faces, name="flag_faces")
        show_object(west_vertices, name="west_vertices")
        show_object(
            the_wind,
            name="the_wind",
            options={"alpha": 0.8, "color": (170 / 255, 85 / 255, 255 / 255)},
        )
        show_object(projected_flag_faces, name="projected_flag_faces")
        show_object(
            flag_parts[0:-1], name="flag_red_parts", options={"color": (255, 0, 0)}
        )
        show_object(
            flag_parts[-1], name="flag_white_part", options={"color": (255, 255, 255)}
        )

elif example == TEXT_ON_PATH:
    """Create 2D text on a path on many planes"""
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
                start=0.05,
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
    print(f"Example #{example} time: {timeit.default_timer() - starttime:0.2f}s")

    if "show_object" in locals():
        show_object(clover, name="clover")
        show_object(order, name="order")


elif example == EMBOSS_TEXT:
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

elif example == PROJECT_TEXT:
    """Project a text string onto a shape"""
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
    arch_path_start = cq.Vertex.makeVertex(*arch_path.positionAt(0).toTuple())
    projected_text = sphere.projectText(
        txt="project - 'the quick brown fox jumped over the lazy dog'",
        fontsize=14,
        font="Serif",
        fontPath="/usr/share/fonts/truetype/freefont",
        depth=3,
        path=arch_path,
    )
    print(f"Example #{example} time: {timeit.default_timer() - starttime:0.2f}s")

    if "show_object" in locals():
        show_object(sphere, name="sphere_solid", options={"alpha": 0.8})
        show_object(arch_path, name="arch_path")
        show_object(arch_path_start, name="arch_path_start")
        show_object(projected_text, name="projected_text")

elif example == EMBOSS_WIRE:
    """Emboss a wire and use it to create a feature"""

    starttime = timeit.default_timer()
    target_object = cq.Solid.makeCylinder(
        50, 100, pnt=cq.Vector(0, 0, -50), dir=cq.Vector(0, 0, 1)
    )
    path = cq.Workplane(target_object).section().edges().val()
    slot_wire = cq.Workplane("XY").slot2D(80, 40).wires().val()
    embossed_slot_wire = slot_wire.embossToShape(
        targetObject=target_object,
        surfacePoint=path.positionAt(0),
        surfaceXDirection=path.tangentAt(0),
        tolerance=0.1,
    )
    embossed_edges = embossed_slot_wire.Edges()
    for i, e in enumerate(slot_wire.Edges()):
        target = e.Length()
        actual = embossed_edges[i].Length()
        print(
            f"Edge lengths: target {target}, actual {actual}, difference {abs(target-actual)}"
        )

    feature_cross_section = cq.Wire.makeCircle(
        radius=2.5,
        center=embossed_slot_wire.positionAt(0),
        normal=embossed_slot_wire.tangentAt(0),
    )
    feature = cq.Solid.sweep(feature_cross_section, [], embossed_slot_wire)

    print(f"Example #{example} time: {timeit.default_timer() - starttime:0.2f}s")

    if "show_object" in locals():
        show_object(target_object, name="target_object", options={"alpha": 0.8})
        show_object(path, name="path")
        show_object(slot_wire, name="slot_wire")
        show_object(embossed_slot_wire, name="embossed_slot_wire")
        show_object(feature, name="feature")
