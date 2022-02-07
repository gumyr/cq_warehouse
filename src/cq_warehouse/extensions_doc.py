from typing import Union, Tuple, Optional, Literal
from fastener import Screw, Nut, Washer
class gp_Ax1:
    pass
class T:
    pass
class VectorLike:
    pass
class BoundBox:
    pass
class Solid:
    pass
class Compound:
    pass
class Location:
    pass
class Assembly(object):
    def translate(self, vec: "VectorLike") -> "Assembly":
        """
        Moves the current assembly (without making a copy) by the specified translation vector
    
        Args:
            vec: The translation vector
    
        Returns:
            The translated Assembly
    
        Example:
            car_assembly.translate((1,2,3))
        """
    def rotate(self, axis: "VectorLike", angle: float) -> "Assembly":
        """Rotate Assembly
    
        Rotates the current assembly (without making a copy) around the axis of rotation
        by the specified angle
    
        Args:
            axis: The axis of rotation (starting at the origin)
            angle: The rotation angle, in degrees
    
        Returns:
            The rotated Assembly
    
        Example:
            car_assembly.rotate((0,0,1),90)
        """
    def fastenerQuantities(self, bom: bool = True, deep: bool = True) -> dict:
        """Fastener Quantities
    
        Generate a bill of materials of the fasteners in an assembly augmented by the hole methods
        bom: returns fastener.info if True else counts fastener instances
    
        Args:
            bom (bool, optional): Select a Bill of Materials or raw fastener instance count. Defaults to True.
            deep (bool, optional): Scan the entire Assembly. Defaults to True.
    
        Returns:
            fastener usage summary
        """
    def fastenerLocations(self, fastener: Union["Nut", "Screw"]) -> list[Location]:
        """Return location(s) of fastener
    
        Generate a list of cadquery Locations for the given fastener relative to the Assembly
    
        Args:
            fastener: fastener to search for
    
        Returns:
            a list of cadquery Location objects for each fastener instance
        """
class Plane(object):
    def toLocalCoords(self, obj: Union["Vector", "Shape", "BoundBox"]):
        """Project the provided coordinates onto this plane
    
        Args:
            obj: an object, vector, or bounding box to convert
    
        Returns:
            an object of the same type, but converted to local coordinates
    
        Most of the time, the z-coordinate returned will be zero, because most
        operations based on a plane are all 2D. Occasionally, though, 3D
        points outside of the current plane are transformed. One such example is
        :py:meth:`Workplane.box`, where 3D corners of a box are transformed to
        orient the box in space correctly.
        """
class Vector(object):
    def rotateX(self, angle: float) -> "Vector":
        """Rotate Vector about X-Axis
    
        Args:
            angle: Angle in degrees
    
        Returns:
            Rotated Vector
        """
    def rotateY(self, angle: float) -> "Vector":
        """Rotate Vector about Y-Axis
    
        Args:
            angle: Angle in degrees
    
        Returns:
            Rotated Vector
        """
    def rotateZ(self, angle: float) -> "Vector":
        """Rotate Vector about Z-Axis
    
        Args:
            angle: Angle in degrees
    
        Returns:
            Rotated Vector
        """
    def toVertex(self) -> "Vertex":
        """Convert to Vector to Vertex
    
        Returns:
            Vertex equivalent of Vector
        """
    def getSignedAngle(self, v: "Vector", normal: "Vector" = None) -> float:
        """Signed Angle Between Vectors
    
        Return the signed angle in RADIANS between two vectors with the given normal
        based on this math: angle = atan2((Va × Vb) ⋅ Vn, Va ⋅ Vb)
    
        Args:
            v: Second Vector.
    
            normal: Vector's Normal. Defaults to -Z Axis.
    
        Returns:
            Angle between vectors
        """
