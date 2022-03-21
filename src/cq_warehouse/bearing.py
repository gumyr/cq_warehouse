"""

Parametric Bearings

name: bearing.py
by:   Gumyr
date: March 20th 2022

desc: This python/cadquery code is a parameterized bearing generator.

TODO:

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
from abc import ABC, abstractmethod
from math import pi
from typing import Literal
from cadquery import Vector, Assembly, Workplane, Location, Solid, Color
from cq_warehouse.fastener import (
    evaluate_parameter_dict,
    read_fastener_parameters_from_csv,
    isolate_fastener_type,
    lookup_drill_diameters,
    select_by_size_fn,
)

MM = 1


class Bearing(ABC):
    """Parametric Bearing

    Base Class used to create standard bearings

    Args:
        size (str): bearing size, e.g. "M8-22-7"
        bearing_type (str): type identifier - e.g. "SKT"
        capped (bool, optional): create sealed bearings. Defaults to True.

    Raises:
        ValueError: bearing_type is invalid
        ValueError: size is invalid

    """

    # Read clearance and tap hole dimesions tables
    # Close, Medium, Loose
    clearance_hole_drill_sizes = read_fastener_parameters_from_csv(
        "clearance_hole_sizes.csv"
    )
    clearance_hole_data = lookup_drill_diameters(clearance_hole_drill_sizes)

    @property
    def clearance_hole_diameters(self):
        """A dictionary of drill diameters for clearance holes"""
        try:
            return self.clearance_hole_data[self.size.split("-")[0]]
        except KeyError as e:
            raise ValueError(
                f"No clearance hole data for size {self.bore_diameter}"
            ) from e

    @property
    def bore_diameter(self) -> float:
        return self.bearing_dict["d"]

    @property
    def outer_diameter(self) -> float:
        return self.bearing_dict["D"]

    @property
    def width(self) -> float:
        return self.bearing_dict["B"]

    @property
    def cq_object(self):
        """A cadquery Assembly bearing as defined by class attributes"""
        return self._cq_object

    @classmethod
    def select_by_size(cls, size: str) -> dict:
        """Return a dictionary of list of fastener types of this size"""
        return select_by_size_fn(cls, size)

    @property
    @classmethod
    @abstractmethod
    def bearing_data(cls):
        """Each derived class must provide a bearing_data dictionary"""
        return NotImplementedError

    @abstractmethod
    def inner_race_section(self) -> Workplane:
        """Each derived class must provide the section of the inner race"""
        return NotImplementedError

    @abstractmethod
    def outer_race_section(self) -> Workplane:
        """Each derived class must provide the section of the outer race"""
        return NotImplementedError

    @abstractmethod
    def roller(self) -> Solid:
        """Each derived class must provide the roller object - a sphere, cylinder or cone"""
        return NotImplementedError

    @abstractmethod
    def cap(self) -> Workplane:
        """Each derived class must provide a sealing cap"""
        return NotImplementedError

    @abstractmethod
    def countersink_profile(self) -> Workplane:
        """Each derived class must provide the profile of a countersink cutter"""
        return NotImplementedError

    @property
    def info(self):
        """Return identifying information"""
        return f"{self.bearing_class}({self.bearing_type}): {self.size}"

    @property
    def bearing_class(self):
        """Which derived class created this bearing"""
        return type(self).__name__

    def length_offset(self):
        """Screw only parameter"""
        return 0

    @classmethod
    def types(cls) -> list[str]:
        """Return a set of the bearing types"""
        return set(p.split(":")[0] for p in list(cls.bearing_data.values())[0].keys())

    @classmethod
    def sizes(cls, bearing_type: str) -> list[str]:
        """Return a list of the bearing sizes for the given type"""
        return list(isolate_fastener_type(bearing_type, cls.bearing_data).keys())

    def __init__(
        self,
        size: str,
        bearing_type: str,
        capped: bool = True,
    ):
        """Parse Bearing input parameters"""
        self.size = size.strip()
        if bearing_type not in self.types():
            raise ValueError(f"{bearing_type} invalid, must be one of {self.types()}")
        self.bearing_type = bearing_type
        self.capped = capped
        self.is_metric = self.size[0] == "M"

        try:
            self.bearing_dict = evaluate_parameter_dict(
                isolate_fastener_type(self.bearing_type, self.bearing_data)[self.size],
                is_metric=self.is_metric,
            )
        except KeyError as e:
            raise ValueError(
                f"{size} invalid, must be one of {self.sizes(self.bearing_type)}"
            ) from e

        (d1, D1) = (self.bearing_dict[p] for p in ["d1", "D1"])
        self.roller_diameter = 0.625 * (D1 - d1)
        self.race_center_radius = (D1 + d1) / 4
        self.roller_count = int(
            1.8 * pi * self.race_center_radius / self.roller_diameter
        )
        self._cq_object = self.make_bearing()

    def make_bearing(self) -> Assembly:
        """Create bearing from the shapes defined in the derived class"""

        def method_exists(method: str) -> bool:
            """Did the derived class create this method"""
            return hasattr(self.__class__, method) and callable(
                getattr(self.__class__, method)
            )

        outer_race = (
            Workplane("XZ").add(self.outer_race_section().val()).toPending().revolve()
        )
        inner_race = (
            Workplane("XZ").add(self.inner_race_section().val()).toPending().revolve()
        )

        bearing = Assembly(outer_race)
        bearing.add(inner_race)
        if self.capped:
            bearing.add(self.cap(), color=Color("darkslategray"))
            bearing.add(
                self.cap().mirror("XY"),
                loc=Location(Vector(0, 0, self.bearing_dict["B"])),
                color=Color("darkslategray"),
            )
        else:
            roller_locations = (
                Workplane("XY")
                .polarArray(
                    self.race_center_radius,
                    0,
                    360,
                    self.roller_count,
                )
                .vals()
            )
            for roller_location in roller_locations:
                bearing.add(
                    self.roller(),
                    loc=roller_location
                    * Location(Vector(0, 0, self.bearing_dict["B"] / 2)),
                )

            if method_exists("cage"):
                bearing.add(self.cage())

        return bearing

    def default_inner_race_section(self):
        """Create 2D profile inner race"""
        (d1, d, B, r) = (self.bearing_dict[p] for p in ["d1", "d", "B", "r"])

        section = (
            Workplane("XZ")
            .sketch()
            .push([((d1 + d) / 4, B / 2)])
            .rect((d1 - d) / 2, B)
            .reset()
            .vertices()
            .fillet(r)
            .finalize()
        )
        return section

    def default_outer_race_section(self) -> Workplane:
        """Create 2D profile inner race"""
        (D1, D, B, r) = (self.bearing_dict[p] for p in ["D1", "D", "B", "r"])

        section = (
            Workplane("XZ")
            .sketch()
            .push([((D1 + D) / 4, B / 2)])
            .rect((D1 - D) / 2, B)
            .reset()
            .vertices()
            .fillet(r)
            .finalize()
        )
        return section

    def default_countersink_profile(self, interference: float = 0) -> Workplane:
        (D, B) = (self.bearing_dict[p] for p in ["D", "B"])
        return Workplane("XZ").rect(D / 2 - interference, B, centered=False)

    def default_roller(self) -> Solid:
        return Solid.makeSphere(self.roller_diameter / 2, angleDegrees1=-90)

    def default_cap(self) -> Workplane:
        (D1, d1, B) = (self.bearing_dict[p] for p in ["D1", "d1", "B"])
        return (
            Workplane("XY", origin=(0, 0, B / 20))
            .circle(D1 / 2)
            .circle(d1 / 2)
            .extrude(B / 20)
        )


class DeepGrooveBallBearing(Bearing):

    bearing_data = read_fastener_parameters_from_csv(
        "deep_groove_ball_bearing_parameters.csv"
    )

    outer_race_section = Bearing.default_outer_race_section
    inner_race_section = Bearing.default_inner_race_section
    roller = Bearing.default_roller
    cap = Bearing.default_cap
    countersink_profile = Bearing.default_countersink_profile
