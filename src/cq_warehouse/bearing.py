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
from warnings import warn
from abc import ABC, abstractmethod
from math import pi, radians, degrees, asin, sin
from cadquery import (
    Vector,
    Assembly,
    Workplane,
    Location,
    Solid,
    Color,
    Sketch,
    Compound,
)
from cq_warehouse.fastener import (
    evaluate_parameter_dict,
    read_fastener_parameters_from_csv,
    isolate_fastener_type,
    lookup_drill_diameters,
    select_by_size_fn,
)

MM = 1


class Bearing(ABC, Compound):
    """Parametric Bearing

    Base Class used to create standard bearings

    Args:
        size (str): bearing size, e.g. "M8-22-7"
        bearing_type (str): type identifier - e.g. "SKT"

    Raises:
        ValueError: bearing_type is invalid
        ValueError: size is invalid

    """

    def method_exists(self, method: str) -> bool:
        """Did the derived class create this method"""
        return hasattr(self.__class__, method) and callable(
            getattr(self.__class__, method)
        )

    # Read clearance and tap hole dimensions tables
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
        """Diameter of central hole"""
        return self.bearing_dict["d"]

    @property
    def outer_diameter(self) -> float:
        """Bearing outer diameter"""
        return self.bearing_dict["D"]

    @property
    def thickness(self) -> float:
        """Bearing thickness"""
        return (
            self.bearing_dict["T"]
            if self.bearing_class == "SingleRowTaperedRollerBearing"
            else self.bearing_dict["B"]
        )

    @property
    def cq_object(self):
        """A cadquery Assembly bearing as defined by class attributes"""
        warn("cq_object will be deprecated.", DeprecationWarning, stacklevel=2)
        return Compound(self.wrapped)

    @classmethod
    def select_by_size(cls, size: str) -> dict:
        """Return a dictionary of list of fastener types of this size"""
        return select_by_size_fn(cls, size)

    @property
    @classmethod
    @abstractmethod
    def bearing_data(cls):
        """Each derived class must provide a bearing_data dictionary"""
        return NotImplementedError  # pragma: no cover

    @abstractmethod
    def inner_race_section(self) -> Workplane:
        """Each derived class must provide the section of the inner race"""
        return NotImplementedError  # pragma: no cover

    @abstractmethod
    def outer_race_section(self) -> Workplane:
        """Each derived class must provide the section of the outer race"""
        return NotImplementedError  # pragma: no cover

    @abstractmethod
    def roller(self) -> Solid:
        """Each derived class must provide the roller object - a sphere, cylinder or cone"""
        return NotImplementedError  # pragma: no cover

    @abstractmethod
    def countersink_profile(self) -> Workplane:
        """Each derived class must provide the profile of a countersink cutter"""
        return NotImplementedError  # pragma: no cover

    @property
    @abstractmethod
    def roller_diameter(self):
        """Each derived class must provide the roller diameter"""
        return NotImplementedError  # pragma: no cover

    @property
    @abstractmethod
    def race_center_radius(self):
        return NotImplementedError  # pragma: no cover

    def default_race_center_radius(self):
        """Default roller race center radius"""
        (d1, D1) = (self.bearing_dict[p] for p in ["d1", "D1"])
        return (D1 + d1) / 4

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

        self.roller_count = int(
            1.8 * pi * self.race_center_radius / self.roller_diameter
        )
        cq_object = self.make_bearing()
        super().__init__(cq_object.wrapped)

    def make_bearing(self) -> Compound:
        """Create bearing from the shapes defined in the derived class"""

        outer_race = (
            Workplane("XZ").add(self.outer_race_section().val()).toPending().revolve()
        )
        inner_race = (
            Workplane("XZ").add(self.inner_race_section().val()).toPending().revolve()
        )

        bearing = outer_race.val()
        bearing = bearing.fuse(inner_race.val())
        if self.capped:
            bearing = bearing.fuse(self.cap().val())
            bearing = bearing.fuse(
                self.cap().mirror("XY").val().translate((0, 0, self.bearing_dict["B"])),
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
                bearing = bearing.fuse(
                    self.roller().located(
                        roller_location
                        * Location(Vector(0, 0, self.bearing_dict["B"] / 2)),
                    )
                )

            if self.method_exists("cage"):
                bearing = bearing.fuse(self.cage())

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
    """Single Row Deep Groove Ball Bearing

    Deep groove ball bearings are particularly
    versatile. They are simple in design, non-
    separable, suitable for high and very high
    speeds and are robust in operation, requiring
    little maintenance. Because deep groove ball
    bearings are the most widely used bearing
    type, they are available in many
    designs, variants and sizes."""

    bearing_data = read_fastener_parameters_from_csv(
        "single_row_deep_groove_ball_bearing_parameters.csv"
    )

    @property
    def roller_diameter(self):
        return self.default_roller_diameter()

    @property
    def race_center_radius(self):
        return self.default_race_center_radius()

    outer_race_section = Bearing.default_outer_race_section
    inner_race_section = Bearing.default_inner_race_section
    roller = Bearing.default_roller
    countersink_profile = Bearing.default_countersink_profile


class SingleRowCappedDeepGrooveBallBearing(Bearing):
    """Single Row Capped Deep Groove Ball Bearings

    Deep groove ball bearings capped with a seal or
    shield on both sides."""

    bearing_data = read_fastener_parameters_from_csv(
        "single_row_capped_deep_groove_ball_bearing_parameters.csv"
    )

    @property
    def roller_diameter(self):
        return self.default_roller_diameter()

    @property
    def race_center_radius(self):
        return self.default_race_center_radius()

    outer_race_section = Bearing.default_outer_race_section
    inner_race_section = Bearing.default_inner_race_section
    roller = Bearing.default_roller
    cap = Bearing.default_cap
    countersink_profile = Bearing.default_countersink_profile


class SingleRowAngularContactBallBearing(Bearing):
    """Single Row Angular Contact Ball Bearing

    Angular contact ball bearings have raceways
    in the inner and outer rings that are displaced
    relative to each other in the direction of the
    bearing axis. This means that they are
    designed to accommodate combined loads, i.e.
    simultaneously acting radial and axial loads.
    The axial load carrying capacity of angular
    contact ball bearings increases with increasing
    contact angle. The contact angle is defined
    as the angle between the line joining the points
    of contact of the ball and the raceways in the
    radial plane, along which the load is transmit-
    ted from one raceway to another, and a line
    perpendicular to the bearing axis."""

    bearing_data = read_fastener_parameters_from_csv(
        "single_row_angular_contact_ball_bearing_parameters.csv"
    )

    @property
    def roller_diameter(self):
        """Default roller diameter"""
        (d, d2, D) = (self.bearing_dict[p] for p in ["d", "d2", "D"])
        D2 = D - (d2 - d)
        return 0.4 * (D2 - d2)

    @property
    def race_center_radius(self):
        return self.default_race_center_radius()

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


class SingleRowCylindricalRollerBearing(Bearing):
    """Single Row Cylindrical Roller Bearings

    Suitable for very heavy radial loads at moderate speeds,
    roller bearings use cylindrical rollers instead of
    spherical ball bearings."""

    bearing_data = read_fastener_parameters_from_csv(
        "single_row_cylindrical_roller_bearing_parameters.csv"
    )

    @property
    def roller_diameter(self):
        return self.default_roller_diameter()

    @property
    def race_center_radius(self):
        return self.default_race_center_radius()

    outer_race_section = Bearing.default_outer_race_section
    inner_race_section = Bearing.default_inner_race_section

    def roller(self) -> Solid:
        roller_length = 0.7 * self.bearing_dict["B"]
        return Solid.makeCylinder(
            self.roller_diameter / 2,
            roller_length,
            pnt=Vector(0, 0, -roller_length / 2),
        )

    countersink_profile = Bearing.default_countersink_profile


class SingleRowTaperedRollerBearing(Bearing):
    """Tapered Roller Bearing

    Tapered roller bearings have tapered inner
    and outer ring raceways and tapered rollers.
    They are designed to accommodate combined
    loads, i.e. simultaneously acting radial and
    axial loads. The projection lines of the race-
    ways meet at a common point on the bearing
    axis to provide true rolling and low
    friction. The axial load carrying capacity of
    tapered roller bearings increases with
    increasing contact angle.  A single row tapered
    roller bearing is typically adjusted against a
    second tapered roller bearing.

    Single row tapered roller bearings are sep-
    ar able, i.e. the inner ring with roller
    and cage assembly (cone) can be mounted
    separately from the outer ring (cup)."""

    bearing_data = read_fastener_parameters_from_csv(
        "single_row_tapered_roller_bearing_parameters.csv"
    )

    @property
    def roller_diameter(self) -> float:
        """Diameter of the larger end of the roller - increased diameter
        allows for room for the cage between the rollers"""
        roller = Workplane(self.roller())
        return roller.faces(">Z").edges().val().radius() * 2.5

    @property
    def cone_angle(self) -> float:
        """Angle of the inner cone raceway"""
        (a, d1, Db) = (self.bearing_dict[p] for p in ["a", "d1", "Dbmin"])
        cone_length = (Db / 2) / asin(radians(a))
        return degrees(asin((d1 / 2) / cone_length))

    @property
    def roller_axis_angle(self) -> float:
        """Angle of the central axis of the rollers"""
        return (self.bearing_dict["a"] + self.cone_angle) / 2

    @property
    def roller_length(self) -> float:
        """Roller length"""
        return 0.7 * self.bearing_dict["B"]

    @property
    def cone_length(self) -> float:
        """Distance to intersection of projection lines"""
        (a, Db) = (self.bearing_dict[p] for p in ["a", "Dbmin"])
        return (Db / 2) / asin(radians(a))

    @property
    def race_center_radius(self) -> float:
        """Radius of cone to place the rollers"""
        return (self.cone_length - self.roller_length / 2) * sin(
            radians(self.roller_axis_angle)
        )

    def outer_race_section(self):
        """Outer Cup"""
        (D, C, Db, a, r34) = (
            self.bearing_dict[p] for p in ["D", "C", "Dbmin", "a", "r34"]
        )
        cup_sketch = (
            Sketch()
            .push([(C / 2, D / 2 - (D - Db) / 4)])
            .trapezoid((D - Db) / 2, C, a + 90, 90, 90)
            .reset()
            .vertices()
            .fillet(r34)
        )
        cup = Workplane(
            cup_sketch._faces.Faces()[0].rotate(Vector(), Vector(0, 1, 0), -90)
        ).wires()

        return cup

    def inner_race_section(self):
        """Central Cone"""
        (d, B, da, r12, T) = (
            self.bearing_dict[p] for p in ["d", "B", "da", "r12", "T"]
        )
        cone_sketch = (
            Sketch()
            .push([(T - B / 2, d / 2 + (da - d) / 2)])
            .trapezoid((da - d) / 2, B, 90 + self.cone_angle, 90, -90)
            .reset()
            .vertices()
            .fillet(r12)
        )
        cone = Workplane(
            cone_sketch._faces.Faces()[0].rotate(Vector(), Vector(0, 1, 0), -90)
        ).wires()
        return cone

    def roller(self) -> Solid:
        """Tapered Roller"""
        roller_cone_angle = self.bearing_dict["a"] - self.cone_angle
        cone_radii = [
            1.2 * (self.cone_length - l) * sin(radians(roller_cone_angle) / 2)
            for l in [0, self.roller_length]
        ]
        return Solid.makeCone(
            cone_radii[1],
            cone_radii[0],
            self.roller_length,
            pnt=Vector(0, 0, -self.roller_length / 2),
        ).rotate(Vector(), Vector(1, 0, 0), -self.roller_axis_angle)

    countersink_profile = Bearing.default_countersink_profile

    def cage(self) -> Compound:
        """Cage holding the rollers together with the cone"""
        thickness = 0.9 * self.bearing_dict["T"]
        cage_radii = [
            (self.cone_length - l) * sin(radians(self.roller_axis_angle)) + 0.5 * MM
            for l in [0, thickness]
        ]
        cage_face = Solid.makeCone(cage_radii[1], cage_radii[0], thickness,).cut(
            Solid.makeCone(
                cage_radii[1] - 1 * MM,
                cage_radii[0] - 1 * MM,
                thickness,
            )
        )
        return cage_face
