"""

Extensions Sketch Unit Tests

name: sketch_tests.py
by:   Gumyr
date: June 10th 2022

desc: Unit tests for the Sketch class of the extensions sub-package of cq_warehouse

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
from math import pi
import unittest
import cadquery as cq
import cq_warehouse.extensions

# from cq_warehouse.extensions import *


def _assertTupleAlmostEquals(self, expected, actual, places, msg=None):
    """Check Tuples"""
    for i, j in zip(actual, expected):
        self.assertAlmostEqual(i, j, places, msg=msg)


unittest.TestCase.assertTupleAlmostEquals = _assertTupleAlmostEquals


class TextTests(unittest.TestCase):
    """Test the Sketch Text feature"""

    def test_simple_text(self):
        simple_text = cq.Sketch().text("sketch", 10)
        self.assertEqual(len(simple_text.faces().vals()), 6)

    def test_rotated_text(self):
        non_rotated_text = cq.Sketch().text("I", 10)
        rotated_text = cq.Sketch().text("I", 10, angle=90)
        self.assertLess(
            non_rotated_text.faces().val().BoundingBox().xlen,
            rotated_text.faces().val().BoundingBox().xlen,
        )

    def test_text_on_path(self):
        linear_text = cq.Sketch().text("x" * 50, 10)
        arc_text = cq.Sketch().arc((0, 0), 100, 0, 180).text("x" * 50, 10)
        self.assertLess(
            linear_text.vertices(">Y").val().Y, arc_text.vertices(">Y").val().Y
        )


class ValTests(unittest.TestCase):
    """Test extraction of objects from a Sketch"""

    def test_val(self):
        rectangle_face = cq.Sketch().rect(10, 20).faces().val()
        self.assertTrue(isinstance(rectangle_face, cq.Face))

    def test_vals(self):
        rectangle_faces = (
            cq.Sketch().rarray(100, 100, 2, 2).rect(10, 10).reset().faces().vals()
        )
        self.assertEqual(len(rectangle_faces), 4)
        self.assertTrue(isinstance(rectangle_faces[0], cq.Face))

    def test_val_exception(self):
        with self.assertRaises(ValueError):
            cq.Sketch().val()

    def test_vals_exception(self):
        with self.assertRaises(ValueError):
            cq.Sketch().vals()


class AddTests(unittest.TestCase):
    """Test adding an object to a Sketch"""

    def test_add(self):
        wire = cq.Wire.makeCircle(10, cq.Vector(0, 0, 0), normal=cq.Vector(0, 0, 1))
        face = cq.Face.makeFromWires(wire)
        edge = cq.Edge.makeLine(cq.Vector(0, 0, 0), cq.Vector(10, 10, 0))

        sketch_faces = cq.Sketch().add(face, tag="face")
        self.assertEqual(len(sketch_faces.faces().vals()), 1)
        self.assertEqual(len(sketch_faces.faces(tag="face").vals()), 1)

        sketch_edges = cq.Sketch().add(edge, tag="edge")
        self.assertEqual(len(sketch_edges.edges().vals()), 1)
        self.assertEqual(len(sketch_edges.edges(tag="edge").vals()), 1)

        sketch_wires = cq.Sketch().add(wire, tag="wire")
        self.assertEqual(len(sketch_wires._wires), 1)
        # Wire selection doesn't seem to be supported
        # self.assertEqual(len(sketch_wires.wires(tag="wire").vals()), 1)


class BoundingBoxTests(unittest.TestCase):
    """Test creating bounding boxes around selected features"""

    def test_single_face(self):
        square = cq.Sketch().rect(10, 10)
        square_face = square.faces().val()
        square_bb_face = square.faces().bounding_box(tag="bb").faces(tag="bb").val()
        self.assertAlmostEqual(square_face.cut(square_bb_face).Area(), 0, 5)

    def test_single_edge(self):
        arc = cq.Sketch().arc((0, 10), 10, 270, 90)
        arc_bb_target_face = (
            cq.Sketch().push([(5, 5)]).rect(10, 10).reset().faces().val()
        )
        arc_bb_face = arc.edges().bounding_box().reset().faces().val()
        self.assertAlmostEqual(arc_bb_target_face.cut(arc_bb_face).Area(), 0, 5)

    def test_multiple_faces(self):
        circle_faces = (
            cq.Sketch()
            .rarray(40, 40, 2, 2)
            .circle(10)
            .reset()
            .faces()
            .bounding_box(tag="x", mode="c")
            .vertices(tag="x")
            .circle(7)
            .clean()
            .reset()
            .faces()
            .vals()
        )
        self.assertEqual(len(circle_faces), 4)
        self.assertEqual(len(circle_faces[0].Edges()), 8)


class MirrorTests(unittest.TestCase):
    """Testing mirror_x and mirror_y"""

    def test_mirror_x(self):
        mirror_edges = (
            cq.Sketch()
            .polyline((0, 0), (0, 1), (1, 1), (1, 0))
            .edges()
            .mirror_x()
            .reset()
            .assemble()
            .faces()
            .val()
        )
        self.assertAlmostEqual(mirror_edges.Area(), 2, 5)

    def test_mirror_y(self):
        mirror_edges = (
            cq.Sketch()
            .polyline((0, 0), (1, 0), (1, 1), (0, 1))
            .edges()
            .mirror_y()
            .reset()
            .assemble()
            .faces()
            .val()
        )
        self.assertAlmostEqual(mirror_edges.Area(), 2, 5)

    def test_mirror_x_exceptions(self):
        with self.assertRaises(ValueError):
            cq.Sketch().mirror_x()

    def test_mirror_y_exceptions(self):
        with self.assertRaises(ValueError):
            cq.Sketch().mirror_y()


class SplineTests(unittest.TestCase):
    """Testing spline"""

    def test_spline(self):
        boomerang = (
            cq.Sketch()
            .center_arc(center=(0, 0), radius=10, start_angle=0, arc_size=90, tag="c")
            .spline("c@1", (10, 10), "c@0")
            .assemble(tag="b")
            .faces(tag="b")
            .val()
        )
        self.assertAlmostEqual(boomerang.Area(), 38.1, 1)

    def test_spline_with_tangents(self):
        boomerang = (
            cq.Sketch()
            .center_arc(center=(0, 0), radius=10, start_angle=0, arc_size=90, tag="c")
            .spline("c@1", (10, 10), "c@0", tangents=("c@1", "c@0"))
            .assemble(tag="b")
            .faces(tag="b")
            .val()
        )
        self.assertAlmostEqual(boomerang.Area(), 54.8, 1)

    def test_spline_with_tangents_and_scalars(self):
        boomerang = (
            cq.Sketch()
            .center_arc(center=(0, 0), radius=10, start_angle=0, arc_size=90, tag="c")
            .spline(
                "c@1", (10, 10), "c@0", tangents=("c@1", "c@0"), tangent_scalars=(5, 5)
            )
            .assemble(tag="b")
            .faces(tag="b")
            .val()
        )
        self.assertAlmostEqual(boomerang.Area(), 94.8, 1)


class PolylineTests(unittest.TestCase):
    """Testing Polyline"""

    def test_polyline(self):
        square = (
            cq.Sketch()
            .polyline((0, 0), (1, 0), tag="l1")
            .polyline("l1@1", (1, 1), tag="l2")
            .polyline("l2@1", (0, 1), tag="l3")
            .polyline("l3@1", "l1@0")
            .assemble()
            .faces()
            .val()
        )
        self.assertAlmostEqual(square.Area(), 1, 5)

    def test_polyline_exceptions(self):
        with self.assertRaises(ValueError):
            cq.Sketch().polyline((0, 0))


class CenterArcTests(unittest.TestCase):
    def test_greater_360(self):
        circle = cq.Sketch().center_arc((0, 0), 1, 0, 720).assemble().faces().val()
        self.assertAlmostEqual(circle.Area(), pi, 5)


class ThreePointArcTests(unittest.TestCase):
    def test_three_point(self):
        three_point_arc = (
            cq.Sketch().three_point_arc((0, 10), (0, 0), (10, 0)).edges().val()
        )
        self.assertTupleAlmostEquals(
            three_point_arc.positionAt(0).toTuple(), (0, 10, 0), 3
        )

    def test_three_point_arc_exception(self):
        with self.assertRaises(ValueError):
            cq.Sketch().three_point_arc((0, 10), (0, 0))


class TangentArcTests(unittest.TestCase):
    def test_tangent_arc(self):
        tangent_arc = (
            cq.Sketch()
            .center_arc(center=(0, 0), radius=10, start_angle=0, arc_size=90, tag="c")
            .tangent_arc("c@0.5", (10, 10), tag="t")
            .edges()
            .vals()
        )
        self.assertTupleAlmostEquals(
            tangent_arc[1].positionAt(1).toTuple(), (10, 10, 0), 3
        )
        tangent_arc = (
            cq.Sketch().tangent_arc((0, 0), (10, 10), tangent=(0, 1)).edges().val()
        )
        self.assertTupleAlmostEquals(
            tangent_arc.positionAt(1).toTuple(), (10, 10, 0), 3
        )

    def test_no_tangents_exception(self):
        with self.assertRaises(ValueError):
            cq.Sketch().tangent_arc((0, 0), (10, 10))

    def test_too_few_points_exception(self):
        with self.assertRaises(ValueError):
            cq.Sketch().tangent_arc((10, 10), tangent=(1, 1))


class PushPointsTests(unittest.TestCase):
    def test_push_tuple(self):
        points = cq.Sketch().push_points((0, 0), (1, 1), (2, 0))
        self.assertEqual(len(points._selection), 3)

    def test_push_snap(self):
        points = (
            cq.Sketch()
            .three_point_arc((0, 0), (0, 10), (10, 10), tag="l1")
            .push_points("l1@0", "l1@0.5", "l1@1", tag="points")
        )
        self.assertEqual(len(points._selection), 3)
        self.assertEqual(len(points._tags["points"]), 3)


class SnapTests(unittest.TestCase):
    def test_simple_snaps(self):
        snap = (
            cq.Sketch()
            .segment((0, 0), (10, 10), tag="l")
            .reset()
            .push_points("l@0", "l@1")
        )
        self.assertEqual(len(snap._selection), 2)

    def test_mixed_snaps(self):
        snap = (
            cq.Sketch()
            .segment((0, 0), (10, 10), tag="l")
            .reset()
            .push_points("l@0", (10, 10), cq.Vector(1, 1))
        )
        self.assertEqual(len(snap._selection), 3)

    def test_start_middle_end_snap(self):
        snap = (
            cq.Sketch()
            .segment((0, 0), (10, 10), tag="l")
            .reset()
            .push_points("l@start", "l@middle", "l@end")
        )
        self.assertEqual(len(snap._selection), 3)

    def test_snap_exception(self):
        with self.assertRaises(ValueError):
            cq.Sketch().segment((0, 0), (10, 10), tag="l").reset().push_points("l@bad")


# class HullTests(unittest.TestCase):
#     def test_hull(self):


if __name__ == "__main__":
    unittest.main()
