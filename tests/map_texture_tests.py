"""
Unit tests for the cq_warehouse map_texture sub-package

name: map_texture_tests.py
by:   Gumyr
date: January 10th 2022

desc: Unit tests for the map_texture sub-package of cq_warehouse

license:

    Copyright 2021 Gumyr

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
import math
import cadquery as cq
from cq_warehouse.map_texture import *


class TestSupportFunctions(unittest.TestCase):
    def testToLocalWorldCoords(self):
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
            p1.toLocalCoords(cq.Location(Vector(1, 1, 1)))

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

    def testGetSignedAngle(self):
        """Verify getSignedAngle calculations with and without a provided normal"""
        a = math.pi / 3
        v1 = Vector(1, 0, 0)
        v2 = Vector(math.cos(a), -math.sin(a), 0)
        d1 = v1.getSignedAngle(v2)
        d2 = v1.getSignedAngle(v2, Vector(0, 0, 1))
        self.assertAlmostEqual(d1, a)
        self.assertAlmostEqual(d2, -a)


class TestTextOnPath(unittest.TestCase):
    def testTextOnPath(self):

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
