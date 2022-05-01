"""

Cadquery GridFinity Implementation

name: gridfinity.py
by:   Jern
date: 2022-04-13

desc:

    Reimplementation of basic gridfinity grid design by Zack Freedman.

license:

    Copyright 2022 Jern

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
import cadquery as cq
import math
from cadquery import exporters

MM = 1


class WeightedGrid:
    """GridFinity Weighted Grid

    _extended_summary_

    Args:
        x_grid_number (int, optional): x grid count. Defaults to 3.
        y_grid_number (int, optional): y grid count. Defaults to 3.
        disable_mholes (bool, optional): disable magnet/bolt holes, includes bolt bore,
            counter bore and countersink. Defaults to False.
        disable_weights (bool, optional): disable tire weight cutouts,
            DOES NOT REDUCE THICKNESS OF PART. Defaults to False
    """

    box_wd = 42 * MM
    box_sub_wd = 42.71 * MM  # x,y width of box to subtract
    c_rad = 4 * MM
    grid_ht = 5 * MM  # overall grid height

    ### dimensions for weighted baseplate with magnet/bolt holes
    csk_hole_chm_ht = (
        3.54 / math.sqrt(2) * MM
    )  # countersink hole height derived from hypoten
    bolt_hole_d = 3.5 * MM  # bolt hole diameter
    bolt_hole_ht = 2.5 * MM  # bolt hole height
    cbore_hole_ht = 2.4 * MM  # counterbore hole height
    cbore_hole_d = 6.5 * MM  # counterbore hole diameter
    mag_dist0 = (
        26 / 2
    ) * MM  # distance from holes to zero-axis (26mm between holes total)

    weight_sq = 21.4 * MM  # weight square cutout x,y dim
    weight_ht = 5.0 * MM  # weight square cutout z depth

    weight_tab_d = 8.5 * MM  # weight tab radius
    weight_tab_slotw = (
        38.37 - weight_tab_d
    ) * MM  # weight tab slot from center to center of tab_d
    weight_tab_ht = 2.0 * MM  # depth of tab slot cut
    weight_base_exht = (
        7.4 * MM  # extra height of weighted base, total reference is 12.4mm
    )

    b_chm_ht = 0.985 / math.sqrt(2) * MM  # base chamfer height
    strt_ht = 1.8 * MM  # straight wall height
    t_chm_ht = grid_ht - b_chm_ht - strt_ht  # top chamfer height

    @property
    def cq_object(self) -> cq.Workplane:
        """cadquery object"""
        return self._cq_object

    @property
    def filename_suffix(self) -> str:
        """filename suffix"""
        return self.fname_sfx

    def __init__(
        self,
        x_grid_number: int = 3,
        y_grid_number: int = 3,
        disable_mholes: bool = False,
        # disable magnet/bolt holes
        # ^includes bolt bore, counter bore and countersink
        disable_weights: bool = False  # disable tire weight cutouts
        # ^DOES NOT REDUCE THICKNESS OF PART
    ):
        self.x_grid_number = x_grid_number
        self.y_grid_number = y_grid_number
        self.disable_mholes = disable_mholes
        self.disable_weights = disable_weights
        # create 2D sketch with rounded corners
        s3a = (
            cq.Sketch()
            .rect(WeightedGrid.box_sub_wd, WeightedGrid.box_sub_wd)
            .vertices()
            .fillet(WeightedGrid.c_rad)
        )

        # take s3a sketch and create the tool that is later used to subtract grid positions
        f2 = (
            cq.Workplane("XY")
            .placeSketch(s3a)
            .extrude(WeightedGrid.t_chm_ht * math.sqrt(2), taper=45)
            .faces(">Z")
            .wires()
            .toPending()
            .extrude(WeightedGrid.strt_ht)
            .faces(">Z")
            .wires()
            .toPending()
            .extrude(WeightedGrid.b_chm_ht * math.sqrt(2), taper=45)
            .rotate((0, 0, 0), (1, 0, 0), 180)
            .translate((0, 0, WeightedGrid.grid_ht))
        )

        # pts is the locations of each grid position
        pts = [
            (x * WeightedGrid.box_wd, y * WeightedGrid.box_wd)
            for x in range(0, x_grid_number)
            for y in range(0, y_grid_number)
        ]

        # preunion all the individual tools for later cutting
        f3 = (
            cq.Workplane("XY")
            .pushPoints(pts)
            .eachpoint(lambda loc: f2.val().moved(loc), combine="a", clean=True)
        )

        # define x,y positions of the exterior walls
        wall_xpos = (WeightedGrid.box_wd) * (x_grid_number - 1) / 2
        wall_ypos = (WeightedGrid.box_wd) * (y_grid_number - 1) / 2

        # create the big baseplate, and finally subtract the grid positions
        f5 = (
            cq.Workplane("XY")
            .box(
                x_grid_number * WeightedGrid.box_wd,
                y_grid_number * WeightedGrid.box_wd,
                WeightedGrid.grid_ht,
            )
            .edges("|Z")
            .fillet(WeightedGrid.c_rad)
            .translate((wall_xpos, wall_ypos, WeightedGrid.grid_ht / 2))
            .faces(">Z")
            .cut(f3)
        )

        # hole_pts used to locate hole positions for magnet/bolt holes
        hole_pts = [
            (
                (x * WeightedGrid.box_wd + WeightedGrid.mag_dist0 * (1 - 2 * i)),
                (y * WeightedGrid.box_wd + WeightedGrid.mag_dist0 * (1 - 2 * j)),
            )
            for x in range(0, x_grid_number)
            for y in range(0, y_grid_number)
            for i in [0, 1]
            for j in [0, 1]
        ]

        # create slots for weights
        s6 = (
            cq.Sketch()
            .slot(
                WeightedGrid.weight_tab_slotw,
                WeightedGrid.weight_tab_d,
            )
            .slot(
                WeightedGrid.weight_tab_slotw,
                WeightedGrid.weight_tab_d,
                angle=90,
            )
            .clean()
        )

        f6 = (  # create main bottom plate that is ONLY used for extra height in this version of baseplates
            cq.Workplane("XY")
            .box(
                x_grid_number * WeightedGrid.box_wd,
                y_grid_number * WeightedGrid.box_wd,
                WeightedGrid.weight_base_exht,
            )
            .edges("|Z")
            .fillet(WeightedGrid.c_rad)
            .translate((wall_xpos, wall_ypos, -WeightedGrid.weight_base_exht / 2))
        )
        # copy workplane
        TopWorkplane_f6 = cq.Workplane().copyWorkplane(f6)

        f6_bolt_holes = (  # create features for bolt holes
            TopWorkplane_f6.pushPoints(hole_pts)
            .circle(WeightedGrid.bolt_hole_d / 2)
            .extrude(-WeightedGrid.bolt_hole_ht - WeightedGrid.cbore_hole_ht)
            .faces(">Z")
            .workplane()
            .pushPoints(hole_pts)
            .circle(WeightedGrid.cbore_hole_d / 2)
            .extrude(-WeightedGrid.cbore_hole_ht)
            .faces("<Z")
            .workplane(invert=True)
            .pushPoints(hole_pts)
            .circle(WeightedGrid.bolt_hole_d / 2)
            .extrude(-WeightedGrid.csk_hole_chm_ht * math.sqrt(2), taper=-45)
        )

        # copy workplane
        BotWorkplane_f6 = cq.Workplane().copyWorkplane(
            f6.faces("<Z").workplane(invert=True)
        )

        f6_weights = (  # create features for weight slots
            BotWorkplane_f6.pushPoints(pts)
            .placeSketch(s6)
            .extrude(WeightedGrid.weight_tab_ht)
            .pushPoints(pts)
            .rect(WeightedGrid.weight_sq, WeightedGrid.weight_sq)
            .extrude(WeightedGrid.weight_ht)
        )

        self.fname_sfx = ""  # filename suffix

        if not disable_mholes:
            f6 = f6.cut(f6_bolt_holes)  # only cut mholes if not disabled
        else:
            self.fname_sfx += "_nohole"  # filename suffix
        if not disable_weights:
            f6 = f6.cut(f6_weights)  # only cut magnet slots if not disabled
        else:
            self.fname_sfx += "_nowt"  # filename suffix

        # f5 is the final part
        self._cq_object = f5.union(f6)


"""Examples - eventually in its own file"""
sample_grid = WeightedGrid()

show_object(sample_grid.cq_object, options={"alpha": 0.10, "color": (65, 94, 55)})
# show_object(f3,options={"alpha":0.10, "color": (165, 94, 55)})


filename = (
    "weighted grid_"
    + str(sample_grid.x_grid_number)
    + "x"
    + str(sample_grid.y_grid_number)
    + sample_grid.filename_suffix
    + ".stl"
)
log(filename)
exporters.export(sample_grid.cq_object, filename, tolerance=0.99, angularTolerance=0.4)
