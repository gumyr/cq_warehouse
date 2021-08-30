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
# from os import setsid
from typing import Set
import unittest
from pydantic.main import BaseModel
from tests import BaseTest
import cadquery as cq
from cq_warehouse.fastener import (
    HexNut,
    SquareNut,
    SocketHeadCapScrew,
    ButtonHeadCapScrew,
    HexBolt,
    SetScrew,
    ExternalThread,
    InternalThread,
    decode_imperial_size,
    imperial_str_to_float,
    metric_str_to_float,
    is_safe,
)

# import cadquery as cq

MM = 1
IN = 25.4 * MM
VERBOSE = False
FULLTEST = False


class TestSupportFunctions(BaseTest):
    def test_decode_imperial_size(self):
        self.assertTupleAlmostEquals((1.524, 0.3175), decode_imperial_size("#0-80"), 5)
        self.assertTupleAlmostEquals(
            (1.25 * IN, IN / 32), decode_imperial_size("1 1/4-32"), 5
        )

    def test_is_safe(self):
        self.assertTrue(is_safe("1 1/8"))
        self.assertFalse(is_safe("rm -rf *.*"))

    def test_imperial_str_to_float(self):
        self.assertAlmostEqual(imperial_str_to_float("1 1/2"), 1.5 * IN)
        with self.assertRaises(ValueError):
            imperial_str_to_float("rm -rf *.*")

    def test_metric_str_to_float(self):
        self.assertEqual(metric_str_to_float(" 1000 "), 1000)
        with self.assertRaises(ValueError):
            metric_str_to_float("rm -rf *.*")


class TestExternalThread(BaseTest):
    def test_exterior_thread(self):
        """ Simple validity check for an exterior thread """

        thread = ExternalThread(
            major_diameter=0.1900 * IN, pitch=IN / 32, length=(1 / 4) * IN
        )
        self.assertTrue(thread.cq_object.isValid())
        self.assertIsNone(thread.external_thread_core_radius)
        with self.assertRaises(ValueError):
            ExternalThread(major_diameter=5, pitch=1, length=5, hand="righty")


class TestInternalThread(BaseTest):
    def test_interior_thread(self):
        """ Simple validity check for an interior thread """

        thread = InternalThread(
            major_diameter=0.1900 * IN, pitch=IN / 32, length=(1 / 4) * IN
        )
        self.assertTrue(thread.cq_object.isValid())
        with self.assertRaises(ValueError):
            InternalThread(major_diameter=5, pitch=1, length=5, hand="righty")


class TestNutParent(BaseTest):
    def test_nut_parameters(self):
        with self.assertRaises(ValueError):
            HexNut(size="missing")


class TestHexNut(BaseTest):
    """ Test HexNut class functionality """

    def test_hexnut_interface_options(self):
        """ Validate both interface types are functional """
        nut = HexNut(size="M4-0.7", simple=True)
        self.assertTrue(nut.cq_object.isValid())
        nut = HexNut(
            width=7,
            thickness=3.2,
            thread_diameter=4,
            thread_pitch=0.7,
            hand="left",
            simple=True,
        )
        self.assertTrue(nut.cq_object.isValid())

    def test_hexnut_validity(self):
        """ Simple validity check for all the stand sized hex head nuts """

        if FULLTEST:
            test_set = HexNut.metric_sizes() + HexNut.imperial_sizes()
        else:
            test_set = HexNut.metric_sizes()[:1]
        for i, size in enumerate(test_set):
            if size in ["M6-1", "1/4-20", "1/4-28", "5/16-18", "5/16-24"]:
                continue
            if VERBOSE:
                print(f"Testing HexNut size {size} - {i+1} of {len(test_set)}")
            with self.subTest(size=size):
                self.assertTrue(HexNut(size=size).cq_object.isValid())


class TestSquareNut(BaseTest):
    """ Test SquareNut class functionality """

    def test_squarenut_validity(self):
        """ Simple validity check for all the stand sized square head nuts """

        if FULLTEST:
            test_set = SquareNut.metric_sizes() + SquareNut.imperial_sizes()
        else:
            test_set = SquareNut.imperial_sizes()[:1]
        for i, size in enumerate(test_set):
            if size in ["M6-1", "1/4-20", "1/4-28", "5/16-18", "5/16-24"]:
                continue
            if VERBOSE:
                print(f"Testing SquareNut size {size} - {i+1} of {len(test_set)}")
            with self.subTest(size=size):
                self.assertTrue(SquareNut(size=size).cq_object.isValid())


