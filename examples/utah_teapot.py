"""

Utah Teapot Example

name: teapot.py
by:   Gumyr
date: June 21st 2022

desc: A example of creating a complex non-planar object with core CadQuery and
      cq_warehouse.extensions.

      The teapot consists of:
      - the pot created by revolving a sketch of the pot's profile
      - the handle created by lofting a set of ellipses
      - the spout created by lofting a set of ellipses
      - the lid created by revolving a sketch of the lid's profile

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
from math import sin, pi
import cadquery as cq
import cq_warehouse.extensions

# Define the thickness of the teapot walls
teapot_thickness = 0.3

"""
Create the main body of the teapot as a solid (not hollow) object.
Locations of the handle attachment points will be extracted from
this shape and it will be used to refine the spout.
"""
# Note: the "b@1" which is an extension that allows a spline
# to use positions on a tagged edge or wire.
pot_profile = (
    cq.Sketch()
    .segment((0, 0.5), (11, 0.5), tag="b")
    .spline("b@1", (15, 2), (13, 20), tag="s")
    .segment((13, 20), (0, 20))
    .close()
    .assemble()
)
pot_solid = cq.Workplane("XZ").placeSketch(pot_profile).revolve()

"""
Create the lid of the teapot from a revolved sketch
"""
lid_profile = (
    cq.Sketch()
    .segment((0, 20), (13, 20))
    .segment((13, 20 + teapot_thickness), tag="b")
    .spline("b@1", (2, 24), (4, 25), (0, 26), tangents=[(-1, 0.3), (-1, 0.1)])
    .close()
    .assemble()
)
lid = (
    cq.Workplane("XZ")
    .placeSketch(lid_profile)
    .revolve()
    .faces("<Z")
    .shell(-teapot_thickness)
    .edges(cq.selectors.RadiusNthSelector(1))
    .fillet(teapot_thickness / 3)
)

"""
Create the handle by creating a series of wires and lofting them.
The handle contacts the pot in two locations and form two non-planar
wires. These wires are created by projecting ellipses onto the pot
(projection is from cq_warehouse.extensions).
"""
handle_bottom_profile = (
    cq.Wire.makeEllipse(
        1.5,
        1.0,
        center=cq.Vector(20, 0, 6),
        normal=cq.Vector(-1, 0, 0),
        xDir=cq.Vector(0, 1, 0),
    )
).projectToShape(pot_solid.val(), direction=(-1, 0, 0))[0]
# Note: projectToShape is from cq_warehouse.extensions
handle_top_profile = (
    cq.Wire.makeEllipse(
        1.5,
        1.0,
        center=cq.Vector(20, 0, 18),
        normal=cq.Vector(-1, 0, 0),
        xDir=cq.Vector(0, 1, 0),
    )
).projectToShape(pot_solid.val(), direction=(-1, 0, 0))[0]

# Create a spline to define the path of the handle
handle_path = cq.Edge.makeSpline(
    [
        handle_bottom_profile.Center(),
        cq.Vector(24, 0, 8),
        cq.Vector(26, 0, 16),
        cq.Vector(21, 0, 18),
        handle_top_profile.Center(),
    ]
)
# The handle width smoothly transitions following 180 degrees of a sin curve
handle_profiles = [
    cq.Wire.makeEllipse(
        1.5 + 1.0 * sin(pi * t / 20),
        1.0,
        center=handle_path.positionAt(t / 20),
        normal=handle_path.tangentAt(t / 20),
        xDir=cq.Vector(0, 1, 0),
    )
    for t in range(2, 19)
]
handle_profiles = [handle_bottom_profile] + handle_profiles + [handle_top_profile]
handle = cq.Solid.makeLoft(handle_profiles)

"""
Create the spout by creating a series of wires and lofting them.
The spout can't be created in the exact same way as the handle
in that lofting with the non-planar contact wire causes OCCT to
fail in creation of the loft. The alternative method used here
is to create a spout that starts within the pot and then use
the pot to remove the extra material.

The hole in the pot at the spout is created by cutting a shape
from the hollowed out pot.
"""
# Define the sizes of the spout on both ends
spout_contact_width = 4
spout_contact_height = 3
spout_tip_width = 0.5
spout_tip_height = 1.25
spout_contact_center_elevation = 8

spout_origin = cq.Vector(-14, 0, spout_contact_center_elevation)
# spout_contact_profile = (
#     cq.Wire.makeEllipse(
#         spout_contact_width,
#         spout_contact_height,
#         center=cq.Vector(-20, 0, spout_contact_center_elevation),
#         normal=cq.Vector(1, 0, 0),
#         xDir=cq.Vector(0, 1, 0),
#     )
# ).projectToShape(pot_solid.val(), direction=(1, 0, 0))[0]
spout_path = cq.Edge.makeSpline(
    [
        spout_origin,
        cq.Vector(-24, 0, 10),
        cq.Vector(-26, 0, 13),
        cq.Vector(-31, 0, 22),
    ],
    [
        cq.Vector(-1, 0, 0),
        cq.Vector(-0.75, 0, 0.750),
    ],
)
spout_profiles = [
    cq.Wire.makeEllipse(
        spout_contact_width
        - (spout_contact_width - spout_tip_width) * (sin((pi / 4) * t / 20)),
        spout_contact_height
        - (spout_contact_height - spout_tip_height) * (sin((pi / 4) * t / 20)),
        center=spout_path.positionAt(t / 20),
        normal=spout_path.tangentAt(t / 20),
        xDir=cq.Vector(0, -1, 0),
    )
    for t in range(0, 21)
]
spout = (
    cq.Workplane(
        cq.Solid.makeLoft(spout_profiles).intersect(
            cq.Solid.makeBox(100, 100, 20.5, pnt=cq.Vector(-50, -50, 0))
        )
    )
    .faces("%Plane")
    .shell(-0.5)
    .cut(pot_solid)
)
# Create an object that will be used to cut out a hole. By intersecting
# the extruded ellipse with the pot body, this ensures only the pot will
# be cut by this shape.
spout_hole = (
    cq.Workplane("YZ")
    .center(0, spout_origin.z)
    .ellipse(
        spout_contact_width - 3 * teapot_thickness,
        spout_contact_height - 3 * teapot_thickness,
    )
    .extrude(-100)
    .intersect(pot_solid)
)

"""
Finish creation of the pot by hollowing it out, attaching the spout and handle
and filleting some of the edges.  Note that the edges at the intersection of the
spout and handles should be filleted (but are not) as it is very difficult to
select these edges and only these edges. Selection of the all the spout contact
edges results in the filleting creating an invalid shape.
"""
hollow_pot = (
    pot_solid.faces(">Z")
    .shell(-teapot_thickness)
    .union(spout)
    .union(handle)
    .faces(">Z or >Z[2]")
    .edges()
    .fillet(teapot_thickness / 3)
    .faces("<Z")
    .workplane()
    # Add a foot on the bottom
    .circle(11)
    .circle(10)
    .extrude(0.5)
    # Connect the pot and spout with a hole
    .cut(spout_hole)
)

# Display the teapot
if "show_object" in locals():
    show_object(hollow_pot, options={"color": (242, 175, 255)}, name="teapot body")
    show_object(lid, options={"color": (242, 175, 255)}, name="teapot lid")
