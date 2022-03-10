from typing import Literal
import cadquery as cq
from cq_warehouse.fastener import Nut, CounterSunkScrew
from functools import reduce
import cq_warehouse.extensions


class BradTeeNut(Nut):
    """
    size: str
    fastener_type: str
        Hilitchi	Brad Tee Nut
    hand: Literal["right", "left"] = "right"
    simple: bool = True
    """

    fastener_data = {
        "M8-1.25": {
            "Hilitchi:m": "16.5",
            "Hilitchi:s": "11.9/2",
            "Hilitchi:dc": "36.3",
            "Hilitchi:c": "2.4",
            "Hilitchi:bcd": "24",
            "Hilitchi:brad": "M4-0.7",
            "Hilitchi:brad#": "3",
        },
    }

    @property
    def cq_object(self):
        """A cadquery Compound nut as defined by class attributes"""
        brad = CounterSunkScrew(
            size=self.nut_data["brad"],
            length=2 * self.nut_data["c"],
            fastener_type="iso10642",
        )
        return (
            cq.Workplane(self._cq_object)
            .faces(">Z")
            .workplane()
            .polarArray(self.nut_data["bcd"] / 2, 0, 360, self.nut_data["brad#"])
            .clearanceHole(fastener=brad)
            .val()
        )

    def nut_profile(self):
        (dc, s, m, c) = (self.nut_data[p] for p in ["dc", "s", "m", "c"])
        return (
            cq.Workplane("XZ")
            .vLine(m)
            .hLine(dc / 2)
            .vLine(-c)
            .hLineTo(s)
            .vLineTo(0)
            .hLineTo(0)
            .close()
        )

    def nut_plan(self):
        return cq.Workplane("XY").circle(self.nut_data["dc"] / 2)

    def countersink_profile(
        self, fit: Literal["Close", "Normal", "Loose"]
    ) -> cq.Workplane:
        """A enlarged cavity allowing the nut to be countersunk"""
        try:
            clearance_hole_diameter = self.clearance_hole_diameters[fit]
        except KeyError as e:
            raise ValueError(
                f"{fit} invalid, must be one of {list(self.clearance_hole_diameters.keys())}"
            ) from e
        (dc, s, m, c) = (self.nut_data[p] for p in ["dc", "s", "m", "c"])
        clearance = (clearance_hole_diameter - self.thread_diameter) / 2
        print(f"{clearance=}")
        return (
            cq.Workplane("XZ")
            .vLine(m)
            .hLine(dc / 2 + clearance)
            .vLine(-c - clearance)
            .hLineTo(s + clearance)
            .vLineTo(-clearance)
            .hLineTo(0)
            .close()
        )


brad_assembly = cq.Assembly(None, "brad test assembly")
brad = BradTeeNut(size="M8-1.25", fastener_type="Hilitchi", simple=False)
print(brad.cq_object.isValid())
print(brad.nut_thickness)
brad_tee_hole = (
    cq.Workplane("XY")
    .rect(60, 60)
    .extrude(-60)
    .faces(">Z")
    .workplane()
    .clearanceHole(
        fastener=brad, fit="Loose", counterSunk=True, baseAssembly=brad_assembly
    )
)
print(brad_assembly.fastenerLocations(brad))
brad_tee_profile = brad.countersink_profile("Close")
if "show_object" in locals():
    show_object(brad.cq_object, name="brad tee nut")
    show_object(brad_tee_hole, name="brad_tee_hole", options={"alpha": 0.8})
    show_object(brad_tee_profile, name="brad_tee_profile")
    # show_object(brad_assembly, name="brad_assembly")