class Vertex(object):
    def __add__(
        self, other: Union["Vertex", "Vector", Tuple[float, float, float]]
    ) -> "Vertex":
        """Add
    
        Add to a Vertex with a Vertex, Vector or Tuple
    
        Args:
            other: Value to add
    
        Raises:
            TypeError: other not in [Tuple,Vector,Vertex]
    
        Returns:
            Result
    
        Example:
            part.faces(">Z").vertices("<Y and <X").val() + (0, 0, 15)
    
            which creates a new Vertex 15mm above one extracted from a part. One can add or
            subtract a cadquery ``Vertex``, ``Vector`` or ``tuple`` of float values to a
            Vertex with the provided extensions.
        """
    def __sub__(self, other: Union["Vertex", "Vector", tuple]) -> "Vertex":
        """Subtract
    
        Substract a Vertex with a Vertex, Vector or Tuple from self
    
        Args:
            other: Value to add
    
        Raises:
            TypeError: other not in [Tuple,Vector,Vertex]
    
        Returns:
            Result
    
        Example:
            part.faces(">Z").vertices("<Y and <X").val() - Vector(10, 0, 0)
        """
    def __str__(self) -> str:
        """To String
    
        Convert Vertex to String for display
    
        Returns:
            Vertex as String
        """
    def toVector(self) -> "Vector":
        """To Vector
    
        Convert a Vertex to Vector
    
        Returns:
            Vector representation of Vertex
        """
