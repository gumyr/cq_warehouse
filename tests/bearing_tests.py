"""

Bearing Unit Tests

name: bearing_tests.py
by:   Gumyr
date: April 7th 2022

desc: Unit tests for the bearing sub-package of cq_warehouse

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
from cq_warehouse.bearing import *
import cq_warehouse.extensions

MM = 1
IN = 25.4 * MM


def _assertTupleAlmostEquals(self, expected, actual, places, msg=None):
    """Check Tuples"""
    for i, j in zip(actual, expected):
        self.assertAlmostEqual(i, j, places, msg=msg)


unittest.TestCase.assertTupleAlmostEquals = _assertTupleAlmostEquals


class TestBearings(unittest.TestCase):
    """Test creation of all bearings"""

    def test_select_by_size(self):
        self.assertGreater(len(Bearing.select_by_size("M8-22-7")), 0)

    def test_bad_size(self):
        with self.assertRaises(ValueError):
            SingleRowDeepGrooveBallBearing(size="M8", bearing_type="SKT")
        with self.assertRaises(ValueError):
            SingleRowDeepGrooveBallBearing(size="M8-22", bearing_type="SKT")

    def test_bad_type(self):
        with self.assertRaises(ValueError):
            SingleRowDeepGrooveBallBearing(size="M8-22-7", bearing_type="common")

    def test_size(self):
        """Validate diameter and thickness of bearings"""
        for bearing_class in Bearing.__subclasses__():
            for bearing_type in bearing_class.types():
                for bearing_size in bearing_class.sizes(bearing_type=bearing_type):
                    with self.subTest(
                        bearing_class=bearing_class.__name__,
                        bearing_type=bearing_type,
                        size=bearing_size,
                    ):
                        bearing = bearing_class(
                            size=bearing_size, bearing_type=bearing_type
                        )
                        self.assertGreater(bearing.outer_diameter, 0)
                        self.assertGreater(bearing.thickness, 0)
                        self.assertGreater(len(bearing.info), 0)
                        self.assertGreater(len(bearing.cq_object.children), 0)

                        # Check the hole data if available
                        try:
                            clearance_normal = bearing.clearance_hole_diameters[
                                "Normal"
                            ]
                            clearance_close = bearing.clearance_hole_diameters["Close"]
                            clearance_loose = bearing.clearance_hole_diameters["Loose"]
                        except ValueError:
                            pass
                        else:
                            self.assertGreater(
                                clearance_normal,
                                clearance_close,
                            )
                            self.assertGreater(
                                clearance_loose,
                                clearance_normal,
                            )

                        self.assertEqual(bearing.bearing_class, bearing_class.__name__)

    def test_countersink(self):
        """Validate diameter and thickness of bearing"""
        for bearing_class in Bearing.__subclasses__():
            bearing_type = list(bearing_class.types())[0]
            bearing_size = bearing_class.sizes(bearing_type=bearing_type)[0]
            bearing = bearing_class(size=bearing_size, bearing_type=bearing_type)

            box = (
                cq.Workplane("XY")
                .box(10, 10, 10)
                .faces(">Z")
                .workplane()
                .pressFitHole(bearing=bearing)
                .val()
            )
            self.assertLess(box.Volume(), 999.99)


if __name__ == "__main__":
    unittest.main()
