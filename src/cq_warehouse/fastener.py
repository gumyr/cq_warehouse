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
from typing import Literal, Tuple, Optional
from math import sin, cos, tan, radians, pi
from functools import cache, cached_property
import cProfile
import cadquery as cq
from cadquery import selectors
import cq_warehouse
from pydantic import BaseModel, PrivateAttr

import csv
import importlib.resources as pkg_resources

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
    if not is_safe(measure):
        raise ValueError(f"The provided measurement {measure} is not safe to eval()")
    return eval(measure.replace(" ", "+")) * IN


def metric_str_to_float(measure: str) -> float:
    if not is_safe(measure):
        raise ValueError(f"The provided measurement {measure} is not safe to eval()")
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

# ISO Standard Metric Hex Nut and Bolt Head sizes
metric_hex_parameters = evaluate_parameter_dict(
    read_fastener_parameters_from_csv("metric_hex_parameters.csv"), units="metric"
)
# Standard Imperial Hex Nut and Bolt Head sizes
imperial_hex_parameters = evaluate_parameter_dict(
    read_fastener_parameters_from_csv("imperial_hex_parameters.csv"), units="imperial"
)


def decode_imperial_size(size: str) -> Tuple[float, float]:
    """ Extract the major diameter and pitch from an imperial size """

    sizes = size.split("-")
    if size[0] == "#":
        major_diameter = imperial_numbered_sizes[sizes[0]]
    else:
        major_diameter = imperial_str_to_float(sizes[0])
    pitch = float(sizes[1]) / IN
    return (major_diameter, pitch)


