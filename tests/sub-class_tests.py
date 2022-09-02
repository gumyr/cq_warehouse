"""

Extensions Sub-class Cadquery Core Unit Tests

name: sub-class_tests.py
by:   Gumyr
date: Aug 31st 2022

desc: Unit tests for the Cadquery core changes to enable sub-classing.

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


def _assertTupleAlmostEquals(self, expected, actual, places, msg=None):
    """Check Tuples"""
    for i, j in zip(actual, expected):
        self.assertAlmostEqual(i, j, places, msg=msg)


unittest.TestCase.assertTupleAlmostEquals = _assertTupleAlmostEquals


class ApplyTransformTests(unittest.TestCase):
    """Test the _apply_transform method"""

    def test_translate(self):
        test_edge = cq.Edge.makeLine((0, 0, 0), (1, 1, 1))
        translated_edge = test_edge.translate((0, 0, 2))
        self.assertTupleAlmostEquals(
            translated_edge.positionAt(0).toTuple(), (0, 0, 2), 5
        )
        test_solid = cq.Solid.makeBox(1, 1, 1)
        translated_box = test_solid.translate((0, 0, 2))
        translated_box_bb = translated_box.BoundingBox()
        self.assertAlmostEqual(translated_box_bb.xmin, 0, 5)
        self.assertAlmostEqual(translated_box_bb.ymin, 0, 5)
        self.assertAlmostEqual(translated_box_bb.zmin, 2, 5)

    def test_rotate(self):
        test_edge = cq.Edge.makeLine((0, 0, 0), (1, 0, 0))
        rotated_edge = test_edge.rotate((0, 0, 0), (0, 0, 1), 90)
        self.assertTupleAlmostEquals(rotated_edge.positionAt(1).toTuple(), (0, 1, 0), 5)
        test_solid = cq.Solid.makeBox(1, 1, 1)
        rotated_box = test_solid.rotate((0, 0, 0), (0, 0, 1), 90)
        rotated_box_bb = rotated_box.BoundingBox()
        self.assertAlmostEqual(rotated_box_bb.xmin, -1, 5)
        self.assertAlmostEqual(rotated_box_bb.ymin, 0, 5)
        self.assertAlmostEqual(rotated_box_bb.zmin, 0, 5)

    def test_translate_rotate(self):
        test_edge = cq.Edge.makeLine((0, 0, 0), (1, 0, 0))
        translated_edge = test_edge.translate((2, 0, 0))
        rotated_edge = translated_edge.rotate((0, 0, 0), (0, 0, 1), 90)
        self.assertTupleAlmostEquals(rotated_edge.positionAt(1).toTuple(), (0, 3, 0), 5)
        test_solid = cq.Solid.makeBox(1, 1, 1)
        translated_box = test_solid.translate((2, 0, 0))
        rotated_box = translated_box.rotate((0, 0, 0), (0, 0, 1), 90)
        rotated_box_bb = rotated_box.BoundingBox()
        self.assertAlmostEqual(rotated_box_bb.xmin, -1, 5)
        self.assertAlmostEqual(rotated_box_bb.ymin, 2, 5)
        self.assertAlmostEqual(rotated_box_bb.zmin, 0, 5)

    def test_rotate_translate(self):
        test_edge = cq.Edge.makeLine((0, 0, 0), (1, 0, 0))
        rotated_edge = test_edge.rotate((0, 0, 0), (0, 0, 1), 90)
        translated_edge = rotated_edge.translate((2, 0, 0))
        self.assertTupleAlmostEquals(
            translated_edge.positionAt(1).toTuple(), (2, 1, 0), 5
        )
        test_solid = cq.Solid.makeBox(1, 1, 1)
        rotated_box = test_solid.rotate((0, 0, 0), (0, 0, 1), 90)
        translated_box = rotated_box.translate((2, 0, 0))
        translated_box_bb = translated_box.BoundingBox()
        self.assertAlmostEqual(translated_box_bb.xmin, 1, 5)
        self.assertAlmostEqual(translated_box_bb.ymin, 0, 5)
        self.assertAlmostEqual(translated_box_bb.zmin, 0, 5)


class MaintainAttributesTest(unittest.TestCase):
    """Test that object attributes are maintained during normal operations"""

    def test_apply_transform(self):
        box = cq.Solid.makeBox(1, 1, 1)
        box.label = "test box"
        box = box.translate((1, 1, 1))
        self.assertAlmostEqual(box.label, "test box")


if __name__ == "__main__":
    unittest.main()
