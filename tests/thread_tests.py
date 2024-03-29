"""

Thread Unit Tests

name: thread_tests.py
by:   Gumyr
date: November 11th 2021

desc: Unit tests for the fastener sub-package of cq_warehouse

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
from cq_warehouse.thread import *
import cq_warehouse.extensions
from OCP.TopoDS import TopoDS_Shape

MM = 1
IN = 25.4 * MM


class TestSupportFunctions(unittest.TestCase):
    def test_is_safe(self):
        self.assertTrue(is_safe("1 1/8"))
        self.assertFalse(is_safe("rm -rf *"))

    def test_imperial_str_to_float(self):
        self.assertAlmostEqual(imperial_str_to_float("1 1/2"), 1.5 * IN)
        self.assertEqual(imperial_str_to_float("rm -rf *"), "rm -rf *")


class TestThread(unittest.TestCase):
    def test_parsing(self):
        with self.assertRaises(ValueError):
            Thread(
                apex_radius=10,
                apex_width=2,
                root_radius=8,
                root_width=3,
                pitch=2,
                length=20,
                end_finishes=("not", "supported"),
            )

    def test_deprecation(self):
        thread = Thread(
            apex_radius=10,
            apex_width=2,
            root_radius=8,
            root_width=3,
            pitch=2,
            length=20,
        )
        with self.assertWarns(DeprecationWarning):
            occt = thread.cq_object
            self.assertTrue(isinstance(occt, Solid))


class TestIsoThread(unittest.TestCase):
    end_finishes = ["raw", "fade", "square", "chamfer"]

    def test_exterior_thread(self):
        """Simple validity check for an exterior thread"""

        for end0 in TestIsoThread.end_finishes:
            for end1 in TestIsoThread.end_finishes:
                with self.subTest(end0=end0, end1=end1):
                    thread = IsoThread(
                        major_diameter=6 * MM,
                        pitch=1 * MM,
                        length=8 * MM,
                        external=True,
                        end_finishes=(end0, end1),
                        hand="right",
                    )
                    self.assertTrue(thread.isValid())

    def test_interior_thread(self):
        """Simple validity check for an interior thread"""

        for end0 in TestIsoThread.end_finishes:
            for end1 in TestIsoThread.end_finishes:
                with self.subTest(end0=end0, end1=end1):
                    thread = IsoThread(
                        major_diameter=6 * MM,
                        pitch=1 * MM,
                        length=8 * MM,
                        external=False,
                        end_finishes=(end0, end1),
                        hand="left" if end0 == end1 else "right",
                    )
                    self.assertTrue(thread.isValid())

    def test_parsing(self):

        with self.assertRaises(ValueError):
            IsoThread(major_diameter=5, pitch=1, length=5, hand="righty")
        with self.assertRaises(ValueError):
            IsoThread(
                major_diameter=5, pitch=1, length=5, end_finishes=("not", "supported")
            )

    def test_deprecation(self):
        thread = IsoThread(major_diameter=6 * MM, pitch=1 * MM, length=8 * MM)
        with self.assertWarns(DeprecationWarning):
            occt = thread.cq_object
            self.assertTrue(isinstance(occt, Solid))

    def test_simple(self):
        thread = IsoThread(
            major_diameter=6 * MM, pitch=1 * MM, length=8 * MM, simple=True
        )
        self.assertTrue(thread.wrapped.IsNull())


class TestAcmeThread(unittest.TestCase):
    def test_exterior_thread(self):
        """Simple validity check for an exterior thread"""

        acme_thread = AcmeThread(
            size="1 1/4",
            length=1 * IN,
            external=True,
        )
        self.assertTrue(acme_thread.isValid())

    def test_interior_thread(self):
        """Simple validity check for an interior thread"""

        acme_thread = AcmeThread(
            size="1 1/4",
            length=1 * IN,
            external=False,
        )
        self.assertTrue(acme_thread.isValid())

    def test_sizes(self):
        """Validate sizes list if created"""
        self.assertGreater(len(AcmeThread.sizes()), 0)

    def test_parsing(self):

        with self.assertRaises(ValueError):
            AcmeThread(size="1 1/4", length=1 * IN, external=False, hand="righty")
        with self.assertRaises(ValueError):
            AcmeThread(size="1.25", length=1 * IN)
        with self.assertRaises(ValueError):
            AcmeThread(size="1 1/4", length=1 * IN, end_finishes=("not", "supported"))

    def test_deprecation(self):
        acme_thread = AcmeThread(
            size="1 1/4",
            length=1 * IN,
            external=False,
        )
        with self.assertWarns(DeprecationWarning):
            occt = acme_thread.cq_object
            self.assertTrue(isinstance(occt, Solid))


class TestMetricTrapezoidalThread(unittest.TestCase):
    def test_exterior_thread(self):
        """Simple validity check for an exterior thread"""

        trap_thread = MetricTrapezoidalThread(
            size="8x1.5",
            length=10 * MM,
            external=True,
        )
        self.assertTrue(trap_thread.isValid())

    def test_interior_thread(self):
        """Simple validity check for an interior thread"""

        trap_thread = MetricTrapezoidalThread(
            size="95x18",
            length=100 * MM,
            external=False,
        )
        self.assertTrue(trap_thread.isValid())

    def test_parsing(self):
        with self.assertRaises(ValueError):
            MetricTrapezoidalThread(size="8x1", length=50 * MM)

    def test_sizes(self):
        """Validate sizes list if created"""
        self.assertGreater(len(MetricTrapezoidalThread.sizes()), 0)


class TestPlasticBottleThread(unittest.TestCase):
    def test_exterior_thread(self):
        """Simple validity check for an exterior thread"""

        bottle_thread = PlasticBottleThread(
            size="M38SP444",
            external=True,
        )
        self.assertTrue(bottle_thread.isValid())

    def test_deprecation(self):
        bottle_thread = PlasticBottleThread(
            size="M38SP444",
            external=True,
        )
        with self.assertWarns(DeprecationWarning):
            occt = bottle_thread.cq_object
            self.assertTrue(isinstance(occt, Solid))

    def test_exterior_left_thread(self):
        """Simple validity check for an exterior thread"""

        bottle_thread = PlasticBottleThread(size="M38SP444", external=True, hand="left")
        self.assertTrue(bottle_thread.isValid())

    def test_interior_thread(self):
        """Simple validity check for an interior thread"""

        bottle_thread = PlasticBottleThread(
            size="L18SP400", external=False, manufacturingCompensation=0.2
        )
        self.assertTrue(bottle_thread.isValid())

    def test_parsing(self):
        """Validate sizes"""
        with self.assertRaises(ValueError):
            PlasticBottleThread(size="Q12SP100")
        with self.assertRaises(ValueError):
            PlasticBottleThread(size="M37SP444")
        with self.assertRaises(ValueError):
            PlasticBottleThread(size="L12XX100")
        with self.assertRaises(ValueError):
            PlasticBottleThread(size="L12SP12")
        with self.assertRaises(ValueError):
            PlasticBottleThread(size="M38SP444", hand="righty")


if __name__ == "__main__":
    unittest.main(failfast=True)