class TestScrewParent(BaseTest):
    def test_screw_parameters(self):
        with self.assertRaises(AttributeError):
            HexBolt(size="M3-0.5")
        with self.assertRaises(ValueError):
            HexBolt(size="missing", length=5)
        # thread_length too long
        with self.assertRaises(ValueError):
            HexBolt(
                length=5,
                head_width=5,
                head_height=3,
                thread_diameter=2,
                thread_pitch=0.5,
                thread_length=12,
            )

    def test_screw_measurements(self):
        self.assertGreater(len(HexBolt.metric_sizes()), 0)
        self.assertGreater(len(HexBolt.imperial_sizes()), 0)

    def test_stepped_bolt(self):
        head = HexBolt(size="M3-0.5", length=15 * MM, simple=True).head
        shank = ExternalThread(
            major_diameter=3 * MM, pitch=0.5 * MM, length=5 * MM, simple=True
        ).make_shank(body_length=10 * MM, body_diameter=4 * MM)
        hex_bolt = head.union(shank, glue=True)
        # cq.exporters.export(hex_bolt.val(), "hex_bolt.step")
        self.assertTrue(hex_bolt.val().isValid())


class TestHexBolt(BaseTest):
    """ Test HexBolt class functionality """

    def test_hexbolt_validity(self):
        """ Simple validity check for all the stand sized hex head bolts """

        if FULLTEST:
            test_set = HexBolt.metric_sizes() + HexBolt.imperial_sizes()
        else:
            test_set = HexBolt.metric_sizes()[:1]
        for i, size in enumerate(test_set):
            if VERBOSE:
                print(f"Testing HexBolt size {size} - {i+1} of {len(test_set)}")
            with self.subTest(size=size):
                self.assertTrue(HexBolt(size=size, length=5 * MM).cq_object.isValid())


class TestSocketHeadCapScrew(BaseTest):
    """ Test SocketHeadCapScrew class functionality """

    def test_socket_head_cap_screw_validity(self):
        """ Simple validity check for all the stand sized socket head cap screws """

        if FULLTEST:
            test_set = (
                SocketHeadCapScrew.metric_sizes() + SocketHeadCapScrew.imperial_sizes()
            )
        else:
            test_set = SocketHeadCapScrew.metric_sizes()[:1]

        for i, size in enumerate(test_set):
            if VERBOSE:
                print(
                    f"Testing SocketHeadCapScrew size {size} - {i+1} of {len(test_set)}"
                )
            with self.subTest(size=size):
                self.assertTrue(
                    SocketHeadCapScrew(size=size, length=5 * MM).cq_object.isValid()
                )

    def test_socket_head_cap_screw_thread_length(self):
        """ Set the thread length parameter """
        self.assertTrue(
            SocketHeadCapScrew(
                length=20,
                head_diameter=10,
                head_height=5,
                thread_diameter=5,
                thread_pitch=1,
                thread_length=10,
                socket_size=4,
                socket_depth=2,
                hand="left",
                simple=True,
            ).cq_object.isValid()
        )


class TestButtonHeadCapScrew(BaseTest):
    """ Test ButtonHeadCapScrew class functionality """

    def test_button_head_cap_screw_validity(self):
        """ Simple validity check for all the stand sized button head cap screws """

        if FULLTEST:
            test_set = (
                ButtonHeadCapScrew.metric_sizes() + ButtonHeadCapScrew.imperial_sizes()
            )
        else:
            test_set = ButtonHeadCapScrew.metric_sizes()[:1]
        for i, size in enumerate(test_set):
            if VERBOSE:
                print(
                    f"Testing ButtonHeadCapScrew size {size} - {i+1} of {len(test_set)}"
                )
            with self.subTest(size=size):
                self.assertTrue(
                    ButtonHeadCapScrew(size=size, length=5 * MM).cq_object.isValid()
                )


class TestSetScrew(BaseTest):
    """ Test SetScrew class functionality """

    def test_setscrew_validity(self):
        """ Simple validity check for all the stand sized setscrews """

        self.assertIsNone(SetScrew(size="#4-40", length=5).make_head())
        self.assertIsNone(SetScrew(size="#4-40", length=5).head)
        self.assertIsNone(SetScrew(size="#4-40", length=5).shank)

        if FULLTEST:
            test_set = SetScrew.metric_sizes()
        else:
            test_set = SetScrew.metric_sizes()[:1]
        for i, size in enumerate(test_set):
            if size in ["M20-2.5"]:
                continue
            if VERBOSE:
                print(f"Testing SetScrew size {size} - {i+1} of {len(test_set)}")
            min_length = SetScrew.metric_parameters[size]["Socket_Depth"] * 1.5
            with self.subTest(size=size):
                self.assertTrue(
                    SetScrew(size=size, length=min_length).cq_object.isValid()
                )
        if FULLTEST:
            test_set = SetScrew.imperial_sizes()
        else:
            test_set = []
        for i, size in enumerate(test_set):
            if size in ["#0-80", "3/8-16", "3/8-24", "7/16-14", "5/8-11"]:
                continue
            if VERBOSE:
                print(f"Testing SetScrew size {size} - {i+1} of {len(test_set)}")
            min_length = SetScrew.imperial_parameters[size]["Socket_Depth"] * 1.5
            with self.subTest(size=size):
                self.assertTrue(
                    SetScrew(size=size, length=min_length).cq_object.isValid()
                )


if __name__ == "__main__":
    unittest.main()