class Workplane(object):
    def textOnPath(
        self: T,
        txt: str,
        fontsize: float,
        distance: float,
        start: float = 0.0,
        cut: bool = True,
        combine: bool = False,
        clean: bool = True,
        font: str = "Arial",
        fontPath: Optional[str] = None,
        kind: Literal["regular", "bold", "italic"] = "regular",
        valign: Literal["center", "top", "bottom"] = "center",
    ) -> T:
        """
        Returns 3D text with the baseline following the given path.
    
        The parameters are largely the same as the
        `Workplane.text() <https://cadquery.readthedocs.io/en/latest/classreference.html#cadquery.Workplane.text>`_
        method. The **start** parameter (normally between 0.0 and 1.0) specify where on the path to
        start the text.
    
        The path that the text follows is defined by the last Edge or Wire in the
        Workplane stack. Path's defined outside of the Workplane can be used with the
        `add(<path>) <https://cadquery.readthedocs.io/en/latest/classreference.html#cadquery.Workplane.add>`_
        method.
    
        .. image:: textOnPath.png
    
        Args:
            txt: text to be rendered
            fontsize: size of the font in model units
            distance: the distance to extrude or cut, normal to the workplane plane, negative means opposite the normal direction
            start: the relative location on path to start the text, values must be between 0.0 and 1.0
            cut: True to cut the resulting solid from the parent solids if found
            combine: True to combine the resulting solid with parent solids if found
            clean: call :py:meth:`clean` afterwards to have a clean shape
            font: font name
            fontPath: path to font file
            kind: font type
    
        Returns:
            a CQ object with the resulting solid selected
    
        The returned object is always a Workplane object, and depends on whether combine is True, and
        whether a context solid is already defined:
    
        *  if combine is False, the new value is pushed onto the stack.
        *  if combine is true, the value is combined with the context solid if it exists,
           and the resulting solid becomes the new context solid.
    
        Examples::
    
            fox = (
                Workplane("XZ")
                .threePointArc((50, 30), (100, 0))
                .textOnPath(
                    txt="The quick brown fox jumped over the lazy dog",
                    fontsize=5,
                    distance=1,
                    start=0.1,
                )
            )
    
            clover = (
                Workplane("front")
                .moveTo(0, 10)
                .radiusArc((10, 0), 7.5)
                .radiusArc((0, -10), 7.5)
                .radiusArc((-10, 0), 7.5)
                .radiusArc((0, 10), 7.5)
                .consolidateWires()
                .textOnPath(
                    txt=".x" * 102,
                    fontsize=1,
                    distance=1,
                )
            )
        """
    def hexArray(
        self,
        diagonal: float,
        xCount: int,
        yCount: int,
        center: Union[bool, tuple[bool, bool]] = True,
    ):
        """Create Hex Array
    
        Creates a hexagon array of points and pushes them onto the stack.
        If you want to position the array at another point, create another workplane
        that is shifted to the position you would like to use as a reference
    
        Args:
            diagonal: tip to tip size of hexagon ( must be > 0)
            xCount: number of points ( > 0 )
            yCount: number of points ( > 0 )
            center: If True, the array will be centered around the workplane center.
                If False, the lower corner will be on the reference point and the array will
                extend in the positive x and y directions. Can also use a 2-tuple to specify
                centering along each axis.
    
        Returns:
            Places points on the Workplane stack
        """
    def thicken(self, depth: float, direction: "Vector" = None):
        """Thicken Face
    
        Find all of the faces on the stack and make them Solid objects by thickening
        along the normals.
    
        Args:
            depth: Amount to thicken face(s), can be positive or negative.
            direction: The direction vector can be used to
                indicate which way is 'up', potentially flipping the face normal direction
                such that many faces with different normals all go in the same direction
                (direction need only be +/- 90 degrees from the face normal). Defaults to None.
    
        Returns:
            A set of new objects on the Workplane stack
        """
    def fastenerHole(
        self: T,
        hole_diameters: dict,
        fastener: Union["Nut", "Screw"],
        depth: float,
        washers: list["Washer"],
        fit: Optional[Literal["Close", "Normal", "Loose"]] = None,
        material: Optional[Literal["Soft", "Hard"]] = None,
        counterSunk: Optional[bool] = True,
        baseAssembly: Optional[Assembly] = None,
        hand: Optional[Literal["right", "left"]] = None,
        simple: Optional[bool] = False,
        clean: Optional[bool] = True,
    ) -> T:
        """Fastener Specific Hole
    
        Makes a counterbore clearance, tap or threaded hole for the given screw for each item
        on the stack. The surface of the hole is at the current workplane.
    
        Args:
            hole_diameters: either clearance or tap hole diameter specifications
            fastener: A nut or screw instance
            depth: hole depth
            washers: A list of washer instances, can be empty
            fit: one of "Close", "Normal", "Loose" which determines clearance hole diameter. Defaults to None.
            material: on of "Soft", "Hard" which determines tap hole size. Defaults to None.
            counterSunk: Is the fastener countersunk into the part?. Defaults to True.
            baseAssembly: Assembly to add faster to. Defaults to None.
            hand: tap hole twist direction either "right" or "left". Defaults to None.
            simple: tap hole thread complexity selector. Defaults to False.
            clean: execute a clean operation remove extraneous internal features. Defaults to True.
    
        Raises:
            ValueError: fit or material not in hole_diameters dictionary
    
        Returns:
            the shape on the workplane stack with a new hole
        """
    def clearanceHole(
        self: T,
        fastener: Union["Nut", "Screw"],
        washers: Optional[list["Washer"]] = None,
        fit: Optional[Literal["Close", "Normal", "Loose"]] = "Normal",
        depth: Optional[float] = None,
        counterSunk: Optional[bool] = True,
        baseAssembly: Optional[Assembly] = None,
        clean: Optional[bool] = True,
    ) -> T:
        """Clearance Hole
    
        Put a clearance hole in a shape at the provided location
    
        For more information on how to use clearanceHole() see
        :ref:`Clearance, Tap and Threaded Holes <clearance holes>`.
    
        Args:
            fastener: A nut or screw instance
            washers: A list of washer instances, can be empty
            fit: one of "Close", "Normal", "Loose" which determines clearance hole diameter. Defaults to None.
            depth: hole depth. Defaults to through part.
            counterSunk: Is the fastener countersunk into the part?. Defaults to True.
            baseAssembly: Assembly to add faster to. Defaults to None.
            clean: execute a clean operation remove extraneous internal features. Defaults to True.
    
        Returns:
            the shape on the workplane stack with a new clearance hole
        """
    def tapHole(
        self: T,
        fastener: Union["Nut", "Screw"],
        washers: Optional[list["Washer"]] = None,
        material: Optional[Literal["Soft", "Hard"]] = "Soft",
        depth: Optional[float] = None,
        counterSunk: Optional[bool] = True,
        fit: Optional[Literal["Close", "Normal", "Loose"]] = "Normal",
        baseAssembly: Optional[Assembly] = None,
        clean: Optional[bool] = True,
    ) -> T:
        """Tap Hole
    
        Put a tap hole in a shape at the provided location
    
        For more information on how to use tapHole() see
        :ref:`Clearance, Tap and Threaded Holes <clearance holes>`.
    
        Args:
            fastener: A nut or screw instance
            washers: A list of washer instances, can be empty
            material: on of "Soft", "Hard" which determines tap hole size. Defaults to None.
            depth: hole depth. Defaults to through part.
            counterSunk: Is the fastener countersunk into the part?. Defaults to True.
            fit: one of "Close", "Normal", "Loose" which determines clearance hole diameter. Defaults to None.
            baseAssembly: Assembly to add faster to. Defaults to None.
            clean: execute a clean operation remove extraneous internal features. Defaults to True.
    
        Returns:
            the shape on the workplane stack with a new tap hole
        """
    def threadedHole(
        self: T,
        fastener: "Screw",
        depth: float,
        washers: Optional[list["Washer"]] = None,
        hand: Literal["right", "left"] = "right",
        simple: Optional[bool] = False,
        counterSunk: Optional[bool] = True,
        fit: Optional[Literal["Close", "Normal", "Loose"]] = "Normal",
        baseAssembly: Optional[Assembly] = None,
        clean: Optional[bool] = True,
    ) -> T:
        """Threaded Hole
    
        Put a threaded hole in a shape at the provided location
    
        For more information on how to use threadedHole() see
        :ref:`Clearance, Tap and Threaded Holes <clearance holes>`.
    
        Args:
            fastener: A nut or screw instance
            depth: hole depth. Defaults to through part.
            washers: A list of washer instances, can be empty
            hand: tap hole twist direction either "right" or "left". Defaults to None.
            simple (Optional[bool], optional): [description]. Defaults to False.
            counterSunk: Is the fastener countersunk into the part?. Defaults to True.
            fit: one of "Close", "Normal", "Loose" which determines clearance hole diameter. Defaults to None.
            baseAssembly: Assembly to add faster to. Defaults to None.
            clean: execute a clean operation remove extraneous internal features. Defaults to True.
    
        Returns:
            the shape on the workplane stack with a new threaded hole
        """
    def pushFastenerLocations(
        self: T,
        fastener: Union["Nut", "Screw"],
        baseAssembly: Assembly,
    ):
        """Push Fastener Locations
    
        Push the Location(s) of the given fastener relative to the given Assembly onto the workplane stack.
    
        Returns:
            Location objects on the workplane stack
        """
