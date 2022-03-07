"""

Extensions Unit Tests

name: extensions_tests.py
by:   Gumyr
date: January 21st 2022

desc: Unit tests for the extensions sub-package of cq_warehouse

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
from random import uniform
import math
import unittest
import cadquery as cq
from cq_warehouse.extensions import *
from cq_warehouse.fastener import SocketHeadCapScrew, DomedCapNut, ChamferedWasher


def _assertTupleAlmostEquals(self, expected, actual, places, msg=None):
    """Check Tuples"""
    for i, j in zip(actual, expected):
        self.assertAlmostEqual(i, j, places, msg=msg)


unittest.TestCase.assertTupleAlmostEquals = _assertTupleAlmostEquals


class AssemblyTests(unittest.TestCase):
    """Test new Assembly methods"""

    def test_translate(self):
        """Validate translate moves an Assembly"""
        test_assembly = cq.Assembly(cq.Workplane("XY").box(10, 10, 10)).translate(
            (20, 20, 20)
        )
        position = test_assembly.loc.toTuple()[0]
        self.assertTupleAlmostEquals(position, (20, 20, 20), 7)

    def test_rotate(self):
        test_assembly = cq.Assembly(cq.Workplane("XY").box(10, 10, 10)).rotate(
            (0, 0, 1), 90
        )
        rotation = test_assembly.loc.toTuple()[1]
        # In radians
        self.assertTupleAlmostEquals(rotation, (0, 0, math.pi / 2), 7)


class FaceTests(unittest.TestCase):
    """Test new Face methods - not including projection or emboss"""

    def test_make_holes(self):
        radius = 10
        circumference = 2 * math.pi * radius
        hex_diagonal = 4 * (circumference / 10) / 3
        cylinder = cq.Workplane("XY").cylinder(
            hex_diagonal * 5, radius, centered=(True, True, False)
        )
        cylinder_wall = cylinder.faces("not %Plane").val()
        hex_wire_vertical = (
            cq.Workplane("XZ", origin=(0, radius, hex_diagonal / 2))
            .polygon(6, hex_diagonal * 0.8)
            .wires()
            .val()
        )
        projected_wire = hex_wire_vertical.projectToShape(
            targetObject=cylinder.val(), center=(0, 0, hex_diagonal / 2)
        )[0]
        projected_wires = [
            projected_wire.rotate((0, 0, 0), (0, 0, 1), i * 360 / 10).translate(
                (0, 0, (j + (i % 2) / 2) * hex_diagonal)
            )
            for i in range(6)
            for j in range(4)
        ]
        cylinder_walls_with_holes = cylinder_wall.makeHoles(projected_wires)
        self.assertTrue(cylinder_walls_with_holes.isValid())
        self.assertLess(cylinder_walls_with_holes.Area(), cylinder_wall.Area())


class ShapeTests(unittest.TestCase):
    """Test new Shape methods"""

    def test_transformed(self):
        """Validate that transformed works the same for Shape and Workplane"""
        rotation = (uniform(0, 360), uniform(0, 360), uniform(0, 360))
        offset = (uniform(0, 50), uniform(0, 50), uniform(0, 50))
        shape_transformed = cq.Solid.makeSphere(
            50, angleDegrees1=0, angleDegrees2=90, angleDegrees3=90
        ).transformed(rotation, offset)
        workplane_transformed = (
            cq.Workplane("XY")
            .transformed(rotation, offset)
            .sphere(50, angle1=0, angle2=90, angle3=90)
        )
        difference = workplane_transformed.cut(shape_transformed).val().Volume()
        self.assertAlmostEqual(difference, 0.0, 7)


class WorkplaneTests(unittest.TestCase):
    """Test 2D text on a path"""

    def test_text_on_path(self):

        # Verify a wire path on a object with cut
        box = cq.Workplane("XY").box(4, 4, 0.5)
        obj1 = (
            box.faces(">Z")
            .workplane()
            .circle(1.5)
            .textOnPath(
                "text on a circle", fontsize=0.5, distance=-0.05, cut=True, clean=False
            )
        )
        # combined object should have smaller volume
        self.assertGreater(box.val().Volume(), obj1.val().Volume())

        # Verify a wire path on a object with combine
        obj2 = (
            box.faces(">Z")
            .workplane()
            .circle(1.5)
            .textOnPath(
                "text on a circle",
                fontsize=0.5,
                distance=0.05,
                font="Sans",
                cut=False,
                combine=True,
            )
        )
        # combined object should have bigger volume
        self.assertLess(box.val().Volume(), obj2.val().Volume())

        # verify that the number of top faces & solids is correct (NB: this is font specific)
        self.assertEqual(len(obj2.faces(">Z").vals()), 14)

        # verify that the fox jumps over the dog
        dog = cq.Workplane("XY", origin=(50, 0, 0)).box(30, 30, 30, centered=True)
        fox = (
            cq.Workplane("XZ")
            .threePointArc((50, 30), (100, 0))
            .textOnPath(
                txt="The quick brown fox jumped over the lazy dog",
                fontsize=5,
                distance=1,
                start=0.1,
                cut=False,
            )
        )
        self.assertEqual(fox.val().intersect(dog.val()).Volume(), 0)

        # Verify that an edge or wire must be present
        with self.assertRaises(Exception):
            cq.Workplane("XY").textOnPath("error", 5, 1, 1)

    def test_hexArray(self):
        hex_positions = (
            cq.Workplane("XY").hexArray(diagonal=1, xCount=2, yCount=2).vals()
        )
        # center: Union[bool, tuple[bool, bool]] = True,
        self.assertTupleAlmostEquals(hex_positions[0].toTuple(), (-0.375, 0.0, 0.0), 7)
        self.assertTupleAlmostEquals(
            hex_positions[1].toTuple(), (-0.375, 0.8660254037844387, 0.0), 7
        )
        self.assertTupleAlmostEquals(
            hex_positions[2].toTuple(), (0.375, 0.4330127018922193, 0.0), 7
        )
        self.assertTupleAlmostEquals(
            hex_positions[3].toTuple(), (0.375, 1.299038105676658, 0.0), 7
        )
        # Verify that an edge or wire must be present
        with self.assertRaises(ValueError):
            cq.Workplane("XY").hexArray(diagonal=0, xCount=2, yCount=2)
        with self.assertRaises(ValueError):
            cq.Workplane("XY").hexArray(diagonal=1, xCount=0, yCount=2)
        with self.assertRaises(ValueError):
            cq.Workplane("XY").hexArray(diagonal=1, xCount=2, yCount=0)

    def test_thicken(self):
        box = cq.Workplane("XY").rect(1, 1).extrude(1).faces("<Z").thicken(2).val()
        self.assertAlmostEqual(box.Volume(), 2, 7)


class PlaneTests(unittest.TestCase):
    def test_to_from_local_coords(self):
        """Tests the toLocalCoords and fromLocalCoords methods"""

        # Test vector translation
        v1 = cq.Vector(1, 2, 0)
        p1 = cq.Plane.named("XZ")
        self.assertTupleAlmostEquals(
            p1.toLocalCoords(v1).toTuple(), (v1.x, v1.z, -v1.y), 3
        )

        # Test shape translation
        box1 = cq.Workplane("XY").box(2, 4, 8)
        box1_max_v = box1.vertices(">X and >Y and >Z").val()  # (1.0, 2.0, 4.0)
        box2_max_v = (
            cq.Workplane(p1)
            .add(p1.toLocalCoords(box1.solids().val()))
            .vertices(">X and >Y and >Z")
            .val()
        )  # (1.0, 4.0, 2.0)
        self.assertTupleAlmostEquals(
            (box1_max_v.X, box1_max_v.Y, box1_max_v.Z),
            (box2_max_v.X, box2_max_v.Z, box2_max_v.Y),
            3,
        )

        # Test bounding box translation
        bb1 = box1.solids().val().BoundingBox()
        bb2 = p1.toLocalCoords(bb1)
        self.assertTupleAlmostEquals((bb2.xmax, bb2.ymax, bb2.zmax), (1, 4, -2), 3)

        # Test for unsupported type (Location unsupported)
        with self.assertRaises(ValueError):
            p1.toLocalCoords(cq.Location(cq.Vector(1, 1, 1)))

        # Test vector translation back to world coordinates
        v2 = (
            cq.Workplane(p1)
            .lineTo(1, 2, 4)
            .vertices(">X and >Y and >Z")
            .val()
            .toTuple()
        )  # (1.0, 2.0, 4.0)
        v3 = p1.fromLocalCoords(v2)  # (1.0, 4.0, -2.0)
        self.assertTupleAlmostEquals(v2, (v3.x, v3.z, -v3.y), 3)


class VectorTests(unittest.TestCase):
    """Extensions to the Vector class"""

    def test_vector_rotate(self):
        """Validate vector rotate methods"""
        vector_x = cq.Vector(1, 0, 1).rotateX(45)
        vector_y = cq.Vector(1, 2, 1).rotateY(45)
        vector_z = cq.Vector(-1, -1, 3).rotateZ(45)
        self.assertTupleAlmostEquals(
            vector_x.toTuple(), (1, -math.sqrt(2) / 2, math.sqrt(2) / 2), 7
        )
        self.assertTupleAlmostEquals(vector_y.toTuple(), (math.sqrt(2), 2, 0), 7)
        self.assertTupleAlmostEquals(vector_z.toTuple(), (0, -math.sqrt(2), 3), 7)

    def testGetSignedAngle(self):
        """Verify getSignedAngle calculations with and without a provided normal"""
        a = math.pi / 3
        v1 = cq.Vector(1, 0, 0)
        v2 = cq.Vector(math.cos(a), -math.sin(a), 0)
        d1 = v1.getSignedAngle(v2)
        d2 = v1.getSignedAngle(v2, cq.Vector(0, 0, 1))
        self.assertAlmostEqual(d1, a)
        self.assertAlmostEqual(d2, -a)

    def test_toVertex(self):
        """Vertify conversion of Vector to Vertex"""
        v = cq.Vector(1, 2, 3).toVertex()
        self.assertTrue(isinstance(v, cq.Vertex))
        self.assertTupleAlmostEquals(v.toTuple(), (1, 2, 3), 5)


class ProjectionTests(unittest.TestCase):
    def test_flat_projection(self):

        sphere = cq.Solid.makeSphere(50, angleDegrees1=-90)
        projection_direction = cq.Vector(0, -1, 0)
        planar_text_faces = (
            cq.Workplane("XZ")
            .text(
                "Flat",
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
        self.assertEqual(len(projected_text_faces), 4)

    def test_conical_projection(self):
        sphere = cq.Solid.makeSphere(50, angleDegrees1=-90)
        projection_center = cq.Vector(0, 0, 0)
        planar_text_faces = (
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
        planar_text_faces = [f.translate((0, -60, 0)) for f in planar_text_faces]

        projected_text_faces = [
            f.projectToShape(sphere, center=projection_center)[0]
            for f in planar_text_faces
        ]
        self.assertEqual(len(projected_text_faces), 8)

    def test_projection_with_internal_points(self):
        sphere = cq.Solid.makeSphere(50, angleDegrees1=-90)
        f = cq.Sketch().rect(10, 10)._faces.Faces()[0].translate(cq.Vector(0, 0, 60))
        pts = [cq.Vector(x, y, 60) for x in [-5, 5] for y in [-5, 5]]
        projected_faces = f.projectToShape(
            sphere, center=(0, 0, 0), internalFacePoints=pts
        )
        self.assertEqual(len(projected_faces), 1)

    def test_text_projection(self):

        sphere = cq.Solid.makeSphere(50, angleDegrees1=-90)
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
        projected_text = sphere.projectText(
            txt="project - 'the quick brown fox jumped over the lazy dog'",
            fontsize=14,
            font="Serif",
            fontPath="/usr/share/fonts/truetype/freefont",
            depth=3,
            path=arch_path,
        )
        self.assertEqual(len(projected_text.Solids()), 49)
        projected_text = sphere.projectText(
            txt="project - 'the quick brown fox jumped over the lazy dog'",
            fontsize=14,
            font="Serif",
            fontPath="/usr/share/fonts/truetype/freefont",
            depth=0,
            path=arch_path,
        )
        self.assertEqual(len(projected_text.Solids()), 0)
        self.assertEqual(len(projected_text.Faces()), 49)

    def test_error_handling(self):
        sphere = cq.Solid.makeSphere(50, angleDegrees1=-90)
        f = cq.Sketch().rect(10, 10)._faces.Faces()[0]
        with self.assertRaises(ValueError):
            f.projectToShape(sphere, center=None, direction=None)[0]
        w = cq.Workplane("XY").rect(10, 10).wires().val()
        with self.assertRaises(ValueError):
            w.projectToShape(sphere, center=None, direction=None)[0]


class EmbossTests(unittest.TestCase):
    def test_emboss_text(self):

        sphere = cq.Solid.makeSphere(50, angleDegrees1=-90)
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
        self.assertEqual(len(projected_text.Solids()), 47)
        projected_text = sphere.embossText(
            txt="emboss - 'the quick brown fox jumped over the lazy dog'",
            fontsize=14,
            font="Serif",
            fontPath="/usr/share/fonts/truetype/freefont",
            depth=0,
            path=arch_path,
        )
        self.assertEqual(len(projected_text.Faces()), 47)
        self.assertEqual(len(projected_text.Solids()), 0)

    def test_emboss_face(self):
        sphere = cq.Solid.makeSphere(50, angleDegrees1=-90)
        square_face = cq.Face.makeFromWires(
            cq.Workplane("XY").rect(12, 12).wires().val(), []
        )
        embossed_face = square_face.embossToShape(
            sphere,
            surfacePoint=(0, 0, 50),
            surfaceXDirection=(1, 1, 0),
        )
        self.assertTrue(embossed_face.isValid())

        pts = [cq.Vector(x, y, 0) for x in [-5, 5] for y in [-5, 5]]
        embossed_face = square_face.embossToShape(
            sphere,
            surfacePoint=(0, 0, 50),
            surfaceXDirection=(1, 1, 0),
            internalFacePoints=pts,
        )
        self.assertTrue(embossed_face.isValid())

        square_face = cq.Sketch().rect(12, 12)._faces.Faces()[0]
        with self.assertRaises(RuntimeError):
            with self.assertWarns(UserWarning):
                square_face.embossToShape(
                    sphere,
                    surfacePoint=(0, 0, 50),
                    surfaceXDirection=(1, 1, 0),
                )

    def test_emboss_wire(self):
        sphere = cq.Solid.makeSphere(50, angleDegrees1=-90)
        triangle_face = cq.Wire.makePolygon(
            [
                cq.Vector(0, 0, 0),
                cq.Vector(6, 6, 0),
                cq.Vector(-6, 6, 0),
                cq.Vector(0, 0, 0),
            ]
        )
        embossed_face = triangle_face.embossToShape(
            sphere,
            surfacePoint=(0, 0, 50),
            surfaceXDirection=(1, 1, 0),
        )
        self.assertTrue(embossed_face.isValid())


class VertexTests(unittest.TestCase):
    """Test the extensions to the cadquery Vertex class"""

    def test_vertex_add(self):
        test_vertex = cq.Vertex.makeVertex(0, 0, 0)
        self.assertTupleAlmostEquals(
            (test_vertex + (100, -40, 10)).toTuple(), (100, -40, 10), 7
        )
        self.assertTupleAlmostEquals(
            (test_vertex + cq.Vector(100, -40, 10)).toTuple(), (100, -40, 10), 7
        )
        self.assertTupleAlmostEquals(
            (test_vertex + cq.Vertex.makeVertex(100, -40, 10)).toTuple(),
            (100, -40, 10),
            7,
        )
        with self.assertRaises(TypeError):
            test_vertex + [1, 2, 3]

    def test_vertex_sub(self):
        test_vertex = cq.Vertex.makeVertex(0, 0, 0)
        self.assertTupleAlmostEquals(
            (test_vertex - (100, -40, 10)).toTuple(), (-100, 40, -10), 7
        )
        self.assertTupleAlmostEquals(
            (test_vertex - cq.Vector(100, -40, 10)).toTuple(), (-100, 40, -10), 7
        )
        self.assertTupleAlmostEquals(
            (test_vertex - cq.Vertex.makeVertex(100, -40, 10)).toTuple(),
            (-100, 40, -10),
            7,
        )
        with self.assertRaises(TypeError):
            test_vertex - [1, 2, 3]

    def test_vertex_str(self):
        self.assertEqual(str(cq.Vertex.makeVertex(0, 0, 0)), "Vertex: (0.0, 0.0, 0.0)")

    def test_vertex_to_vector(self):
        self.assertIsInstance(cq.Vertex.makeVertex(0, 0, 0).toVector(), cq.Vector)
        self.assertTupleAlmostEquals(
            cq.Vertex.makeVertex(0, 0, 0).toVector().toTuple(), (0.0, 0.0, 0.0), 7
        )


class FastenerTests(unittest.TestCase):
    def test_clearance_hole(self):
        screw = SocketHeadCapScrew(size="M6-1", fastener_type="iso4762", length=40)
        depth = screw.min_hole_depth()
        pillow_block = cq.Assembly(None, name="pillow_block")
        box = (
            cq.Workplane("XY")
            .box(10, 10, 10)
            .faces(">Z")
            .workplane()
            .clearanceHole(fastener=screw, baseAssembly=pillow_block, depth=depth)
            .val()
        )
        self.assertLess(box.Volume(), 999.99)
        self.assertEqual(len(pillow_block.children), 1)
        self.assertEqual(pillow_block.fastenerQuantities(bom=False)[screw], 1)
        self.assertEqual(len(pillow_block.fastenerQuantities(bom=True)), 1)
        self.assertEqual(len(pillow_block.fastenerQuantities(bom=True, deep=False)), 1)

    def test_invalid_clearance_hole(self):
        for fastener_class in Screw.__subclasses__() + Nut.__subclasses__():
            fastener_type = list(fastener_class.types())[0]
            fastener_size = fastener_class.sizes(fastener_type=fastener_type)[0]
            if fastener_class in Screw.__subclasses__():
                fastener = fastener_class(
                    size=fastener_size,
                    fastener_type=fastener_type,
                    length=15,
                    simple=True,
                )
            else:
                fastener = fastener_class(
                    size=fastener_size, fastener_type=fastener_type, simple=True
                )
            with self.assertRaises(ValueError):
                (
                    cq.Workplane("XY")
                    .box(10, 10, 10)
                    .faces(">Z")
                    .workplane()
                    .clearanceHole(fastener=fastener, depth=40, fit="Bad")
                )
        nut = HeatSetNut(size="M3-0.5-Standard", fastener_type="McMaster-Carr")
        with self.assertRaises(ValueError):
            (
                cq.Workplane("XY")
                .box(20, 20, 20)
                .faces(">Z")
                .workplane()
                .clearanceHole(fastener=nut, depth=40)
            )

    def test_tap_hole(self):
        nut = DomedCapNut(size="M6-1", fastener_type="din1587")
        washer = ChamferedWasher(size="M6", fastener_type="iso7090")
        pillow_block = cq.Assembly(None, name="pillow_block")
        box = (
            cq.Workplane("XY")
            .box(10, 10, 10)
            .faces(">Z")
            .workplane()
            .tapHole(fastener=nut, baseAssembly=pillow_block, washers=[washer])
            .val()
        )
        self.assertLess(box.Volume(), 999.99)
        self.assertEqual(len(pillow_block.children), 2)

    def test_invalid_tap_hole(self):
        for fastener_class in Screw.__subclasses__() + Nut.__subclasses__():
            fastener_type = list(fastener_class.types())[0]
            fastener_size = fastener_class.sizes(fastener_type=fastener_type)[0]
            if fastener_class in Screw.__subclasses__():
                fastener = fastener_class(
                    size=fastener_size,
                    fastener_type=fastener_type,
                    length=15,
                    simple=True,
                )
            else:
                fastener = fastener_class(
                    size=fastener_size, fastener_type=fastener_type, simple=True
                )
            with self.assertRaises(ValueError):
                (
                    cq.Workplane("XY")
                    .box(10, 10, 10)
                    .faces(">Z")
                    .workplane()
                    .tapHole(fastener=fastener, depth=40, material="Bad")
                )
        nut = HeatSetNut(size="M3-0.5-Standard", fastener_type="McMaster-Carr")
        with self.assertRaises(ValueError):
            (
                cq.Workplane("XY")
                .box(20, 20, 20)
                .faces(">Z")
                .workplane()
                .tapHole(fastener=nut, depth=40)
            )

    def test_threaded_hole(self):
        screw = SocketHeadCapScrew(size="M6-1", fastener_type="iso4762", length=40)
        washer = ChamferedWasher(size="M6", fastener_type="iso7090")
        pillow_block = cq.Assembly(None, name="pillow_block")
        box = (
            cq.Workplane("XY")
            .box(20, 20, 20)
            .faces(">Z")
            .workplane()
            .threadedHole(
                fastener=screw,
                depth=20,
                baseAssembly=pillow_block,
                washers=[washer, washer],
                simple=False,
                counterSunk=False,
            )
            .faces("<X")
            .workplane()
            .threadedHole(
                fastener=screw,
                depth=20,
                simple=True,
                counterSunk=False,
            )
            .val()
        )
        self.assertLess(box.Volume(), 8000)
        self.assertEqual(len(pillow_block.children), 3)
        self.assertEqual(len(pillow_block.fastenerLocations(screw)), 1)

    def test_invalid_threaded_hole(self):
        nut = HeatSetNut(size="M3-0.5-Standard", fastener_type="McMaster-Carr")
        with self.assertRaises(ValueError):
            (
                cq.Workplane("XY")
                .box(20, 20, 20)
                .faces(">Z")
                .workplane()
                .threadedHole(fastener=nut, depth=40)
            )

    def test_push_fastener_locations(self):
        # Create the screws that will fasten the plates together
        cap_screw = SocketHeadCapScrew(
            size="M2-0.4", length=6, fastener_type="iso4762", simple=False
        )

        # Two assemblies are required - the top will contain the screws
        bracket_assembly = cq.Assembly(None, name="top_plate_assembly")
        square_tube_assembly = cq.Assembly(None, name="base_plate_assembly")

        # Create an angle bracket and add clearance holes for the screws
        angle_bracket = (
            cq.Workplane("YZ")
            .moveTo(-9, 1)
            .hLine(10)
            .vLine(-10)
            .offset2D(1)
            .extrude(10, both=True)
            .faces(">Z")
            .workplane()
            .pushPoints([(5, -5), (-5, -5)])
            .clearanceHole(
                fastener=cap_screw, counterSunk=False, baseAssembly=bracket_assembly
            )
            .faces(">Y")
            .workplane()
            .pushPoints([(0, -7)])
            .clearanceHole(
                fastener=cap_screw, counterSunk=False, baseAssembly=bracket_assembly
            )
        )
        # Add the top plate to the top assembly so it can be placed with the screws
        bracket_assembly.add(angle_bracket, name="angle_bracket")
        # Add the top plate and screws to the base assembly
        square_tube_assembly.add(
            bracket_assembly,
            name="top_plate_assembly",
            loc=cq.Location(cq.Vector(20, 10, 10)),
        )

        # Create the square tube
        square_tube = (
            cq.Workplane("YZ")
            .rect(18, 18)
            .rect(14, 14)
            .offset2D(1)
            .extrude(30, both=True)
        )
        original_tube_volume = square_tube.val().Volume()
        # Complete the square tube assembly by adding the square tube
        square_tube_assembly.add(square_tube, name="square_tube")
        # Add tap holes to the square tube that align with the angle bracket
        square_tube = square_tube.pushFastenerLocations(
            cap_screw, square_tube_assembly
        ).tapHole(fastener=cap_screw, counterSunk=False, depth=10)
        self.assertLess(square_tube.val().Volume(), original_tube_volume)

        # Where are the cap screw holes in the square tube?
        fastener_positions = [(25.0, 5.0, 12.0), (15.0, 5.0, 12.0), (20.0, 12.0, 5.0)]
        for i, loc in enumerate(square_tube_assembly.fastenerLocations(cap_screw)):
            self.assertTupleAlmostEquals(loc.toTuple()[0], fastener_positions[i], 7)
            self.assertTrue(str(fastener_positions[i]) in str(loc))

    def test_fastener_quantities(self):
        screw = SocketHeadCapScrew(size="M6-1", fastener_type="iso4762", length=40)
        depth = screw.min_hole_depth()
        pillow_block = cq.Assembly(None, name="pillow_block")
        box = (
            cq.Workplane("XY")
            .box(10, 10, 10)
            .faces(">Z")
            .workplane()
            .clearanceHole(fastener=screw, baseAssembly=pillow_block, depth=depth)
            .val()
        )
        machine = cq.Assembly(None, name="machine")
        machine.add(pillow_block)
        self.assertLess(box.Volume(), 999.99)
        self.assertEqual(len(pillow_block.children), 1)
        self.assertEqual(pillow_block.fastenerQuantities(bom=False)[screw], 1)
        self.assertDictEqual(
            pillow_block.fastenerQuantities(bom=True),
            {"SocketHeadCapScrew(iso4762): M6-1x40": 1},
        )
        self.assertEqual(len(machine.fastenerQuantities(bom=True, deep=False)), 0)
        self.assertEqual(len(machine.fastenerQuantities(bom=True, deep=True)), 1)

    def test_insert_hole(self):
        nut = HeatSetNut(size="M3-0.5-Standard", fastener_type="McMaster-Carr")
        block_assembly = cq.Assembly(None, name="block_assembly")
        box = (
            cq.Workplane("XY")
            .box(20, 20, 20)
            .faces(">Z")
            .workplane()
            .insertHole(fastener=nut, baseAssembly=block_assembly)
            .val()
        )
        self.assertLess(box.Volume(), 7999.99)
        self.assertEqual(len(block_assembly.children), 1)
        self.assertEqual(block_assembly.fastenerQuantities(bom=False)[nut], 1)

    def test_invalid_insert_hole(self):
        screw = SocketHeadCapScrew(size="M6-1", fastener_type="iso4762", length=40)
        with self.assertRaises(ValueError):
            (
                cq.Workplane("XY")
                .box(20, 20, 20)
                .faces(">Z")
                .workplane()
                .insertHole(fastener=screw)
            )


if __name__ == "__main__":
    unittest.main()
