"""

Parametric Threaded Fasteners

name: fastener.py
by:   Gumyr
date: August 14th 2021

desc:

    This python/cadquery code is a parameterized threaded fastener generator.
    Currently the following classes are defined:
    - Thread
    - HexNut
    - SquareNut
    - Screw
    - SocketHeadCapScrew
    - ButtonHeadCapScrew
    - HexBolt
    - SetScrew

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
from typing import Literal, Tuple, Optional, overload, List
from math import sin, cos, tan, radians, pi, degrees
from functools import cache
import csv
import importlib.resources as pkg_resources
from pydantic import BaseModel, PrivateAttr
import cadquery as cq
import cq_warehouse

# import cProfile
# from functools import cache, cached_property

MM = 1
IN = 25.4 * MM


def read_fastener_parameters_from_csv(filename: str) -> dict:
    """ Parse a csv parameter file into a dictionary of strings """

    parameters = {}
    with pkg_resources.open_text(cq_warehouse, filename) as csvfile:
        reader = csv.DictReader(csvfile)
        fieldnames = reader.fieldnames
        for row in reader:
            key = row[fieldnames[0]]
            row.pop(fieldnames[0])
            parameters[key] = row

    return parameters


def is_safe(value: str) -> bool:
    """ Evaluate if the given string is a fractional number save for eval() """
    return len(value) <= 10 and all(c in "0123456789./ " for c in set(value))


def imperial_str_to_float(measure: str) -> float:
    """ Convert an imperial measurement (possibly a fraction) to a float value """
    if not is_safe(measure):
        raise ValueError(f"{measure} is not a valid measurement")
    # pylint: disable=eval-used
    # Before eval() is called the string extracted from the csv file is verified as safe
    return eval(measure.strip().replace(" ", "+")) * IN


def decode_imperial_size(size: str) -> Tuple[float, float]:
    """ Extract the major diameter and pitch from an imperial size """

    # Imperial # sizes to diameters
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

    sizes = size.split("-")
    if size[0] == "#":
        major_diameter = imperial_numbered_sizes[sizes[0]]
    else:
        major_diameter = imperial_str_to_float(sizes[0])
    pitch = IN / (imperial_str_to_float(sizes[1]) / IN)
    return (major_diameter, pitch)


def metric_str_to_float(measure: str) -> float:
    """ Convert a metric measurement to a float value """

    if not is_safe(measure):
        raise ValueError(f"{measure} is not a valid measurement")
    # pylint: disable=eval-used
    # Before eval() is called the string, extracted from the csv file, is verified as safe
    return eval(measure)


def evaluate_parameter_dict(
    parameters: dict, units: Literal["metric", "imperial"] = "metric"
) -> dict:
    """ Convert string values in a dict of dict structure to floats based on provided units """

    measurements = {}
    for key, data in parameters.items():
        if units == "metric":
            measurements[key] = {
                params: metric_str_to_float(value) for params, value in data.items()
            }
        else:
            measurements[key] = {
                params: imperial_str_to_float(value) for params, value in data.items()
            }

    return measurements


class Thread(BaseModel):
    """ Parametric Thread Objects """

    major_diameter: float
    pitch: float
    length: float
    hand: Literal["right", "left"] = "right"
    hollow: bool = False
    thread_angle: Optional[float] = 60.0  # Default to ISO standard

    # Private Attributes
    _cq_object: cq.Workplane = PrivateAttr()

    @property
    def h_parameter(self) -> float:
        """ Calculate the h parameter as shown in the following diagram:
        https://en.wikipedia.org/wiki/ISO_metric_screw_thread#/media/File:ISO_and_UTS_Thread_Dimensions.svg
        """
        return (self.pitch / 2) / tan(radians(self.thread_angle / 2))

    @property
    def min_radius(self) -> float:
        """ The inside of the thread as shown in the following diagram:
        https://en.wikipedia.org/wiki/ISO_metric_screw_thread#/media/File:ISO_and_UTS_Thread_Dimensions.svg
        """
        return (self.major_diameter - 2 * (5 / 8) * self.h_parameter) / 2

    @property
    def thread_radius(self) -> float:
        """ The center of the thread radius or pitch radius
            Replaced by child class implementation """
        return None

    @property
    # @cached_property
    def cq_object(self):
        """ A cadquery Solid thread as defined by class attributes """
        return self._cq_object
        # return self.make_thread()

    def __init__(self, **data):
        """ Validate inputs and create the chain assembly object """
        # Use the BaseModel initializer to validate the attributes
        super().__init__(**data)
        # Create the thread
        self._cq_object = self.make_thread()

    @staticmethod
    def find_perimeter_edges(all_edges: List[cq.Edge]) -> List[cq.Edge]:
        """ Filter the edge list to those on the exterior of the thread section """

        # Filter out edges that radiate from the origin
        outside_edges = [
            edge
            for edge in all_edges
            if abs(degrees(edge.positionAt(0).getAngle(edge.tangentAt(0))) - 90) < 20
        ]
        min_radius = min([e.positionAt(0).Length for e in outside_edges])
        # Filter out edges in the inner ring
        outside_edges = [
            edge
            for edge in outside_edges
            if edge.positionAt(0).Length > 1.2 * min_radius
        ]
        return outside_edges

    def thread_profile(self) -> cq.Workplane:
        """ Replaced by child class implementation """

    def revolve_wires(self, thread_wire) -> Tuple[cq.Wire, cq.Wire]:
        """ Replaced by child class implementation """

    def make_thread(self) -> cq.Solid:
        """
        Create a Solid thread object.

        External threads would typically be combined with other objects via a union() into a bolt.
        Internal threads would typically be placed into an appropriately sized hole and combined
        with other objects via a union(). This construction method allows the OCCT core to
        successfully build threaded objects and does so significantly faster if the 'glue' mode of
        the union method is used (glue requires non-overlapping shapes). Other build techniques,
        like using the cut() method to remove an internal thread from an object, often fails or
        takes an excessive amount of time.

        The thread is created in three steps:
        1) Generate the 2D profile of an external thread with the given parameters on XZ plane
        2) Sweep the thread profile creating a single thread then extract the outer wire on XY plane
        3) extrudeLinearWithRotation the outer wire to the desired length

        This process is used to avoid the OCCT core issues with sweeping the thread profile
        such that it contacts itself as the helix makes a full loop.

        """
        # print(self.__dict__.items())

        # Step 1 - Create the 2D thread profile
        # pylint: disable=assignment-from-no-return
        # thread_profile() defined in child class
        thread_profile = self.thread_profile()

        # Step 2: Sweep the profile along the threadPath and extract the wires
        thread_path = cq.Wire.makeHelix(
            pitch=self.pitch,
            height=self.pitch / 2,
            radius=self.thread_radius,
            lefthand=self.hand == "left",
        )
        half_thread = cq.Workplane("XY").add(
            thread_profile.sweep(path=cq.Workplane(thread_path), isFrenet=True)
        )
        # Frustratingly, sweep() is inconsistent in the vertical alignment of the object
        # so the thread needs to centered vertically
        half_thread = half_thread.translate(
            (0, 0, -half_thread.val().Center().z + self.pitch / 4)
        )
        all_edges = half_thread.section().edges()
        # Select all the edges on the perimeter of the thread as there are edges
        # that radiate from the center to the perimeter in all_edges
        outside_edges = Thread.find_perimeter_edges(all_edges.vals())
        partial_thread_wire = cq.Wire.assembleEdges(outside_edges)
        # Create the other half of the thread outline
        thread_wire = cq.Wire.combine(
            [partial_thread_wire, partial_thread_wire.mirror("XZ")]
        )[0]

        # Step 3: Create thread by rotating while extruding thread wire
        # pylint: disable=assignment-from-no-return
        # revolve_wires() defined in child class
        (outer_wire, inner_wires) = self.revolve_wires(thread_wire)

        sign = 1 if self.hand == "right" else -1
        thread = cq.Solid.extrudeLinearWithRotation(
            outerWire=outer_wire,
            innerWires=inner_wires,
            vecCenter=cq.Vector(0, 0, 0),
            vecNormal=cq.Vector(0, 0, self.length),
            angleDegrees=sign * 360 * (self.length / self.pitch),
        )

        return thread

    def make_shank(
        self, body_length: float, body_diameter: Optional[float] = None
    ) -> cq.Solid:
        """ Create a bolt shank consisting of an optional non-threaded body & threaded section """
        if body_length > 0:
            if body_diameter is not None:
                diameter = body_diameter
                chamfer_size = (body_diameter - self.major_diameter) / 2
            else:
                diameter = self.major_diameter
                chamfer_size = None
            shank = cq.Workplane("XY").circle(diameter / 2).extrude(-body_length)
            if chamfer_size is not None and chamfer_size != 0:
                shank = shank.faces("<Z").chamfer(chamfer_size)
            shank = shank.union(
                self.cq_object.translate((0, 0, -body_length - self.length))
            )
        else:
            shank = self.cq_object.translate((0, 0, -self.length))
        return shank


class ExternalThread(Thread):
    """ Create a thread object used in a bolt """

    @property
    def thread_radius(self) -> float:
        """ The center of the thread radius or pitch radius """
        return self.min_radius - self.h_parameter / 4

    @property
    def external_thread_core_radius(self) -> float:
        """ The radius of an internal thread object used to size an appropriate hole """
        if self.hollow:
            value = self.major_diameter / 2 - 7 * self.h_parameter / 8
        else:
            value = None
        return value

    def thread_profile(self) -> cq.Workplane:
        """
        Generae a 2D profile of a single external thread based on this diagram:
        https://en.wikipedia.org/wiki/ISO_metric_screw_thread#/media/File:ISO_and_UTS_Thread_Dimensions.svg
        """

        # Note: starting the thread profile at the origin will result in inconsistent results when
        # sweeping and extracting the outer edges
        thread_profile = (
            cq.Workplane("XZ")
            .moveTo(self.thread_radius / 2, 0)
            .lineTo(self.min_radius - self.h_parameter / 12, 0)
            .spline(
                [(self.min_radius, self.pitch / 8)],
                tangents=[
                    (0, 1, 0),
                    (
                        sin(radians(90 - self.thread_angle / 2)),
                        cos(radians(90 - self.thread_angle / 2)),
                    ),
                ],
                includeCurrent=True,
            )
            .lineTo(self.major_diameter / 2, 7 * self.pitch / 16)
            .lineTo(self.major_diameter / 2, 9 * self.pitch / 16)
            .lineTo(self.min_radius, 7 * self.pitch / 8)
            .spline(
                [(self.min_radius - self.h_parameter / 12, self.pitch)],
                tangents=[
                    (
                        -sin(radians(90 - self.thread_angle / 2)),
                        cos(radians(90 - self.thread_angle / 2)),
                    ),
                    (0, 1, 0),
                ],
                includeCurrent=True,
            )
            .lineTo(self.thread_radius / 2, self.pitch)
            .close()
        )
        return thread_profile

    def revolve_wires(self, thread_wire) -> Tuple:
        if self.hollow:
            inner_wires = [
                cq.Wire.makeCircle(
                    radius=self.major_diameter / 2 - 7 * self.h_parameter / 8,
                    center=cq.Vector(0, 0, 0),
                    normal=cq.Vector(0, 0, 1),
                )
            ]
        else:
            inner_wires = []
        return (thread_wire, inner_wires)


class InternalThread(Thread):
    """ Create a thread object used in a nut """

    @property
    def thread_radius(self) -> float:
        """ The center of the thread radius or pitch radius """
        return self.min_radius + 3 * self.h_parameter / 4

    @property
    def internal_thread_socket_radius(self) -> float:
        """ The radius of an internal thread object used to size an appropriate hole """
        return self.major_diameter / 2 + 3 * self.h_parameter / 4

    def thread_profile(self) -> cq.Workplane:
        """
        Generae a 2D profile of a single internal thread based on this diagram:
        https://en.wikipedia.org/wiki/ISO_metric_screw_thread#/media/File:ISO_and_UTS_Thread_Dimensions.svg
        """

        thread_profile = (
            cq.Workplane("XZ")
            .moveTo(self.thread_radius / 2, 0)
            .lineTo(self.min_radius, 0)
            .lineTo(self.min_radius, self.pitch / 8)
            .lineTo(self.major_diameter / 2, 7 * self.pitch / 16)
            .spline(
                [(self.major_diameter / 2, 9 * self.pitch / 16)],
                tangents=[
                    (
                        sin(radians(90 - self.thread_angle / 2)),
                        cos(radians(90 - self.thread_angle / 2)),
                    ),
                    (
                        -sin(radians(90 - self.thread_angle / 2)),
                        cos(radians(90 - self.thread_angle / 2)),
                    ),
                ],
                includeCurrent=True,
            )
            .lineTo(self.min_radius, 7 * self.pitch / 8)
            .lineTo(self.min_radius, self.pitch)
            .lineTo(self.thread_radius / 2, self.pitch)
            .close()
        )
        return thread_profile

    def revolve_wires(self, thread_wire) -> Tuple:
        outer_wire = cq.Wire.makeCircle(
            radius=self.major_diameter / 2 + 3 * self.h_parameter / 4,
            center=cq.Vector(0, 0, 0),
            normal=cq.Vector(0, 0, 1),
        )
        return (outer_wire, [thread_wire])


class Nut:
    """ Parent Class used to create standard or custom threaded nuts """

    @classmethod
    def set_parameters(cls):
        """ Create the class variables for the screw parameters """
        cls.metric_parameters = {}  # Empty metric data to be replaced by child
        cls.imperial_parameters = {}  # Empty imperial data to be replaced by child

    @cache
    def __init__(
        self,
        size: Optional[str] = None,
        width: Optional[float] = None,
        thread_diameter: Optional[float] = None,
        thread_pitch: Optional[float] = None,
        thickness: Optional[float] = None,
        hand: Literal["right", "left"] = "right",
    ):
        self.set_parameters()
        self.hand = hand
        if size is not None:
            self.size = size
            self._extract_nut_parameters()
        else:
            self.width = width
            self.thread_diameter = thread_diameter
            self.thread_pitch = thread_pitch
            self.thickness = thickness
        self.cq_object = self.make_nut()

    def _extract_nut_parameters(self):
        """ Parse the nut size string into thread_diameter, thread_pitch, width and thickness """
        if self.size in self.metric_parameters.keys():
            nut_data = self.metric_parameters[self.size]
            self.width = nut_data["Width"]
            self.thickness = nut_data["Height"]
            size_parts = self.size.split("-")
            self.thread_diameter = float(size_parts[0][1:])
            self.thread_pitch = float(size_parts[1])
        elif self.size in self.imperial_parameters.keys():
            nut_data = self.imperial_parameters[self.size]
            self.width = nut_data["Width"]
            self.thickness = nut_data["Height"]
            (self.thread_diameter, self.thread_pitch) = decode_imperial_size(self.size)
        else:
            raise ValueError(
                f"Invalid nut size {self.size} - must be one of:"
                f"{list(self.metric_parameters.keys())+list(self.imperial_parameters.keys())}"
            )

    def make_nut_body(self, internal_thread_socket_radius) -> cq.Workplane:
        """ Replaced by child class implementation """
        # pass

    def make_nut(self) -> cq.Solid:
        """ Create an arbitrary sized nut """

        thread = InternalThread(
            major_diameter=self.thread_diameter,
            pitch=self.thread_pitch,
            length=self.thickness,
            hand=self.hand,
        )
        nut = (
            self.make_nut_body(thread.internal_thread_socket_radius)
            # .union(thread.cq_object, glue=True)
            .val()
        )
        return nut


class HexNut(Nut):
    """ Create a hex nut """

    @classmethod
    def set_parameters(cls):
        cls.metric_parameters = evaluate_parameter_dict(
            read_fastener_parameters_from_csv("metric_hex_parameters.csv"),
            units="metric",
        )

        cls.imperial_parameters = evaluate_parameter_dict(
            read_fastener_parameters_from_csv("imperial_hex_parameters.csv"),
            units="imperial",
        )

    def make_nut_body(self, internal_thread_socket_radius) -> cq.Workplane:
        """ Create a hex nut body with chamferred top and bottom """

        # Distance across the tips of the hex
        hex_diameter = self.width / cos(pi / 6)
        # Chamfer between the hex tips and flats
        chamfer_size = (hex_diameter - self.width) / 2

        nut_body = (
            cq.Workplane("XY")
            .circle(hex_diameter / 2)  # Create a circle that contains the hexagon
            .circle(internal_thread_socket_radius)  # .. with a hole in the center
            .extrude(self.thickness)
            .edges(cq.selectors.RadiusNthSelector(1))
            .chamfer(chamfer_size / 2, chamfer_size)  # Chamfer the circular edges
            .intersect(
                cq.Workplane("XY").polygon(6, hex_diameter).extrude(self.thickness)
            )
        )
        return nut_body


class SquareNut(Nut):
    """ Create a square nut """

    @classmethod
    def set_parameters(cls):
        cls.metric_parameters = evaluate_parameter_dict(
            read_fastener_parameters_from_csv("metric_hex_parameters.csv"),
            units="metric",
        )

        cls.imperial_parameters = evaluate_parameter_dict(
            read_fastener_parameters_from_csv("imperial_hex_parameters.csv"),
            units="imperial",
        )

    def make_nut_body(self, internal_thread_socket_radius) -> cq.Workplane:

        nut_body = (
            cq.Workplane("XY")
            .rect(self.width, self.width)
            .circle(internal_thread_socket_radius)
            .extrude(self.thickness)
        )
        return nut_body


class Screw:
    """ Parent class for a set of threaded screws or bolts """

    @property
    def head(self):
        """ A cadquery Solid thread as defined by class attributes """
        return self.make_head()

    @property
    def shank(self):
        """ A cadquery Solid thread as defined by class attributes """
        return ExternalThread(
            major_diameter=self.thread_diameter,
            pitch=self.thread_pitch,
            length=self.thread_length,
            hand=self.hand,
        ).make_shank(self.body_length)

    @property
    def cq_object(self):
        """ A cadquery Solid thread as defined by class attributes """
        return self.head.union(self.shank, glue=True).val()

    @classmethod
    def set_parameters(cls):
        """ Create the class variables for the screw parameters """
        cls.metric_parameters = {}  # Empty metric data to be replaced by child
        cls.imperial_parameters = {}  # Empty imperial data to be replaced by child

    def __init__(self):
        """ Must be executed after __init__ in the child class where instance variables
            are assigned. Extract key parameters for standard sized screws """
        if not hasattr(self, "length"):
            raise AttributeError(
                "the attribute 'length' must be set in the child class of Screw"
            )

        # pylint: disable=no-member
        length = self.length
        if hasattr(self, "size"):
            # pylint: disable=no-member
            size_parts = self.size.split("-")
            if self.size in self.metric_parameters.keys():
                screw_data = self.metric_parameters[self.size]
                self.thread_diameter = float(size_parts[0][1:])
                self.thread_pitch = float(size_parts[1])
            elif self.size in self.imperial_parameters.keys():
                screw_data = self.imperial_parameters[self.size]
                (self.thread_diameter, self.thread_pitch) = decode_imperial_size(
                    self.size
                )
            else:
                raise ValueError(
                    f"Invalid socket head cap screw size {self.size}, must be one of:"
                    f"{list(self.metric_parameters.keys())}"
                    f"{list(self.imperial_parameters.keys())}"
                )
            for key in screw_data.keys():
                setattr(self, key.lower(), screw_data[key.title()])
        if not hasattr(self, "hand"):
            self.hand = "right"
        if not hasattr(self, "max_thread_length"):
            self.max_thread_length = length
        if not hasattr(self, "thread_length"):
            self.body_length = max(0, length - self.max_thread_length)
            self.thread_length = length - self.body_length
        elif self.thread_length > length:
            raise ValueError(
                f"thread length ({self.thread_length}) "
                "must be less than of equal to length ({self.length})"
            )
        else:
            self.body_length = max(0, length - self.max_thread_length)

    def make_head(self) -> cq.Workplane:
        """ Empty parent make screw head method to be replaced by child implementations """


class SocketHeadCapScrew(Screw):
    """ Create a standard or arbitrary sized socket head cap screw """

    @classmethod
    def set_parameters(cls):
        cls.metric_parameters = evaluate_parameter_dict(
            read_fastener_parameters_from_csv(
                "metric_socket_head_cap_screw_parameters.csv"
            ),
            units="metric",
        )
        cls.imperial_parameters = evaluate_parameter_dict(
            read_fastener_parameters_from_csv(
                "imperial_socket_head_cap_screw_parameters.csv"
            ),
            units="imperial",
        )

    @overload
    def __init__(
        self, size: str, length: float, hand: Literal["right", "left"] = "right"
    ):
        ...

    @overload
    def __init__(
        self,
        length: float,
        head_diameter: float,
        head_height: float,
        thread_diameter: float,
        thread_pitch: float,
        thread_length: float,
        socket_size: float,
        socket_depth: float,
        hand: Literal["right", "left"] = "right",
    ):
        ...

    @cache
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.set_parameters()
        super().__init__()

    def make_head(self) -> cq.Workplane:
        """ Construct cap screw head """

        screw_head = (
            cq.Workplane("XY")
            .circle(self.head_diameter / 2)  # pylint: disable=no-member
            .extrude(self.head_height - self.socket_depth)  # pylint: disable=no-member
            .faces(">Z")
            .workplane()
            .circle(self.head_diameter / 2)  # pylint: disable=no-member
            .polygon(6, self.socket_size / cos(pi / 6))  # pylint: disable=no-member
            .extrude(self.socket_depth)  # pylint: disable=no-member
            .faces(">Z")
            .edges(cq.selectors.RadiusNthSelector(0))
            .fillet(self.head_diameter / 20)  # pylint: disable=no-member
            .edges("<Z")
            .fillet(self.head_diameter / 40)  # pylint: disable=no-member
        )
        return screw_head


class ButtonHeadCapScrew(Screw):
    """ Create standard or arbitrary sized button head cap screws """

    @classmethod
    def set_parameters(cls):
        cls.metric_parameters = evaluate_parameter_dict(
            read_fastener_parameters_from_csv(
                "metric_button_head_cap_screw_parameters.csv"
            ),
            units="metric",
        )
        cls.imperial_parameters = evaluate_parameter_dict(
            read_fastener_parameters_from_csv(
                "imperial_button_head_cap_screw_parameters.csv"
            ),
            units="imperial",
        )

    @overload
    def __init__(
        self, size: str, length: float, hand: Literal["right", "left"] = "right"
    ):
        ...

    @overload
    def __init__(
        self,
        length: float,
        head_diameter: float,
        head_height: float,
        thread_diameter: float,
        thread_pitch: float,
        thread_length: float,
        socket_size: float,
        socket_depth: float,
        hand: Literal["right", "left"] = "right",
    ):
        ...

    @cache
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.set_parameters()
        super().__init__()

    def make_head(self) -> cq.Workplane:
        """ Construct button cap screw head """

        button_head = (
            cq.Workplane("XZ")
            .hLineTo(self.head_diameter / 2)  # pylint: disable=no-member
            .spline(
                listOfXYTuple=[(0, self.head_height)],  # pylint: disable=no-member
                includeCurrent=True,
            )
            .close()
            .revolve()
            .cut(
                cq.Workplane("XY")
                .polygon(
                    # pylint: disable=no-member
                    nSides=6,
                    diameter=self.socket_size / cos(pi / 6),
                )
                .extrude(self.socket_depth)  # pylint: disable=no-member
                .translate(
                    # pylint: disable=no-member
                    (0, 0, self.head_height - self.socket_depth)
                )
            )
            .edges("<Z")
            .fillet(self.head_diameter / 40)  # pylint: disable=no-member
        )
        return button_head


class HexBolt(Screw):
    """ Create a sock head cap screw as described either by a size sting or a set of parameters """

    @classmethod
    def set_parameters(cls):
        cls.metric_parameters = evaluate_parameter_dict(
            read_fastener_parameters_from_csv("metric_hex_parameters.csv"),
            units="metric",
        )

        cls.imperial_parameters = evaluate_parameter_dict(
            read_fastener_parameters_from_csv("imperial_hex_parameters.csv"),
            units="imperial",
        )

    @overload
    def __init__(
        self, size: str, length: float, hand: Literal["right", "left"] = "right"
    ):
        ...

    @overload
    def __init__(
        self,
        length: float,
        head_width: float,
        head_height: float,
        thread_diameter: float,
        thread_pitch: float,
        thread_length: float,
        hand: Literal["right", "left"] = "right",
    ):
        ...

    @cache
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.set_parameters()
        super().__init__()

    def make_head(self):
        """ Construct an arbitrary size hex bolt head """
        # Distance across the tips of the hex
        hex_diameter = self.width / cos(pi / 6)  # pylint: disable=no-member
        # Chamfer between the hex tips and flats
        chamfer_size = (hex_diameter - self.width) / 2  # pylint: disable=no-member
        bolt_head = (
            cq.Workplane("XY")
            .circle(hex_diameter / 2)  # Create a circle that contains the hexagon
            .extrude(self.height)  # pylint: disable=no-member
            .edges()
            .chamfer(chamfer_size / 2, chamfer_size)  # Chamfer the outside edges
            # pylint: disable=no-member
            .intersect(cq.Workplane("XY").polygon(6, hex_diameter).extrude(self.height))
        )

        return bolt_head


class SetScrew(Screw):
    """ Create standard or arbitrary set screws """

    @classmethod
    def set_parameters(cls):
        cls.metric_parameters = evaluate_parameter_dict(
            read_fastener_parameters_from_csv("metric_set_screw_parameters.csv"),
            units="metric",
        )
        cls.imperial_parameters = evaluate_parameter_dict(
            read_fastener_parameters_from_csv("imperial_set_screw_parameters.csv"),
            units="imperial",
        )

    @property
    def head(self):
        """ Setscrews don't have heads """
        return None

    @property
    def shank(self):
        """ Setscrews don't have shanks """
        return None

    @property
    def cq_object(self):
        """ A cadquery Solid thread as defined by class attributes """
        return self.make_setscrew()

    @overload
    def __init__(
        self, size: str, length: float, hand: Literal["right", "left"] = "right"
    ):
        ...

    @overload
    def __init__(
        self,
        length: float,
        thread_diameter: float,
        thread_pitch: float,
        socket_size: float,
        socket_depth: float,
        hand: Literal["right", "left"] = "right",
    ):
        ...

    @cache
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.set_parameters()
        super().__init__()

    def make_setscrew(self) -> cq.Workplane:
        """ Construct set screw shape """

        chamfer_size = self.thread_diameter / 4
        thread = ExternalThread(
            major_diameter=self.thread_diameter,
            pitch=self.thread_pitch,
            length=self.length - chamfer_size,
            hollow=True,
            hand=self.hand,
        )
        core = (
            cq.Workplane("XY")
            .circle(thread.external_thread_core_radius)
            .polygon(6, self.socket_size / cos(pi / 6))  # pylint: disable=no-member
            .extrude(self.socket_depth)  # pylint: disable=no-member
            .faces(">Z")
            .workplane()
            .circle(thread.external_thread_core_radius)
            .extrude(
                # pylint: disable=no-member
                self.length
                - self.socket_depth
            )
            .faces(">Z")
            .chamfer(chamfer_size)
            .mirror()
        )
        return core.union(
            thread.cq_object.translate((0, 0, -thread.length)), glue=True
        ).val()


nut = SquareNut(size="1/4-20")
cq.exporters.export(nut.cq_object, "nut.step")
# SetScrew.set_parameters()
# min_length = SetScrew.metric_parameters["M3-0.5"]["Socket_Depth"] * 1.5
# screw = SetScrew(size="M3-0.5", length=min_length)
# cq.exporters.export(screw.cq_object, "setscrew.step")

if "show_object" in locals():
    # show_object(thread.cq_object, name="thread")
    # show_object(nut.cq_object, name="nut")
    show_object(screw.cq_object, name="screw")
    # show_object(internal, name="internal")
    # show_object(external, name="external")
    # show_object(threadGuide,name="threadGuide")
