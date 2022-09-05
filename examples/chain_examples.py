"""

Parametric Chains Examples

name: chain_examples.py
by:   Gumyr
date: July 11th 2021

desc: Examples of building chains and entire transmissions

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
from enum import Enum, auto
import cadquery as cq
from cadquery import Vector
from cq_warehouse.chain import *
from cq_warehouse.sprocket import *

MM = 1
INCH = 25.4 * MM


class TestCases(Enum):
    TWO_SPROCKETS = auto()
    TWO_SPROCKETS_ON_YZ = auto()
    BICYCLE_DERAILUER = auto()
    FIVE_SPROCKET = auto()
    TRANSLATED_AND_ROTATED = auto()
    OBLIQUE_PLANE = auto()


test_case = TestCases.OBLIQUE_PLANE

#
# Create a set of sprockets for these examples
print("Creating sprockets...")
spkt32 = Sprocket(
    num_teeth=32,
    clearance=0.05,
    bolt_circle_diameter=104 * MM,
    num_mount_bolts=4,
    mount_bolt_diameter=10 * MM,
    bore_diameter=80 * MM,
)
spkt10 = Sprocket(num_teeth=10, clearance=0.05, num_mount_bolts=0, bore_diameter=5 * MM)
spkt16 = Sprocket(
    num_teeth=16, clearance=0.05, num_mount_bolts=0, bore_diameter=30 * MM
)

if test_case == TestCases.TWO_SPROCKETS:
    #
    # Create a set of example transmissions
    print("Simple two sprocket example...")
    two_sprocket_chain = Chain(
        spkt_teeth=[32, 32],
        positive_chain_wrap=[True, True],
        spkt_locations=[Vector(-5 * INCH, 0, 0), Vector(+5 * INCH, 0, 0)],
    )
    sprocket_transmission = two_sprocket_chain.assemble_chain_transmission(
        spkts=[spkt32, spkt32]
    )

elif test_case == TestCases.TWO_SPROCKETS_ON_YZ:
    #
    # Create a set of example transmissions
    print("Two sprockets on YZ plane example...")
    spkt32_y = spkt32.rotate((0, 0, 0), (0, 1, 0), 90)
    two_sprocket_chain = Chain(
        spkt_teeth=[32, 32],
        positive_chain_wrap=[True, True],
        spkt_locations=[
            Vector(-50 * MM, -5 * INCH, 20 * MM),
            Vector(-50 * MM, +5 * INCH, 20 * MM),
        ],
        spkt_normal=(1, 0, 0),
    )
    sprocket_transmission = two_sprocket_chain.assemble_chain_transmission(
        spkts=[spkt32_y, spkt32_y]
    )
    # sprocket_transmission.save("two_sprocket.step")

elif test_case == TestCases.BICYCLE_DERAILUER:

    print("Bicycle derailuer example...")
    derailleur_chain = Chain(
        spkt_teeth=[32, 10, 10, 16],
        positive_chain_wrap=[True, True, False, True],
        spkt_locations=[
            (0, 158.9 * MM, 50 * MM),
            (+190 * MM, 0, 50 * MM),
            (+190 * MM, 78.9 * MM, 50 * MM),
            (+205 * MM, 158.9 * MM, 50 * MM),
        ],
    )
    sprocket_transmission = derailleur_chain.assemble_chain_transmission(
        spkts=[spkt32, spkt10, spkt10, spkt16]
    )
    # sprocket_transmission.save("deraileur.step")

elif test_case == TestCases.OBLIQUE_PLANE:
    print("Chain on oblique plane example...")
    derailleur_chain = Chain(
        spkt_teeth=[32, 10, 16],
        positive_chain_wrap=[True, True, True],
        spkt_locations=[
            (-50 * MM, 20 * MM, 10 * MM),
            (190 * MM, -30 * MM, -150 * MM),
            (55 * MM, 10 * MM, 40 * MM),
        ],
    )
    # Align the sprockets to the oblique plane defined by the spkt locations
    spkts_aligned = [
        s._apply_transform(derailleur_chain.chain_plane.rG.wrapped.Trsf())
        for s in [spkt32, spkt10, spkt16]
    ]
    sprocket_transmission = derailleur_chain.assemble_chain_transmission(
        spkts=spkts_aligned
    )


elif test_case == TestCases.FIVE_SPROCKET:
    print(
        "Complex five sprocket example showing all possible sprocket to sprocket paths..."
    )
    five_sprocket_chain = Chain(
        spkt_teeth=[32, 10, 10, 10, 16],
        positive_chain_wrap=[True, True, False, False, True],
        spkt_locations=[
            Vector(0, 158.9 * MM, 25 * MM),
            Vector(+190 * MM, -50 * MM, 25 * MM),
            Vector(+140 * MM, 20 * MM, 25 * MM),
            Vector(+120 * MM, 90 * MM, 25 * MM),
            Vector(+205 * MM, 158.9 * MM, 25 * MM),
        ],
    )
    sprocket_transmission = five_sprocket_chain.assemble_chain_transmission(
        spkts=[spkt32, spkt10, spkt10, spkt10, spkt16]
    )
    # sprocket_transmission.save("five_sprocket.step")

elif test_case == TestCases.TRANSLATED_AND_ROTATED:

    print("Chains translated and rotated...")
    two_sprocket_chain = Chain(
        spkt_teeth=[32, 32],
        positive_chain_wrap=[True, True],
        spkt_locations=[(-5 * INCH, 0), (+5 * INCH, 0)],
    )
    sprocket_transmission = (
        two_sprocket_chain.assemble_chain_transmission(spkts=[spkt32, spkt32])
        .rotate(axis=(0, 1, 1), angle=45)
        .translate((20, 20, 20))
    )
    # sprocket_transmission.save("planeXZ.step")

# If running from within the cq-editor, show the assemblies
if "show_object" in locals():
    show_object(sprocket_transmission, name="sprocket_transmission")
