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
import math
import unittest
import cadquery as cq
from cq_warehouse.extensions import *


def _assertTupleAlmostEquals(self, expected, actual, places, msg=None):
    """Check Tuples"""
    for i, j in zip(actual, expected):
        self.assertAlmostEqual(i, j, places, msg=msg)


unittest.TestCase.assertTupleAlmostEquals = _assertTupleAlmostEquals


class Workplane(unittest.TestCase):
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


class TestPlane(unittest.TestCase):
    def test_toLocalWorldCoords(self):
        """Tests the toLocalCoords and toGlocalCoords methods"""

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
        v3 = p1.toWorldCoords(v2)  # (1.0, 4.0, -2.0)
        self.assertTupleAlmostEquals(v2, (v3.x, v3.z, -v3.y), 3)


class TestVectorMethods(unittest.TestCase):
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

    def test_point_to_vector(self):
        """Validate conversion of 2D points to 3D vectors"""
        point = cq.Vector(1, 2)
        with self.assertRaises(ValueError):
            point.pointToVector((1, 0, 0))
        with self.assertRaises(ValueError):
            point.pointToVector("x")
        self.assertTupleAlmostEquals(point.pointToVector("XY").toTuple(), (1, 2, 0), 7)
        self.assertTupleAlmostEquals(
            point.pointToVector("XY", 4).toTuple(), (1, 2, 4), 7
        )
        self.assertTupleAlmostEquals(
            point.pointToVector("XZ", 3).toTuple(), (1, 3, 2), 7
        )
        self.assertTupleAlmostEquals(
            point.pointToVector("YZ", 5).toTuple(), (5, 1, 2), 7
        )

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


class TestProjection(unittest.TestCase):
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


class TestEmboss(unittest.TestCase):
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


class TestVertexExtensions(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