class Face(object):
    def thicken(self, depth: float, direction: "Vector" = None) -> "Solid":
        """Thicken Face
    
        Create a solid from a potentially non planar face by thickening along the normals.
    
        .. image:: thickenFace.png
    
        Non-planar faces are thickened both towards and away from the center of the sphere.
    
        Args:
            depth: Amount to thicken face(s), can be positive or negative.
            direction: The direction vector can be used to
                indicate which way is 'up', potentially flipping the face normal direction
                such that many faces with different normals all go in the same direction
                (direction need only be +/- 90 degrees from the face normal). Defaults to None.
    
        Raises:
            RuntimeError: Opencascade internal failures
    
        Returns:
            The resulting Solid object
        """
    def projectToShape(
        self,
        targetObject: "Shape",
        direction: "VectorLike" = None,
        center: "VectorLike" = None,
        internalFacePoints: list["Vector"] = [],
    ) -> list["Face"]:
        """Project Face to target Object
    
        Project a Face onto a Shape generating new Face(s) on the surfaces of the object
        one and only one of `direction` or `center` must be provided.
    
        The two types of projections are illustrated below:
    
        .. image:: flatProjection.png
            :alt: flatProjection
    
        .. image:: conicalProjection.png
            :alt: conicalProjection
    
        Note that an array of Faces is returned as the projection might result in faces
        on the "front" and "back" of the object (or even more if there are intermediate
        surfaces in the projection path). Faces "behind" the projection are not
        returned.
    
        To help refine the resulting face, a list of planar points can be passed to
        augment the surface definition. For example, when projecting a circle onto a
        sphere, a circle will result which will get converted to a planar circle face.
        If no points are provided, a single center point will be generated and used for
        this purpose.
    
        Args:
            targetObject: Object to project onto
            direction: Parallel projection direction. Defaults to None.
            center: Conical center of projection. Defaults to None.
            internalFacePoints: Points refining shape. Defaults to [].
    
        Raises:
            ValueError: Only one of direction or center must be provided
    
        Returns:
            Face(s) projected on target object
        """
    def embossToShape(
        self,
        targetObject: "Shape",
        surfacePoint: "VectorLike",
        surfaceXDirection: "VectorLike",
        internalFacePoints: list["Vector"] = [],
    ) -> "Face":
        """Emboss Face on target object
    
        Emboss a Face on the XY plane onto a Shape while maintaining
        original face dimensions where possible.
    
        Unlike projection, a single Face is returned. The internalFacePoints
        parameter works as with projection.
    
        Args:
            targetObject: Object to emboss onto
            surfacePoint: Point on target object to start embossing
            surfaceXDirection: Direction of X-Axis on target object
            internalFacePoints: Surface refinement points. Defaults to [].
    
        Returns:
            Face: Embossed face
        """
