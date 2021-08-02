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
from math import sin, asin, cos, pi, radians, sqrt
from typing import Union, Tuple
from pydantic import BaseModel, PrivateAttr, validator, validate_arguments, Field
import cadquery as cq

VectorLike = Union[Tuple[float, float], Tuple[float, float, float], cq.Vector]

VERSION = 1.0
MM = 1
INCH = 25.4 * MM

#
#  =============================== CLASSES ===============================
#
class Sprocket(BaseModel):
    """
    Create a new sprocket object as defined by the given parameters. The input parameter
    defaults are appropriate for a standard bicycle chain.

    Usage:
        s = Sprocket(num_teeth=32)
        print(s.pitch_radius)                   # 64.78458745735234
        s.cq_object.rotate((0,0,0),(0,0,1),10)

    Attributes
    ----------
    num_teeth : int
        the number of teeth on the perimeter of the sprocket
    chain_pitch : float
        the distance between the centers of two adjacent rollers (default 1/2 INCH)
    roller_diameter : float
        the size of the cylindrical rollers within the chain (default 5/16 INCH)
    clearance : float
        the size of the gap between the chain's rollers and the sprocket's teeth (default 0)
    thickness : float
        the thickness of the sprocket (default 0.084 INCH)
    bolt_circle_diameter : float
        the diameter of the mounting bolt hole pattern (default 0)
    num_mount_bolts : int
        the number of bolt holes (default 0) - if 0, no bolt holes are added to the sprocket
    mount_bolt_diameter : float
        the size of the bolt holes use to mount the sprocket (default 0)
    bore_diameter : float
        the size of the central hole in the sprocket (default 0) - if 0, no bore hole is added
        to the sprocket
    pitch_radius : float
        the radius of the circle formed by the center of the chain rollers
    outer_radius : float
        the size of the sprocket from center to tip of the teeth
    pitch_circumference : float
        the circumference of the sprocket at the pitch radius
    cq_object : cq.Workplane
        the cadquery sprocket object

    Methods
    -------

    sprocket_pitch_radius(num_teeth,chain_pitch) -> float:
        Calculate and return the pitch radius of a sprocket with the given number of teeth
        and chain pitch

    sprocket_circumference(num_teeth,chain_pitch) -> float:
        Calculate and return the pitch circumference of a sprocket with the given number
        of teeth and chain pitch
    """

    # Instance Attributes
    num_teeth: int = Field(..., gt=2)
    chain_pitch: float = (1 / 2) * INCH
    roller_diameter: float = (5 / 16) * INCH
    clearance: float = 0.0
    thickness: float = 0.084 * INCH
    bolt_circle_diameter: float = 0.0
    num_mount_bolts: int = 0
    mount_bolt_diameter: float = 0.0
    bore_diameter: float = 0.0

    # Private Attributes
    _flat_teeth: bool = PrivateAttr()
    _cq_object: cq.Workplane = PrivateAttr()

    # pylint: disable=no-self-argument
    # pylint: disable=no-self-use
    @validator("roller_diameter")
    def is_roller_too_large(cls, i, values):
        """ Ensure that the roller would fit in the chain """
        if i >= values["chain_pitch"]:
            raise ValueError(
                f"roller_diameter {i} is too large for chain_pitch {values['chain_pitch']}"
            )
        return i

    @property
    def pitch_radius(self):
        """ The radius of the circle formed by the center of the chain rollers """
        return Sprocket.sprocket_pitch_radius(self.num_teeth, self.chain_pitch)

    @property
    def outer_radius(self):
        """ The size of the sprocket from center to tip of the teeth """
        if self._flat_teeth:
            o_radius = self.pitch_radius + self.roller_diameter / 4
        else:
            o_radius = sqrt(
                self.pitch_radius ** 2 - (self.chain_pitch / 2) ** 2
            ) + sqrt(
                (self.chain_pitch - self.roller_diameter / 2) ** 2
                - (self.chain_pitch / 2) ** 2
            )
        return o_radius

    @property
    def pitch_circumference(self):
        """ The circumference of the sprocket at the pitch radius """
        return Sprocket.sprocket_circumference(self.num_teeth, self.chain_pitch)

    @property
    def cq_object(self):
        """ A cadquery Workplane sprocket as defined by class attributes """
        return self._cq_object

    def __init__(self, **data):
        """ Validate inputs and create the chain assembly object """
        # Use the BaseModel initializer to validate the attributes
        super().__init__(**data)
        # Create the sprocket
        self._cq_object = self._make_sprocket()

    def _make_sprocket(self) -> cq.Workplane:
        """ Create a new sprocket object as defined by the class attributes """
        sprocket = (
            cq.Workplane("XY")
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

        return sprocket

    @staticmethod
    @validate_arguments
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
    @validate_arguments
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


@validate_arguments
def make_tooth_outline(
    num_teeth: int, chain_pitch: float, roller_diameter: float, clearance: float = 0.0
) -> cq.Wire:
    """
    Create a cq.Wire in the shape of a single tooth of the sprocket defined by the input parameters

    There are two different shapes that the tooth could take:
    1) "Spiky" teeth: given sufficiently large rollers, there is no circular top
    2) "Flat" teeth: given smaller rollers, a circular "flat" section bridges the
       space between roller slots
    """

    roller_rad = roller_diameter / 2 + clearance
    tooth_a_degrees = 360 / num_teeth
    half_tooth_a = radians(tooth_a_degrees / 2)
    pitch_rad = sqrt(chain_pitch ** 2 / (2 * (1 - cos(radians(tooth_a_degrees)))))
    outer_rad = pitch_rad + roller_rad / 2

    # Calculate the a at which the tooth arc intersects the outside edge arc
    outer_intersect_a_r = asin(
        (
            outer_rad ** 3 * (-(pitch_rad * sin(half_tooth_a)))
            + sqrt(
                outer_rad ** 6 * (-((pitch_rad * cos(half_tooth_a)) ** 2))
                + 2
                * outer_rad ** 4
                * (chain_pitch - roller_rad) ** 2
                * (pitch_rad * cos(half_tooth_a)) ** 2
                + 2 * outer_rad ** 4 * (pitch_rad * cos(half_tooth_a)) ** 4
                + 2
                * outer_rad ** 4
                * (pitch_rad * cos(half_tooth_a)) ** 2
                * (pitch_rad * sin(half_tooth_a)) ** 2
                - outer_rad ** 2
                * (chain_pitch - roller_rad) ** 4
                * (pitch_rad * cos(half_tooth_a)) ** 2
                + 2
                * outer_rad ** 2
                * (chain_pitch - roller_rad) ** 2
                * (pitch_rad * cos(half_tooth_a)) ** 4
                + 2
                * outer_rad ** 2
                * (chain_pitch - roller_rad) ** 2
                * (pitch_rad * cos(half_tooth_a)) ** 2
                * (pitch_rad * sin(half_tooth_a)) ** 2
                - outer_rad ** 2 * (pitch_rad * cos(half_tooth_a)) ** 6
                - 2
                * outer_rad ** 2
                * (pitch_rad * cos(half_tooth_a)) ** 4
                * (pitch_rad * sin(half_tooth_a)) ** 2
                - outer_rad ** 2
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
                outer_rad ** 2 * (pitch_rad * cos(half_tooth_a)) ** 2
                + outer_rad ** 2 * (pitch_rad * sin(half_tooth_a)) ** 2
            )
        )
    )

    # Bottom of the roller arc
    start_pt = cq.Vector(pitch_rad - roller_rad, 0).rotateZ(tooth_a_degrees / 2)
    # Where the roller arc meets transitions to the top half of the tooth
    tangent_pt = cq.Vector(0, -roller_rad).rotateZ(-tooth_a_degrees / 2) + cq.Vector(
        pitch_rad, 0
    ).rotateZ(tooth_a_degrees / 2)
    # The intersection point of the tooth and the outer rad
    outer_pt = cq.Vector(
        outer_rad * cos(outer_intersect_a_r), outer_rad * sin(outer_intersect_a_r)
    )
    # The location of the tip of the spike if there is no "flat" section
    spike_pt = cq.Vector(
        sqrt(pitch_rad ** 2 - (chain_pitch / 2) ** 2)
        + sqrt((chain_pitch - roller_rad) ** 2 - (chain_pitch / 2) ** 2),
        0,
    )

    # Generate the tooth outline
    if outer_pt.y > 0:  # "Flat" topped sprockets
        tooth = (
            cq.Workplane("XY")
            .moveTo(start_pt.x, start_pt.y)
            .radiusArc(tangent_pt.toTuple(), -roller_rad)
            .radiusArc(outer_pt.toTuple(), chain_pitch - roller_rad)
            .radiusArc(outer_pt.flipY().toTuple(), outer_rad)
            .radiusArc(tangent_pt.flipY().toTuple(), chain_pitch - roller_rad)
            .radiusArc(start_pt.flipY().toTuple(), -roller_rad)
            .consolidateWires()
            .translate((-pitch_rad, 0, 0))
            .rotate((0, 0, 0), (0, 0, 1), 90)
        )
    else:  # "Spiky" sprockets
        tooth = (
            cq.Workplane("XY")
            .moveTo(start_pt.x, start_pt.y)
            .radiusArc(tangent_pt.toTuple(), -roller_rad)
            .radiusArc(spike_pt.toTuple(), chain_pitch - roller_rad)
            .radiusArc(tangent_pt.flipY().toTuple(), chain_pitch - roller_rad)
            .radiusArc(start_pt.flipY().toTuple(), -roller_rad)
            .consolidateWires()
            .translate((-pitch_rad, 0, 0))
            .rotate((0, 0, 0), (0, 0, 1), 90)
        )
    return tooth.val()


def _tooth_outline(
    self, num_teeth, chain_pitch, roller_diameter, clearance
) -> cq.Workplane:
    """ Wrap make_tooth_outline for use within cq.Workplane with multiple sprocket teeth """
    # pylint: disable=unnecessary-lambda
    tooth = make_tooth_outline(num_teeth, chain_pitch, roller_diameter, clearance)
    return self.eachpoint(lambda loc: tooth.moved(loc), True)


cq.Workplane.tooth_outline = _tooth_outline

#
# Extensions to the Vector class
def _vector_rotate_x(self, angle: float) -> cq.Vector:
    """ cq.Vector rotate angle in degrees about x-axis """
    return cq.Vector(
        self.x,
        self.y * cos(radians(angle)) - self.z * sin(radians(angle)),
        self.y * sin(radians(angle)) + self.z * cos(radians(angle)),
    )


cq.Vector.rotateX = _vector_rotate_x


def _vector_rotate_y(self, angle: float) -> cq.Vector:
    """ cq.Vector rotate angle in degrees about y-axis """
    return cq.Vector(
        self.x * cos(radians(angle)) + self.z * sin(radians(angle)),
        self.y,
        -self.x * sin(radians(angle)) + self.z * cos(radians(angle)),
    )


cq.Vector.rotateY = _vector_rotate_y


def _vector_rotate_z(self, angle: float) -> cq.Vector:
    """ cq.Vector rotate angle in degrees about z-axis """
    return cq.Vector(
        self.x * cos(radians(angle)) - self.y * sin(radians(angle)),
        self.x * sin(radians(angle)) + self.y * cos(radians(angle)),
        self.z,
    )


cq.Vector.rotateZ = _vector_rotate_z


def _vector_flip_y(self) -> cq.Vector:
    """ cq.Vector reflect across the XZ plane """
    return cq.Vector(self.x, -self.y, self.z)


cq.Vector.flipY = _vector_flip_y


def _point_to_vector(self, plane: str, offset: float = 0.0) -> cq.Vector:
    """ map a 2D point on the XY plane to 3D space on the given plane at the offset """
    if not isinstance(plane, str) or plane not in ["XY", "XZ", "YZ"]:
        raise ValueError("plane " + str(plane) + " must be one of: XY,XZ,YZ")
    if plane == "XY":
        mapped_point = cq.Vector(self.x, self.y, offset)
    elif plane == "XZ":
        mapped_point = cq.Vector(self.x, offset, self.y)
    else:  # YZ
        mapped_point = cq.Vector(offset, self.x, self.y)
    return mapped_point


cq.Vector.pointToVector = _point_to_vector
