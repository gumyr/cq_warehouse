"""

Parametric Thread Examples

name: thread_examples.py
by:   Gumyr
date: November 17th 2021

desc: Examples of the IsoThread, AcmeThread and MetricTrapezoidalThread classes.

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
import cadquery as cq
from cq_warehouse.thread import IsoThread, AcmeThread, MetricTrapezoidalThread

MM = 1
IN = 25.4 * MM

""" IsoThread Example """
starttime = timeit.default_timer()
iso_thread = IsoThread(
    major_diameter=4,
    pitch=1,
    length=4.35,
    external=False,
    end_finishes=("square", "chamfer"),
    hand="left",
    simple=False,
)
elapsed_time = timeit.default_timer() - starttime
print(f"IsoThread elapsed time: {elapsed_time}")
iso = iso_thread.cq_object
iso_core = (
    cq.Workplane("XY")
    .polygon(6, iso_thread.major_diameter * 1.5)
    .circle(iso_thread.major_diameter / 2)
    .extrude(iso_thread.length)
)

""" AcmeThread Example """
starttime = timeit.default_timer()
acme_thread = AcmeThread(
    size="1/4",
    length=1 * IN,
    end_finishes=("raw", "fade"),
    simple=False,
    external=True,
)
elapsed_time = timeit.default_timer() - starttime
print(f"AcmeThread elapsed time: {elapsed_time}")
acme_core = (
    cq.Workplane("XY").circle(acme_thread.root_radius).extrude(acme_thread.length)
)

""" MetricTrapezoidalThread example """
metric_thread = MetricTrapezoidalThread(
    size="8x1.5", length=20 * MM, simple=False, external=True
)
elapsed_time = timeit.default_timer() - starttime
print(f"MetricTrapezoidalThread elapsed time: {elapsed_time}")
metric_core = (
    cq.Workplane("XY").circle(metric_thread.root_radius).extrude(metric_thread.length)
)

if "show_object" in locals():
    show_object(iso_thread.cq_object, name="iso_thread")
    show_object(iso_core, name="iso_core")
    show_object(acme_thread.cq_object, name="acme_thread")
    show_object(acme_core, name="acme_core")
    show_object(metric_thread.cq_object, name="metric_thread")
    show_object(metric_core, name="metric_core")
