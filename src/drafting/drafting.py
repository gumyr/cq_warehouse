"""

Dimension lines for documentation of cadquery designs

name: dimension_line.py
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
from collections import defaultdict
from math import sqrt, cos, sin, pi
from typing import overload, Union, Tuple
from numpy import arange
import cadquery as cq
# import cProfile
# import pstats

VectorLike = Union[Tuple[float, float], Tuple[float, float, float], cq.Vector]

class Draft:
    """
    Create 3D engineering dimension lines for documenting cadquery designs

    The class stores the style descriptor for the methods

    Methods
    -------
    dimension_line - 2 points
    dimension_line - path
    angular_dimension
    label - target point, label point

    """
    def __init__(self,
        default_font_size: float = None,
        default_color: cq.Color = None,
        default_arrow_diameter: float = None,
        default_arrow_length: float = None,
        ):
        self.font_size = default_font_size if default_font_size is not None else 8
        self.color = default_color if default_color is not None else cq.Color(0.25,0.25,0.25)
        self.arrow_diameter = default_arrow_diameter if default_arrow_diameter is not None else 1
        self.arrow_length = default_arrow_length if default_arrow_length is not None else 3

    def dimension_line(self,
        label:str,
        font_size:float = None,
        label_normal:VectorLike = None,
        arrow_heads:tuple[bool,bool] = None,
        start:VectorLike = None,
        end:VectorLike = None,
        path:Union[cq.Wire,cq.Edge] = None
        ) -> cq.Workplane:
        """ Create a 3D engineering dimension line for documenting CAD designs """

        def arrow_head(
            path:Union[cq.Edge,cq.Wire],
            tip_pos:float,
            tail_pos:float
            ) -> cq.Solid:

            radius = self.arrow_diameter/2
            """ Create an arrow head which follows the provided path """
            arrow_tip = cq.Wire.assembleEdges([
                cq.Edge.makeCircle(
                    radius=0.0001,
                    pnt=path.positionAt(tip_pos),
                    dir=path.tangentAt(tip_pos)
                )
            ])
            arrow_mid = cq.Wire.assembleEdges([
                cq.Edge.makeCircle(
                    radius=0.4*radius,
                    pnt=path.positionAt((tail_pos+tip_pos)/2),
                    dir=path.tangentAt((tail_pos+tip_pos)/2))
            ])
            arrow_tail = cq.Wire.assembleEdges([
                cq.Edge.makeCircle(
                    radius=radius,
                    pnt=path.positionAt(tail_pos),
                    dir=path.tangentAt(tail_pos)
                )
            ])
            return cq.Solid.makeLoft([arrow_tip,arrow_mid,arrow_tail])

        def line_segment(path:Union[cq.Edge,cq.Wire],tip_pos:float,tail_pos:float) -> cq.Workplane:
            """ Create a sub path between tip and tail (inclusive) """
            sub_path = cq.Edge.makeSpline(
                listOfVector=[
                    path.positionAt(t)
                    for t in arange(tip_pos,tail_pos+0.00001,(tail_pos-tip_pos)/16)
                ],
                tangents=[ path.tangentAt(t) for t in [tip_pos,tail_pos] ]
            )
            return sub_path

        # Parse arguments
        if path is None:
            if start is None or end is None:
                raise ValueError("Either a path or start and end points must be provided")
            line_path = cq.Wire.assembleEdges([cq.Edge.makeLine(cq.Vector(start),cq.Vector(end))])
        else:
            line_path = cq.Wire.assembleEdges([path])
        label_size = self.font_size if font_size is None else font_size

        arrows = [True,True] if arrow_heads is None else arrow_heads
        label_norm = cq.Vector(0,0,1) if label_normal is None else label_normal.normalized()

        line_length = line_path.Length()

        # Create the lable object and rotate it to align with the dimension line and normal
        label_xy_object = cq.Workplane('XY').text(txt=label,fontsize=label_size,distance=label_size/20)
        label_length = 2.5*max([ v.X for v in label_xy_object.vertices().vals() ])
        text_plane = cq.Plane(origin=line_path.positionAt(0.5),xDir=line_path.tangentAt(0.5),normal=label_norm)
        label_object = cq.Workplane(text_plane).text(txt=label,fontsize=label_size,distance=label_size/20)

        # Calculate the relative positions along the dimension line of the key features
        line_controls = [
            self.arrow_length/line_length if arrows[0] else 0.0,
            0.5-(label_length/2)/line_length,
            0.5+(label_length/2)/line_length,
            1.0-self.arrow_length/line_length if arrows[1] else 1.0
        ]
        if line_controls[0]>line_controls[1] or line_controls[2]>line_controls[3]:
            raise ValueError(f'Label "{label}" is too large for given dimension')

        # Compose an assembly with the component parts of the dimension line
        d_line = cq.Assembly(None,name=label+'_dimension_line',color=self.color)
        # d_line = cq.Assembly(None,name=label+'_dimension_line',color=cq.Color(1,0,0))
        if arrows[0]:
            d_line.add(
                arrow_head(line_path,tip_pos=0.0,tail_pos=line_controls[0]),
                name='start_arrow'
            )
        d_line.add(
            line_segment(line_path,tip_pos=line_controls[0],tail_pos=line_controls[1]),
            name='start_line'
        )
        d_line.add(label_object,name='label')
        d_line.add(
            line_segment(line_path,tip_pos=line_controls[2],tail_pos=line_controls[3]),
            name='end_line'
        )
        if arrows[1]:
            d_line.add(
                arrow_head(line_path,tip_pos=1.0,tail_pos=line_controls[3]),
                name='end_arrow'
            )

        return d_line

if __name__ == '__main__' or "show_object" in locals():
    draft_obj = Draft(default_font_size=8,default_color=cq.Color(0.75,0.25,0.25))
    test0 = draft_obj.dimension_line(
        label = "test0",
        start = (0,0,0),
        end = (40*cos(pi/6),-40*sin(pi/6),0)
    )
    test1 = draft_obj.dimension_line(
        label="test1",
        label_normal=cq.Vector(0,-1,0),
        start=(-40,0,0),
        end=(40,0,0)
    )
    test2 = draft_obj.dimension_line("test2",8,label_normal=cq.Vector(0,-1,0),
        path=cq.Edge.makeThreePointArc(
            cq.Vector(-40,0,0),
            cq.Vector(-40*sqrt(2)/2,0,40*sqrt(2)/2),
            cq.Vector(0,0,40)
        )
    )
    test3 = draft_obj.dimension_line("test3",8,label_normal=cq.Vector(0,-1,0),
        path=cq.Edge.makeThreePointArc(
            cq.Vector(0,0,40),
            cq.Vector(40*sqrt(2)/2,0,40*sqrt(2)/2),
            cq.Vector(40,0,0)
        )
    )
    test4 = draft_obj.dimension_line("test4", 8, label_normal = cq.Vector(0,0,1),
        path=cq.Edge.makeThreePointArc(
            cq.Vector(-40,0,0),
            cq.Vector(0,-40,0),
            cq.Vector(40,0,0)
        )
    )
    test5 = draft_obj.dimension_line("test5", 8, label_normal = cq.Vector(0,-.5,1),
        path=cq.Edge.makeSpline([cq.Vector(-40,0,0),cq.Vector(35,20,10),cq.Vector(40,0,0)])
    )
    test6 = draft_obj.dimension_line(
        label = "test6",
        arrow_heads = [False,True],
        start = cq.Vector(40,0,0),
        end = (80,0,0)
    )
    test7 = draft_obj.dimension_line(
        label = "test7",
        arrow_heads = [True,False],
        start = (-80,0,0),
        end = cq.Vector(-40,0,0)
    )

    # with cProfile.Profile() as pr:
    #     test3 = dimension_line("test3",8,label_normal=cq.Vector(0,-1,0),
    #         path=cq.Edge.makeThreePointArc(
    #             cq.Vector(0,0,40),
    #             cq.Vector(40*sqrt(2)/2,0,40*sqrt(2)/2),
    #             cq.Vector(40,0,0)
    #         )
    #     )
    # stats = pstats.Stats(pr)
    # stats.sort_stats(pstats.SortKey.TIME)
    # stats.print_stats()


# If running from within the cq-editor, show the dimension lines
if "show_object" in locals():
    show_object(test0,name="test0")
    show_object(test1,name="test1")
    show_object(test2,name="test2")
    show_object(test3,name="test3")
    show_object(test4,name="test4")
    show_object(test5,name="test5")
    show_object(test6,name="test6")
    show_object(test7,name="test7")
