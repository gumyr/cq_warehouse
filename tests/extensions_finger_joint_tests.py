"""

Finger Joint Boxes Unit Tests

name: finger_joint_tests.py
by:   Gumyr
date: May 30th 2022

desc: Unit tests for the finger joint part of the extensions sub-package of cq_warehouse

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


class FingerJointBoxTests(unittest.TestCase):
    """Test the Finger Jointed Box feature"""

    def test_simple_box(self):
        """Test that the fingers are generated correctly"""
        simple_box_assembly = cq.Assembly()
        simple_box = cq.Workplane("XY").box(100, 80, 50)
        simple_box_volume = (
            simple_box.faces(">Z").shell(-5, kind="intersection").val().Volume()
        )
        simple_box_faces = (
            simple_box.edges("not >Z")
            .makeFingerJoints(
                materialThickness=5,
                targetFingerWidth=10,
                kerfWidth=0,
                baseAssembly=simple_box_assembly,
            )
            .faces()
            .vals()
        )
        self.assertEqual(len(simple_box_faces), 5)
        self.assertTrue(simple_box_assembly.areObjectsValid())
        self.assertFalse(simple_box_assembly.doObjectsIntersect())
        self.assertAlmostEqual(
            simple_box_volume, simple_box_assembly.toCompound().Volume(), 5
        )

    def test_internal_corner(self):
        """Test that an internal corner is handled correctly"""
        internal_corner_assembly = Assembly()
        internal_corner_box = (
            Workplane("XY")
            .moveTo(10, -20)
            .hLine(40)
            .vLine(70)
            .hLine(-100)
            .vLine(-100)
            .hLine(60)
            .close()
            .extrude(60)
        )
        internal_corner_box_volume = (
            internal_corner_box.faces(">Z")
            .shell(-5, kind="intersection")
            .val()
            .Volume()
        )
        internal_corner_box_faces = (
            internal_corner_box.rotate((0, 0, 0), (0, 0, 1), 30)
            .edges("not >Z")
            # .edges(cq.selectors.BoxSelector((-15, -25, -5), (15, 15, 65)))
            .makeFingerJoints(
                materialThickness=5,
                targetFingerWidth=20,
                kerfWidth=0,
                baseAssembly=internal_corner_assembly,
            )
            .faces()
            .vals()
        )
        self.assertEqual(len(internal_corner_box_faces), 7)
        self.assertTrue(internal_corner_assembly.areObjectsValid())
        self.assertFalse(internal_corner_assembly.doObjectsIntersect())
        self.assertAlmostEqual(
            internal_corner_box_volume,
            internal_corner_assembly.toCompound().Volume(),
            5,
        )

    def test_acute_angles(self):
        """Test that the finger depth is calculated correctly"""
        acute_angle_box_assembly = Assembly()
        acute_angle_box_faces = (
            Workplane("XY")
            .polygon(5, 100)
            .extrude(60)
            .edges("not >Z")
            .makeFingerJoints(
                materialThickness=5,
                targetFingerWidth=20,
                kerfWidth=0,
                baseAssembly=acute_angle_box_assembly,
            )
            .faces()
            .vals()
        )
        self.assertEqual(len(acute_angle_box_faces), 6)
        self.assertTrue(acute_angle_box_assembly.areObjectsValid())
        self.assertFalse(acute_angle_box_assembly.doObjectsIntersect(1e-3))

    def test_obtuse_angles(self):
        """Test that the finger depth is calculated correctly"""
        obtuse_angle_box_assembly = Assembly()
        obtuse_box_faces = (
            Workplane("XY")
            .polygon(3, 100)
            .extrude(60)
            .edges("not >Z")
            .makeFingerJoints(
                materialThickness=5,
                targetFingerWidth=20,
                kerfWidth=0,
                baseAssembly=obtuse_angle_box_assembly,
            )
            .faces()
            .vals()
        )
        self.assertEqual(len(obtuse_box_faces), 4)
        self.assertTrue(obtuse_angle_box_assembly.areObjectsValid())
        self.assertFalse(obtuse_angle_box_assembly.doObjectsIntersect())


if __name__ == "__main__":
    unittest.main()
