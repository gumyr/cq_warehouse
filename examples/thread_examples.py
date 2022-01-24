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
from cq_warehouse.thread import (
    IsoThread,
    AcmeThread,
    MetricTrapezoidalThread,
    PlasticBottleThread,
)

MM = 1
IN = 25.4 * MM

ISO_INTERNAL = 0
ISO_EXTERNAL = 1
ACME = 2
METRIC_TRAPEZOIDAL = 3
END_FINISHES = 4
PLASTIC_EXTERNAL = 5
PLASTIC_INTERNAL = 6
example = PLASTIC_EXTERNAL


if example == ISO_INTERNAL:
    """IsoThread Internal Example"""
    starttime = timeit.default_timer()
    iso_internal_thread = IsoThread(
        major_diameter=6 * MM,
        pitch=1 * MM,
        length=4.35 * MM,
        external=False,
        end_finishes=("square", "chamfer"),
        hand="left",
    )
    elapsed_time = timeit.default_timer() - starttime
    print(f"IsoThread internal elapsed time: {elapsed_time:.3f}s")
    iso_internal_core = (
        cq.Workplane("XY")
        .polygon(6, iso_internal_thread.major_diameter * 1.5)
        .circle(iso_internal_thread.major_diameter / 2)
        .extrude(iso_internal_thread.length)
    )
    iso_internal = iso_internal_thread.cq_object.fuse(iso_internal_core.val())
    print(f"{iso_internal.isValid()=}")

    if "show_object" in locals():
        show_object(iso_internal_thread.cq_object, name="iso_internal_thread")
        show_object(iso_internal_core, name="iso_internal_core")
        show_object(iso_internal, name="iso_internal")

elif example == ISO_EXTERNAL:

    """IsoThread External Example"""
    starttime = timeit.default_timer()
    iso_external_thread = IsoThread(
        major_diameter=6 * MM,
        pitch=1 * MM,
        length=10 * MM,
        external=True,
        end_finishes=("fade", "square"),
        hand="left",
    )
    elapsed_time = timeit.default_timer() - starttime

    iso_external_core = (
        cq.Workplane("XY")
        .circle(iso_external_thread.min_radius)
        .extrude(iso_external_thread.length)
    )
    iso_external = iso_external_thread.cq_object.fuse(iso_external_core.val())
    print(f"{iso_external.isValid()=}")

    if "show_object" in locals():
        show_object(iso_external_thread.cq_object, name="iso_external_thread")
        show_object(iso_external_core, name="iso_external_core")
        show_object(iso_external, name="iso_external")

elif example == ACME:

    """AcmeThread Example"""
    starttime = timeit.default_timer()
    acme_thread = AcmeThread(size="1/4", length=1 * IN)
    elapsed_time = timeit.default_timer() - starttime
    print(f"AcmeThread elapsed time: {elapsed_time:.3f}s")
    acme_core = (
        cq.Workplane("XY").circle(acme_thread.root_radius).extrude(acme_thread.length)
    )
    acme = acme_thread.cq_object.fuse(acme_core.val())
    print(f"{acme.isValid()=}")

    if "show_object" in locals():
        show_object(acme_thread.cq_object, name="acme_thread")
        show_object(acme_core, name="acme_core")
        show_object(acme, name="acme")

elif example == METRIC_TRAPEZOIDAL:

    """MetricTrapezoidalThread example"""
    starttime = timeit.default_timer()
    metric_thread = MetricTrapezoidalThread(size="8x1.5", length=20 * MM)
    elapsed_time = timeit.default_timer() - starttime
    print(f"MetricTrapezoidalThread elapsed time: {elapsed_time:.3f}s")
    metric_core = (
        cq.Workplane("XY")
        .circle(metric_thread.root_radius)
        .extrude(metric_thread.length)
    )
    metric = metric_thread.cq_object.fuse(metric_core.val())
    print(f"{metric.isValid()=}")

    if "show_object" in locals():
        show_object(metric_thread.cq_object, name="metric_thread")
        show_object(metric_core, name="metric_core")
        show_object(metric, name="metric")

elif example == END_FINISHES:
    """end_finishes example"""
    end_finishes = [["raw", "fade"], ["square", "chamfer"]]
    end_examples = []
    end_examples_cores = []
    for i in range(2):
        for j in range(2):
            iso_end_thread = IsoThread(
                major_diameter=3 * MM,
                pitch=1 * MM,
                length=4 * MM,
                end_finishes=("square", end_finishes[i][j]),
            )
            end_examples.append(
                iso_end_thread.cq_object.translate(
                    cq.Vector((i - 0.5) * 5, (j - 0.5) * 5, 0)
                )
            )
            end_examples_cores.append(
                cq.Workplane("XY")
                .cylinder(
                    4 * MM, iso_end_thread.min_radius, centered=(True, True, False)
                )
                .translate(cq.Vector((i - 0.5) * 5, (j - 0.5) * 5, 0))
            )

    if "show_object" in locals():
        show_object(end_examples, name="end_examples")
        show_object(end_examples_cores, name="end_examples_cores")

elif example == PLASTIC_EXTERNAL:
    """asymmetric thread"""
    plastic_thread = PlasticBottleThread("M40SP444", external=True)
    # print(plastic_thread.__dict__)

    if "show_object" in locals():
        show_object(plastic_thread.cq_object, name="bottle thread")

elif example == PLASTIC_INTERNAL:
    """asymmetric thread"""
    plastic_thread = PlasticBottleThread("M38SP444", external=False)
    print(plastic_thread.__dict__)

    if "show_object" in locals():
        show_object(plastic_thread.cq_object, name="bottle thread")
