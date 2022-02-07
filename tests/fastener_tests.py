"""

Fastener Unit Tests

name: fastener_tests.py
by:   Gumyr
date: August 24th 2021

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
import cadquery as cq
from cq_warehouse.fastener import *
import cq_warehouse.extensions

MM = 1
IN = 25.4 * MM


def _assertTupleAlmostEquals(self, expected, actual, places, msg=None):
    """Check Tuples"""
    for i, j in zip(actual, expected):
        self.assertAlmostEqual(i, j, places, msg=msg)


unittest.TestCase.assertTupleAlmostEquals = _assertTupleAlmostEquals


class TestRecessExceptions(unittest.TestCase):
    def test_decode_imperial_size(self):
        self.assertTupleAlmostEquals((1.524, 0.3175), decode_imperial_size("#0-80"), 5)
        self.assertTupleAlmostEquals(
            (1.25 * IN, IN / 32), decode_imperial_size("1 1/4-32"), 5
        )

    def test_metric_str_to_float(self):
        self.assertEqual(metric_str_to_float(" 1000 "), 1000)
        self.assertEqual(metric_str_to_float("rm -rf *"), "rm -rf *")


class TestRecessExceptions(unittest.TestCase):
    def test_bad_recess(self):
        with self.assertRaises(ValueError):
            cross_recess("PH5")
        with self.assertRaises(ValueError):
            hexalobular_recess("T0")
        with self.assertRaises(ValueError):
            square_recess("R8")


class TestWashers(unittest.TestCase):
    """Test creation of all washers"""

    def test_select_by_size(self):
        self.assertGreater(len(Washer.select_by_size("M6")), 0)

    def test_size(self):
        """Validate diameter and thickness of washers"""
        for washer_class in Washer.__subclasses__():
            for washer_type in washer_class.types():
                for washer_size in washer_class.sizes(fastener_type=washer_type):
                    with self.subTest(
                        washer_class=washer_class.__name__,
                        fastener_type=washer_type,
                        size=washer_size,
                    ):
                        washer = washer_class(
                            size=washer_size, fastener_type=washer_type
                        )
                        self.assertGreater(washer.washer_diameter, 0)
                        self.assertGreater(washer.washer_thickness, 0)
                        self.assertGreater(len(washer.info), 0)

                        # Check the hole data if available
                        try:
                            clearance_normal = washer.clearance_hole_diameters["Normal"]
                            clearance_close = washer.clearance_hole_diameters["Close"]
                            clearance_loose = washer.clearance_hole_diameters["Loose"]
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

                        self.assertEqual(washer.washer_class, washer_class.__name__)


class TestNuts(unittest.TestCase):
    """Test creation of all nuts"""

    def test_select_by_size(self):
        self.assertGreater(len(Nut.select_by_size("M6-1")), 0)

    def test_bad_size(self):
        with self.assertRaises(ValueError):
            DomedCapNut(size="M6", fastener_type="din1587")
        with self.assertRaises(ValueError):
            DomedCapNut(size="M6-4", fastener_type="din1587")

    def test_bad_type(self):
        with self.assertRaises(ValueError):
            DomedCapNut(size="M6-1", fastener_type="common")

    def test_bad_hand(self):
        with self.assertRaises(ValueError):
            DomedCapNut(size="M6-1", fastener_type="din1587", hand="lefty")

    def test_size(self):
        """Validate diameter and thickness of nuts"""
        for nut_class in Nut.__subclasses__():
            for nut_type in nut_class.types():
                for nut_size in nut_class.sizes(fastener_type=nut_type):
                    simple_thread = not (
                        nut_type == list(nut_class.types())[0]
                        and nut_size == nut_class.sizes(fastener_type=nut_type)[0]
                    )
                    with self.subTest(
                        nut_class=nut_class.__name__,
                        fastener_type=nut_type,
                        size=nut_size,
                    ):
                        nut = nut_class(
                            size=nut_size, fastener_type=nut_type, simple=simple_thread
                        )
                        self.assertGreater(nut.nut_diameter, 0)
                        self.assertGreater(nut.nut_thickness, 0)
                        self.assertGreater(len(nut.info), 0)
                        # Check the hole data if available
                        try:
                            clearance_normal = nut.clearance_hole_diameters["Normal"]
                            clearance_close = nut.clearance_hole_diameters["Close"]
                            clearance_loose = nut.clearance_hole_diameters["Loose"]
                            tap_soft = nut.tap_hole_diameters["Soft"]
                            tap_hard = nut.tap_hole_diameters["Hard"]
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
                            self.assertGreater(
                                clearance_close,
                                tap_hard,
                            )
                            self.assertGreater(
                                tap_hard,
                                tap_soft,
                            )
                        self.assertEqual(nut.nut_class, nut_class.__name__)

    def test_countersink(self):
        """Validate diameter and thickness of nuts"""
        for nut_class in Nut.__subclasses__():
            nut_type = list(nut_class.types())[0]
            nut_size = nut_class.sizes(fastener_type=nut_type)[0]
            nut = nut_class(size=nut_size, fastener_type=nut_type, simple=True)

            box = (
                cq.Workplane("XY")
                .box(10, 10, 10)
                .faces(">Z")
                .workplane()
                .clearanceHole(fastener=nut, counterSunk=True)
                .val()
            )
            self.assertLess(box.Volume(), 999.99)


class TestScrews(unittest.TestCase):
    """Test creation of all screws"""

    def test_select_by_size(self):
        self.assertGreater(len(Screw.select_by_size("M6-1")), 0)

    def test_bad_size(self):
        with self.assertRaises(ValueError):
            ButtonHeadScrew(size="M6", fastener_type="iso7380_1", length=20)
        with self.assertRaises(ValueError):
            ButtonHeadScrew(size="M6-4", fastener_type="iso7380_1", length=20)

    def test_bad_type(self):
        with self.assertRaises(ValueError):
            ButtonHeadScrew(size="M6-1", fastener_type="common", length=20)

    def test_bad_hand(self):
        with self.assertRaises(ValueError):
            ButtonHeadScrew(
                size="M6-1", fastener_type="iso7380_1", length=20, hand="lefty"
            )

    def test_screw_shorter_then_head(self):
        """Validate check for countersunk screws too short for their head"""
        with self.assertRaises(ValueError):
            CounterSunkScrew(size="M20-2.5", fastener_type="iso2009", length=10)

    def test_size(self):
        """Validate head diameter and height of screws"""
        # ValueError: No tap hole data for size 1-14

        for screw_class in Screw.__subclasses__():
            for screw_type in screw_class.types():
                for screw_size in screw_class.sizes(fastener_type=screw_type):
                    simple_thread = not (
                        screw_type == list(screw_class.types())[0]
                        and screw_size == screw_class.sizes(fastener_type=screw_type)[0]
                    )
                    with self.subTest(
                        screw_class=screw_class.__name__,
                        fastener_type=screw_type,
                        size=screw_size,
                    ):
                        screw = screw_class(
                            size=screw_size,
                            fastener_type=screw_type,
                            length=15,
                            simple=simple_thread,
                        )
                        if screw.head is None:
                            self.assertEqual(screw.head_height, 0)
                            self.assertEqual(screw.head_diameter, 0)
                        else:
                            self.assertGreater(screw.head_height, 0)
                            self.assertGreater(screw.head_diameter, 0)
                        self.assertGreater(len(screw.info), 0)
                        # Check the hole data if available
                        try:
                            clearance_normal = screw.clearance_hole_diameters["Normal"]
                            clearance_close = screw.clearance_hole_diameters["Close"]
                            clearance_loose = screw.clearance_hole_diameters["Loose"]
                            tap_soft = screw.tap_hole_diameters["Soft"]
                            tap_hard = screw.tap_hole_diameters["Hard"]
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
                            self.assertGreater(
                                clearance_close,
                                tap_hard,
                            )
                            self.assertGreater(
                                tap_hard,
                                tap_soft,
                            )
                        self.assertEqual(screw.screw_class, screw_class.__name__)

    def test_countersink(self):
        """Validate diameter and thickness of screws"""
        for screw_class in Screw.__subclasses__():
            screw_type = list(screw_class.types())[0]
            screw_size = screw_class.sizes(fastener_type=screw_type)[0]
            screw = screw_class(
                size=screw_size, fastener_type=screw_type, length=15, simple=True
            )

            box = (
                cq.Workplane("XY")
                .box(10, 10, 10)
                .faces(">Z")
                .workplane()
                .clearanceHole(fastener=screw, counterSunk=True)
                .val()
            )
            self.assertLess(box.Volume(), 999.99)

    def test_min_hole_depth(self):
        screw = SocketHeadCapScrew(
            size="1 1/2-12", fastener_type="asme_b18.3", length=30, simple=True
        )
        self.assertLess(
            screw.min_hole_depth(counter_sunk=False),
            screw.min_hole_depth(counter_sunk=True),
        )

    def test_hollow_thread(self):
        screw = SetScrew(size="M6-1", fastener_type="iso4026", length=5, simple=False)
        self.assertEqual(screw.head_diameter, 0)
        self.assertEqual(screw.head_height, 0)
        self.assertIsNotNone(screw.cq_object)
        self.assertIsNone(screw.shank)
        self.assertGreater(len(screw.nominal_lengths), 0)

    def test_missing_hole_data(self):
        """Check for missing data handling - note test will failure if csv populated"""
        screw = SocketHeadCapScrew(
            size="1 1/2-12", fastener_type="asme_b18.3", length=30, simple=True
        )
        with self.assertRaises(ValueError):
            screw.tap_hole_diameters["Hard"]
        with self.assertRaises(ValueError):
            screw.tap_hole_diameters["Soft"]

        self.assertIsNone(screw.nominal_lengths)


class TestWorkplaneMethods(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
