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
import cadquery as cq
from sprocket_and_chain import Sprocket, Chain

MM = 1
INCH = 25.4*MM

#
# Create a set of sprockets for these examples
print("Creating sprockets...")
spkt0 = Sprocket(
    num_teeth=32,
    clearance = 0.05,
    bolt_circle_diameter = 104*MM,
    num_mount_bolts = 4,
    mount_bolt_diameter = 10*MM,
    bore_diameter = 80*MM
)
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
spkt0.cq_object.exportSvg('sprocket32.svg')
spkt1.cq_object.exportSvg('sprocket10.svg')
spkt2.cq_object.exportSvg('sprocket16.svg')
#
# Create a set of example transmissions
print("Simple two sprocket example...")
two_sprocket_chain = Chain(
    spkt_teeth=[32,32],
    positive_chain_wrap=[True,True],
    spkt_locations=[ cq.Vector(-5*INCH,0,0), cq.Vector(+5*INCH,0,0) ],
)
two_sprocket_transmission = two_sprocket_chain.assemble_chain_transmission(
    spkts = [spkt0.cq_object,spkt0.cq_object]
)
two_sprocket_transmission.save('two_sprocket.step')

print("Bicycle derailuer example...")
derailleur_chain = Chain(
    spkt_teeth=[32,10,10,16],
    positive_chain_wrap=[True,True,False,True],
    spkt_locations=[
        (0,158.9*MM,50*MM),
        (+190*MM,0,50*MM),
        (+190*MM,78.9*MM,50*MM),
        (+205*MM,158.9*MM,50*MM)
    ]
)
derailleur_transmission = derailleur_chain.assemble_chain_transmission(
    spkts = [spkt0.cq_object,spkt1.cq_object,spkt1.cq_object,spkt2.cq_object]
)
derailleur_transmission.save('deraileur.step')

print("Complex five sprocket example showing all possible sprocket to sprocket paths...")
five_sprocket_chain = Chain(
    spkt_teeth=[32,10,10,10,16],
    positive_chain_wrap=[True,True,False,False,True],
    spkt_locations=[
        cq.Vector(0,158.9*MM,25*MM),
        cq.Vector(+190*MM,-50*MM,25*MM),
        cq.Vector(+140*MM,20*MM,25*MM),
        cq.Vector(+120*MM,90*MM,25*MM),
        cq.Vector(+205*MM,158.9*MM,25*MM)
    ]
)
five_sprocket_transmission = five_sprocket_chain.assemble_chain_transmission(
    spkts = [spkt0.cq_object,spkt1.cq_object,spkt1.cq_object,spkt1.cq_object,spkt2.cq_object]
)
five_sprocket_transmission.save('five_sprocket.step')

print("Chains moved and rotated...")
relocated_transmission = Chain(
    spkt_teeth = [32,32],
    positive_chain_wrap = [True,True],
    spkt_locations = [ (-5*INCH,0), (+5*INCH,0) ]
)
relocated_transmission = relocated_transmission.assemble_chain_transmission(
    spkts = [spkt0.cq_object,spkt0.cq_object]
).rotate(axis=(0,1,1),angle=45).translate((20,20,20))
relocated_transmission.save('planeXZ.step')

# If running from within the cq-editor, show the assemblies
if "show_object" in locals():
    show_object(two_sprocket_transmission,name="two_sprocket_transmission")
    show_object(five_sprocket_transmission,name="five_sprocket_transmission")
    show_object(derailleur_transmission,name="derailleur_transmission")
    show_object(relocated_transmission,name="relocated_transmission")
    show_object(spkt0.cq_object,name="sprocket32")