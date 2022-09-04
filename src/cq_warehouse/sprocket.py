"""

Parametric Sprockets

name: sprocket.py
by:   Gumyr
date: July 9th 2021

desc:

    This python/cadquery code is a parameterized sprocket generator.
    Given a chain pitch, a number of teeth and other optional parameters, a
    sprocket centered on the origin is generated.

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
from warnings import warn
from math import sin, asin, cos, pi, radians, sqrt
from OCP.TopoDS import TopoDS_Shape
from OCP.BRepBuilderAPI import BRepBuilderAPI_Copy
import cadquery as cq
from cadquery import Vector, Workplane, Wire, Compound, Solid
import cq_warehouse.extensions

MM = 1
INCH = 25.4 * MM

#
#  =============================== CLASSES ===============================
#
class Sprocket(Solid):
    """
    Create a new sprocket object as defined by the given parameters. The input parameter
    defaults are appropriate for a standard bicycle chain.

    Args:
        num_teeth (int): number of teeth on the perimeter of the sprocket
        chain_pitch (float): distance between the centers of two adjacent rollers.
            Defaults to 1/2 inch.
        roller_diameter (float): size of the cylindrical rollers within the chain.
            Defaults to 5/16 inch.
        clearance (float): size of the gap between the chain's rollers and the sprocket's teeth.
            Defaults to 0.
        thickness (float): thickness of the sprocket.
            Defaults to 0.084 inch.
        bolt_circle_diameter (float): diameter of the mounting bolt hole pattern.
            Defaults to 0.
        num_mount_bolts (int): number of bolt holes (default 0) - if 0, no bolt holes
            are added to the sprocket
        mount_bolt_diameter (float): size of the bolt holes use to mount the sprocket.
            Defaults to 0.
        bore_diameter (float): size of the central hole in the sprocket (default 0) - if 0,
            no bore hole is added to the sprocket

    **NOTE**: Default parameters are for standard single sprocket bicycle chains.

    Attributes:
        pitch_radius (float): radius of the circle formed by the center of the chain rollers
        outer_radius (float): size of the sprocket from center to tip of the teeth
        pitch_circumference (float): circumference of the sprocket at the pitch radius

    Example:

        .. doctest::

            >>> s = Sprocket(num_teeth=32)
            >>> print(s.pitch_radius)
            64.78458745735234
            >>> s.rotate((0,0,0),(0,0,1),10)

    """

    @property
    def pitch_radius(self):
        """The radius of the circle formed by the center of the chain rollers"""
        return Sprocket.sprocket_pitch_radius(self.num_teeth, self.chain_pitch)

    @property
    def outer_radius(self):
        """The size of the sprocket from center to tip of the teeth"""
        if self._flat_teeth:
            o_radius = self.pitch_radius + self.roller_diameter / 4
        else:
            o_radius = sqrt(
                self.pitch_radius**2 - (self.chain_pitch / 2) ** 2
            ) + sqrt(
                (self.chain_pitch - self.roller_diameter / 2) ** 2
                - (self.chain_pitch / 2) ** 2
            )
        return o_radius

    @property
    def pitch_circumference(self):
        """The circumference of the sprocket at the pitch radius"""
        return Sprocket.sprocket_circumference(self.num_teeth, self.chain_pitch)

    @property
    def cq_object(self) -> cq.Compound:
        """A cadquery Solid sprocket as defined by class attributes"""
        warn("cq_object will be deprecated.", DeprecationWarning, stacklevel=2)
        return Solid(self.wrapped)

    def __init__(
        self,
        num_teeth: int,
        chain_pitch: float = (1 / 2) * INCH,
        roller_diameter: float = (5 / 16) * INCH,
        clearance: float = 0.0,
        thickness: float = 0.084 * INCH,
        bolt_circle_diameter: float = 0.0,
        num_mount_bolts: int = 0,
        mount_bolt_diameter: float = 0.0,
        bore_diameter: float = 0.0,
    ):
        """Validate inputs and create the chain assembly object"""
        self.num_teeth = num_teeth
        self.chain_pitch = chain_pitch
        self.roller_diameter = roller_diameter
        self.clearance = clearance
        self.thickness = thickness
        self.bolt_circle_diameter = bolt_circle_diameter
        self.num_mount_bolts = num_mount_bolts
        self.mount_bolt_diameter = mount_bolt_diameter
        self.bore_diameter = bore_diameter

        # Validate inputs
        """Ensure that the roller would fit in the chain"""
        if self.roller_diameter >= self.chain_pitch:
            raise ValueError(
                f"roller_diameter {self.roller_diameter} is too large for chain_pitch {self.chain_pitch}"
            )
        if not isinstance(num_teeth, int) or num_teeth <= 2:
            raise ValueError(
                f"num_teeth must be an integer greater than 2 not {num_teeth}"
            )
        # Create the sprocket
        cq_object = self._make_sprocket()

        # Unwrap the Compound - it always gets generated but is unnecessary
        # (possibly due to some cadquery internals that might change)
        if isinstance(cq_object, Compound) and len(cq_object.Solids()) == 1:
            super().__init__(cq_object.Solids()[0].wrapped)
        else:
            super().__init__(cq_object.wrapped)

    def _make_sprocket(self) -> cq.Compound:
        """Create a new sprocket object as defined by the class attributes"""
        sprocket = (
            Workplane("XY")
            .polarArray(self.pitch_radius, 0, 360, self.num_teeth)
            .tooth_outline(
                self.num_teeth, self.chain_pitch, self.roller_diameter, self.clearance
            )
            .consolidateWires()
            .rotate(
                (0, 0, 0), (0, 0, 1), 90
            )  # Align for sprocket rotation calculations
            .extrude(self.thickness)
            .translate((0, 0, -self.thickness / 2))
        )

        # Chamfer the outside edges if the sprocket has "flat" teeth determined by ..
        # .. extracting all the unique radii
        arc_list = {round(a.radius(), 7) for a in sprocket.edges("%circle").vals()}
        self._flat_teeth = len(arc_list) == 3
        if self._flat_teeth:
            sprocket = sprocket.edges(cq.selectors.RadiusNthSelector(2)).chamfer(
                self.thickness * 0.25, self.thickness * 0.5
            )
        #
        # Create bolt holes
        if (
            self.bolt_circle_diameter != 0
            and self.num_mount_bolts != 0
            and self.mount_bolt_diameter != 0
        ):
            sprocket = (
                sprocket.faces(">Z")
                .workplane()
                .polarArray(self.bolt_circle_diameter / 2, 0, 360, self.num_mount_bolts)
                .circle(self.mount_bolt_diameter / 2)
                .cutThruAll()
            )
        #
        # Create a central bore
        if self.bore_diameter != 0:
            sprocket = sprocket.circle(self.bore_diameter / 2).cutThruAll()
        return sprocket.val()

    def copy(self) -> "Sprocket":
        sprocket_copy = Sprocket(
            self.num_teeth,
            self.chain_pitch,
            self.roller_diameter,
            self.clearance,
            self.thickness,
            self.bolt_circle_diameter,
            self.num_mount_bolts,
            self.mount_bolt_diameter,
            self.bore_diameter,
        )
        sprocket_copy.wrapped = BRepBuilderAPI_Copy(self.wrapped).Shape()
        sprocket_copy.forConstruction = self.forConstruction
        sprocket_copy.label = self.label
        return sprocket_copy

    @staticmethod
    def sprocket_pitch_radius(num_teeth: int, chain_pitch: float) -> float:
        """
        Calculate and return the pitch radius of a sprocket with the given number of teeth
                                and chain pitch

        Parameters
        ----------
        num_teeth : int
            the number of teeth on the perimeter of the sprocket
        chain_pitch : float
            the distance between two adjacent pins in a single link (default 1/2 INCH)
        """
        return sqrt(chain_pitch * chain_pitch / (2 * (1 - cos(2 * pi / num_teeth))))

    @staticmethod
    def sprocket_circumference(num_teeth: int, chain_pitch: float) -> float:
        """
        Calculate and return the pitch circumference of a sprocket with the given number of
                                teeth and chain pitch

        Parameters
        ----------
        num_teeth : int
            the number of teeth on the perimeter of the sprocket
        chain_pitch : float
            the distance between two adjacent pins in a single link (default 1/2 INCH)
        """
        return (
            2
            * pi
            * sqrt(chain_pitch * chain_pitch / (2 * (1 - cos(2 * pi / num_teeth))))
        )


#
#  =============================== FUNCTIONS BOUND TO OTHER CLASSES ===============================
#


def make_tooth_outline(
    num_teeth: int, chain_pitch: float, roller_diameter: float, clearance: float = 0.0
) -> Wire:
    """
    Create a Wire in the shape of a single tooth of the sprocket defined by the input parameters

    There are two different shapes that the tooth could take:
    1) "Spiky" teeth: given sufficiently large rollers, there is no circular top
    2) "Flat" teeth: given smaller rollers, a circular "flat" section bridges the
       space between roller slots
    """

    roller_rad = roller_diameter / 2 + clearance
    tooth_a_degrees = 360 / num_teeth
    half_tooth_a = radians(tooth_a_degrees / 2)
    pitch_rad = sqrt(chain_pitch**2 / (2 * (1 - cos(radians(tooth_a_degrees)))))
    outer_rad = pitch_rad + roller_rad / 2

    # Calculate the a at which the tooth arc intersects the outside edge arc
    outer_intersect_a_r = asin(
        (
            outer_rad**3 * (-(pitch_rad * sin(half_tooth_a)))
            + sqrt(
                outer_rad**6 * (-((pitch_rad * cos(half_tooth_a)) ** 2))
                + 2
                * outer_rad**4
                * (chain_pitch - roller_rad) ** 2
                * (pitch_rad * cos(half_tooth_a)) ** 2
                + 2 * outer_rad**4 * (pitch_rad * cos(half_tooth_a)) ** 4
                + 2
                * outer_rad**4
                * (pitch_rad * cos(half_tooth_a)) ** 2
                * (pitch_rad * sin(half_tooth_a)) ** 2
                - outer_rad**2
                * (chain_pitch - roller_rad) ** 4
                * (pitch_rad * cos(half_tooth_a)) ** 2
                + 2
                * outer_rad**2
                * (chain_pitch - roller_rad) ** 2
                * (pitch_rad * cos(half_tooth_a)) ** 4
                + 2
                * outer_rad**2
                * (chain_pitch - roller_rad) ** 2
                * (pitch_rad * cos(half_tooth_a)) ** 2
                * (pitch_rad * sin(half_tooth_a)) ** 2
                - outer_rad**2 * (pitch_rad * cos(half_tooth_a)) ** 6
                - 2
                * outer_rad**2
                * (pitch_rad * cos(half_tooth_a)) ** 4
                * (pitch_rad * sin(half_tooth_a)) ** 2
                - outer_rad**2
                * (pitch_rad * cos(half_tooth_a)) ** 2
                * (pitch_rad * sin(half_tooth_a)) ** 4
            )
            + outer_rad
            * (chain_pitch - roller_rad) ** 2
            * (pitch_rad * sin(half_tooth_a))
            - outer_rad
            * (pitch_rad * cos(half_tooth_a)) ** 2
            * (pitch_rad * sin(half_tooth_a))
            - outer_rad * (pitch_rad * sin(half_tooth_a)) ** 3
        )
        / (
            2
            * (
                outer_rad**2 * (pitch_rad * cos(half_tooth_a)) ** 2
                + outer_rad**2 * (pitch_rad * sin(half_tooth_a)) ** 2
            )
        )
    )

    # Bottom of the roller arc
    start_pt = Vector(pitch_rad - roller_rad, 0).rotateZ(tooth_a_degrees / 2)
    # Where the roller arc meets transitions to the top half of the tooth
    tangent_pt = Vector(0, -roller_rad).rotateZ(-tooth_a_degrees / 2) + Vector(
        pitch_rad, 0
    ).rotateZ(tooth_a_degrees / 2)
    # The intersection point of the tooth and the outer rad
    outer_pt = Vector(
        outer_rad * cos(outer_intersect_a_r), outer_rad * sin(outer_intersect_a_r)
    )
    # The location of the tip of the spike if there is no "flat" section
    spike_pt = Vector(
        sqrt(pitch_rad**2 - (chain_pitch / 2) ** 2)
        + sqrt((chain_pitch - roller_rad) ** 2 - (chain_pitch / 2) ** 2),
        0,
    )

    # Generate the tooth outline
    if outer_pt.y > 0:  # "Flat" topped sprockets
        tooth = (
            Workplane("XY")
            .moveTo(start_pt.x, start_pt.y)
            .radiusArc(tangent_pt.toTuple(), -roller_rad)
            .radiusArc(outer_pt.toTuple(), chain_pitch - roller_rad)
            .radiusArc(outer_pt.flipY().toTuple(), outer_rad)
            .radiusArc(tangent_pt.flipY().toTuple(), chain_pitch - roller_rad)
            .radiusArc(start_pt.flipY().toTuple(), -roller_rad)
            .consolidateWires()
            .translate((-pitch_rad, 0, 0))
            # .rotate((0, 0, 0), (0, 0, 1), 90) # polarArray start angle, and rotation fix (#1006)
        )
    else:  # "Spiky" sprockets
        tooth = (
            Workplane("XY")
            .moveTo(start_pt.x, start_pt.y)
            .radiusArc(tangent_pt.toTuple(), -roller_rad)
            .radiusArc(spike_pt.toTuple(), chain_pitch - roller_rad)
            .radiusArc(tangent_pt.flipY().toTuple(), chain_pitch - roller_rad)
            .radiusArc(start_pt.flipY().toTuple(), -roller_rad)
            .consolidateWires()
            .translate((-pitch_rad, 0, 0))
            # .rotate((0, 0, 0), (0, 0, 1), 90)# polarArray start angle, and rotation fix (#1006)
        )
    return tooth.val()


def _tooth_outline(
    self, num_teeth, chain_pitch, roller_diameter, clearance
) -> Workplane:
    """Wrap make_tooth_outline for use within Workplane with multiple sprocket teeth"""
    # pylint: disable=unnecessary-lambda
    tooth = make_tooth_outline(num_teeth, chain_pitch, roller_diameter, clearance)
    return self.eachpoint(lambda loc: tooth.moved(loc), True)


Workplane.tooth_outline = _tooth_outline

#
# Extensions to the Vector class
def _vector_flip_y(self) -> Vector:
    """Vector reflect across the XZ plane"""
    return Vector(self.x, -self.y, self.z)


Vector.flipY = _vector_flip_y
