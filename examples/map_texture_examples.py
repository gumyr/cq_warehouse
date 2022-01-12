"""

Texture Mapping Examples

name: map_texture_examples.py
by:   Gumyr
date: January 10th 2022

desc: Examples face projection, thickening and textOnPath methods.

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

FLAT_PROJECTION = 0
CONICAL_PROJECTION = 1
CYLINDER_MAP = 2
FACE_ON_SPHERE = 3
CANADIAN_FLAG = 4
TEXT_ON_PATH = 5

example = CANADIAN_FLAG

# A sphere used as a projection target
sphere = cq.Solid.makeSphere(50, angleDegrees1=-90)


if example == FLAT_PROJECTION:
    """Example 1 - Flat Projection of Text on Sphere"""
    starttime = timeit.default_timer()

    projection_direction = cq.Vector(0, 1, 0)
    text_faces = (
        cq.Workplane("XZ")
        .text(
            "Beingφθ⌀",
            fontsize=20,
            distance=1,
            font="Serif",
            fontPath="/usr/share/fonts/truetype/freefont",
            halign="center",
        )
        .faces(">Y")
        .vals()
    )

    projected_text_faces = [
        f.projectToSurface(sphere, projection_direction)[BACK] for f in text_faces
    ]
    projected_text = cq.Compound.makeCompound(
        [f.thicken(-5, direction=projection_direction) for f in projected_text_faces]
    )
    print(f"Example #{example} time: {timeit.default_timer() - starttime:0.2f}s")
    if "show_object" in locals():
        show_object(sphere, name="sphere_solid", options={"alpha": 0.8})
        show_object(text_faces, name="text_faces")
        show_object(projected_text, name="projected_sphere_text_solid")


elif example == CONICAL_PROJECTION:
    """Example 2 - Conical Projection of Text on Sphere"""
    starttime = timeit.default_timer()

    projection_center = cq.Vector(0, 700, 0)
    text_faces = (
        cq.Workplane("XZ")
        .text(
            "φθ⌀ #" + str(example),
            fontsize=20,
            distance=1,
            font="Serif",
            fontPath="/usr/share/fonts/truetype/freefont",
            halign="center",
        )
        .faces(">Y")
        .vals()
    )
    text_faces = [f.translate((0, -60, 0)) for f in text_faces]

    projected_text_faces = [
        f.projectToSurface(sphere, center=projection_center)[FRONT] for f in text_faces
    ]
    projected_text = cq.Compound.makeCompound(
        [
            f.thicken(-5, direction=text_faces[0].Center() - projection_center)
            for f in projected_text_faces
        ]
    )
    print(f"Example #{example} time: {timeit.default_timer() - starttime:0.2f}s")
    if "show_object" in locals():
        show_object(sphere, name="sphere_solid", options={"alpha": 0.8})
        show_object(text_faces, name="text_faces")
        show_object(projected_text_faces, name="projected_text_faces")
        show_object(projected_text, name="projected_sphere_text_solid")
        show_object(
            cq.Vertex.makeVertex(*projection_center.toTuple()), name="projection center"
        )


elif example == CYLINDER_MAP:
    """Example 3 - Mapping Text on Cylinder"""
    starttime = timeit.default_timer()

    text_faces = (
        cq.Workplane("XY")
        .text(
            "Example #" + str(example) + " Cylinder Wrap ⌀100",
            fontsize=20,
            distance=1,
            font="Serif",
            fontPath="/usr/share/fonts/truetype/freefont",
            halign="center",
        )
        .faces("<Z")
        .vals()
    )

    projected_text_faces = [f.projectToCylinder(radius=50) for f in text_faces]
    projected_text = cq.Compound.makeCompound(
        [f.thicken(5, f.Center()) for f in projected_text_faces]
    )
    print(f"Example #{example} time: {timeit.default_timer() - starttime:0.2f}s")
    if "show_object" in locals():
        show_object(
            cq.Solid.makeCylinder(50, 100, cq.Vector(0, 0, -50)),
            name="sphere_solid",
            options={"alpha": 0.8},
        )
        show_object(text_faces, name="text_faces")
        show_object(projected_text, name="projected_text")

elif example == FACE_ON_SPHERE:
    """Example 4 - Mapping A Face on Sphere"""
    starttime = timeit.default_timer()
    projection_direction = cq.Vector(0, 0, 1)

    square = cq.Workplane("XY").rect(20, 20).extrude(1).faces("<Z").val()
    square_projected = square.projectToSurface(sphere, projection_direction)
    square_solids = cq.Compound.makeCompound([f.thicken(2) for f in square_projected])
    print(f"Example #{example} time: {timeit.default_timer() - starttime:0.2f}s")
    if "show_object" in locals():
        show_object(sphere, name="sphere_solid", options={"alpha": 0.8})
        show_object(square_solids, name="square_solids")

elif example == CANADIAN_FLAG:
    """Example 5 - A Canadian Flag blowing in the wind"""
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
    flag_surface = (
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
    # To help build a good projection, provide a couple points in the face
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
        flag_faces[2].projectToSurface(
            flag_surface, direction=cq.Vector(0, 0, -1), internalFacePoints=west_points
        )[FRONT]
    ]
    projected_flag_faces.extend(
        [
            f.projectToSurface(
                flag_surface,
                direction=cq.Vector(0, 0, -1),
            )[FRONT]
            for f in [flag_faces[0], flag_faces[1], flag_faces[3]]
        ]
    )
    flag_parts = [f.thicken(1, cq.Vector(0, 0, 1)) for f in projected_flag_faces]
    print(f"Example #{example} time: {timeit.default_timer() - starttime:0.2f}s")

    if "show_object" in locals():
        show_object(flag_faces, name="flag_faces")
        show_object(west_vertices, name="west_vertices")
        show_object(
            flag_surface,
            name="flag_surface",
            options={"alpha": 0.8, "color": (170 / 255, 85 / 255, 255 / 255)},
        )
        show_object(projected_flag_faces, name="projected_flag_faces")
        # show_object(vertices, name="vertices")
        show_object(
            flag_parts[0:-1], name="flag_red_parts", options={"color": (255, 0, 0)}
        )
        show_object(
            flag_parts[-1], name="flag_white_part", options={"color": (255, 255, 255)}
        )

elif example == TEXT_ON_PATH:
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
    if "show_object" in locals():
        show_object(clover, name="clover")


else:
    """Example 6 - Compound Solid - under construction"""
    compound_solid = (
        cq.Workplane("XY")
        .rect(100, 50)
        .rect(50, 100)
        .extrude(50, both=True)
        .edges("|Z")
        .fillet(10)
    )

    compound_solid_faces = compound_solid.faces().vals()
    print(f"{len(compound_solid_faces)=}")
    text_path = compound_solid.section().wires().val()
    for i, f in enumerate(compound_solid_faces):
        print(f"{i}:{f.isInside(text_path.positionAt(0))}")
    print(type(text_path))

    # text_on_compound = textOnSolid(
    #     txt="The quick brown fox jumped over the lazy dog",
    #     fontsize=10,
    #     distance=5,
    #     path=text_path,
    #     start=0,
    #     solid_object=compound_solid.val(),
    # )

    if "show_object" in locals():
        show_object(compound_solid, name="compound_solid", options={"alpha": 0.8})
        show_object(text_path, name="text_path")
        show_object(text_on_compound, name="text_on_compound")
