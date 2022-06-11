"""

Extensions Sketch Unit Tests

name: finger_joint_tests.py
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
import unittest
import cadquery as cq
from cq_warehouse.extensions import *


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
        # self.assertEqual(len(sketch_wires.wires(tag="wire").vals()), 1)


class PushCenterTests(unittest.TestCase):
    """Test use of the center of an existing object to locate something else"""

    def test_pushCenter(self):

        hull_sketch = (
            cq.Sketch()
            .arc((0, 0), 1.0, 0.0, 360.0)
            .arc((1, 1.5), 0.5, 0.0, 360.0)
            .segment((0.0, 2), (-1, 3.0))
            .hull()
        )
        before_area = hull_sketch.faces().val().Area()
        after_area = (
            hull_sketch.faces()
            .pushCenter()
            .rect(0.1, 0.1, mode="s")
            .reset()
            .faces()
            .val()
            .Area()
        )
        self.assertAlmostEqual(before_area - 0.01, after_area, 5)

    def test_centerOptions(self):
        """Use a triangle to compare center locations"""
        center_of_mass = (
            cq.Sketch()
            .segment((0, 0), (10, 0))
            .segment((0, 5))
            .close()
            .assemble()
            .reset()
            .faces()
            .pushCenter("CenterOfMass")
            ._selection[-1]
        )
        center_of_bb = (
            cq.Sketch()
            .segment((0, 0), (10, 0))
            .segment((0, 5))
            .close()
            .assemble()
            .faces()
            .pushCenter("CenterOfBoundBox")
            ._selection[-1]
        )
        self.assertGreater(center_of_bb.toTuple()[0][1], center_of_mass.toTuple()[0][1])

    def test_error(self):
        with self.assertRaises(ValueError):
            cq.Sketch().rect(10, 10).pushCenter("Error")


if __name__ == "__main__":
    unittest.main()
