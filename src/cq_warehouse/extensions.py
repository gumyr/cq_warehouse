"""
Cadquery Extensions

name: extensions.py
by:   Gumyr
date: August 2nd 2021

desc:

    This python module provides extensions to the native cadquery code base.
    Hopefully future generations of cadquery will incorporate this or similar
    functionality.

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
from math import sin, cos, radians
from typing import Union, Tuple
import cadquery as cq

VectorLike = Union[Tuple[float, float], Tuple[float, float, float], cq.Vector]

"""

Assembly extensions: rotate(), translate()

"""


def _translate(self, vec: VectorLike):
    """
    Moves the current assembly (without making a copy) by the specified translation vector
    :param vec: The translation vector
    """
    self.loc = self.loc * cq.Location(cq.Vector(vec))
    return self


cq.Assembly.translate = _translate


def _rotate(self, axis: VectorLike, angle: float):
    """
    Rotates the current assembly (without making a copy) around the axis of rotation
    by the specified angle

    :param axis: The axis of rotation (starting at the origin)
    :type axis: a 3-tuple of floats
    :param angle: the rotation angle, in degrees
    :type angle: float
    """
    self.loc = self.loc * cq.Location(cq.Vector(0, 0, 0), cq.Vector(axis), angle)
    return self


cq.Assembly.rotate = _rotate

"""

Vector extensions: rotateX(), rotateY(), rotateZ(), pointToVector()

"""


def _vector_rotate_x(self, angle: float) -> cq.Vector:
    """ cq.Vector rotate angle in degrees about x-axis """
    return cq.Vector(
        self.x,
        self.y * cos(radians(angle)) - self.z * sin(radians(angle)),
        self.y * sin(radians(angle)) + self.z * cos(radians(angle)),
    )


cq.Vector.rotateX = _vector_rotate_x


def _vector_rotate_y(self, angle: float) -> cq.Vector:
    """ cq.Vector rotate angle in degrees about y-axis """
    return cq.Vector(
        self.x * cos(radians(angle)) + self.z * sin(radians(angle)),
        self.y,
        -self.x * sin(radians(angle)) + self.z * cos(radians(angle)),
    )


cq.Vector.rotateY = _vector_rotate_y


def _vector_rotate_z(self, angle: float) -> cq.Vector:
    """ cq.Vector rotate angle in degrees about z-axis """
    return cq.Vector(
        self.x * cos(radians(angle)) - self.y * sin(radians(angle)),
        self.x * sin(radians(angle)) + self.y * cos(radians(angle)),
        self.z,
    )


cq.Vector.rotateZ = _vector_rotate_z


def _point_to_vector(self, plane: str, offset: float = 0.0) -> cq.Vector:
    """ map a 2D point on the XY plane to 3D space on the given plane at the offset """
    if not isinstance(plane, str) or plane not in ["XY", "XZ", "YZ"]:
        raise ValueError("plane " + str(plane) + " must be one of: XY,XZ,YZ")
    if plane == "XY":
        mapped_point = cq.Vector(self.x, self.y, offset)
    elif plane == "XZ":
        mapped_point = cq.Vector(self.x, offset, self.y)
    else:  # YZ
        mapped_point = cq.Vector(offset, self.x, self.y)
    return mapped_point


cq.Vector.pointToVector = _point_to_vector

"""

Vertex extensions: __add__(), __sub__(), __str__()

"""


def __vertex_add__(
    self, other: Union[cq.Vertex, cq.Vector, Tuple[float, float, float]]
) -> cq.Vertex:
    """ Add a Vector or tuple of floats to a Vertex """
    if isinstance(other, cq.Vertex):
        new_vertex = cq.Vertex.makeVertex(
            self.X + other.X, self.Y + other.Y, self.Z + other.Z
        )
    elif isinstance(other, (cq.Vector, tuple)):
        new_other = cq.Vector(other)
        new_vertex = cq.Vertex.makeVertex(
            self.X + new_other.x, self.Y + new_other.y, self.Z + new_other.z
        )
    else:
        raise TypeError(
            "Vertex addition only supports Vertex,Vector or tuple(float,float,float) as input"
        )
    return new_vertex


cq.Vertex.__add__ = __vertex_add__


def __vertex_sub__(self, other: Union[cq.Vertex, cq.Vector, tuple]) -> cq.Vertex:
    """ Subtract a Vector or tuple of floats to a Vertex """
    if isinstance(other, cq.Vertex):
        new_vertex = cq.Vertex.makeVertex(
            self.X - other.X, self.Y - other.Y, self.Z - other.Z
        )
    elif isinstance(other, (cq.Vector, tuple)):
        new_other = cq.Vector(other)
        new_vertex = cq.Vertex.makeVertex(
            self.X - new_other.x, self.Y - new_other.y, self.Z - new_other.z
        )
    else:
        raise TypeError(
            "Vertex subtraction only supports Vertex,Vector or tuple(float,float,float) as input"
        )
    return new_vertex


cq.Vertex.__sub__ = __vertex_sub__


def __vertex_str__(self) -> str:
    """ Display a Vertex """
    return f"Vertex: ({self.X}, {self.Y}, {self.Z})"


cq.Vertex.__str__ = __vertex_str__


def _vertex_to_vector(self) -> cq.Vector:
    """ Convert a Vertex to a Vector """
    return cq.Vector(self.toTuple())


cq.Vertex.toVector = _vertex_to_vector