class Wire(object):
    def makeNonPlanarFace(
        self,
        surfacePoints: list["Vector"] = None,
        interiorWires: list["Wire"] = None,
    ) -> "Face":
        """Create Non-Planar Face with perimeter Wire
    
        Create a potentially non-planar face bounded by exterior Wire,
        optionally refined by surfacePoints with optional holes defined by
        interiorWires.
    
        The **surfacePoints** parameter can be used to refine the resulting Face. If no
        points are provided a single central point will be used to help avoid the
        creation of a planar face.
    
        Args:
            surfacePoints: Points on the surface that refine the shape. Defaults to None.
            interiorWires: Hole(s) in the face. Defaults to None.
    
        Raises:
            RuntimeError: Opencascade core exceptions building face
    
        Returns:
            Non planar face
        """
    def projectToShape(
        self,
        targetObject: "Shape",
        direction: "VectorLike" = None,
        center: "VectorLike" = None,
    ) -> list["Wire"]:
        """Project Wire
    
        Project a Wire onto a Shape generating new Wires on the surfaces of the object
        one and only one of `direction` or `center` must be provided. Note that one or
        more wires may be generated depending on the topology of the target object and
        location/direction of projection.
    
        To avoid flipping the normal of a face built with the projected wire the orientation
        of the output wires are forced to be the same as self.
    
        Args:
            targetObject: Object to project onto
            direction: Parallel projection direction. Defaults to None.
            center: Conical center of projection. Defaults to None.
    
        Raises:
            ValueError: Only one of direction or center must be provided
    
        Returns:
            Projected wire(s)
        """
    def embossToShape(
        self,
        targetObject: "Shape",
        surfacePoint: "VectorLike",
        surfaceXDirection: "VectorLike",
        tolerance: float = 0.01,
    ) -> "Wire":
        """Emboss Wire on target object
    
        Emboss an Wire on the XY plane onto a Shape while maintaining
        original wire dimensions where possible.
    
        .. image:: embossWire.png
    
        The embossed wire can be used to build features as:
    
        .. image:: embossFeature.png
    
        with the `sweep() <https://cadquery.readthedocs.io/en/latest/_modules/cadquery/occ_impl/shapes.html#Solid.sweep>`_ method.
    
        Args:
            targetObject: Object to emboss onto
            surfacePoint: Point on target object to start embossing
            surfaceXDirection: Direction of X-Axis on target object
            tolerance: maximum allowed error in embossed wire length. Defaults to 0.01.
    
        Raises:
            RuntimeError: Embosses wire is invalid
    
        Returns:
            Embossed wire
        """
class Edge(object):
    def projectToShape(
        self,
        targetObject: "Shape",
        direction: "VectorLike" = None,
        center: "VectorLike" = None,
    ) -> list["Edge"]:
        """Project Edge
    
        Project an Edge onto a Shape generating new Wires on the surfaces of the object
        one and only one of `direction` or `center` must be provided. Note that one or
        more wires may be generated depending on the topology of the target object and
        location/direction of projection.
    
        To avoid flipping the normal of a face built with the projected wire the orientation
        of the output wires are forced to be the same as self.
    
        Args:
            targetObject: Object to project onto
            direction: Parallel projection direction. Defaults to None.
            center: Conical center of projection. Defaults to None.
    
        Raises:
            ValueError: Only one of direction or center must be provided
    
        Returns:
            Projected Edge(s)
        """
    def embossToShape(
        self,
        targetObject: "Shape",
        surfacePoint: "VectorLike",
        surfaceXDirection: "VectorLike",
        tolerance: float = 0.01,
    ) -> "Edge":
        """Emboss Edge on target object
    
        Emboss an Edge on the XY plane onto a Shape while maintaining
        original edge dimensions where possible.
    
        Args:
            targetObject: Object to emboss onto
            surfacePoint: Point on target object to start embossing
            surfaceXDirection: Direction of X-Axis on target object
            tolerance: maximum allowed error in embossed edge length
    
        Returns:
            Embossed edge
        """
