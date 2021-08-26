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


class TestSupportFunctions(BaseTest):
    def test_decode_imperial_size(self):
        self.assertTupleAlmostEquals((1.524, 0.3175), decode_imperial_size("#0-80"), 5)
        self.assertTupleAlmostEquals(
            (1.25 * IN, IN / 32), decode_imperial_size("1 1/4-32"), 5
        )

    def test_is_safe(self):
        self.assertTrue(is_safe("1 1/8"))
        self.assertFalse(is_safe("rm -R *.*"))


class TestFunctionality(BaseTest):
    """ Test core fastener functionality """

    def test_exterior_thread(self):
        """ Simple validity check for an exterior thread """

        thread = ExternalThread(
            major_diameter=0.1900 * IN, pitch=32 / IN, length=(1 / 2) * IN
        )
        self.assertTrue(thread.cq_object.isValid())

    def test_interior_thread(self):
        """ Simple validity check for an interior thread """

        thread = InternalThread(
            major_diameter=0.1900 * IN, pitch=32 / IN, length=(1 / 2) * IN
        )
        self.assertTrue(thread.cq_object.isValid())

    def test_hexnut(self):
        """ Simple validity check for all the stand sized hex head nuts """

        HexNut.set_parameters()
        test_set = list(HexNut.metric_parameters.keys()) + list(
            HexNut.imperial_parameters.keys()
        )
        for i, size in enumerate(test_set):
            if VERBOSE:
                print(f"Testing HexNut size {size} - {i+1} of {len(test_set)}")
            nut = HexNut(size=size)
            self.assertTrue(nut.cq_object.isValid())

    def test_squarenut(self):
        """ Simple validity check for all the stand sized square head nuts """

        SquareNut.set_parameters()
        test_set = list(SquareNut.metric_parameters.keys()) + list(
            SquareNut.imperial_parameters.keys()
        )
        for i, size in enumerate(test_set):
            if VERBOSE:
                print(f"Testing SquareNut size {size} - {i+1} of {len(test_set)}")
            nut = SquareNut(size=size)
            self.assertTrue(nut.cq_object.isValid())

    def test_hexbolt(self):
        """ Simple validity check for all the stand sized hex head bolts """

        HexBolt.set_parameters()
        test_set = list(HexBolt.metric_parameters.keys()) + list(
            HexBolt.imperial_parameters.keys()
        )
        for i, size in enumerate(test_set):
            if VERBOSE:
                print(f"Testing HexBolt size {size} - {i+1} of {len(test_set)}")
            bolt = HexBolt(size=size, length=10 * MM)
            self.assertTrue(bolt.cq_object.isValid())

    def test_socket_head_cap_screw(self):
        """ Simple validity check for all the stand sized socket head cap screws """

        SocketHeadCapScrew.set_parameters()
        test_set = list(SocketHeadCapScrew.metric_parameters.keys()) + list(
            SocketHeadCapScrew.imperial_parameters.keys()
        )
        for i, size in enumerate(test_set):
            if VERBOSE:
                print(
                    f"Testing SocketHeadCapScrew size {size} - {i+1} of {len(test_set)}"
                )
            screw = SocketHeadCapScrew(size=size, length=10 * MM)
            self.assertTrue(screw.cq_object.isValid())

    def test_button_head_cap_screw(self):
        """ Simple validity check for all the stand sized button head cap screws """

        ButtonHeadCapScrew.set_parameters()
        test_set = list(ButtonHeadCapScrew.metric_parameters.keys()) + list(
            ButtonHeadCapScrew.imperial_parameters.keys()
        )
        for i, size in enumerate(test_set):
            if VERBOSE:
                print(
                    f"Testing ButtonHeadCapScrew size {size} - {i+1} of {len(test_set)}"
                )
            button = ButtonHeadCapScrew(size=size, length=10 * MM)
            self.assertTrue(button.cq_object.isValid())

    # def test_setscrew(self):
    #     """ Simple validity check for all the stand sized setscrews """

    #     SetScrew.set_parameters()
    #     test_set = list(SetScrew.metric_parameters.keys()) + list(
    #         SetScrew.imperial_parameters.keys()
    #     )
    #     for i, size in enumerate(test_set):
    #         if VERBOSE:
    #             print(f"Testing SetScrew size {size} - {i+1} of {len(test_set)}")
    #         setscrew = SetScrew(size=size, length=(1 / 2) * IN)
    #         self.assertTrue(setscrew.cq_object.isValid())


if __name__ == "__main__":
    unittest.main()
