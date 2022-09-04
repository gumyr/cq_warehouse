"""

Parametric Threads

name: thread.py
by:   Gumyr
date: November 11th 2021

desc: This python/cadquery code is a parameterized thread generator.

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
import re
from warnings import warn
from abc import ABC, abstractmethod
from typing import Literal, Optional, Tuple, List
from math import sin, cos, tan, radians, pi
import cadquery as cq
from cadquery import Solid, Compound
from OCP.TopoDS import TopoDS_Shape

# from functools import cached_property, cache

MM = 1
IN = 25.4 * MM


def is_safe(value: str) -> bool:
    """Evaluate if the given string is a fractional number safe for eval()"""
    return len(value) <= 10 and all(c in "0123456789./ " for c in set(value))


def imperial_str_to_float(measure: str) -> float:
    """Convert an imperial measurement (possibly a fraction) to a float value"""
    if is_safe(measure):
        # pylint: disable=eval-used
        # Before eval() is called the string extracted from the csv file is verified as safe
        result = eval(measure.strip().replace(" ", "+")) * IN
    else:
        result = measure
    return result


class Thread(Solid):
    """Helical thread

    The most general thread class used to build all of the other threads.
    Creates right or left hand helical thread with the given
    root and apex radii.

    Args:
        apex_radius: Radius at the narrow tip of the thread.
        apex_width: Radius at the wide base of the thread.
        root_radius: Radius at the wide base of the thread.
        root_width: Thread base width.
        pitch: Length of 360° of thread rotation.
        length: End to end length of the thread.
        apex_offset: Asymmetric thread apex offset from center. Defaults to 0.0.
        hand: Twist direction. Defaults to "right".
        taper_angle: Cone angle for tapered thread. Defaults to None.
        end_finishes: Profile of each end, one of:

            "raw"
                unfinished which typically results in the thread
                extended below z=0 or above z=length
            "fade"
                the thread height drops to zero over 90° of arc
                (or 1/4 pitch)
            "square"
                clipped by the z=0 or z=length plane
            "chamfer"
                conical ends which facilitates alignment of a bolt
                into a nut

            Defaults to ("raw","raw").
        simple: Stop at thread calculation, don't create thread. Defaults to False.

    Raises:
        ValueError: if end_finishes not in ["raw", "square", "fade", "chamfer"]:
    """

    def fade_helix(
        self, t: float, apex: bool, vertical_displacement: float
    ) -> Tuple[float, float, float]:
        """A helical function used to create the faded tips of threads that spirals
        self.tooth_height in self.pitch/4"""
        if self.external:
            radius = (
                self.apex_radius - sin(t * pi / 2) * self.tooth_height
                if apex
                else self.root_radius
            )
        else:
            radius = (
                self.apex_radius + sin(t * pi / 2) * self.tooth_height
                if apex
                else self.root_radius
            )

        z_pos = t * self.pitch / 4 + t * vertical_displacement
        x_pos = radius * cos(t * pi / 2)
        y_pos = radius * sin(t * pi / 2)
        return (x_pos, y_pos, z_pos)

    @property
    def cq_object(self):
        """A cadquery Solid thread as defined by class attributes"""
        warn("cq_object will be deprecated.", DeprecationWarning, stacklevel=2)
        return Solid(self.wrapped)

    def __init__(
        self,
        apex_radius: float,
        apex_width: float,
        root_radius: float,
        root_width: float,
        pitch: float,
        length: float,
        apex_offset: float = 0.0,
        hand: Literal["right", "left"] = "right",
        taper_angle: Optional[float] = None,
        end_finishes: Tuple[
            Literal["raw", "square", "fade", "chamfer"],
            Literal["raw", "square", "fade", "chamfer"],
        ] = ("raw", "raw"),
        simple: bool = False,
    ):
        """Store the parameters and create the thread object"""
        for finish in end_finishes:
            if finish not in ["raw", "square", "fade", "chamfer"]:
                raise ValueError(
                    'end_finishes invalid, must be tuple() of "raw, square, taper, or chamfer"'
                )
        self.external = apex_radius > root_radius
        self.apex_radius = apex_radius
        self.apex_width = apex_width
        # Unfortunately, when creating "fade" ends inaccuracies in parametric curve calculations
        # can result in a gap which causes the OCCT core to fail when combining with other
        # object (like the core of the thread). To avoid this, subtract (or add) a fudge factor
        # to the root radius to make it small enough to intersect the given radii.
        self.root_radius = root_radius - (0.001 if self.external else -0.001)
        self.root_width = root_width
        self.pitch = pitch
        self.length = length
        self.apex_offset = apex_offset
        self.right_hand = hand == "right"
        self.end_finishes = end_finishes
        self.tooth_height = abs(self.apex_radius - self.root_radius)
        self.taper = 360 if taper_angle is None else taper_angle
        self.simple = simple

        if not simple:
            # Create base cylindrical thread
            number_faded_ends = self.end_finishes.count("fade")
            cylindrical_thread_length = self.length + self.pitch * (
                1 - 1 * number_faded_ends
            )
            if self.end_finishes[0] == "fade":
                cylindrical_thread_displacement = self.pitch / 2
            else:
                cylindrical_thread_displacement = -self.pitch / 2

            # Either create a cylindrical thread for further processing
            # or create a cylindrical thread segment with faded ends
            if number_faded_ends == 0:
                cq_object = self.make_thread_solid(cylindrical_thread_length).translate(
                    (0, 0, cylindrical_thread_displacement)
                )
            else:
                cq_object = self.make_thread_with_faded_ends(
                    number_faded_ends,
                    cylindrical_thread_length,
                    cylindrical_thread_displacement,
                )

            # Square off ends if requested
            cq_object = self.square_off_ends(cq_object)
            # Chamfer ends if requested
            cq_object = self.chamfer_ends(cq_object)
            if isinstance(cq_object, Compound) and len(cq_object.Solids()) == 1:
                super().__init__(cq_object.Solids()[0].wrapped)
            else:
                super().__init__(cq_object.wrapped)
        else:
            # Initialize with a valid shape then nullify
            super().__init__(Solid.makeBox(1, 1, 1).wrapped)
            self.wrapped = TopoDS_Shape()

    def make_thread_with_faded_ends(
        self,
        number_faded_ends,
        cylindrical_thread_length,
        cylindrical_thread_displacement,
    ):
        """Build the thread object from cylindrical thread faces and
        faded ends faces"""
        (thread_faces, end_faces) = self.make_thread_faces(cylindrical_thread_length)

        # Need to operate on each face below
        thread_faces = [
            f.translate((0, 0, cylindrical_thread_displacement)) for f in thread_faces
        ]
        end_faces = [
            f.translate((0, 0, cylindrical_thread_displacement)) for f in end_faces
        ]
        cylindrical_thread_angle = (
            (360 if self.right_hand else -360) * cylindrical_thread_length / self.pitch
        )
        (fade_faces, _fade_ends) = self.make_thread_faces(
            self.pitch / 4, fade_helix=True
        )
        if not self.right_hand:
            fade_faces = [f.mirror("XZ") for f in fade_faces]

        if self.end_finishes[0] == "fade":
            # If the thread is asymmetric the bottom fade end needs to be recreated as
            # no amount of flipping or rotating can generate the shape
            if self.apex_offset != 0:
                (fade_faces_bottom, _fade_ends) = self.make_thread_faces(
                    self.pitch / 4, fade_helix=True, asymmetric_flip=True
                )
                if not self.right_hand:
                    fade_faces_bottom = [f.mirror("XZ") for f in fade_faces_bottom]
            else:
                fade_faces_bottom = fade_faces
            fade_faces_bottom = [
                f.mirror("XZ").mirror("XY").translate(cq.Vector(0, 0, self.pitch / 2))
                for f in fade_faces_bottom
            ]
        if self.end_finishes[1] == "fade":
            fade_faces_top = [
                f.translate(
                    cq.Vector(
                        0,
                        0,
                        cylindrical_thread_length + cylindrical_thread_displacement,
                    )
                ).rotate((0, 0, 0), (0, 0, 1), cylindrical_thread_angle)
                for f in fade_faces
            ]
        if number_faded_ends == 2:
            thread_shell = cq.Shell.makeShell(
                thread_faces + fade_faces_bottom + fade_faces_top
            )
        elif self.end_finishes[0] == "fade":
            thread_shell = cq.Shell.makeShell(
                thread_faces + fade_faces_bottom + [end_faces[1]]
            )
        else:
            thread_shell = cq.Shell.makeShell(
                thread_faces + fade_faces_top + [end_faces[0]]
            )
        return cq.Solid.makeSolid(thread_shell)

    def square_off_ends(self, cq_object: Solid):
        """Square off the ends of the thread"""

        squared = cq_object
        if self.end_finishes.count("square") != 0:
            # Note: box_size must be > max(apex,root) radius or the core doesn't cut correctly
            half_box_size = 2 * max(self.apex_radius, self.root_radius)
            box_size = 2 * half_box_size
            cutter = cq.Solid.makeBox(
                length=box_size,
                width=box_size,
                height=self.length,
                pnt=cq.Vector(-half_box_size, -half_box_size, -self.length),
            )
            for i in range(2):
                if self.end_finishes[i] == "square":
                    squared = cq_object.cut(
                        cutter.translate(cq.Vector(0, 0, 2 * i * self.length))
                    )
        return squared

    def chamfer_ends(self, cq_object: Solid):
        """Chamfer the ends of the thread"""

        chamfered = cq_object
        if self.end_finishes.count("chamfer") != 0:
            cutter = (
                cq.Workplane("XY")
                .circle(self.root_radius)
                .circle(self.apex_radius)
                .extrude(self.length)
            )
            face_selectors = ["<Z", ">Z"]
            edge_radius_selector = 1 if self.apex_radius > self.root_radius else 0
            for i in range(2):
                if self.end_finishes[i] == "chamfer":
                    cutter = (
                        cutter.faces(face_selectors[i])
                        .edges(cq.selectors.RadiusNthSelector(edge_radius_selector))
                        .chamfer(self.tooth_height * 0.5, self.tooth_height * 0.75)
                    )
            chamfered = cq_object.intersect(cutter.val())
        return chamfered

    def make_thread_faces(
        self, length: float, fade_helix: bool = False, asymmetric_flip: bool = False
    ) -> Tuple[List[cq.Face]]:
        """Create the thread object from basic CadQuery objects

        This method creates three types of thread objects:
        1. cylindrical - i.e. following a simple helix
        2. tapered - i.e. following a conical helix
        3. faded - cylindrical but spiralling towards the root in 90°

        After testing many alternatives (sweep, extrude with rotation, etc.) the
        following algorithm was found to be the fastest and most reliable:
        a. first create all the edges - helical, linear or parametric
        b. create either 5 or 6 faces from the edges (faded needs 5)
        c. create a shell from the faces
        d. create a solid from the shell
        """
        local_apex_offset = -self.apex_offset if asymmetric_flip else self.apex_offset
        apex_helix_wires = [
            cq.Workplane("XY")
            .parametricCurve(
                lambda t: self.fade_helix(t, apex=True, vertical_displacement=0)
            )
            .val()
            .translate((0, 0, i * self.apex_width + local_apex_offset))
            if fade_helix
            else cq.Wire.makeHelix(
                pitch=self.pitch,
                height=length,
                radius=self.apex_radius,
                angle=self.taper,
                lefthand=not self.right_hand,
            ).translate((0, 0, i * self.apex_width + local_apex_offset))
            for i in [-0.5, 0.5]
        ]
        assert apex_helix_wires[0].isValid()
        root_helix_wires = [
            cq.Workplane("XY")
            .parametricCurve(
                lambda t: self.fade_helix(
                    t,
                    apex=False,
                    vertical_displacement=-i * (self.root_width - self.apex_width),
                )
            )
            .val()
            .translate((0, 0, i * self.root_width))
            if fade_helix
            else cq.Wire.makeHelix(
                pitch=self.pitch,
                height=length,
                radius=self.root_radius,
                angle=self.taper,
                lefthand=not self.right_hand,
            ).translate((0, 0, i * self.root_width))
            for i in [-0.5, 0.5]
        ]
        # When creating a cylindrical or tapered thread two end faces are required
        # to enclose the thread object, while faded thread only has one end face
        end_caps = [0] if fade_helix else [0, 1]
        end_cap_wires = [
            cq.Wire.makePolygon(
                [
                    apex_helix_wires[0].positionAt(i),
                    apex_helix_wires[1].positionAt(i),
                    root_helix_wires[1].positionAt(i),
                    root_helix_wires[0].positionAt(i),
                    apex_helix_wires[0].positionAt(i),
                ]
            )
            for i in end_caps
        ]
        thread_faces = [
            cq.Face.makeRuledSurface(apex_helix_wires[0], apex_helix_wires[1]),
            cq.Face.makeRuledSurface(apex_helix_wires[1], root_helix_wires[1]),
            cq.Face.makeRuledSurface(root_helix_wires[1], root_helix_wires[0]),
            cq.Face.makeRuledSurface(root_helix_wires[0], apex_helix_wires[0]),
        ]
        end_faces = [cq.Face.makeFromWires(end_cap_wires[i]) for i in end_caps]
        return (thread_faces, end_faces)

    def make_thread_solid(
        self,
        length: float,
        fade_helix: bool = False,
    ) -> cq.Solid:
        """Create a solid object by first creating the faces"""
        (thread_faces, end_faces) = self.make_thread_faces(length, fade_helix)

        thread_shell = cq.Shell.makeShell(thread_faces + end_faces)
        thread_solid = cq.Solid.makeSolid(thread_shell)
        return thread_solid


class IsoThread(Solid):
    """ISO Standard Thread

    Both external and internal ISO standard 60° threads as shown in
    the following diagram (from https://en.wikipedia.org/wiki/ISO_metric_screw_thread):

    .. image:: https://upload.wikimedia.org/wikipedia/commons/4/4b/ISO_and_UTS_Thread_Dimensions.svg

    The following is an example of an internal thread with a chamfered end as might
    be found inside a nut:

    .. image:: internal_iso_thread.png

    Args:
        major_diameter (float): Primary thread diameter
        pitch (float): Length of 360° of thread rotation
        length (float): End to end length of the thread
        external (bool, optional): External or internal thread selector. Defaults to True.
        hand (Literal[, optional): Twist direction. Defaults to "right".
        end_finishes (Tuple[ Literal[, optional): Profile of each end, one of:

            "raw"
                unfinished which typically results in the thread
                extended below z=0 or above z=length
            "fade"
                the thread height drops to zero over 90° of arc
                (or 1/4 pitch)
            "square"
                clipped by the z=0 or z=length plane
            "chamfer"
                conical ends which facilitates alignment of a bolt
                into a nut

            Defaults to ("fade", "square").
        simple: Stop at thread calculation, don't create thread. Defaults to False.

    Attributes:
        thread_angle (int): 60 degrees
        h_parameter (float): Value of `h` as shown in the thread diagram
        min_radius (float): Inside radius of the thread diagram

    Raises:
        ValueError: if hand not in ["right", "left"]:
        ValueError: end_finishes not in ["raw", "square", "fade", "chamfer"]

    """

    @property
    def h_parameter(self) -> float:
        """Calculate the h parameter"""
        return (self.pitch / 2) / tan(radians(self.thread_angle / 2))

    @property
    def min_radius(self) -> float:
        """The radius of the root of the thread"""
        return (self.major_diameter - 2 * (5 / 8) * self.h_parameter) / 2

    @property
    def cq_object(self):
        """A cadquery Solid thread as defined by class attributes"""
        warn("cq_object will be deprecated.", DeprecationWarning, stacklevel=2)
        return Solid(self.wrapped)

    def __init__(
        self,
        major_diameter: float,
        pitch: float,
        length: float,
        external: bool = True,
        hand: Literal["right", "left"] = "right",
        end_finishes: Tuple[
            Literal["raw", "square", "fade", "chamfer"],
            Literal["raw", "square", "fade", "chamfer"],
        ] = ("fade", "square"),
        simple: bool = False,
    ):

        self.major_diameter = major_diameter
        self.pitch = pitch
        self.length = length
        self.external = external
        self.thread_angle = 60
        if hand not in ["right", "left"]:
            raise ValueError(f'hand must be one of "right" or "left" not {hand}')
        self.hand = hand
        for finish in end_finishes:
            if finish not in ["raw", "square", "fade", "chamfer"]:
                raise ValueError(
                    'end_finishes invalid, must be tuple() of "raw, square, taper, or chamfer"'
                )
        self.end_finishes = end_finishes
        self.simple = simple
        self.apex_radius = self.major_diameter / 2 if external else self.min_radius
        apex_width = self.pitch / 8 if external else self.pitch / 4
        self.root_radius = self.min_radius if external else self.major_diameter / 2
        root_width = 3 * self.pitch / 4 if external else 7 * self.pitch / 8
        cq_object = Thread(
            apex_radius=self.apex_radius,
            apex_width=apex_width,
            root_radius=self.root_radius,
            root_width=root_width,
            pitch=self.pitch,
            length=self.length,
            end_finishes=self.end_finishes,
            hand=self.hand,
            simple=simple,
        )
        if simple:
            # Initialize with a valid shape then nullify
            super().__init__(Solid.makeBox(1, 1, 1).wrapped)
            self.wrapped = TopoDS_Shape()
        else:
            super().__init__(cq_object.wrapped)


class TrapezoidalThread(ABC, Solid):
    """Trapezoidal Thread Base Class

    Trapezoidal Thread base class for Metric and Acme derived classes

    Trapezoidal thread forms are screw thread profiles with trapezoidal outlines. They are
    the most common forms used for leadscrews (power screws). They offer high strength
    and ease of manufacture. They are typically found where large loads are required, as
    in a vise or the leadscrew of a lathe.

    Args:
        size (str): specified by derived class
        length (float): thread length
        external (bool, optional): external or internal thread selector. Defaults to True.
        hand (Literal[, optional): twist direction. Defaults to "right".
        end_finishes (Tuple[ Literal[, optional): Profile of each end, one of:

            "raw"
                unfinished which typically results in the thread
                extended below z=0 or above z=length
            "fade"
                the thread height drops to zero over 90° of arc
                (or 1/4 pitch)
            "square"
                clipped by the z=0 or z=length plane
            "chamfer"
                conical ends which facilitates alignment of a bolt
                into a nut

            Defaults to ("fade", "fade").

    Raises:
        ValueError: hand must be one of "right" or "left"
        ValueError: end_finishes invalid, must be tuple() of "raw, square, taper, or chamfer"

    Attributes:
        thread_angle (int): thread angle in degrees
        diameter (float): thread diameter
        pitch (float): thread pitch

    """

    @property
    def cq_object(self):
        """A cadquery Solid thread as defined by class attributes"""
        warn("cq_object will be deprecated.", DeprecationWarning, stacklevel=2)
        return Solid(self.wrapped)

    @property
    @abstractmethod
    def thread_angle(self) -> float:  # pragma: no cover
        """The thread angle in degrees"""
        return NotImplementedError

    @classmethod
    @abstractmethod
    def parse_size(cls, size: str) -> Tuple[float, float]:  # pragma: no cover
        """Convert the provided size into a tuple of diameter and pitch"""
        return NotImplementedError

    def __init__(
        self,
        size: str,
        length: float,
        external: bool = True,
        hand: Literal["right", "left"] = "right",
        end_finishes: tuple[
            Literal["raw", "square", "fade", "chamfer"],
            Literal["raw", "square", "fade", "chamfer"],
        ] = ("fade", "fade"),
    ):
        self.size = size
        self.external = external
        self.length = length
        (self.diameter, self.pitch) = self.parse_size(self.size)
        shoulder_width = (self.pitch / 2) * tan(radians(self.thread_angle / 2))
        apex_width = (self.pitch / 2) - shoulder_width
        root_width = (self.pitch / 2) + shoulder_width
        if self.external:
            self.apex_radius = self.diameter / 2
            self.root_radius = self.diameter / 2 - self.pitch / 2
        else:
            self.apex_radius = self.diameter / 2 - self.pitch / 2
            self.root_radius = self.diameter / 2

        if hand not in ["right", "left"]:
            raise ValueError(f'hand must be one of "right" or "left" not {hand}')
        self.hand = hand
        for finish in end_finishes:
            if not finish in ["raw", "square", "fade", "chamfer"]:
                raise ValueError(
                    'end_finishes invalid, must be tuple() of "raw, square, taper, or chamfer"'
                )
        self.end_finishes = end_finishes
        cq_object = Thread(
            apex_radius=self.apex_radius,
            apex_width=apex_width,
            root_radius=self.root_radius,
            root_width=root_width,
            pitch=self.pitch,
            length=self.length,
            end_finishes=self.end_finishes,
            hand=self.hand,
        )
        super().__init__(cq_object.wrapped)


class AcmeThread(TrapezoidalThread):
    """ACME Thread

    The original trapezoidal thread form, and still probably the one most commonly encountered
    worldwide, with a 29° thread angle, is the Acme thread form.

    The following is the acme thread with faded ends:

    .. image:: acme_thread.png

    Args:
        size (str): size as a string (i.e. "3/4" or "1 1/4")
        length (float): thread length
        external (bool, optional): external or internal thread selector. Defaults to True.
        hand (Literal[, optional): twist direction. Defaults to "right".
        end_finishes (Tuple[ Literal[, optional): Profile of each end, one of:

            "raw"
                unfinished which typically results in the thread
                extended below z=0 or above z=length
            "fade"
                the thread height drops to zero over 90° of arc
                (or 1/4 pitch)
            "square"
                clipped by the z=0 or z=length plane
            "chamfer"
                conical ends which facilitates alignment of a bolt
                into a nut

            Defaults to ("fade", "fade").

    Raises:
        ValueError: hand must be one of "right" or "left"
        ValueError: end_finishes invalid, must be tuple() of "raw, square, taper, or chamfer"

    Attributes:
        thread_angle (int): thread angle in degrees
        diameter (float): thread diameter
        pitch (float): thread pitch

    """

    acme_pitch = {
        "1/4": (1 / 16) * IN,
        "5/16": (1 / 14) * IN,
        "3/8": (1 / 12) * IN,
        "1/2": (1 / 10) * IN,
        "5/8": (1 / 8) * IN,
        "3/4": (1 / 6) * IN,
        "7/8": (1 / 6) * IN,
        "1": (1 / 5) * IN,
        "1 1/4": (1 / 5) * IN,
        "1 1/2": (1 / 4) * IN,
        "1 3/4": (1 / 4) * IN,
        "2": (1 / 4) * IN,
        "2 1/2": (1 / 3) * IN,
        "3": (1 / 2) * IN,
    }

    thread_angle = 29.0  # in degrees

    @classmethod
    def sizes(cls) -> List[str]:
        """Return a list of the thread sizes"""
        return list(AcmeThread.acme_pitch.keys())

    @classmethod
    def parse_size(cls, size: str) -> Tuple[float, float]:
        """Convert the provided size into a tuple of diameter and pitch"""
        if not size in AcmeThread.acme_pitch.keys():
            raise ValueError(
                f"size invalid, must be one of {AcmeThread.acme_pitch.keys()}"
            )
        diameter = imperial_str_to_float(size)
        pitch = AcmeThread.acme_pitch[size]
        return (diameter, pitch)


class MetricTrapezoidalThread(TrapezoidalThread):
    """Metric Trapezoidal Thread

    The ISO 2904 standard metric trapezoidal thread with a thread angle of 30°

    Args:
        size (str): specified as a sting with diameter x pitch in mm (i.e. "8x1.5")
        length (float): End to end length of the thread
        external (bool, optional): external or internal thread selector. Defaults to True.
        hand (Literal[, optional): twist direction. Defaults to "right".
        end_finishes (Tuple[ Literal[, optional): Profile of each end, one of:

            "raw"
                unfinished which typically results in the thread
                extended below z=0 or above z=length
            "fade"
                the thread height drops to zero over 90° of arc
                (or 1/4 pitch)
            "square"
                clipped by the z=0 or z=length plane
            "chamfer"
                conical ends which facilitates alignment of a bolt
                into a nut

            Defaults to ("fade", "fade").

    Raises:
        ValueError: hand must be one of "right" or "left"
        ValueError: end_finishes invalid, must be tuple() of "raw, square, taper, or chamfer"

    Attributes:
        thread_angle (int): thread angle in degrees
        diameter (float): thread diameter
        pitch (float): thread pitch
    """

    # Turn off black auto-format for this array as it will be spread over hundreds of lines
    # fmt: off
    standard_sizes = [
		"8x1.5","9x1.5","9x2","10x1.5","10x2","11x2","11x3","12x2","12x3","14x2",
		"14x3","16x2","16x3","16x4","18x2","18x3","18x4","20x2","20x3","20x4",
		"22x3","22x5","22x8","24x3","24x5","24x8","26x3","26x5","26x8","28x3",
		"28x5","28x8","30x3","30x6","30x10","32x3","32x6","32x10","34x3","34x6",
		"34x10","36x3","36x6","36x10","38x3","38x7","38x10","40x3","40x7","40x10",
		"42x3","42x7","42x10","44x3","44x7","44x12","46x3","46x8","46x12","48x3",
		"48x8","48x12","50x3","50x8","50x12","52x3","52x8","52x12","55x3","55x9",
		"55x14","60x3","60x9","60x14","65x4","65x10","65x16","70x4","70x10","70x16",
		"75x4","75x10","75x16","80x4","80x10","80x16","85x4","85x12","85x18","90x4",
		"90x12","90x18","95x4","95x12","95x18","100x4","100x12","100x20","105x4",
		"105x12","105x20","110x4","110x12","110x20","115x6","115x12","115x14",
		"115x22","120x6","120x12","120x14","120x22","125x6","125x12","125x14",
		"125x22","130x6","130x12","130x14","130x22","135x6","135x12","135x14",
		"135x24","140x6","140x12","140x14","140x24","145x6","145x12","145x14",
		"145x24","150x6","150x12","150x16","150x24","155x6","155x12","155x16",
		"155x24","160x6","160x12","160x16","160x28","165x6","165x12","165x16",
		"165x28","170x6","170x12","170x16","170x28","175x8","175x12","175x16",
		"175x28","180x8","180x12","180x18","180x28","185x8","185x12","185x18",
		"185x24","185x32","190x8","190x12","190x18","190x24","190x32","195x8",
		"195x12","195x18","195x24","195x32","200x8","200x12","200x18","200x24",
		"200x32","205x4","210x4","210x8","210x12","210x20","210x24","210x36","215x4",
		"220x4","220x8","220x12","220x20","220x24","220x36","230x4","230x8","230x12",
		"230x20","230x24","230x36","235x4","240x4","240x8","240x12","240x20",
		"240x22","240x24","240x36","250x4","250x12","250x22","250x24","250x40",
		"260x4","260x12","260x20","260x22","260x24","260x40","270x12","270x24",
		"270x40","275x4","280x4","280x12","280x24","280x40","290x4","290x12",
		"290x24","290x44","295x4","300x4","300x12","300x24","300x44","310x5","315x5"
    ]
    # fmt: on

    thread_angle = 30.0  # in degrees

    @classmethod
    def sizes(cls) -> List[str]:
        """Return a list of the thread sizes"""
        return MetricTrapezoidalThread.standard_sizes

    @classmethod
    def parse_size(cls, size: str) -> Tuple[float, float]:
        """Convert the provided size into a tuple of diameter and pitch"""
        if not size in MetricTrapezoidalThread.standard_sizes:
            raise ValueError(
                f"size invalid, must be one of {MetricTrapezoidalThread.standard_sizes}"
            )
        (diameter, pitch) = (float(part) for part in size.split("x"))
        return (diameter, pitch)


class PlasticBottleThread(Solid):
    """ASTM D2911 Plastic Bottle Thread

    The `ASTM D2911 Standard <https://www.astm.org/d2911-10.html>`_ Plastic Bottle Thread.

    L Style:
        All-Purpose Thread - trapezoidal shape with 30° shoulders, metal or platsic closures
    M Style:
        Modified Buttress Thread - asymmetric shape with 10° and 40/45/50°
        shoulders, plastic closures

    .. image:: plasticThread.png

    Args:
        size (str): as defined by the ASTM is specified as
            [L|M][diameter(mm)]SP[100|103|110|200|400|410|415|425|444]
        external (bool, optional): external or internal thread selector. Defaults to True.
        hand (Literal[, optional): twist direction. Defaults to "right".
        manufacturingCompensation (float, optional): used to compensate for over-extrusion of 3D
            printers. A value of 0.2mm will reduce the radius of an external thread by 0.2mm (and
            increase the radius of an internal thread) such that the resulting 3D printed part
            matches the target dimensions. Defaults to 0.0.

    Raises:
        ValueError: hand must be one of "right" or "left"
        ValueError: size invalid, must match
            [L|M][diameter(mm)]SP[100|103|110|200|400|410|415:425|444]
        ValueError: finish invalid
        ValueError: diameter invalid

    Example:
        .. code-block:: python

            thread = PlasticBottleThread(
                size="M38SP444", external=False, manufacturingCompensation=0.2 * MM
            )

    """

    # {TPI: [root_width,thread_height]}
    l_style_thread_dimensions = {
        4: [3.18, 1.57],
        5: [3.05, 1.52],
        6: [2.39, 1.19],
        8: [2.13, 1.07],
        12: [1.14, 0.76],
    }
    m_style_thread_dimensions = {
        4: [3.18, 1.57],
        5: [3.05, 1.52],
        6: [2.39, 1.19],
        8: [2.13, 1.07],
        12: [1.29, 0.76],
    }

    thread_angles = {
        "L100": [30, 30],
        "M100": [10, 40],
        "L103": [30, 30],
        "M103": [10, 40],
        "L110": [30, 30],
        "M110": [10, 50],
        "L200": [30, 30],
        "M200": [10, 40],
        "L400": [30, 30],
        "M400": [10, 45],
        "L410": [30, 30],
        "M410": [10, 45],
        "L415": [30, 30],
        "M415": [10, 45],
        "L425": [30, 30],
        "M425": [10, 45],
        "L444": [30, 30],
        "M444": [10, 45],
    }

    # {finish:[min turns,[diameters,...]]}
    # fmt: off
    finish_data = {
        100: [1.125,[22,24,28,30,33,35,38]],
        103: [1.125,[26]],
        110: [1.125,[28]],
        200: [1.5,[24.28]],
        400: [1.0,[18,20,22,24,28,30,33,35,38,40,43,45,48,51,53,58,60,63,66,70,75,77,83,89,100,110,120]],
        410: [1.5,[18,20,22,24,28]],
        415: [2.0,[13,15,18,20,22,24,28,30,33]],
        425: [2.0,[13,15]],
        444: [1.125,[24,28,30,33,35,38,40,43,45,48,51,53,58,60,63,66,70,75,77,83]]
    }
    # fmt: on

    # {thread_size:[max,min,TPI]}
    thread_dimensions = {
        13: [13.06, 12.75, 12],
        15: [14.76, 14.45, 12],
        18: [17.88, 17.47, 8],
        20: [19.89, 19.48, 8],
        22: [21.89, 21.49, 8],
        24: [23.88, 23.47, 8],
        26: [25.63, 25.12, 8],
        28: [27.64, 27.13, 6],
        30: [28.62, 28.12, 6],
        33: [32.13, 31.52, 6],
        35: [34.64, 34.04, 6],
        38: [37.49, 36.88, 6],
        40: [40.13, 39.37, 6],
        43: [42.01, 41.25, 6],
        45: [44.20, 43.43, 6],
        48: [47.50, 46.74, 6],
        51: [49.99, 49.10, 6],
        53: [52.50, 51.61, 6],
        58: [56.49, 55.60, 6],
        60: [59.49, 58.60, 6],
        63: [62.51, 61.62, 6],
        66: [65.51, 64.62, 6],
        70: [69.49, 68.60, 6],
        75: [73.99, 73.10, 6],
        77: [77.09, 76.20, 6],
        83: [83.01, 82.12, 5],
        89: [89.18, 88.29, 5],
        100: [100.00, 99.11, 5],
        110: [110.01, 109.12, 5],
        120: [119.99, 119.10, 5],
    }

    @property
    def cq_object(self):
        """A cadquery Solid thread as defined by class attributes"""
        warn("cq_object will be deprecated.", DeprecationWarning, stacklevel=2)
        return Solid(self.wrapped)

    def __init__(
        self,
        size: str,
        external: bool = True,
        hand: Literal["right", "left"] = "right",
        manufacturingCompensation: float = 0.0,
    ):
        self.size = size
        self.external = external
        if hand not in ["right", "left"]:
            raise ValueError(f'hand must be one of "right" or "left" not {hand}')
        self.hand = hand
        size_match = re.match(r"([LM])(\d+)SP(\d+)", size)
        if not size_match:
            raise ValueError(
                "size invalid, must match \
                    [L|M][diameter(mm)]SP[100|103|110|200|400|410|415:425|444]"
            )
        self.style = size_match.group(1)
        self.diameter = int(size_match.group(2))
        self.finish = int(size_match.group(3))
        if self.finish not in PlasticBottleThread.finish_data.keys():
            raise ValueError(
                f"finish ({self.finish}) invalid, must be one of"
                f" {list(PlasticBottleThread.finish_data.keys())}"
            )
        if not self.diameter in PlasticBottleThread.finish_data[self.finish][1]:
            raise ValueError(
                f"diameter ({self.diameter}) invalid, must be one"
                f" of {PlasticBottleThread.finish_data[self.finish][1]}"
            )
        (diameter_max, diameter_min, self.tpi) = PlasticBottleThread.thread_dimensions[
            self.diameter
        ]
        if self.style == "L":
            (
                self.root_width,
                thread_height,
            ) = PlasticBottleThread.l_style_thread_dimensions[self.tpi]
        else:
            (
                self.root_width,
                thread_height,
            ) = PlasticBottleThread.m_style_thread_dimensions[self.tpi]
        if self.external:
            self.apex_radius = diameter_min / 2 - manufacturingCompensation
            self.root_radius = (
                diameter_min / 2 - thread_height - manufacturingCompensation
            )
        else:
            self.root_radius = diameter_max / 2 + manufacturingCompensation
            self.apex_radius = (
                diameter_max / 2 - thread_height + manufacturingCompensation
            )
        self.thread_angles = PlasticBottleThread.thread_angles[
            self.style + str(self.finish)
        ]
        shoulders = [thread_height * tan(radians(a)) for a in self.thread_angles]
        self.apex_width = self.root_width - sum(shoulders)
        self.apex_offset = shoulders[0] + self.apex_width / 2 - self.root_width / 2
        if not self.external:
            self.apex_offset = -self.apex_offset
        self.pitch = 25.4 * MM / self.tpi
        self.length = (
            PlasticBottleThread.finish_data[self.finish][0] + 0.75
        ) * self.pitch
        cq_object = Thread(
            apex_radius=self.apex_radius,
            apex_width=self.apex_width,
            root_radius=self.root_radius,
            root_width=self.root_width,
            pitch=self.pitch,
            length=self.length,
            apex_offset=self.apex_offset,
            hand=self.hand,
            end_finishes=("fade", "fade"),
        )
        super().__init__(cq_object.wrapped)