class Shape(object):
    def findIntersection(
        self, point: "Vector", direction: "Vector"
    ) -> list[tuple["Vector", "Vector"]]:
        """Find point and normal at intersection
    
        Return both the point(s) and normal(s) of the intersection of the line and the shape
    
        Args:
            point: point on intersecting line
            direction: direction of intersecting line
    
        Returns:
            Point and normal of intersection
        """
    def projectText(
        self,
        txt: str,
        fontsize: float,
        depth: float,
        path: Union["Wire", "Edge"],
        font: str = "Arial",
        fontPath: Optional[str] = None,
        kind: Literal["regular", "bold", "italic"] = "regular",
        valign: Literal["center", "top", "bottom"] = "center",
        start: float = 0,
    ) -> "Compound":
        """Projected 3D text following the given path on Shape
    
        Create 3D text using projection by positioning each face of
        the planar text normal to the shape along the path and projecting
        onto the surface. If depth is not zero, the resulting face is
        thickened to the provided depth.
    
        Note that projection may result in text distortion depending on
        the shape at a position along the path.
    
        .. image:: projectText.png
    
        Args:
            txt: Text to be rendered
            fontsize: Size of the font in model units
            depth: Thickness of text, 0 returns a Face object
            path: Path on the Shape to follow
            font: Font name. Defaults to "Arial".
            fontPath: Path to font file. Defaults to None.
            kind: Font type - one of "regular", "bold", "italic". Defaults to "regular".
            valign: Vertical Alignment - one of "center", "top", "bottom". Defaults to "center".
            start: Relative location on path to start the text. Defaults to 0.
    
        Returns:
            The projected text
        """
    def embossText(
        self,
        txt: str,
        fontsize: float,
        depth: float,
        path: Union["Wire", "Edge"],
        font: str = "Arial",
        fontPath: Optional[str] = None,
        kind: Literal["regular", "bold", "italic"] = "regular",
        valign: Literal["center", "top", "bottom"] = "center",
        start: float = 0,
    ) -> "Compound":
        """Embossed 3D text following the given path on Shape
    
        Create 3D text by embossing each face of the planar text onto
        the shape along the path. If depth is not zero, the resulting
        face is thickened to the provided depth.
    
        .. image:: embossText.png
    
        Args:
            txt: Text to be rendered
            fontsize: Size of the font in model units
            depth: Thickness of text, 0 returns a Face object
            path: Path on the Shape to follow
            font: Font name. Defaults to "Arial".
            fontPath: Path to font file. Defaults to None.
            kind: Font type - one of "regular", "bold", "italic". Defaults to "regular".
            valign: Vertical Alignment - one of "center", "top", "bottom". Defaults to "center".
            start: Relative location on path to start the text. Defaults to 0.
    
        Returns:
            The embossed text
        """
class Location(object):
    def __str__(self):
        """To String
    
        Convert Location to String for display
    
        Returns:
            Location as String
        """
def makeNonPlanarFace(
    exterior: Union["Wire", list["Edge"]],
    surfacePoints: list["VectorLike"] = None,
    interiorWires: list["Wire"] = None,
) -> "Face":
    """Create Non-Planar Face

    Create a potentially non-planar face bounded by exterior (wire or edges),
    optionally refined by surfacePoints with optional holes defined by
    interiorWires.

    Args:
        exterior: Perimeter of face
        surfacePoints: Points on the surface that refine the shape. Defaults to None.
        interiorWires: Hole(s) in the face. Defaults to None.

    Raises:
        RuntimeError: Opencascade core exceptions building face

    Returns:
        Non planar face
    """
