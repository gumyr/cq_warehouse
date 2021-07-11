"""

Parametric Sprockets and Chains Examples

name: sprocket_and_chain_examples.py
by:   Gumyr
date: June 28th 2021

desc:

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
from math import sin, cos, pi, radians
import cadquery as cq
from sprocket_and_chain import Sprocket, Chain
from draft_objects import Draft

MM = 1
INCH = 25.4*MM

MAKE_SPROCKET = False
MAKE_CHAIN = True

small_draft = Draft(
    default_font_size = 3,
    default_arrow_diameter = 0.5,
    default_arrow_length = 1.5
)
large_draft = Draft(
    default_font_size = 6,
    default_arrow_diameter = 3,
    default_arrow_length = 4.5
)
#
# Create a set of sprockets for these examples
print("Creating sprockets...")
spkt0 = Sprocket(
    num_teeth=32,
    clearance = 0.1*MM,
    bolt_circle_diameter = 104*MM,
    num_mount_bolts = 4,
    mount_bolt_diameter = 10*MM,
    bore_diameter = 80*MM
)
if MAKE_CHAIN:
    spkt1 = Sprocket(
        num_teeth=10,
        clearance = 0.05,
        num_mount_bolts = 0,
        bore_diameter = 5*MM
    )
    spkt2 = Sprocket(
        num_teeth=16,
        clearance = 0.05,
        num_mount_bolts = 0,
        bore_diameter = 30*MM
    )

if MAKE_SPROCKET:
    # Sprocket Labels
    bore_line = large_draft.dimension_line(label = "bore", start = (-spkt0.bore_diameter/2,0,0), end = (spkt0.bore_diameter/2,0,0))
    bcd_line = large_draft.dimension_line(label = "bcd", start = (0,0,spkt0.thickness/2), end = (spkt0.bolt_circle_diameter*cos(-pi/6)/2,spkt0.bolt_circle_diameter*sin(-pi/6)/2,spkt0.thickness/2))
    bolt_line = small_draft.dimension_line(label = "bolt", start = (spkt0.bolt_circle_diameter/2-10/2,0,0), end = (spkt0.bolt_circle_diameter/2+10/2,0,0))
    bolt_circle = cq.Wire.makeCircle(spkt0.bolt_circle_diameter/2,cq.Vector(0,0,0),cq.Vector(0,0,1)).translate((0,0,spkt0.thickness/2))
    half_chain_pitch_angle = 180/spkt0.num_teeth
    roller_center = cq.Vector(spkt0.pitch_radius,0,0).rotateZ(-half_chain_pitch_angle)
    half_roller_angle = 180*spkt0.roller_diameter/spkt0.pitch_circumference
    roller_circle = cq.Wire.makeCircle(spkt0.roller_diameter/2,roller_center,cq.Vector(0,0,1))
    roller_line = small_draft.dimension_line(label = "roller", font_size = 2, start = roller_center.rotateZ(-half_roller_angle), end = roller_center.rotateZ(half_roller_angle))
    chain_pitch_line = small_draft.dimension_line(
        label = "pitch",
        start = roller_center.rotateZ(-4*half_chain_pitch_angle)+cq.Vector(0,0,spkt0.thickness/2),
        end = roller_center.rotateZ(-2*half_chain_pitch_angle)+cq.Vector(0,0,spkt0.thickness/2)
    )

if MAKE_CHAIN:
    #
    # Create an example transmission
    print("Complex five sprocket example showing all possible sprocket to sprocket paths...")
    five_sprocket_chain = Chain(
        spkt_teeth=[32,10,10,10,16],
        positive_chain_wrap=[True,True,False,False,True],
        spkt_locations=[
            cq.Vector(0,158.9*MM,0),
            cq.Vector(+190*MM,-50*MM,0),
            cq.Vector(+140*MM,20*MM,0),
            cq.Vector(+120*MM,90*MM,0),
            cq.Vector(+205*MM,158.9*MM,0)
        ]
    )
    five_sprocket_transmission = five_sprocket_chain.assemble_chain_transmission(
        spkts = [spkt0.cq_object,spkt1.cq_object,spkt1.cq_object,spkt1.cq_object,spkt2.cq_object]
    )
    chain_direction = []
    for s in range(5):
        r = Sprocket.sprocket_pitch_radius(five_sprocket_chain.spkt_teeth[s],five_sprocket_chain.chain_pitch) + 12.5*MM
        entry_a = radians(five_sprocket_chain.chain_angles[s][0]+90)
        exit_a = radians(five_sprocket_chain.chain_angles[s][1]+90)
        mid_a = entry_a + ((entry_a-exit_a)/2)%360 if five_sprocket_chain.positive_chain_wrap[s] else entry_a - ((entry_a-exit_a)/2)%360
        chain_direction.append(
            large_draft.dimension_line(
                label = str(five_sprocket_chain.positive_chain_wrap[s]),
                path = cq.Edge.makeThreePointArc(
                    cq.Vector(r*cos(entry_a),r*sin(entry_a),0) + five_sprocket_chain.spkt_locations[s],
                    cq.Vector(r*cos(mid_a),r*sin(mid_a),0) + five_sprocket_chain.spkt_locations[s],
                    cq.Vector(r*cos(exit_a),r*sin(exit_a),0) + five_sprocket_chain.spkt_locations[s],
                ),
                arrow_heads = [False,True]
            )
        )

    print(five_sprocket_chain.chain_angles)

# If running from within the cq-editor, show the assemblies
if "show_object" in locals():
    if MAKE_SPROCKET:
        show_object(spkt0.cq_object,name="sprocket32")
        show_object(bore_line,name="bore_line")
        show_object(bcd_line,name="bcd_line")
        show_object(bolt_line,name="bolt_line")
        show_object(bolt_circle,name="bolt_circle")
        show_object(roller_circle,name="roller_circle")
        show_object(roller_line,name="roller_line")
        show_object(chain_pitch_line,name="chain_pitch_line")
    if MAKE_CHAIN:
        show_object(five_sprocket_transmission,name="five_sprocket_transmission")
        show_object(chain_direction[0],name="chain_direction0")
        show_object(chain_direction[1],name="chain_direction1")
        show_object(chain_direction[2],name="chain_direction2")
        show_object(chain_direction[3],name="chain_direction3")
        show_object(chain_direction[4],name="chain_direction4")