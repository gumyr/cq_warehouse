"""

Brad Tee and HeatSet Nuts Example

name: brad_tee_and_heatset_nuts.py
by:   Gumyr
date: February 28th 2022

desc: Example of using the BradTee and HeatSet nuts with pushFastenerLocations()
      method to align holes.

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
import cadquery as cq
from cq_warehouse.fastener import BradTeeNut, CounterSunkScrew, HeatSetNut
import cq_warehouse.extensions

MM = 1

# Create the fasteners used in this example
bradtee_nut = BradTeeNut(size="M8-1.25", fastener_type="Hilitchi", simple=False)
brad = CounterSunkScrew(
    size=bradtee_nut.nut_data["brad_size"],
    length=20 * MM,
    fastener_type="iso10642",
    simple=False,
)
heatset = HeatSetNut(
    size=bradtee_nut.nut_data["brad_size"] + "-Standard",
    fastener_type="McMaster-Carr",
    simple=True,
)
# Create an empty Assembly to hold all of the fasteners
fastener_assembly = cq.Assembly(None, name="plate")

# Create a simple plate with appropriate holes to house all the fasteners
plate_size = (50 * MM, 50 * MM, 20 * MM)
plate = (
    cq.Workplane("XY")
    .box(*plate_size, centered=(True, True, False))
    .faces(">Z")
    .workplane()
    .clearanceHole(fastener=bradtee_nut, baseAssembly=fastener_assembly)
    .polarArray(
        bradtee_nut.nut_data["bcd"] / 2, 0, 360, bradtee_nut.nut_data["brad_num"]
    )
    .clearanceHole(fastener=brad, baseAssembly=fastener_assembly)
    # Place HeatSetNuts for the brads on the bottom of the plate
    .pushFastenerLocations(
        fastener=brad,
        baseAssembly=fastener_assembly,
        offset=-plate_size[2],
        flip=True,
    )
    .insertHole(fastener=heatset, baseAssembly=fastener_assembly)
)
print(fastener_assembly.fastenerQuantities())
print(HeatSetNut.sizes("McMaster-Carr"))

if "show_object" in locals():
    show_object(plate, name="plate", options={"alpha": 0.8})
    show_object(fastener_assembly, name="fastener_assembly")
