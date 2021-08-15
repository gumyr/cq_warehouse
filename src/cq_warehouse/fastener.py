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
from typing import Literal, Tuple
import cadquery as cq
import math
from math import sin, cos, tan, radians, pi, ceil
import cProfile
from cadquery import selectors

MM = 1
IN = 25.4 * MM

# from tqdm import tqdm

# ISO Standard Metric Nut sizes
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


# Size:Diameter,Pitch,Head Diameter,Head Height,Hexagon Socket Size,Key Engagement
socketHeadCapScrew = {
    "M3-0.5": [3.00, 0.50, 5.50, 3.00, 2.50, 1.50],
    "M4-0.7": [4.00, 0.70, 7.00, 4.00, 3.00, 2.00],
    "M5-0.8": [5.00, 0.80, 8.50, 5.00, 4.0, 2.50],
    "M6-1.0": [6.00, 1.00, 10.00, 6.00, 5.00, 3.00],
    "M8-1.25": [8.00, 1.25, 13.00, 8.00, 6.00, 4.00],
    "M10-1.5": [10.00, 1.50, 16.00, 10.00, 8.00, 5.00],
    "M12-1.75": [12.00, 1.75, 18.00, 12.00, 10.00, 6.00],
    "M14-2.0": [14.00, 2.00, 21.00, 14.00, 12.00, 7.00],
    "M16-2.0": [16.00, 2.00, 24.00, 16.00, 14.00, 8.00],
    "M20-2.5": [20.00, 2.50, 30.00, 20.00, 17.00, 10.00],
    "M24-3.0": [24.00, 3.00, 36.00, 24.00, 19.00, 12.00],
    "M30-3.5": [30.00, 3.50, 45.00, 30.00, 22.00, 15.00],
    "M36-4.0": [36.00, 4.00, 54.00, 36.00, 27.00, 18.00],
    "M42-4.5": [42.00, 4.50, 63.00, 42.00, 32.00, 21.00],
    "M48-5.0": [48.00, 5.00, 72.00, 48.00, 36.00, 24.00],
}
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


def thread_h_parameter(pitch: float, thread_angle: float = 60) -> float:
    return (pitch / 2) / tan(radians(thread_angle / 2))


def internalIsoThreadProfile(
    diameter: float, pitch: float
) -> Tuple[cq.Workplane, float]:
    """
    Based on this diagram:
    https://en.wikipedia.org/wiki/ISO_metric_screw_thread#/media/File:ISO_and_UTS_Thread_Dimensions.svg
    """

    thread_angle = 60  # ISO standard
    h = thread_h_parameter(pitch, thread_angle)
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


def externalIsoThreadProfile(
    diameter: float, pitch: float
) -> Tuple[cq.Workplane, float]:
    """
    Based on this diagram:
    https://en.wikipedia.org/wiki/ISO_metric_screw_thread#/media/File:ISO_and_UTS_Thread_Dimensions.svg
    """
    thread_angle = 60  # ISO standard
    # h = (pitch / 2) / tan(radians(thread_angle / 2))
    h = thread_h_parameter(pitch, thread_angle)

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


