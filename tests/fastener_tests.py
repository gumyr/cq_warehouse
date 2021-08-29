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
from os import setsid
from typing import Set
import unittest
from pydantic.main import BaseModel
from tests import BaseTest
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
    is_safe,
)

# import cadquery as cq

MM = 1
IN = 25.4 * MM
VERBOSE = True


# class TestSupportFunctions(BaseTest):
#     def test_decode_imperial_size(self):
#         self.assertTupleAlmostEquals((1.524, 0.3175), decode_imperial_size("#0-80"), 5)
#         self.assertTupleAlmostEquals(
#             (1.25 * IN, IN / 32), decode_imperial_size("1 1/4-32"), 5
#         )

#     def test_is_safe(self):
#         self.assertTrue(is_safe("1 1/8"))
#         self.assertFalse(is_safe("rm -rf *.*"))


# class TestExternalThread(BaseTest):
#     def test_exterior_thread(self):
#         """ Simple validity check for an exterior thread """

#         thread = ExternalThread(
#             major_diameter=0.1900 * IN, pitch=IN / 32, length=(1 / 4) * IN
#         )
#         self.assertTrue(thread.cq_object.isValid())


# class TestInternalThread(BaseTest):
#     def test_interior_thread(self):
#         """ Simple validity check for an interior thread """

#         thread = InternalThread(
#             major_diameter=0.1900 * IN, pitch=IN / 32, length=(1 / 4) * IN
#         )
#         self.assertTrue(thread.cq_object.isValid())


class TestFunctionality(BaseTest):
    """ Test core fastener functionality """

    # def test_hexnut(self):
    #     """ Simple validity check for all the stand sized hex head nuts """

    #     test_set = HexNut.metric_sizes()+HexNut.imperial_sizes()
    #     for i, size in enumerate(test_set):
    #         if size in ["M6-1", "1/4-20", "1/4-28", "5/16-18", "5/16-24"]:
    #             continue
    #         if VERBOSE:
    #             print(f"Testing HexNut size {size} - {i+1} of {len(test_set)}")
    #         with self.subTest(size=size):
    #             self.assertTrue(HexNut(size=size).cq_object.isValid())

    # def test_squarenut(self):
    #     """ Simple validity check for all the stand sized square head nuts """

    #     test_set = SquareNut.metric_sizes()+SquareNut.imperial_sizes()
    #     for i, size in enumerate(test_set):
    #         if size in ["M6-1", "1/4-20", "1/4-28", "5/16-18", "5/16-24"]:
    #             continue
    #         if VERBOSE:
    #             print(f"Testing SquareNut size {size} - {i+1} of {len(test_set)}")
    #         with self.subTest(size=size):
    #             self.assertTrue(SquareNut(size=size).cq_object.isValid())

    def test_hexbolt(self):
        """ Simple validity check for all the stand sized hex head bolts """

        test_set = HexBolt.metric_sizes() + HexBolt.imperial_sizes()
        for i, size in enumerate(test_set):
            if VERBOSE:
                print(f"Testing HexBolt size {size} - {i+1} of {len(test_set)}")
            with self.subTest(size=size):
                self.assertTrue(HexBolt(size=size, length=5 * MM).cq_object.isValid())

    def test_socket_head_cap_screw(self):
        """ Simple validity check for all the stand sized socket head cap screws """

        test_set = (
            SocketHeadCapScrew.metric_sizes() + SocketHeadCapScrew.imperial_sizes()
        )
        for i, size in enumerate(test_set):
            if VERBOSE:
                print(
                    f"Testing SocketHeadCapScrew size {size} - {i+1} of {len(test_set)}"
                )
            with self.subTest(size=size):
                self.assertTrue(
                    SocketHeadCapScrew(size=size, length=5 * MM).cq_object.isValid()
                )

    def test_button_head_cap_screw(self):HexNut.metric_sizes()
        """ Simple validity check for all the stand sized button head cap screws """

        test_set = (
            ButtonHeadCapScrew.metric_sizes() + ButtonHeadCapScrew.imperial_sizes()
        )
        for i, size in enumerate(test_set):
            if VERBOSE:
                print(
                    f"Testing ButtonHeadCapScrew size {size} - {i+1} of {len(test_set)}"
                )HexNut.metric_sizes()
            with self.subTest(size=size):
                self.assertTrue(
                    ButtonHeadCapScrew(size=size, length=5 * MM).cq_object.isValid()
                )

    def test_setscrew(self):
        """ Simple validity check for all the stand sized setscrews """

        test_set = SetScrew.metric_sizes()
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
        test_set = SetScrew.imperial_sizes()
        for i, size in enumerate(test_set):
            if size in ["#0-80","3/8-16","3/8-24","7/16-14","5/8-11"]:
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
