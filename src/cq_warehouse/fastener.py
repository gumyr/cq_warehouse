"""

Parametric Threaded Fasteners

name: fastener.py
by:   Gumyr
date: August 14th 2021

desc:

    This python/cadquery code is a parameterized threaded fastener generator.
    Currently the following is supported:
    - external ISO threads
    - internal ISO threads
    - nuts
    - caphead bolts

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
# import csv
# csvfile = csv.reader(open("airports.csv"))
# airportCode = dict(csvfile)
from os import major
from typing import Literal, Tuple, Optional
import cadquery as cq
import math
from math import sin, cos, tan, radians, pi, ceil
import cProfile
from cadquery import selectors
from pydantic import BaseModel, PrivateAttr, validator, validate_arguments, Field
from functools import cache

MM = 1
IN = 25.4 * MM

# from tqdm import tqdm


imperial_numbered_sizes = {
    "#0000": 0.0210 * IN,
    "#000": 0.0340 * IN,
    "#00": 0.0470 * IN,
    "#0": 0.0600 * IN,
    "#1": 0.0730 * IN,
    "#2": 0.0860 * IN,
    "#3": 0.0990 * IN,
    "#4": 0.1120 * IN,
    "#5": 0.1250 * IN,
    "#6": 0.1380 * IN,
    "#8": 0.1640 * IN,
    "#10": 0.1900 * IN,
    "#12": 0.2160 * IN,
}


def decode_imperial_size(size: str) -> Tuple[float, float]:
    """ Extract the major diameter and pitch from an imperial size """

    def imperial_size_to_float(size: str) -> float:
        size_to_eval = size.replace(" ", "+").replace('"', "")
        return eval(f"({size_to_eval})*IN")

    sizes = size.split("-")
    if size[0] == "#":
        major_diameter = imperial_numbered_sizes[sizes[0]]
        pitch = sizes[1] / IN
    else:
        major_diameter = imperial_size_to_float(sizes[0])
        pitch = imperial_size_to_float(sizes[0]) / IN
    return (major_diameter, pitch)


# Size,Diameter,Pitch,Knurl & Cup Point Diameter,Flat Point Diameter,Oval Point Radius,Half Dog Point Diameter,Half Dog Point Length,Hexagon Socket Size,Key Engagement
socketSetScrews = {
    "M1.6-0.35": [1.6, 0.35, 0.80, 0.80, 1.600, 0.80, 0.53, 0.70, 0.60],
    "M2-0.40": [2.0, 0.40, 1.00, 1.00, 1.90, 1.00, 0.64, 0.90, 0.80],
    "M2.5-0.45": [2.5, 0.45, 1.25, 1.50, 2.28, 1.50, 1.25, 1.30, 1.10],
    "M3-0.50": [3.0, 0.50, 1.50, 2.00, 2.65, 2.00, 1.75, 1.50, 1.50],
    "M4-0.70": [4.0, 0.70, 2.00, 2.50, 3.80, 2.50, 1.20, 2.00, 1.80],
    "M5-0.80": [5.0, 0.80, 2.50, 3.50, 4.55, 3.50, 1.37, 2.50, 2.70],
    "M6-1.00": [6.0, 1.00, 3.00, 4.00, 5.30, 4.00, 1.74, 3.00, 3.00],
    "M8-1.25": [8.0, 1.25, 4.00, 5.50, 6.80, 5.50, 2.28, 4.00, 4.00],
    "M10-1.50": [10.0, 1.50, 5.00, 7.00, 8.30, 7.00, 2.82, 5.00, 5.00],
    "M12-1.75": [12.0, 1.75, 6.00, 8.50, 9.80, 8.50, 3.35, 6.00, 6.00],
    "M16-2.00": [16.0, 2.00, 8.00, 12.00, 12.80, 12.00, 4.40, 8.00, 8.00],
    "M20-2.50": [20.0, 2.50, 10.00, 15.00, 15.80, 15.00, 5.45, 10.00, 9.00],
}
# Size,Shoulder Diameter,Head Diameter,Head Height,Hexagon Socket Size,Thread Diameter,Thread Pitch,Thread Length
socketHeadShoulderScrew = {
    "M6": [5.990, 10.00, 4.500, 3.00, 5.00, 0.8, 9.750],
    "M8": [7.987, 13.00, 5.500, 4.00, 6.00, 1.0, 11.25],
    "M10": [9.987, 16.00, 7.00, 5.00, 8.00, 1.25, 13.25],
    "M12": [11.984, 18.00, 8.00, 6.00, 10.0, 1.50, 16.40],
    "M16": [15.984, 24.00, 11.00, 8.00, 12.0, 1.75, 18.40],
    "M20": [19.980, 30.00, 14.00, 10.00, 16.0, 2.00, 22.40],
}

# Size,Pitch,Head Diameter,Head Height,Hexagon Socket Size,Key Engagement
flatHeadSocketCapScrew = {
    "M3-0.5": [0.5, 6.72, 1.86, 2.00, 1.10],
    "M4-0.7": [0.7, 8.96, 2.48, 2.50, 1.50],
    "M5-0.8": [0.8, 11.20, 3.10, 3.00, 1.90],
    "M6-1.0": [1.0, 13.44, 3.72, 4.00, 2.20],
    "M8-1.25": [1.25, 17.92, 4.96, 5.00, 3.00],
    "M10-1.50": [1.50, 22.40, 6.20, 6.00, 3.60],
    "M12-1.75": [1.75, 26.88, 7.44, 8.00, 4.30],
    "M16-2.00": [2.00, 33.60, 8.80, 10.00, 4.80],
    "M20-2.50": [2.50, 40.32, 10.16, 12.00, 5.60],
}

# Size,Pitch,Head Diameter,Head Height,Hexagon Socket Size,Key Engagement
buttonHeadSocketCapScrew = {
    "M3-0.5": [0.5, 0.5, 5.700, 1.65, 2.00, 1.04],
    "M4-0.7": [0.7, 0.7, 7.60, 2.20, 2.50, 1.30],
    "M5-0.8": [0.8, 0.8, 9.50, 2.75, 3.00, 1.56],
    "M6-1.0": [1.0, 1.0, 10.50, 3.30, 4.00, 2.08],
    "M8-1.25": [1.25, 1.25, 14.00, 4.40, 5.00, 2.60],
    "M10-1.50": [1.50, 1.50, 17.50, 5.50, 6.00, 3.12],
    "M12-1.75": [1.75, 1.75, 21.00, 6.60, 8.00, 4.16],
}


class Thread:
    @staticmethod
    def thread_h_parameter(pitch: float, thread_angle: float = 60) -> float:
        return (pitch / 2) / tan(radians(thread_angle / 2))

    @staticmethod
    def internal_iso_thread_profile(
        diameter: float, pitch: float
    ) -> Tuple[cq.Workplane, float]:
        """
        Based on this diagram:
        https://en.wikipedia.org/wiki/ISO_metric_screw_thread#/media/File:ISO_and_UTS_Thread_Dimensions.svg
        """

        thread_angle = 60  # ISO standard
        h = Thread.thread_h_parameter(pitch, thread_angle)
        maxD = diameter
        minR = (maxD - 2 * (5 / 8) * h) / 2
        threadRadius = minR + 3 * h / 4

        threadProfile = (
            cq.Workplane("XZ")
            # .moveTo(outer_radius, 0)
            .lineTo(minR, 0)
            .lineTo(minR, pitch / 8)
            .lineTo(maxD / 2, 7 * pitch / 16)
            .spline(
                [(maxD / 2, 9 * pitch / 16)],
                tangents=[
                    (
                        sin(radians(90 - thread_angle / 2)),
                        cos(radians(90 - thread_angle / 2)),
                    ),
                    (
                        -sin(radians(90 - thread_angle / 2)),
                        cos(radians(90 - thread_angle / 2)),
                    ),
                ],
                includeCurrent=True,
            )
            .lineTo(minR, 7 * pitch / 8)
            .lineTo(minR, pitch)
            .lineTo(0, pitch)
            # .lineTo(outer_radius, pitch)
            .close()
        )
        return (threadProfile, threadRadius)

    @staticmethod
    def external_iso_thread_profile(
        diameter: float, pitch: float
    ) -> Tuple[cq.Workplane, float]:
        """
        Based on this diagram:
        https://en.wikipedia.org/wiki/ISO_metric_screw_thread#/media/File:ISO_and_UTS_Thread_Dimensions.svg
        """
        thread_angle = 60  # ISO standard
        h = Thread.thread_h_parameter(pitch, thread_angle)

        maxD = diameter
        minR = (maxD - 2 * (5 / 8) * h) / 2
        threadRadius = minR - h / 4

        threadProfile = (
            cq.Workplane("XZ")
            .lineTo(minR - h / 12, 0)
            .spline(
                [(minR, pitch / 8)],
                tangents=[
                    (0, 1, 0),
                    (
                        sin(radians(90 - thread_angle / 2)),
                        cos(radians(90 - thread_angle / 2)),
                    ),
                ],
                includeCurrent=True,
            )
            .lineTo(maxD / 2, 7 * pitch / 16)
            .lineTo(maxD / 2, 9 * pitch / 16)
            .lineTo(minR, 7 * pitch / 8)
            .spline(
                [(minR - h / 12, pitch)],
                tangents=[
                    (
                        -sin(radians(90 - thread_angle / 2)),
                        cos(radians(90 - thread_angle / 2)),
                    ),
                    (0, 1, 0),
                ],
                includeCurrent=True,
            )
            .lineTo(threadRadius, pitch)
            .lineTo(0, pitch)
            .close()
        )
        return (threadProfile, threadRadius)

    @staticmethod
    def make_iso_thread(
        diameter: float, pitch: float, length: float, external: bool = True
    ) -> cq.Solid:
        """
        Create a Solid thread object.

        External threads would typically be combined with other objects via a union() into a bolt.
        Internal threads would typically be placed into an appropriately sized hole and combined with
        other objects via a union(). This construction method allows the OCCT core to successfully
        build threaded objects and does so significantly faster if the 'glue' mode of the union
        method is used (glue requires non-overlapping shapes). Other build techniques, like using
        the cut() method to remove an internal thread from an object, often fails or takes an
        excessive amount of time.

        The thread is created in three steps:
        1) Generate the 2D profile of an external thread with the given parameters on XZ plane
        2) Sweep the thread profile creating a single thread then extract the outer wire on XY plane
        3) extrudeLinearWithRotation the outer wire to the desired length

        This process is used to avoid the OCCT core issues with sweeping the thread profile
        such that it contacts itself as the helix makes a full loop.

        """
        # Step 1 - Create the 2D thread profile
        if external:
            (threadProfile, threadRadius) = Thread.external_iso_thread_profile(
                diameter, pitch
            )
            sweep_offset = 0
        else:
            (threadProfile, threadRadius) = Thread.internal_iso_thread_profile(
                diameter, pitch
            )
            sweep_offset = -pitch

        # Step 2: Sweep the profile along the threadPath and extract the outer wire
        threadPath = cq.Wire.makeHelix(pitch=pitch, height=pitch, radius=threadRadius)
        threadWire = (
            cq.Workplane("XY")
            .add(
                threadProfile.sweep(
                    path=cq.Workplane(threadPath), isFrenet=True
                ).translate((0, 0, sweep_offset))
            )
            .section()
            .wires(selectors.AreaNthSelector(0))
            .val()
        )
        if external:
            outerWire = threadWire
            innerWires = []
        else:
            outerWire = cq.Wire.makeCircle(
                radius=diameter / 2 + 3 * Thread.thread_h_parameter(pitch) / 4,
                center=cq.Vector(0, 0, 0),
                normal=cq.Vector(0, 0, 1),
            )
            innerWires = [threadWire]

        # Step 3: Create thread by extruding thread wire
        thread = cq.Solid.extrudeLinearWithRotation(
            outerWire=outerWire,
            innerWires=innerWires,
            vecCenter=cq.Vector(0, 0, 0),
            vecNormal=cq.Vector(0, 0, length),
            angleDegrees=360 * (length / pitch),
        )
        # Is the thread valid?
        # print(thread.isValid())

        return thread


class InternalThread:
    @cache
    def __init__(
        self, major_diameter: float, thread_pitch: float, thread_length: float
    ):
        self.major_diameter = major_diameter
        self.thread_pitch = thread_pitch
        self.thread_length = thread_length
        self.socket_radius = (
            self.major_diameter / 2
            + 3 * Thread.thread_h_parameter(self.thread_pitch) / 4
        )
        self.cq_object = Thread.make_iso_thread(
            self.major_diameter, self.thread_pitch, self.thread_length, external=False
        )


class ExternalThread:
    @cache
    def __init__(
        self, major_diameter: float, thread_pitch: float, thread_length: float
    ):
        self.major_diameter = major_diameter
        self.thread_pitch = thread_pitch
        self.thread_length = thread_length
        self.cq_object = Thread.make_iso_thread(
            self.major_diameter, self.thread_pitch, self.thread_length, external=True
        )


class Nut:
    """ Create standard or custom nuts with ISO standard threads """

    @cache
    def __init__(
        self,
        size: Optional[str] = None,
        width: Optional[float] = None,
        thread_diameter: Optional[float] = None,
        thread_pitch: Optional[float] = None,
        thickness: Optional[float] = None,
        shape: Optional[Literal["hex", "square"]] = "hex",
    ):
        if shape in ["hex", "square"]:
            self.shape = shape
        else:
            raise ValueError('shape must be one of "hex" or "square"')
        if size is not None:
            (
                self.thread_diameter,
                self.thread_pitch,
                self.width,
                self.thickness,
            ) = Nut._extract_nut_parameters(size)
        else:
            self.width = width
            self.thread_diameter = thread_diameter
            self.thread_pitch = thread_pitch
            self.thickness = thickness
        self.cq_object = Nut.make_nut(
            self.width,
            self.thread_diameter,
            self.thread_pitch,
            self.thickness,
            self.shape,
        )

    @staticmethod
    def _extract_nut_parameters(size: str) -> Tuple[float, float, float, float]:
        """ Parse the nut size string into thread_diameter, thread_pitch, width and thickness """
        size_parts = size.split("-")
        if size in Nut.metric_nut_parameters.keys():
            nut_data = Nut.metric_nut_parameters[size]
            width = nut_data["wd"]
            thickness = nut_data["ht"]
            thread_diameter = float(size_parts[0][1:])
            thread_pitch = float(size_parts[1])
        elif size in Nut.imperial_nut_parameters.keys():
            nut_data = Nut.imperial_nut_parameters[size]
            width = nut_data["wd"]
            thickness = nut_data["ht"]
            (thread_diameter, thread_pitch) = decode_imperial_size(size)
        else:
            raise ValueError(
                "Invalid nut size - must be one of:"
                f"{list(Nut.metric_nut_parameters.keys())+list(Nut.imperial_nut_parameters.keys())}"
            )
        return (thread_diameter, thread_pitch, width, thickness)

    @staticmethod
    @cache
    def make_nut(
        width: float,
        thread_diameter: float,
        thread_pitch: float,
        thickness: float,
        shape: Optional[Literal["hex", "square"]] = "hex",
    ) -> cq.Solid:
        """ Create an arbitrary sized hex or square nut """

        thread_object = InternalThread(
            major_diameter=thread_diameter,
            thread_pitch=thread_pitch,
            thread_length=thickness,
        )
        if shape == "hex":
            # Distance across the tips of the hex
            hex_diameter = width / cos(pi / 6)
            # Chamfer between the hex tips and flats
            chamfer_size = (hex_diameter - width) / 2
            # The nutBody define the chamfered edges of the nut
            nutBody = (
                cq.Workplane("XY")
                .circle(hex_diameter / 2)  # Create a circle that contains the hexagon
                .circle(thread_object.socket_radius)  # .. with a hole in the center
                .extrude(thickness)
                .edges(selectors.RadiusNthSelector(1))
                .chamfer(chamfer_size / 2, chamfer_size)  # Chamfer the outside edges
                .intersect(
                    cq.Workplane("XY").polygon(6, hex_diameter).extrude(thickness)
                )
            )
        else:
            nutBody = (
                cq.Workplane("XY")
                .rect(width, width)
                .circle(thread_object.socket_radius)
                .extrude(thickness)
            )
        nut = nutBody.union(thread_object.cq_object, glue=True).val()
        return nut

    # ISO Standard Metric Nut sizes
    # Size-Pitch: wd=Width, ht=Height
    metric_nut_parameters = {
        "M1-0.25": {"wd": 2.5, "ht": 0.8},
        "M1.2-0.25": {"wd": 3, "ht": 1},
        "M1.4-0.3": {"wd": 3, "ht": 1.2},
        "M1.6-0.35": {"wd": 3.2, "ht": 1.3},
        "M2-0.4": {"wd": 4, "ht": 1.6},
        "M2.5-0.45": {"wd": 5, "ht": 2},
        "M3-0.5": {"wd": 5.5, "ht": 2.4},
        "M3.5-0.6": {"wd": 6, "ht": 2.8},
        "M4-0.7": {"wd": 7, "ht": 3.2},
        "M5-0.8": {"wd": 8, "ht": 4},
        "M6-1": {"wd": 10, "ht": 5},
        "M7-1": {"wd": 11, "ht": 5.5},
        "M8-1.25": {"wd": 13, "ht": 6.5},
        "M8-1": {"wd": 13, "ht": 6.5},
        "M10-1.25": {"wd": 17, "ht": 8},
        "M10-1.5": {"wd": 17, "ht": 8},
        "M10-1": {"wd": 17, "ht": 8},
        "M12-1.25": {"wd": 19, "ht": 10},
        "M12-1.5": {"wd": 19, "ht": 10},
        "M12-1.75": {"wd": 19, "ht": 10},
        "M12-1": {"wd": 19, "ht": 10},
        "M14-1.5": {"wd": 22, "ht": 11},
        "M14-2": {"wd": 22, "ht": 11},
        "M16-1.5": {"wd": 24, "ht": 13},
        "M16-2": {"wd": 24, "ht": 13},
        "M18-1.5": {"wd": 27, "ht": 15},
        "M18-2.5": {"wd": 27, "ht": 15},
        "M20-1.5": {"wd": 30, "ht": 16},
        "M20-2.5": {"wd": 30, "ht": 16},
        "M20-2": {"wd": 30, "ht": 14.3},
        "M22-1.5": {"wd": 32, "ht": 18},
        "M22-2.5": {"wd": 32, "ht": 18},
        "M24-1.5": {"wd": 36, "ht": 19},
        "M24-2": {"wd": 36, "ht": 19},
        "M24-3": {"wd": 36, "ht": 19},
        "M27-1.5": {"wd": 41, "ht": 20.7},
        "M27-2": {"wd": 41, "ht": 20.7},
        "M27-3": {"wd": 41, "ht": 22},
        "M30-1.5": {"wd": 46, "ht": 24},
        "M30-2": {"wd": 46, "ht": 22.7},
        "M30-3.5": {"wd": 46, "ht": 24},
        "M33-1.5": {"wd": 50, "ht": 24.7},
        "M33-2": {"wd": 50, "ht": 24.7},
        "M33-3.5": {"wd": 50, "ht": 24.7},
        "M36-1.5": {"wd": 55, "ht": 29},
        "M36-3": {"wd": 55, "ht": 27.4},
        "M36-4": {"wd": 55, "ht": 29},
        "M42-4.5": {"wd": 65, "ht": 34},
        "M48-5": {"wd": 75, "ht": 38},
    }

    # Standard Imperial Nut sizes
    # Size-TPI: wd=Width, ht=Height
    imperial_nut_parameters = {
        "#0000-160": {"wd": (1 / 16) * IN, "ht": (1 / 32) * IN},
        "#000-120": {"wd": (5 / 64) * IN, "ht": (1 / 32) * IN},
        "#00-90": {"wd": (5 / 64) * IN, "ht": (3 / 64) * IN},
        "#00-96": {"wd": (5 / 64) * IN, "ht": (3 / 64) * IN},
        "#0-80": {"wd": (5 / 32) * IN, "ht": (3 / 64) * IN},
        "#1-64": {"wd": (5 / 32) * IN, "ht": (3 / 64) * IN},
        "#1-72": {"wd": (5 / 32) * IN, "ht": (3 / 64) * IN},
        "#2-56": {"wd": (3 / 16) * IN, "ht": (1 / 16) * IN},
        "#2-64": {"wd": (3 / 16) * IN, "ht": (1 / 16) * IN},
        "#3-48": {"wd": (3 / 16) * IN, "ht": (1 / 16) * IN},
        "#3-56": {"wd": (3 / 16) * IN, "ht": (1 / 16) * IN},
        "#4-36": {"wd": (1 / 4) * IN, "ht": (3 / 32) * IN},
        "#4-40": {"wd": (1 / 4) * IN, "ht": (3 / 32) * IN},
        "#4-48": {"wd": (1 / 4) * IN, "ht": (3 / 32) * IN},
        "#5-40": {"wd": (5 / 16) * IN, "ht": (7 / 64) * IN},
        "#5-44": {"wd": (5 / 16) * IN, "ht": (7 / 64) * IN},
        "#6-32": {"wd": (5 / 16) * IN, "ht": (7 / 64) * IN},
        "#6-40": {"wd": (5 / 16) * IN, "ht": (7 / 64) * IN},
        "#8-32": {"wd": (11 / 32) * IN, "ht": (1 / 8) * IN},
        "#8-36": {"wd": (11 / 32) * IN, "ht": (1 / 8) * IN},
        "#10-24": {"wd": (3 / 8) * IN, "ht": (1 / 8) * IN},
        "#10-32": {"wd": (3 / 8) * IN, "ht": (1 / 8) * IN},
        "#12-24": {"wd": (7 / 16) * IN, "ht": (5 / 32) * IN},
        "#12-28": {"wd": (7 / 16) * IN, "ht": (5 / 32) * IN},
        '1/4"-20': {"wd": (7 / 16) * IN, "ht": (7 / 32) * IN},
        '1/4"-28': {"wd": (7 / 16) * IN, "ht": (7 / 32) * IN},
        '5/16"-18': {"wd": (1 / 2) * IN, "ht": (17 / 64) * IN},
        '5/16"-24': {"wd": (1 / 2) * IN, "ht": (17 / 64) * IN},
        '3/8"-16': {"wd": (9 / 16) * IN, "ht": (21 / 64) * IN},
        '3/8"-24': {"wd": (9 / 16) * IN, "ht": (21 / 64) * IN},
        '7/16"-14': {"wd": (11 / 16) * IN, "ht": (3 / 8) * IN},
        '7/16"-20': {"wd": (11 / 16) * IN, "ht": (3 / 8) * IN},
        '1/2"-13': {"wd": (3 / 4) * IN, "ht": (7 / 16) * IN},
        '1/2"-20': {"wd": (3 / 4) * IN, "ht": (7 / 16) * IN},
        '9/16"-12': {"wd": (7 / 8) * IN, "ht": (31 / 64) * IN},
        '9/16"-18': {"wd": (7 / 8) * IN, "ht": (31 / 64) * IN},
        '5/8"-11': {"wd": (15 / 16) * IN, "ht": (35 / 64) * IN},
        '5/8"-18': {"wd": (15 / 16) * IN, "ht": (35 / 64) * IN},
        '3/4"-10': {"wd": (1 + 1 / 8) * IN, "ht": (41 / 64) * IN},
        '3/4"-16': {"wd": (1 + 1 / 8) * IN, "ht": (41 / 64) * IN},
        '7/8"-14': {"wd": (1 + 5 / 16) * IN, "ht": (3 / 4) * IN},
        '7/8"-9': {"wd": (1 + 5 / 16) * IN, "ht": (3 / 4) * IN},
        '1"-8': {"wd": (1 + 1 / 2) * IN, "ht": (55 / 64) * IN},
        '1"-12': {"wd": (1 + 1 / 2) * IN, "ht": (55 / 64) * IN},
        '1"-14': {"wd": (1 + 1 / 2) * IN, "ht": (55 / 64) * IN},
        '1 1/8"-7': {"wd": (1 + 11 / 16) * IN, "ht": (31 / 32) * IN},
        '1 1/8"-12': {"wd": (1 + 11 / 16) * IN, "ht": (31 / 32) * IN},
        '1 1/4"-7': {"wd": (1 + 7 / 8) * IN, "ht": (1 + 1 / 16) * IN},
        '1 1/4"-12': {"wd": (1 + 7 / 8) * IN, "ht": (1 + 1 / 16) * IN},
        '1 3/8"-12': {"wd": (2 + 1 / 16) * IN, "ht": (1 + 11 / 64) * IN},
        '1 3/8"-6': {"wd": (2 + 1 / 16) * IN, "ht": (1 + 11 / 64) * IN},
        '1 1/2"-6': {"wd": (2 + 1 / 4) * IN, "ht": (1 + 9 / 32) * IN},
        '1 1/2"-12': {"wd": (2 + 1 / 4) * IN, "ht": (1 + 9 / 32) * IN},
        '1 5/8"-5 1/2': {"wd": (2 + 7 / 16) * IN, "ht": (1 + 25 / 64) * IN},
        '1 5/8"-12': {"wd": (2 + 7 / 16) * IN, "ht": (1 + 25 / 64) * IN},
        '1 3/4"-5': {"wd": (2 + 5 / 8) * IN, "ht": (1 + 1 / 2) * IN},
        '1 3/4"-12': {"wd": (2 + 5 / 8) * IN, "ht": (1 + 1 / 2) * IN},
        '1 7/8"-5': {"wd": (2 + 13 / 16) * IN, "ht": (1 + 39 / 64) * IN},
        '1 7/8"-12': {"wd": (2 + 13 / 16) * IN, "ht": (1 + 39 / 64) * IN},
        '2"-4 1/2': {"wd": (3) * IN, "ht": (1 + 23 / 32) * IN},
        '2"-12': {"wd": (3) * IN, "ht": (1 + 23 / 32) * IN},
        '2 1/4"-4 1/2': {"wd": (3 + 3 / 8) * IN, "ht": (1 + 15 / 16) * IN},
        '2 1/4"-12': {"wd": (3 + 3 / 8) * IN, "ht": (1 + 15 / 16) * IN},
        '2 1/2"-4': {"wd": (3 + 3 / 4) * IN, "ht": (2 + 5 / 32) * IN},
        '2 1/2"-12': {"wd": (3 + 3 / 4) * IN, "ht": (2 + 5 / 32) * IN},
        '2 3/4"-4': {"wd": (4 + 1 / 8) * IN, "ht": (2 + 3 / 8) * IN},
        '3"-4': {"wd": (4 + 1 / 2) * IN, "ht": (2 + 19 / 32) * IN},
        '3"-12': {"wd": (4 + 1 / 2) * IN, "ht": (2 + 19 / 32) * IN},
        '3 1/2"-4': {"wd": (5 + 3 / 8) * IN, "ht": (3 + 1 / 2) * IN},
    }


class SocketHeadCapScrew:
    @cache
    def __init__(
        self,
        size: Optional[str] = None,
        length: float = None,
        head_diameter: Optional[float] = None,
        head_height: Optional[float] = None,
        thread_diameter: Optional[float] = None,
        thread_pitch: Optional[float] = None,
        thread_length: Optional[float] = None,
        socket_size: Optional[float] = None,
        socket_depth: Optional[float] = None,
    ):
        if size is not None:
            (
                self.thread_diameter,
                self.thread_pitch,
                self.head_diameter,
                self.head_height,
                self.socket_size,
                self.socket_depth,
            ) = SocketHeadCapScrew._extract_screw_parameters(size)
        else:
            self.thread_diameter = thread_diameter
            self.thread_pitch = thread_pitch
            self.head_diameter = head_diameter
            self.head_height = head_height
            self.socket_size = socket_size
            self.socket_depth = socket_depth
        if thread_length is not None:
            if thread_length > length:
                raise ValueError(
                    f"thread length ({thread_length}) must be less than of equal to length ({length})"
                )
            self.thread_length = thread_length
        else:
            self.thread_length = length
        self.length = length
        self.cq_object = SocketHeadCapScrew.make_socket_head_cap_screw(
            self.thread_diameter,
            self.thread_pitch,
            self.head_diameter,
            self.head_height,
            self.socket_size,
            self.socket_depth,
            self.length,
            self.thread_length,
        )

    def _extract_screw_parameters(
        size: str,
    ) -> Tuple[float, float, float, float, float, float]:
        """ Parse the screw size string into width, major_diameter, pitch and thickness """
        size_parts = size.split("-")
        if size in SocketHeadCapScrew.metric_socket_head_cap_screw_parametes.keys():
            nut_data = SocketHeadCapScrew.metric_socket_head_cap_screw_parametes[size]
            head_diameter = nut_data["hd"]
            head_height = nut_data["hh"]
            socket_size = nut_data["ss"]
            socket_depth = nut_data["sd"]
            thread_diameter = float(size_parts[0][1:])
            thread_pitch = float(size_parts[1])
        elif size in SocketHeadCapScrew.imperial_nut_parameters.keys():
            nut_data = SocketHeadCapScrew.imperial_nut_parameters[size]
            head_diameter = nut_data["wd"]
            thickness = nut_data["ht"]
            (thread_diameter, thread_pitch) = decode_imperial_size(size)
        else:
            raise ValueError(
                "Invalid socket head cap screw size, must be one of:"
                f"{list(SocketHeadCapScrew.metric_socket_head_cap_screw_parametes.keys())+list(Nut.imperial_nut_parameters.keys())}"
            )
        return (
            thread_diameter,
            thread_pitch,
            head_diameter,
            head_height,
            socket_size,
            socket_depth,
        )

    def make_socket_head_cap_screw(
        thread_diameter: float,
        thread_pitch: float,
        head_diameter: float,
        head_height: float,
        socket_size: float,
        socket_depth: float,
        length: float,
        thread_length: float,
    ):

        body_length = 0 if thread_length is None else length - thread_length

        print(
            thread_diameter,
            thread_pitch,
            head_diameter,
            head_height,
            socket_size,
            socket_depth,
        )
        thread_object = ExternalThread(
            major_diameter=thread_diameter,
            thread_pitch=thread_pitch,
            thread_length=thread_length,
        )

        screw = (
            cq.Workplane("XY")
            .circle(head_diameter / 2)
            .polygon(6, socket_size / cos(pi / 6))
            .extrude(socket_depth)
            .faces("<Z")
            .edges(cq.selectors.RadiusNthSelector(0))
            .fillet(head_diameter / 20)
            .faces(">Z")
            .workplane()
            .circle(head_diameter / 2)
            .extrude(head_height - socket_depth)
            .faces(">Z")
            .edges(cq.selectors.RadiusNthSelector(0))
            .fillet(head_diameter / 20)
        )
        if body_length != 0:
            screw = (
                screw.faces(">Z")
                .workplane()
                .circle(thread_diameter / 2)
                .extrude(body_length)
                .faces(">Z[2]")
                .edges()
                .fillet(head_diameter / 20)
            )
        screw = screw.union(
            thread_object.cq_object.translate((0, 0, head_height + body_length)),
            glue=True,
        )
        return screw

    # Size-Pitch: hd=Head Diameter, hh=Head Height, ss=Hexagon Socket Size, sd=Hexagon Socket Depth
    metric_socket_head_cap_screw_parametes = {
        "M3-0.5": {"hd": 5.50, "hh": 3.00, "ss": 2.50, "sd": 1.50},
        "M4-0.7": {"hd": 7.00, "hh": 4.00, "ss": 3.00, "sd": 2.00},
        "M5-0.8": {"hd": 8.50, "hh": 5.00, "ss": 4.0, "sd": 2.50},
        "M6-1.0": {"hd": 10.00, "hh": 6.00, "ss": 5.00, "sd": 3.00},
        "M8-1.25": {"hd": 13.00, "hh": 8.00, "ss": 6.00, "sd": 4.00},
        "M10-1.5": {"hd": 16.00, "hh": 10.00, "ss": 8.00, "sd": 5.00},
        "M12-1.75": {"hd": 18.00, "hh": 12.00, "ss": 10.00, "sd": 6.00},
        "M14-2.0": {"hd": 21.00, "hh": 14.00, "ss": 12.00, "sd": 7.00},
        "M16-2.0": {"hd": 24.00, "hh": 16.00, "ss": 14.00, "sd": 8.00},
        "M20-2.5": {"hd": 30.00, "hh": 20.00, "ss": 17.00, "sd": 10.00},
        "M24-3.0": {"hd": 36.00, "hh": 24.00, "ss": 19.00, "sd": 12.00},
        "M30-3.5": {"hd": 45.00, "hh": 30.00, "ss": 22.00, "sd": 15.00},
        "M36-4.0": {"hd": 54.00, "hh": 36.00, "ss": 27.00, "sd": 18.00},
        "M42-4.5": {"hd": 63.00, "hh": 42.00, "ss": 32.00, "sd": 21.00},
        "M48-5.0": {"hd": 72.00, "hh": 48.00, "ss": 36.00, "sd": 24.00},
    }


# nut = Nut("M4-0.7")
# # nut = Nut("M4-0.7", shape="square")
# print(nut.cq_object.isValid())
# cq.exporters.export(nut.cq_object, "nut.step")

# screw = SocketHeadCapScrew("M4-0.7", length=20*MM)
# print(screw.cq_object.isValid())
# cq.exporters.export(screw.cq_object, "screw.step")

thread = ExternalThread(major_diameter=4, thread_pitch=0.7, thread_length=20 * MM)
if "show_object" in locals():
    # show_object(t,name="thread")
    # show_object(nut.cq_object, name="nut")
    show_object(screw.cq_object, name="screw")
    # show_object(internal, name="internal")
    # show_object(external, name="external")
    # show_object(threadGuide,name="threadGuide")