# Size,Diameter,Pitch,Knurl & Cup Point Diameter,Flat Point Diameter,Oval Point Radius,
# Half Dog Point Diameter,Half Dog Point Length,Hexagon Socket Size,Key Engagement
socket_set_screws = {
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
# Size,Shoulder Diameter,Head Diameter,Head Height,Hexagon Socket Size,Thread Diameter,
# Thread Pitch,Thread Length
socket_head_shoulder_screw = {
    "M6": [5.990, 10.00, 4.500, 3.00, 5.00, 0.8, 9.750],
    "M8": [7.987, 13.00, 5.500, 4.00, 6.00, 1.0, 11.25],
    "M10": [9.987, 16.00, 7.00, 5.00, 8.00, 1.25, 13.25],
    "M12": [11.984, 18.00, 8.00, 6.00, 10.0, 1.50, 16.40],
    "M16": [15.984, 24.00, 11.00, 8.00, 12.0, 1.75, 18.40],
    "M20": [19.980, 30.00, 14.00, 10.00, 16.0, 2.00, 22.40],
}

# Size,Pitch,Head Diameter,Head Height,Hexagon Socket Size,Key Engagement
flat_head_socket_cap_screw = {
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
button_head_socket_cap_screw = {
    "M3-0.5": [0.5, 0.5, 5.700, 1.65, 2.00, 1.04],
    "M4-0.7": [0.7, 0.7, 7.60, 2.20, 2.50, 1.30],
    "M5-0.8": [0.8, 0.8, 9.50, 2.75, 3.00, 1.56],
    "M6-1.0": [1.0, 1.0, 10.50, 3.30, 4.00, 2.08],
    "M8-1.25": [1.25, 1.25, 14.00, 4.40, 5.00, 2.60],
    "M10-1.50": [1.50, 1.50, 17.50, 5.50, 6.00, 3.12],
    "M12-1.75": [1.75, 1.75, 21.00, 6.60, 8.00, 4.16],
}


class Thread(BaseModel):
    """ Common methods for the creation of thread objects """

    major_diameter: float
    pitch: float
    length: float
    external: Optional[bool] = True
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
        """ The center of the thread radius or pitch radius """
        return (
            self.min_radius - self.h_parameter / 4
            if self.external
            else self.min_radius + 3 * self.h_parameter / 4
        )

    @property
    def internal_thread_socket_radius(self) -> float:
        """ The radius of an internal thread object used to size an appropriate hole """
        return (
            None
            if self.external
            else self.major_diameter / 2 + 3 * self.h_parameter / 4
        )

    @property
    # @cached_property
    def cq_object(self):
        """ A cadquery Solid thread as defined by class attributes """
        return self._cq_object
        # return self.make_iso_thread()

    def __init__(self, **data):
        """ Validate inputs and create the chain assembly object """
        # Use the BaseModel initializer to validate the attributes
        super().__init__(**data)
        # Create the thread
        self._cq_object = self.make_iso_thread()

    def internal_iso_thread_profile(self) -> cq.Workplane:
        """
        Generae a 2D profile of a single internal thread based on this diagram:
        https://en.wikipedia.org/wiki/ISO_metric_screw_thread#/media/File:ISO_and_UTS_Thread_Dimensions.svg
        """

        thread_profile = (
            cq.Workplane("XZ")
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
            .lineTo(0, self.pitch)
            .close()
        )
        return thread_profile

    def external_iso_thread_profile(self) -> cq.Workplane:
        """
        Generae a 2D profile of a single external thread based on this diagram:
        https://en.wikipedia.org/wiki/ISO_metric_screw_thread#/media/File:ISO_and_UTS_Thread_Dimensions.svg
        """

        thread_profile = (
            cq.Workplane("XZ")
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
            .lineTo(self.thread_radius, self.pitch)
            .lineTo(0, self.pitch)
            .close()
        )
        return thread_profile

    def make_iso_thread(self) -> cq.Solid:
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
        # Step 1 - Create the 2D thread profile
        if self.external:
            thread_profile = self.external_iso_thread_profile()
        else:
            thread_profile = self.internal_iso_thread_profile()

        # Step 2: Sweep the profile along the threadPath and extract the wires
        thread_path = cq.Wire.makeHelix(
            pitch=self.pitch, height=self.pitch, radius=self.thread_radius
        )
        thread_wire = (
            cq.Workplane("XY")
            .add(
                thread_profile.sweep(
                    path=cq.Workplane(thread_path), isFrenet=True
                ).translate((0, 0, -self.pitch))
            )
            .section()
            .wires()
            .vals()
        )
        if self.external:
            outer_wire = thread_wire[1]
            inner_wires = []
        else:
            outer_wire = cq.Wire.makeCircle(
                radius=self.major_diameter / 2 + 3 * self.h_parameter / 4,
                center=cq.Vector(0, 0, 0),
                normal=cq.Vector(0, 0, 1),
            )
            inner_wires = [thread_wire[0]]

        # Step 3: Create thread by extruding thread wire
        thread = cq.Solid.extrudeLinearWithRotation(
            outerWire=outer_wire,
            innerWires=inner_wires,
            vecCenter=cq.Vector(0, 0, 0),
            vecNormal=cq.Vector(0, 0, self.length),
            angleDegrees=360 * (self.length / self.pitch),
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
            shank = shank.union(self.cq_object.mirror().translate((0, 0, -body_length)))
        else:
            shank = self.cq_object
        return shank


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
        if self.size in metric_hex_parameters.keys():
            nut_data = metric_hex_parameters[self.size]
            self.width = nut_data["Width"]
            self.thickness = nut_data["Height"]
            size_parts = self.size.split("-")
            self.thread_diameter = float(size_parts[0][1:])
            self.thread_pitch = float(size_parts[1])
        elif self.size in imperial_hex_parameters.keys():
            nut_data = imperial_hex_parameters[self.size]
            self.width = nut_data["Width"]
            self.thickness = nut_data["Height"]
            (self.thread_diameter, self.thread_pitch) = decode_imperial_size(self.size)
        else:
            raise ValueError(
                f"Invalid nut size {self.size} - must be one of:"
                f"{list(metric_hex_parameters.keys())+list(imperial_hex_parameters.keys())}"
            )

    def make_nut(self) -> cq.Solid:
        """ Create an arbitrary sized hex or square nut """

        thread = Thread(
            major_diameter=self.thread_diameter,
            pitch=self.thread_pitch,
            length=self.thickness,
            external=False,
        )
        if self.shape == "hex":
            # Distance across the tips of the hex
            hex_diameter = self.width / cos(pi / 6)
            # Chamfer between the hex tips and flats
            chamfer_size = (hex_diameter - self.width) / 2
            # The nutBody define the chamfered edges of the nut
            nut_body = (
                cq.Workplane("XY")
                .circle(hex_diameter / 2)  # Create a circle that contains the hexagon
                .circle(
                    thread.internal_thread_socket_radius
                )  # .. with a hole in the center
                .extrude(self.thickness)
                .edges(selectors.RadiusNthSelector(1))
                .chamfer(chamfer_size / 2, chamfer_size)  # Chamfer the outside edges
                .intersect(
                    cq.Workplane("XY").polygon(6, hex_diameter).extrude(self.thickness)
                )
            )
        else:
            nut_body = (
                cq.Workplane("XY")
                .rect(self.width, self.width)
                .circle(thread.internal_thread_socket_radius)
                .extrude(self.thickness)
            )
        nut = nut_body.union(thread.cq_object, glue=True).val()
        return nut


class SocketHeadCapScrew:
    """ Create a sock head cap screw as described either by a size sting or a set of parameters """

    # Socket Head Cap Screw parameters
    metric_socket_head_cap_screw_parameters = evaluate_parameter_dict(
        read_fastener_parameters_from_csv(
            "metric_socket_head_cap_screw_parameters.csv"
        ),
        units="metric",
    )
    imperial_socket_head_cap_screw_parameters = evaluate_parameter_dict(
        read_fastener_parameters_from_csv(
            "imperial_socket_head_cap_screw_parameters.csv"
        ),
        units="imperial",
    )

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
        """ Create an arbitrary sized socket head cap screw """
        self.length = length
        if size is not None:
            self.size = size
            self._extract_screw_parameters()
        else:
            self.thread_diameter = thread_diameter
            self.thread_pitch = thread_pitch
            self.head_diameter = head_diameter
            self.head_height = head_height
            self.socket_size = socket_size
            self.socket_depth = socket_depth
            self.max_thread_length = thread_length

        if thread_length is None:
            self.body_length = max(0, length - self.max_thread_length)
            self.thread_length = self.length - self.body_length
        elif thread_length > length:
            raise ValueError(
                f"thread length ({thread_length}) must be less than of equal to length ({length})"
            )
        else:
            self.thread_length = thread_length
            self.body_length = self.length - self.thread_length

        self.cq_object = (
            self.make_socket_cap_screw_head()
            .union(
                Thread(
                    major_diameter=self.thread_diameter,
                    pitch=self.thread_pitch,
                    length=self.thread_length,
                ).make_shank(self.body_length)
            )
            .val()
        )

    def _extract_screw_parameters(self):
        """ Parse the screw size string into width, major_diameter, pitch and thickness """
        size_parts = self.size.split("-")
        if (
            self.size
            in SocketHeadCapScrew.metric_socket_head_cap_screw_parameters.keys()
        ):
            nut_data = SocketHeadCapScrew.metric_socket_head_cap_screw_parameters[
                self.size
            ]
            self.head_diameter = nut_data["Head_Diameter"]
            self.head_height = nut_data["Head_Height"]
            self.socket_size = nut_data["Socket_Size"]
            self.socket_depth = nut_data["Socket_Depth"]
            self.max_thread_length = nut_data["Max_Thread_Length"]
            self.thread_diameter = float(size_parts[0][1:])
            self.thread_pitch = float(size_parts[1])
        elif (
            self.size
            in SocketHeadCapScrew.imperial_socket_head_cap_screw_parameters.keys()
        ):
            nut_data = SocketHeadCapScrew.imperial_socket_head_cap_screw_parameters[
                self.size
            ]
            self.head_diameter = nut_data["Head_Diameter"]
            self.head_height = nut_data["Head_Height"]
            self.socket_size = nut_data["Socket_Size"]
            self.socket_depth = nut_data["Socket_Depth"]
            self.max_thread_length = nut_data["Max_Thread_Length"]
            (self.thread_diameter, self.thread_pitch) = decode_imperial_size(self.size)
        else:
            raise ValueError(
                "Invalid socket head cap screw size, must be one of:"
                f"{list(SocketHeadCapScrew.metric_socket_head_cap_screw_parameters.keys())}"
                f"{list(SocketHeadCapScrew.imperial_socket_head_cap_screw_parameters.keys())}"
            )

    def make_socket_cap_screw_head(self):
        """ Construct an arbitrary size socket head cap screw """

        screw_head = (
            cq.Workplane("XY")
            .circle(self.head_diameter / 2)
            .extrude(self.head_height - self.socket_depth)
            .faces(">Z")
            .workplane()
            .circle(self.head_diameter / 2)
            .polygon(6, self.socket_size / cos(pi / 6))
            .extrude(self.socket_depth)
            .faces(">Z")
            .edges(cq.selectors.RadiusNthSelector(0))
            .fillet(self.head_diameter / 20)
            .edges("<Z")
            .fillet(self.head_diameter / 40)
        )
        return screw_head


nut = Nut("M4-0.7")
# nut = Nut("M4-0.7", shape="square")
print(nut.cq_object.isValid())
cq.exporters.export(nut.cq_object, "nut.step")

# screw = SocketHeadCapScrew("M4-0.7", length=20 * MM)
screw = SocketHeadCapScrew("#10-32", length=2 * IN)
print(screw.cq_object.isValid())
cq.exporters.export(screw.cq_object, "screw.step")

# thread = Thread.make_iso_thread(4, 0.7, 5, False)
# thread = ExternalThread(major_diameter=4, thread_pitch=0.7, thread_length=20 * MM)

if "show_object" in locals():
    # show_object(thread, name="thread")
    show_object(nut.cq_object, name="nut")
    # show_object(screw.cq_object, name="screw")
    # show_object(internal, name="internal")
    # show_object(external, name="external")
    # show_object(threadGuide,name="threadGuide")
