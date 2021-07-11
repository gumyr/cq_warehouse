"""

Parametric Sprockets Examples

name: sprocket_examples.py
by:   Gumyr
date: July 11th 2021

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
from sprocket import Sprocket

MM = 1

#
# Create a set of sprockets for these examples
print("Creating sprockets...")
sprocket32 = Sprocket(
    num_teeth=32,
    clearance = 0.05,
    bolt_circle_diameter = 104*MM,
    num_mount_bolts = 4,
    mount_bolt_diameter = 10*MM,
    bore_diameter = 80*MM
)
sprocket10 = Sprocket(
    num_teeth=10,
    clearance = 0.05,
    num_mount_bolts = 0,
    bore_diameter = 5*MM
)
sprocket16 = Sprocket(
    num_teeth=16,
    num_mount_bolts = 6,
    bolt_circle_diameter = 44*MM,
    mount_bolt_diameter = 5*MM,
    bore_diameter = 0
)
cq.exporters.export(sprocket32.cq_object,'sprocket32.step')
cq.exporters.export(sprocket10.cq_object,'sprocket10.step')
cq.exporters.export(sprocket16.cq_object,'sprocket16.step')

# If running from within the cq-editor, show the sprockets
if "show_object" in locals():
    show_object(sprocket32.cq_object,name="sprocket32")
    show_object(sprocket10.cq_object,name="sprocket10")
    show_object(sprocket16.cq_object,name="sprocket16")