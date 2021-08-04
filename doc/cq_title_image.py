import cadquery as cq
from cq_warehouse.sprocket import Sprocket
from cq_warehouse.drafting import Draft

spkt = Sprocket(num_teeth=16)
title_draft = Draft(font_size=8, label_normal=(0, -1, 1))
title_line = title_draft.extension_line(
    object_edge=[
        (-spkt.outer_radius, 0, spkt.thickness / 2),
        (+spkt.outer_radius, 0, spkt.thickness / 2),
    ],
    offset=-5,
    label="cq_warehouse",
)
if "show_object" in locals():
    show_object(spkt.cq_object, name="sprocket12")
    show_object(title_line, name="title_line")
