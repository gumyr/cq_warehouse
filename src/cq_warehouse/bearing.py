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

    def method_exists(self, method: str) -> bool:
        """Did the derived class create this method"""
        return hasattr(self.__class__, method) and callable(
            getattr(self.__class__, method)
        )

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

    # @abstractmethod
    # def cap(self) -> Workplane:
    #     """Each derived class must provide a sealing cap"""
    #     return NotImplementedError

    @abstractmethod
    def countersink_profile(self) -> Workplane:
        """Each derived class must provide the profile of a countersink cutter"""
        return NotImplementedError

    @property
    @abstractmethod
    def roller_diameter(self):
        """Each derived class must provide the roller diameter"""
        return NotImplementedError

    def default_roller_diameter(self):
        """Default roller diameter"""
        (d1, D1) = (self.bearing_dict[p] for p in ["d1", "D1"])
        return 0.625 * (D1 - d1)

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
    ):
        """Parse Bearing input parameters"""
        self.size = size.strip()
        if bearing_type not in self.types():
            raise ValueError(f"{bearing_type} invalid, must be one of {self.types()}")
        self.bearing_type = bearing_type
        self.capped = self.method_exists("cap")
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
        self.race_center_radius = (D1 + d1) / 4
        self.roller_count = int(
            1.8 * pi * self.race_center_radius / self.roller_diameter
        )
        self._cq_object = self.make_bearing()

    def make_bearing(self) -> Assembly:
        """Create bearing from the shapes defined in the derived class"""

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

            if self.method_exists("cage"):
                bearing.add(self.cage())

        return bearing

    def default_inner_race_section(self):
        """Create 2D profile inner race"""
        (d1, d, B, r12) = (self.bearing_dict[p] for p in ["d1", "d", "B", "r12"])

        section = (
            Workplane("XZ")
            .sketch()
            .push([((d1 + d) / 4, B / 2)])
            .rect((d1 - d) / 2, B)
            .reset()
            .vertices()
            .fillet(r12)
            .finalize()
        )
        return section

    def default_outer_race_section(self) -> Workplane:
        """Create 2D profile inner race"""
        (D1, D, B, r12) = (self.bearing_dict[p] for p in ["D1", "D", "B", "r12"])

        section = (
            Workplane("XZ")
            .sketch()
            .push([((D1 + D) / 4, B / 2)])
            .rect((D1 - D) / 2, B)
            .reset()
            .vertices()
            .fillet(r12)
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


class SingleRowDeepGrooveBallBearing(Bearing):

    bearing_data = read_fastener_parameters_from_csv(
        "single_row_deep_groove_ball_bearing_parameters.csv"
    )

    @property
    def roller_diameter(self):
        return self.default_roller_diameter()

    outer_race_section = Bearing.default_outer_race_section
    inner_race_section = Bearing.default_inner_race_section
    roller = Bearing.default_roller
    countersink_profile = Bearing.default_countersink_profile


class SingleRowCappedDeepGrooveBallBearing(Bearing):

    bearing_data = read_fastener_parameters_from_csv(
        "single_row_capped_deep_groove_ball_bearing_parameters.csv"
    )

    @property
    def roller_diameter(self):
        return self.default_roller_diameter()

    outer_race_section = Bearing.default_outer_race_section
    inner_race_section = Bearing.default_inner_race_section
    roller = Bearing.default_roller
    cap = Bearing.default_cap
    countersink_profile = Bearing.default_countersink_profile


class SingleRowAngularContactBallBearing(Bearing):
    bearing_data = read_fastener_parameters_from_csv(
        "single_row_angular_contact_ball_bearing_parameters.csv"
    )

    @property
    def roller_diameter(self):
        """Default roller diameter"""
        (d, d2, D) = (self.bearing_dict[p] for p in ["d", "d2", "D"])
        D2 = D - (d2 - d)
        return 0.4 * (D2 - d2)

    def inner_race_section(self):
        (d, d1, d2, r12, B) = (
            self.bearing_dict[p] for p in ["d", "d1", "d2", "r12", "B"]
        )

        inner_race = (
            Workplane("XZ")
            .moveTo(d2 / 2 - r12, 0)
            .radiusArc((d2 / 2, r12), -r12)
            .spline([(d1 / 2, B - r12)], tangents=[(0, 1), (0, 1)], includeCurrent=True)
            .radiusArc((d1 / 2 - r12, B), -r12)
            .hLineTo(d / 2 + r12)
            .radiusArc((d / 2, B - r12), -r12)
            .vLineTo(r12)
            .radiusArc((d / 2 + r12, 0), -r12)
            .close()
        )
        return inner_race

    def outer_race_section(self):
        (d, D, D1, d2, r12, r34, B) = (
            self.bearing_dict[p] for p in ["d", "D", "D1", "d2", "r12", "r34", "B"]
        )
        D2 = D - (d2 - d)
        outer_race = (
            Workplane("XZ")
            .moveTo(D / 2 - r12, 0)
            .radiusArc((D / 2, r12), -r12)
            .vLineTo(B - r34)
            .radiusArc((D / 2 - r34, B), -r34)
            .hLineTo(D2 / 2 + r12)
            .radiusArc((D2 / 2, B - r12), -r12)
            .spline([(D1 / 2, r12)], tangents=[(0, -1), (0, -1)], includeCurrent=True)
            .radiusArc((D1 / 2 + r12, 0), -r12)
            .close()
        )
        return outer_race

    def cap(self) -> Workplane:
        (d, D, d2, B) = (self.bearing_dict[p] for p in ["d", "D", "d2", "B"])
        D2 = D - (d2 - d)
        return (
            Workplane("XY", origin=(0, 0, B / 20))
            .circle(D2 / 2)
            .circle(d2 / 2)
            .extrude(B / 20)
        )

    roller = Bearing.default_roller

    countersink_profile = Bearing.default_countersink_profile


angular = SingleRowAngularContactBallBearing(size="M10-30-9", bearing_type="SKT")
bearing = SingleRowDeepGrooveBallBearing(size="M8-22-7", bearing_type="SKT")
capped = SingleRowCappedDeepGrooveBallBearing(size="M8-22-7", bearing_type="SKT")
print(SingleRowAngularContactBallBearing.types())
print(Bearing.select_by_size("M8-22-7"))
print(SingleRowCappedDeepGrooveBallBearing.sizes("SKT"))

if "show_object" in locals():
    show_object(angular.cq_object, name="angular")
    show_object(bearing.cq_object, name="bearing")
    show_object(capped.cq_object, name="capped")