def makeIsoThread(
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
        (threadProfile, threadRadius) = externalIsoThreadProfile(diameter, pitch)
        sweep_offset = 0
    else:
        (threadProfile, threadRadius) = internalIsoThreadProfile(diameter, pitch)
        sweep_offset = -pitch

    # Step 2: Sweep the profile along the threadPath and extract the outer wire
    threadPath = cq.Wire.makeHelix(pitch=pitch, height=pitch, radius=threadRadius)
    threadWire = (
        cq.Workplane("XY")
        .add(
            threadProfile.sweep(path=cq.Workplane(threadPath), isFrenet=True).translate(
                (0, 0, sweep_offset)
            )
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
            radius=diameter / 2 + 3 * thread_h_parameter(pitch) / 4,
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


def make_standard_nut(size: str, shape: Literal["hex", "square"] = "hex") -> cq.Solid:
    """ Create a standard sized hex or square nut """
    size_parts = size.split("-")
    if size in metric_nut_parameters.keys():
        nut_data = metric_nut_parameters[size]
        width = nut_data["wd"]
        thickness = nut_data["ht"]
        major_diameter = float(size_parts[0][1:])
        pitch = float(size_parts[1])
    elif size in imperial_nut_parameters.keys():
        nut_data = imperial_nut_parameters[size]
        width = nut_data["wd"]
        thickness = nut_data["ht"]
        (major_diameter, pitch) = decode_imperial_size(size)
    else:
        raise ValueError(
            "Invalid nut size - must be one of:"
            f"{list(metric_nut_parameters.keys())+list(imperial_nut_parameters.keys())}"
        )

    return make_nut(width, major_diameter, pitch, thickness, shape)


def make_nut(
    width: float,
    major_diameter: float,
    pitch: float,
    thickness: float,
    shape: Literal["hex", "square"] = "hex",
) -> cq.Solid:
    """ Create an arbitrary sized hex or square nut """

    outer_diameter = width / cos(pi / 6)

    # Calculate the chamfer size
    c = 1.0 * major_diameter * (1 / cos(pi / 6) - 1) / 2

    thread_outer_diameter = major_diameter + 3 * thread_h_parameter(pitch) / 2
    # Create the thread
    thread = makeIsoThread(
        diameter=major_diameter, pitch=pitch, length=thickness, external=False
    )

    if shape == "hex":
        # The nutBody define the chamfered edges of the nut
        nutBody = (
            cq.Workplane("XY")
            .circle(outer_diameter / 2)  # Create a circle that contains the hexagon
            .circle(thread_outer_diameter / 2)  # .. with a hole in the center
            .extrude(thickness)
            .edges(selectors.RadiusNthSelector(1))
            .chamfer(c / 2, c)  # Chamfer the outside edges
            .intersect(
                cq.Workplane("XY")
                .polygon(6, major_diameter / cos(pi / 6))
                .extrude(thickness)
            )
        )
    else:
        nutBody = (
            cq.Workplane("XY")
            .rect(width, width)
            .circle(thread_outer_diameter / 2)
            .extrude(thickness)
        )
    nut = nutBody.union(thread, glue=True).val()
    return nut


def makeSocketHeadCapScrew(size: str, length: float, threadLength: float = None):

    try:
        (
            diameter,
            pitch,
            headDiameter,
            headHeight,
            hexagonSocketSize,
            keyEngagement,
        ) = socketHeadCapScrew[size]
    except ValueError:
        print(
            "Invalid socket head cap screw size, must be one of:",
            list(socketHeadCapScrew.keys()),
        )

    gripLength = 0 if threadLength is None else length - threadLength

    print(diameter, pitch, headDiameter, headHeight, hexagonSocketSize, keyEngagement)
    thread = makeIsoThread(
        diameter=diameter, pitch=pitch, length=length - gripLength, external=True
    )
    # thread = cq.Workplane("XY").circle(diameter/2).extrude(length).faces(">Z").edges().chamfer(diameter/8).intersect(thread)

    screw = (
        cq.Workplane("XY")
        .circle(headDiameter / 2)
        .polygon(6, hexagonSocketSize / cos(pi / 6))
        .extrude(keyEngagement)
        .faces("<Z")
        .edges(cq.selectors.RadiusNthSelector(0))
        .fillet(headDiameter / 20)
        .faces(">Z")
        .workplane()
        .circle(headDiameter / 2)
        .extrude(headHeight - keyEngagement)
        .faces(">Z")
        .edges(cq.selectors.RadiusNthSelector(0))
        .fillet(headDiameter / 20)
        # .circle(rmin)
        # .extrude(length)
        # .union(thread.translate((0,0,headHeight)))
    )
    if gripLength != 0:
        screw = (
            screw.faces(">Z")
            .workplane()
            .circle(diameter / 2)
            .extrude(gripLength)
            .faces(">Z[2]")
            .edges()
            .fillet(headDiameter / 20)
        )
    screw = screw.union(thread.translate((0, 0, headHeight + gripLength)))
    return screw


# threadAngle = 60  # ISO standard
# pitch = 0.8
# diameter = 5
# (internal, thread_radius) = internalIsoThreadProfile(diameter, pitch)
# external = externalIsoThreadProfile(diameter, pitch)

# internal = makeInternalIsoThread(diameter=diameter, pitch=pitch, length=4)
# external = makeExternalIsoThread(diameter=diameter, pitch=pitch, length=4)
# internal = makeIsoThread(diameter=diameter, pitch=pitch, length=4, external=False)
# external = makeIsoThread(diameter=diameter, pitch=pitch, length=4, external=True)
# "(external, m, n) = makeExternalIsoThread(diameter=diameter, pitch=pitch, length=4)",
# cProfile.run(
#     "(internal, m, n) = makeInternalIsoThread(diameter=diameter, pitch=pitch, length=4)",
#     sort=1,
# )
# # Used to verify the thread profile against the standard

# h = (pitch/2)/tan(radians(threadAngle/2))
# maxD = diameter
# minR = (maxD - 2*(5/8)*h)/2
# threadGuide = (cq.Workplane("XZ")
#     .moveTo(minR-h/4,0)
#     .lineTo(maxD/2+h/8,pitch/2)
#     .lineTo(minR-h/4,pitch)
#     .close()
# )

# thread = makeIsoThread(diameter=diameter, pitch=pitch, length=4, external=False)

# nut = make_nut("#10")

nut = make_standard_nut("M4-0.7")
print(nut.isValid())

# screw = makeSocketHeadCapScrew(size="M4-0.7",length=20,threadLength=5)
# (valley, m, n) = makeExternalIsoThread(diameter=diameter, pitch=pitch, length=10)
# cq.exporters.export(screw, "screw.step")

# test = cq.Assembly(None)
# test.add(thread)
# test.add(nut)
# test.save("test.step")
cq.exporters.export(nut, "nut.step")


# if __name__ == "__main__" or "show_object" in locals():

if "show_object" in locals():
    # show_object(t,name="thread")
    show_object(nut, name="nut")
    # show_object(screw,name="screw")
    # show_object(internal, name="internal")
    # show_object(external, name="external")
    # show_object(threadGuide,name="threadGuide")
