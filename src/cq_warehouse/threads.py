"""

Parametric Threads

name: threads.py
by:   Gumyr
date: November 11th 2021

desc: This python/cadquery code is a parameterized threads generator.

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
import timeit
from typing import Literal, Optional
from math import sin, cos, tan, radians, pi
import cadquery as cq

# TODO: faded thread with left hand thread
# TODO: sin function faded radius transition
# TODO: faded with length not a multiple of pitch


class Thread:
    """ Create a helical thread
    Each end of the thread can finished as follows:
    - "raw"     unfinished which typically results in the thread extended below
                z=0 or above z=length
    - "square"  clipped by the z=0 or z=length plane
    - "fade"    the thread height drops to zero over 90° of arc (or 1/4 pitch)
    - "chamfer" conical ends which facilitates alignment of a bolt into a nut

    Note that the performance of this Thread class varies significantly by end
    finish. Here are some sample measurements (both ends finished) to illustate
    how the time required to create the thread varies:
    - "raw"     0.037s
    - "square"  0.568s
    - "fade"    0.675s
    - "chamfer" 1.810s

    """

    def fade_helix(
        self, t: float, apex: bool, vertical_displacement: float
    ) -> tuple[float, float, float]:
        """ A helical function that spirals self.tooth_height in self.pitch/4 """
        r = self.apex_radius - t * self.tooth_height if apex else self.root_radius
        z = t * self.pitch / 4 + t * vertical_displacement
        x = r * cos(t * pi / 2)
        y = r * sin(t * pi / 2)
        return (x, y, z)

    @property
    def cq_object(self):
        """ A cadquery Solid thread as defined by class attributes """
        return self._cq_object

    def __init__(
        self,
        apex_radius: float,
        apex_width: float,
        root_radius: float,
        root_width: float,
        pitch: float,
        length: float,
        hand: Literal["right", "left"] = "right",
        simple: bool = True,
        end_finishes: tuple[
            Literal["raw", "square", "fade", "chamfer"],
            Literal["raw", "square", "fade", "chamfer"],
        ] = ("raw", "raw"),
    ):
        """ Store the parameters and create the thread object """
        for finish in end_finishes:
            if not finish in ["raw", "square", "fade", "chamfer"]:
                raise ValueError(
                    f'end_finishes invalid, must be tuple() of "raw, square, taper, or chamfer"'
                )
        self.apex_radius = apex_radius
        self.apex_width = apex_width
        self.root_radius = root_radius
        self.root_width = root_width
        self.pitch = pitch
        self.length = length
        self.right_hand = hand == "right"
        self.simple = simple
        self.end_finishes = end_finishes
        self.tooth_height = abs(self.apex_radius - self.root_radius)

        number_faded_ends = self.end_finishes.count("fade")
        cylindrical_thread_length = self.length + self.pitch * (
            1 - 1 * number_faded_ends
        )
        if self.end_finishes[0] == "fade":
            cylindrical_thread_displacement = pitch / 2
        else:
            cylindrical_thread_displacement = -pitch / 2
        self._cq_object = self.make_thread(cylindrical_thread_length).translate(
            (0, 0, cylindrical_thread_displacement)
        )
        if number_faded_ends != 0:
            fade_thread = self.make_thread(self.pitch / 4, fade_helix=True)
            if self.end_finishes[0] == "fade":
                self._cq_object = self._cq_object.fuse(
                    fade_thread.mirror("XZ").mirror("XY").translate((0, 0, pitch / 2)),
                    glue=True,
                )
            if self.end_finishes[1] == "fade":
                self._cq_object = self._cq_object.fuse(
                    fade_thread.translate(
                        (0, 0, cylindrical_thread_length - pitch / 2)
                    ),
                    glue=True,
                )

        # Square the ends off
        if self.end_finishes.count("square") != 0:
            half_box_size = max(self.apex_radius, self.root_radius)
            box_size = 2 * half_box_size
            cutter = cq.Solid.makeBox(
                length=box_size,
                width=box_size,
                height=self.length,
                pnt=cq.Vector(-half_box_size, -half_box_size, -self.length),
            )
            for i in range(2):
                if self.end_finishes[i] == "square":
                    self._cq_object = self._cq_object.cut(
                        cutter.translate((0, 0, 2 * i * self.length))
                    )

        # Chamfer the ends
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
            self._cq_object = self._cq_object.intersect(cutter.val())

        # if self.simple:
        #     self._cq_object = self.make_simple_thread()
        # else:
        #     self._cq_object = self.make_thread()

    def make_thread(
        self,
        length: float,
        taper_angle: Optional[float] = None,
        fade_helix: bool = False,
    ):
        """ Create the thread object from basic CadQuery objects
        1- first create all the edges - helical or linear
        2- create either 5 or 6 faces from the edges
        3- create a shell from the faces
        4- create a solid from the shell
        """
        taper = 360 if taper_angle is None else taper_angle

        apex_helix_wires = [
            cq.Workplane("XY")
            .parametricCurve(
                lambda t: self.fade_helix(t, apex=True, vertical_displacement=0)
            )
            .val()
            .translate((0, 0, i * self.apex_width))
            if fade_helix
            else cq.Wire.makeHelix(
                pitch=self.pitch,
                height=length,
                radius=self.apex_radius,
                angle=taper,
                lefthand=not self.right_hand,
            ).translate((0, 0, i * self.apex_width))
            for i in [-0.5, 0.5]
        ]
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
                angle=taper,
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
        thread_shell = cq.Shell.makeShell(thread_faces + end_faces)
        thread_solid = cq.Solid.makeSolid(thread_shell)
        return thread_solid


class IsoThread:
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
    def cq_object(self) -> cq.Solid:
        """ A cadquery Solid thread as defined by class attributes """
        return self._cq_object

    def __init__(
        self,
        major_diameter: float,
        pitch: float,
        length: float,
        external: bool = True,
        hand: Literal["right", "left"] = "right",
        simple: bool = True,
        end_finishes: tuple[
            Literal["raw", "square", "fade", "chamfer"],
            Literal["raw", "square", "fade", "chamfer"],
        ] = ("square", "fade"),
    ):

        self.major_diameter = major_diameter
        self.pitch = pitch
        self.length = length
        self.simple = simple
        self.external = external
        self.thread_angle = 60
        if hand not in ["right", "left"]:
            raise ValueError(f'hand must be one of "right" or "left" not {hand}')
        self.hand = hand
        for finish in end_finishes:
            if not finish in ["raw", "square", "fade", "chamfer"]:
                raise ValueError(
                    f'end_finishes invalid, must be tuple() of "raw, square, taper, or chamfer"'
                )
        self.end_finishes = end_finishes
        apex_radius = self.major_diameter / 2 if external else self.min_radius
        apex_width = self.pitch / 8 if external else self.pitch / 4
        root_radius = self.min_radius if external else self.major_diameter / 2
        root_width = 3 * self.pitch / 4 if external else 7 * self.pitch / 8
        self._cq_object = Thread(
            apex_radius=apex_radius,
            apex_width=apex_width,
            root_radius=root_radius,
            root_width=root_width,
            pitch=self.pitch,
            length=self.length,
            end_finishes=self.end_finishes,
            hand=self.hand,
            simple=self.simple,
        ).cq_object


starttime = timeit.default_timer()
iso_thread = IsoThread(
    major_diameter=4,
    pitch=1,
    length=4,
    external=True,
    end_finishes=("chamfer", "chamfer"),
)
print("The time difference is :", timeit.default_timer() - starttime)

# th = Thread(
#     apex_radius=iso_thread.major_diameter / 2,
#     apex_width=iso_thread.pitch / 8,
#     root_radius=iso_thread.min_radius,
#     root_width=3 * iso_thread.pitch / 4,
#     pitch=iso_thread.pitch,
#     length=iso_thread.length,
# )

print(f"{iso_thread.__dict__=}")

# # res = core.union(cq.Compound.makeCompound([th1, th2]))
t = iso_thread.cq_object
# t = iso_thread.thread_object.make_thread(iso_thread.length, taper=True)
core = cq.Workplane("XY").circle(iso_thread.min_radius).extrude(4)
# fh = cq.Workplane("XY").parametricCurve(lambda t: th.fade_helix(t, th.apex_radius))
# h = cq.Wire.makeHelix(pitch=1, height=5, radius=0, angle=-15)
if "show_object" in locals():
    # show_object(res, name="res")
    # show_object(res2, name="res2")
    # show_object(chamfer, name="chamfer")
    # show_object(th1, name="th1")
    # show_object(th2, name="th2")
    # show_object(core, name="core")
    # show_object(iso_thread_object, name="iso_thread")
    show_object(core, name="core")
    # show_object(h, name="h")
    # show_object(fh, name="fh")
    show_object(t, name="t")

