"""

Extensions Examples

name: projection.py
by:   Gumyr
date: January 10th 2022

desc: Projection examples.

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
from math import sin, cos, pi
import timeit
from enum import Enum, auto
import cadquery as cq
import cq_warehouse.extensions

# The projection examples
class Testcase(Enum):
    FLAT_PROJECTION = auto()
    CONICAL_PROJECTION = auto()
    FACE_ON_SPHERE = auto()
    CANADIAN_FLAG = auto()
    PROJECT_TEXT = auto()


# A sphere used as a projection target
sphere = cq.Solid.makeSphere(50, angleDegrees1=-90)

for example in list(Testcase):
    # if example != Testcase.FACE_ON_SPHERE:
    #     continue

    if example == Testcase.FLAT_PROJECTION:
        """Example 1 - Flat Projection of Text on Sphere"""
        starttime = timeit.default_timer()

        projection_direction = cq.Vector(0, -1, 0)
        flat_planar_text_faces = (
            cq.Workplane("XZ")
            .text(
                "Flat",
                fontsize=30,
                distance=1,
            )
            .faces(">Y")
            .vals()
        )
        flat_projected_text_faces = [
            f.projectToShape(sphere, projection_direction)[0]
            for f in flat_planar_text_faces
        ]
        flat_projection_beams = [
            cq.Solid.extrudeLinear(f, cq.Vector(projection_direction * 80))
            for f in flat_planar_text_faces
        ]
        print(f"Example #{example} time: {timeit.default_timer() - starttime:0.2f}s")
        if "show_object" in locals():
            show_object(sphere, name="sphere_solid", options={"alpha": 0.8})
            show_object(flat_planar_text_faces, name="flat_planar_text_faces")
            show_object(flat_projected_text_faces, name="flat_projected_text_faces")
            show_object(
                flat_projection_beams,
                name="flat_projection_beams",
                options={"alpha": 0.9, "color": (170 / 255, 170 / 255, 255 / 255)},
            )

    elif example == Testcase.CONICAL_PROJECTION:
        """Example 2 - Conical Projection of Text on Sphere"""
        starttime = timeit.default_timer()

        # projection_center = cq.Vector(0, 700, 0)
        projection_center = cq.Vector(0, 0, 0)
        conical_planar_text_faces = (
            cq.Workplane("XZ")
            .text(
                "Conical",
                fontsize=25,
                distance=1,
                font="Serif",
                fontPath="/usr/share/fonts/truetype/freefont",
                halign="center",
            )
            .faces(">Y")
            .vals()
        )
        conical_planar_text_faces = [
            f.translate((0, -60, 0)) for f in conical_planar_text_faces
        ]

        conical_projected_text_faces = [
            f.projectToShape(sphere, center=projection_center)[0]
            for f in conical_planar_text_faces
        ]
        projection_source = cq.Solid.makeBox(1, 1, 1, pnt=cq.Vector(-0.5, -0.5, -0.5))
        conial_projected_text_source_faces = [
            f.projectToShape(projection_source, center=projection_center)[0]
            for f in conical_planar_text_faces
        ]
        conical_projection_beams = [
            cq.Solid.makeLoft(
                [
                    conial_projected_text_source_faces[i].outerWire(),
                    conical_planar_text_faces[i].outerWire(),
                ]
            )
            for i in range(len(conical_planar_text_faces))
        ]
        print(f"Example #{example} time: {timeit.default_timer() - starttime:0.2f}s")
        if "show_object" in locals():
            show_object(sphere, name="sphere_solid", options={"alpha": 0.8})
            show_object(
                conical_planar_text_faces,
                name="conical_planar_text_faces",
                options={"alpha": 0.5},
            )
            show_object(
                conical_projected_text_faces, name="conical_projected_text_faces"
            )
            show_object(
                conial_projected_text_source_faces,
                name="conial_projected_text_source_faces",
            )
            show_object(
                cq.Vertex.makeVertex(*projection_center.toTuple()),
                name="projection center",
            )
            show_object(
                conical_projection_beams,
                name="conical_projection_beams",
                options={"alpha": 0.9, "color": (170 / 255, 170 / 255, 255 / 255)},
            )

    elif example == Testcase.FACE_ON_SPHERE:
        """Example 4 - Mapping A Face on Sphere"""
        starttime = timeit.default_timer()
        projection_direction = cq.Vector(0, 0, 1)

        square = (
            cq.Workplane("XY", origin=(0, 0, -60))
            .rect(20, 20)
            .extrude(1)
            .faces("<Z")
            .val()
        )
        square_projected = square.projectToShape(sphere, projection_direction)
        square_solids = cq.Compound.makeCompound(
            [f.thicken(2) for f in square_projected]
        )
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

    elif example == Testcase.CANADIAN_FLAG:
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
                flag_parts[-1],
                name="flag_white_part",
                options={"color": (255, 255, 255)},
            )

    elif example == Testcase.PROJECT_TEXT:
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
