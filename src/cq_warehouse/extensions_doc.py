from typing import Union, Tuple, Optional, Literal, Iterable
from fastener import Screw, Nut, Washer
from bearing import Bearing
class gp_Ax1:
    pass
class gp_Trsf:
    pass
class T:
    pass
class Vector:
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
Modes = Literal['a', 's', 'i', 'c']
Real = Union[int, float]
Point = Union[Vector, Tuple[Real, Real]]
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
    def findLocation(self, target: str) -> Location:
        """Find Location of named target
    
        Return the Location of the target object relative to the given Assembly
        including the given Assembly.
    
        Args:
            target (str): name of target object
    
        Raises:
            ValueError: target object not in found in Assembly
    
        Returns:
            cq.Location: Location of target relative to self
        """
    def doObjectsIntersect(self, tolerance: float = 1e-5) -> bool:
        """Do Objects Intersect
    
        Determine if any of the objects within an Assembly intersect by
        intersecting each of the shapes with each other and checking for
        a common volume.
    
        Args:
            self (Assembly): Assembly to test
            tolerance (float, optional): maximum allowable volume difference. Defaults to 1e-5.
    
        Returns:
            bool: do the object intersect
        """
    def areObjectsValid(self) -> bool:
        """Are Objects Valid
    
        Check the validity of all the objects in this Assembly
    
        Returns:
            bool: all objects are valid
        """
    def section(self, plane: "Plane") -> "Assembly":
        """Cross Section
    
        Generate a 2D slice of an assembly as a colorize Assembly
    
        Args:
            plane (Plane): the plane with which to slice the Assembly
    
        Returns:
            Assembly: The cross section assembly with original colors
        """
class Plane(object):
    def _toFromLocalCoords(
        self, obj: Union["VectorLike", "Shape", "BoundBox"], to: bool = True
    ):
        """Reposition the object relative to this plane
    
        Args:
            obj: an object, vector, or bounding box to convert
            to: convert `to` or from local coordinates. Defaults to True.
    
        Returns:
            an object of the same type, but repositioned to local coordinates
    
        """
    def toLocalCoords(self, obj: Union["VectorLike", "Shape", "BoundBox"]):
        """Reposition the object relative to this plane
    
        Args:
            obj: an object, vector, or bounding box to convert
    
        Returns:
            an object of the same type, but repositioned to local coordinates
    
        """
    def fromLocalCoords(self, obj: Union[tuple, "Vector", "Shape", "BoundBox"]):
        """Reposition the object relative from this plane
    
        Args:
            obj: an object, vector, or bounding box to convert
    
        Returns:
            an object of the same type, but repositioned to world coordinates
    
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
    def __repr__(self) -> str:
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
        cut: bool = True,
        combine: bool = False,
        clean: bool = True,
        font: str = "Arial",
        fontPath: Optional[str] = None,
        kind: Literal["regular", "bold", "italic"] = "regular",
        halign: Literal["center", "left", "right"] = "left",
        valign: Literal["center", "top", "bottom"] = "center",
        positionOnPath: float = 0.0,
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
            cut: True to cut the resulting solid from the parent solids if found
            combine: True to combine the resulting solid with parent solids if found
            clean: call :py:meth:`clean` afterwards to have a clean shape
            font: font name
            fontPath: path to font file
            kind: font style
            halign: horizontal alignment
            valign: vertical alignment
            positionOnPath: the relative location on path to position the text, values must be between 0.0 and 1.0
    
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
        washers: list["Washer"],
        countersinkProfile: "Workplane",
        depth: Optional[float] = None,
        fit: Optional[Literal["Close", "Normal", "Loose"]] = None,
        material: Optional[Literal["Soft", "Hard"]] = None,
        counterSunk: Optional[bool] = True,
        captiveNut: Optional[bool] = False,
        baseAssembly: Optional["Assembly"] = None,
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
            washers: A list of washer instances, can be empty
            countersinkProfile: the 2D side profile of the fastener (not including a screw's shaft)
            depth: hole depth. Defaults to through part.
            fit: one of "Close", "Normal", "Loose" which determines clearance hole diameter. Defaults to None.
            material: on of "Soft", "Hard" which determines tap hole size. Defaults to None.
            counterSunk: Is the fastener countersunk into the part?. Defaults to True.
            captiveNut: Countersink with a rectangular, filleted, hole. Defaults to False.
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
        captiveNut: Optional[bool] = False,
        baseAssembly: Optional["Assembly"] = None,
        clean: Optional[bool] = True,
    ) -> T:
        """Clearance Hole
    
        Put a clearance hole in a shape at the provided location
    
        For more information on how to use clearanceHole() see
        :ref:`Custom Holes <custom holes>`.
    
        Args:
            fastener: A nut or screw instance
            washers: A list of washer instances, can be empty
            fit: one of "Close", "Normal", "Loose" which determines clearance hole diameter. Defaults to "Normal".
            depth: hole depth. Defaults to through part.
            counterSunk: Is the fastener countersunk into the part?. Defaults to True.
            baseAssembly: Assembly to add faster to. Defaults to None.
            clean: execute a clean operation remove extraneous internal features. Defaults to True.
    
        Raises:
            ValueError: clearanceHole doesn't accept fasteners of type HeatSetNut - use insertHole instead
    
        Returns:
            the shape on the workplane stack with a new clearance hole
        """
    def insertHole(
        self: T,
        fastener: "Nut",
        fit: Optional[Literal["Close", "Normal", "Loose"]] = "Normal",
        depth: Optional[float] = None,
        baseAssembly: Optional["Assembly"] = None,
        clean: Optional[bool] = True,
        manufacturingCompensation: float = 0.0,
    ) -> T:
        """Insert Hole
    
        Put a hole appropriate for an insert nut at the provided location
    
        For more information on how to use insertHole() see
        :ref:`Custom Holes <custom holes>`.
    
        Args:
            fastener: An insert nut instance
            fit: one of "Close", "Normal", "Loose" which determines clearance hole diameter. Defaults to "Normal".
            depth: hole depth. Defaults to through part.
            baseAssembly: Assembly to add faster to. Defaults to None.
            clean: execute a clean operation remove extraneous internal features. Defaults to True.
            manufacturingCompensation (float, optional): used to compensate for over-extrusion
                of 3D printers. A value of 0.2mm will reduce the radius of an external thread
                by 0.2mm (and increase the radius of an internal thread) such that the resulting
                3D printed part matches the target dimensions. Defaults to 0.0.
    
        Raises:
            ValueError: insertHole only accepts fasteners of type HeatSetNut
    
        Returns:
            the shape on the workplane stack with a new clearance hole
        """
    def pressFitHole(
        self: T,
        bearing: "Bearing",
        interference: float = 0,
        fit: Optional[Literal["Close", "Normal", "Loose"]] = "Normal",
        depth: Optional[float] = None,
        baseAssembly: Optional["Assembly"] = None,
        clean: Optional[bool] = True,
    ) -> T:
        """Press Fit Hole
    
        Put a hole appropriate for a bearing at the provided location
    
        For more information on how to use pressFitHole() see
        :ref:`Custom Holes <custom holes>`.
    
        Args:
            bearing: A bearing instance
            interference: The amount the decrease the hole radius from the bearing outer radius. Defaults to 0.
            fit: one of "Close", "Normal", "Loose" which determines hole diameter for the bore. Defaults to "Normal".
            depth: hole depth. Defaults to through part.
            baseAssembly: Assembly to add faster to. Defaults to None.
            clean: execute a clean operation remove extraneous internal features. Defaults to True.
    
        Raises:
            ValueError: pressFitHole only accepts bearings of type Bearing
    
        Returns:
            the shape on the workplane stack with a new press fit hole
        """
    def tapHole(
        self: T,
        fastener: Union["Nut", "Screw"],
        washers: Optional[list["Washer"]] = None,
        material: Optional[Literal["Soft", "Hard"]] = "Soft",
        depth: Optional[float] = None,
        counterSunk: Optional[bool] = True,
        fit: Optional[Literal["Close", "Normal", "Loose"]] = "Normal",
        baseAssembly: Optional["Assembly"] = None,
        clean: Optional[bool] = True,
    ) -> T:
        """Tap Hole
    
        Put a tap hole in a shape at the provided location
    
        For more information on how to use tapHole() see
        :ref:`Custom Holes <custom holes>`.
    
        Args:
            fastener: A nut or screw instance
            washers: A list of washer instances, can be empty
            material: on of "Soft", "Hard" which determines tap hole size. Defaults to "Soft".
            depth: hole depth. Defaults to through part.
            counterSunk: Is the fastener countersunk into the part?. Defaults to True.
            fit: one of "Close", "Normal", "Loose" which determines clearance hole diameter. Defaults to None.
            baseAssembly: Assembly to add faster to. Defaults to None.
            clean: execute a clean operation remove extraneous internal features. Defaults to True.
    
        Raises:
            ValueError: tapHole doesn't accept fasteners of type HeatSetNut - use insertHole instead
    
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
        baseAssembly: Optional["Assembly"] = None,
        clean: Optional[bool] = True,
    ) -> T:
        """Threaded Hole
    
        Put a threaded hole in a shape at the provided location
    
        For more information on how to use threadedHole() see
        :ref:`Custom Holes <custom holes>`.
    
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
    
        Raises:
            ValueError: threadedHole doesn't accept fasteners of type HeatSetNut - use insertHole instead
    
        Returns:
            the shape on the workplane stack with a new threaded hole
        """
    def pushFastenerLocations(
        self: T,
        fastener: Union["Nut", "Screw"],
        baseAssembly: "Assembly",
        offset: float = 0,
        flip: bool = False,
    ):
        """Push Fastener Locations
    
        Push the Location(s) of the given fastener relative to the given Assembly onto the workplane stack.
    
        Returns:
            Location objects on the workplane stack
        """
    def makeFingerJoints(
        self: T,
        materialThickness: float,
        targetFingerWidth: float,
        kerfWidth: float = 0.0,
        baseAssembly: "Assembly" = None,
    ) -> T:
        """makeFingerJoints
    
        Starting with a base object and a set of selected edges, create Faces with
        finger joints that they could be laser cut from flat material.
    
        Example:
    
            For example, make a simple open topped laser cut box.
    
        .. code-block:: python
    
            finger_jointed_box_assembly = Assembly()
            finger_jointed_faces = (
                Workplane("XY")
                .box(100, 80, 60)
                .edges("not >Z")
                .makeFingerJoints(
                    materialThickness=5,
                    targetFingerWidth=10,
                    kerfWidth=1,
                    baseAssembly=finger_jointed_box_assembly,
                )
            )
    
    
        The assembly part is optional but if present the Assembly will
        contain the parts as if they were laser cut from a material of the
        given thickness.
    
        Args:
            self (T): workplane
            materialThickness (float): thickness of finger joints
            targetFingerWidth (float): approximate with of notch - actual finger width
                will be calculated such that there are an integer number of fingers on Edge
            kerfWidth (float, optional): Extra size to add (or subtract) to account
                for the kerf of the laser cutter. Defaults to 0.0.
            baseAssembly (Assembly, optional): Assembly to add parts to
    
        Raises:
            ValueError: Missing Solid object
            ValueError: Missing finger joint Edges
    
        Returns:
            T: Faces ready to be exported to DXF files and laser cut
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
        internalFacePoints: list["Vector"] = None,
        tolerance: float = 0.01,
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
            internalFacePoints: Surface refinement points. Defaults to None.
            tolerance: maximum allowed error in embossed wire length. Defaults to 0.01.
    
        Returns:
            Face: Embossed face
        """
    def makeHoles(self, interiorWires: list["Wire"]) -> "Face":
        """Make Holes in Face
    
        Create holes in the Face 'self' from interiorWires which must be entirely interior.
        Note that making holes in Faces is more efficient than using boolean operations
        with solid object. Also note that OCCT core may fail unless the orientation of the wire
        is correct - use ``cq.Wire(forward_wire.wrapped.Reversed())`` to reverse a wire.
    
        Example:
    
            For example, make a series of slots on the curved walls of a cylinder.
    
        .. code-block:: python
    
            cylinder = cq.Workplane("XY").cylinder(100, 50, centered=(True, True, False))
            cylinder_wall = cylinder.faces("not %Plane").val()
            path = cylinder.section(50).edges().val()
            slot_wire = cq.Workplane("XY").slot2D(60, 10, angle=90).wires().val()
            embossed_slot_wire = slot_wire.embossToShape(
                targetObject=cylinder.val(),
                surfacePoint=path.positionAt(0),
                surfaceXDirection=path.tangentAt(0),
            )
            embossed_slot_wires = [
                embossed_slot_wire.rotate((0, 0, 0), (0, 0, 1), a) for a in range(90, 271, 20)
            ]
            cylinder_wall_with_holes = cylinder_wall.makeHoles(embossed_slot_wires)
    
        .. image:: slotted_cylinder.png
    
        Args:
            interiorWires: a list of hole outline wires
    
        Raises:
            RuntimeError: adding interior hole in non-planar face with provided interiorWires
            RuntimeError: resulting face is not valid
    
        Returns:
            Face: 'self' with holes
        """
    def isInside(self, point: VectorLike, tolerance: float = 1.0e-6) -> bool:
        """Point inside Face
    
        Returns whether or not the point is inside a Face within the specified tolerance.
        Points on the edge of the Face are considered inside.
    
        Args:
            point (VectorLike): tuple or Vector representing 3D point to be tested
            tolerance (float, optional): tolerance for inside determination. Defaults to 1.0e-6.
    
        Returns:
            bool: indicating whether or not point is within Face
        """
    def makeFingerJoints(
        self: "Face",
        fingerJointEdge: "Edge",
        fingerDepth: float,
        targetFingerWidth: float,
        cornerFaceCounter: dict,
        openInternalVertices: dict,
        alignToBottom: bool = True,
        externalCorner: bool = True,
        faceIndex: int = 0,
    ) -> "Face":
        """makeFingerJoints
    
        Given a Face and an Edge, create finger joints by cutting notches.
    
        Args:
            self (Face): Face to modify
            fingerJointEdge (Edge): Edge of Face to modify
            fingerDepth (float): thickness of the notch from edge
            targetFingerWidth (float): approximate with of notch - actual finger width
                will be calculated such that there are an integer number of fingers on Edge
            cornerFaceCounter (dict): the set of faces associated with every corner
            openInternalVertices (dict): is a vertex part an opening?
            alignToBottom (bool, optional): start with a finger or notch. Defaults to True.
            externalCorner (bool, optional): cut from external corners, add to internal corners.
                Defaults to True.
            faceIndex (int, optional): the index of the current face. Defaults to 0.
    
        Returns:
            Face: the Face with notches on one edge
        """
class Sketch(object):
    def snap_to_vector(
        self,
        pts: Iterable[Union[Point, str]],
        find_tangents: bool = False,
    ) -> list[Vector]:
        """Snap to Vector
    
        Convert Snaps to Vector
    
        Args:
            pts (Union[Point,str]): list of Snaps
            find_tangents (bool): return tangents instead of positions. Defaults to False.
    
        Returns:
            list(Vector): a list of Vectors possibly extracted from tagged objects
        """
    def text(
        self: T,
        txt: str,
        fontsize: float,
        font: str = "Arial",
        font_path: Optional[str] = None,
        font_style: Literal["regular", "bold", "italic"] = "regular",
        halign: Literal["center", "left", "right"] = "left",
        valign: Literal["center", "top", "bottom"] = "center",
        # font_style: Font_Style = Font_Style.REGULAR,
        # halign: Halign = Halign.LEFT,
        # valign: Valign = Valign.CENTER,
        position_on_path: float = 0.0,
        angle: float = 0,
        mode: "Modes" = "a",
        # mode: Mode = Mode.ADDITION,
        tag: Optional[str] = None,
    ) -> T:
        """
        Text that optionally follows a path.
    
        The text that is created can be combined as with other sketch features by specifying
        a mode or rotated by the given angle.  In addition, the text will follow the path defined
        by edges that have been previously created with arc or segment. The positionOnPath
        parameter can be used to shift the text along the path to achieve precise positioning.
    
        Examples::
    
            simple_text = cq.Sketch().text("simple", 10, angle=10)
    
            loop_sketch = (
                cq.Sketch()
                    .arc((-50, 0), 50, 90, 270)
                    .arc((50, 0), 50, 270, 270)
                    .text("loop_" * 20, 10)
            )
    
        Args:
            txt: text to be rendered
            fontsize: size of the font in model units
            font: font name
            font_path: system path to font file
            font_style: one of ["regular", "bold", "italic"]. Defaults to "regular".
            halign: horizontal alignment, one of ["center", "left", "right"].
                Defaults to "left".
            valign: vertical alignment, one of ["center", "top", "bottom"].
                Defaults to "center".
            position_on_path: the relative location on path to locate the text, between 0.0 and 1.0.
                Defaults to 0.0.
            angle: rotation angle. Defaults to 0.0.
            mode: combination mode, one of ["a","s","i","c"]. Defaults to "a".
            tag: feature label. Defaults to None.
    
        Returns:
            a Sketch object
    
        """
    def vals(self) -> list[Union["Vertex", "Wire", "Edge", "Face"]]:
        """Return a list of selected values
    
        Examples::
    
            face_objects = cq.Sketch().text("test", 10).faces().vals()
    
        Raises:
            ValueError: Nothing selected
    
        Returns:
            list[Union[Vertex, Wire, Edge, Face]]: List of selected occ_impl objects
    
        """
    def val(self) -> Union["Vertex", "Wire", "Edge", "Face"]:
        """Return the first selected value
    
        Examples::
    
            edge_object = cq.Sketch().arc((-50, 0), 50, 90, 270).edges().val()
    
        Raises:
            ValueError: Nothing selected
    
        Returns:
            Union[Vertex, Wire, Edge, Face]: The first selected occ_impl object
    
        """
    def add(
        self: T,
        obj: Union["Wire", "Edge", "Face"],
        angle: float = 0,
        mode: "Modes" = "a",
        # mode: Mode = Mode.ADDITION,
        tag: Optional[str] = None,
    ) -> T:
        """add
    
        Add a Wire, Edge or Face to this sketch
    
        Examples::
    
            added_edge = cq.Sketch().arc((50, 0), 50, 270, 270).add(external_edge).assemble()
    
        Args:
            obj (Union[Wire, Edge, Face]): the object to add
            angle (float, optional): rotation angle. Defaults to 0.0.
            mode (Modes, optional): combination mode, one of ["a","s","i","c"]. Defaults to "a".
            tag (Optional[str], optional): feature label. Defaults to None.
    
        Returns:
            Updated sketch
    
        """
    def mirror_x(self):
        """Mirror across X axis
    
        Mirror the selected items across the X axis
    
        Raises:
            ValueError: Nothing selected
    
        Returns:
            Updated Sketch
        """
    def mirror_y(self):
        """Mirror across Y axis
    
        Mirror the selected items across the Y axis
    
        Raises:
            ValueError: Nothing selected
    
        Returns:
            Updated Sketch
        """
    def spline(
        self: T,
        *pts: Union[Point, str],
        tangents: Iterable[Union[Point, str]] = None,
        tangent_scalars: Iterable[float] = None,
        periodic: bool = False,
        # mode: Mode = Mode.ADDITION,
        tag: str = None,
        for_construction: bool = False,
    ) -> T:
        """spline
    
        Construct a spline
    
        Examples::
    
            boomerang = (
                cq.Sketch()
                .center_arc(center=(0, 0), radius=10, start_angle=0, arc_size=90, tag="c")
                .spline("c@1", (10, 10), "c@0", tangents=("c@1", "c@0"))
            )
    
        Args:
            pts (Union[Point,str]): sequence of points or snaps defining the spline
            tangents (Iterable[Union[Point, str]], optional): spline tangents or snaps. Defaults to None.
            tangent_scalars (Iterable[float], optional): tangent multipliers to refine the shape.
                Defaults to None.
            periodic (bool, optional): creation of periodic curves. Defaults to False.
            tag (str, optional): feature label. Defaults to None.
            for_construction (bool, optional): edge used to build other geometry. Defaults to False.
    
        Returns:
            Updated Sketch
        """
    def polyline(
        self,
        *pts: Union[Point, str],
        # mode: Mode = Mode.ADDITION,
        tag: str = None,
        for_construction: bool = False,
    ):
        """Polyline
    
        A polyline defined by two or more points or snaps
    
        Examples::
    
            pline = cq.Sketch().polyline((0, 0), (1, 1), (2, 0), (3, 1), (4, 0))
    
            triangle = (
                cq.Sketch()
                .polyline((0, 0), (2, 0), tag="base")
                .polyline("base@0", (1, 1), tag="left")
                .polyline("left@1", "base@1")
            )
    
        Args:
            pts (Union[Point,str]): sequence of points or snaps
            tag (str, optional): feature label. Defaults to None.
            for_construction (bool, optional): edge used to build other geometry. Defaults to False.
    
        Raises:
            ValueError: polyline requires two or more pts
    
        Returns:
            Updated sketch
        """
    def center_arc(
        self,
        center: Union[Point, str],
        radius: float,
        start_angle: float,
        arc_size: float,
        # mode: Mode = Mode.ADDITION,
        tag: str = None,
        for_construction: bool = False,
    ):
        """Center Arc
    
        A partial or complete circle with defined center
    
        Examples::
    
            chord = (
                cq.Sketch()
                .center_arc(center=(0, 0), radius=10, start_angle=0, arc_size=60, tag="c")
                .polyline("c@1", "c@0")
                .assemble()
            )
    
        Args:
            center (Union[Point, str]): point or snap defining the arc center
            radius (float): arc radius
            start_angle (float): in degrees, where zero corresponds to the +vs X axis
            arc_size (float): size of arc counter clockwise from start
            tag (str, optional): feature label. Defaults to None.
            for_construction (bool, optional): edge used to build other geometry. Defaults to False.
    
        Returns:
            Updated sketch
        """
    def three_point_arc(
        self: T,
        *pts: Union[Point, str],
        # mode: Mode = Mode.ADDITION,
        tag: str = None,
        for_construction: bool = False,
    ) -> T:
        """Three Point Arc
    
        Construct an arc through a sequence of points or snaps
    
        Examples::
    
            three_point_arc = (
                cq.Sketch()
                .polyline((0, 10), (0, 0), (10, 0), tag="p")
                .three_point_arc("p@0", "p@0.5", "p@1")
            )
    
        Args:
            pts (Union[Point,str]): sequence of points or snaps
            tag (str, optional): feature label. Defaults to None.
            for_construction (bool, optional): edge used to build other geometry. Defaults to False.
    
        Raises:
            ValueError: three_point_arc requires three points
    
        Returns:
            Updated sketch
    
        """
    def tangent_arc(
        self,
        *pts: Union[Point, str],
        tangent: Point = None,
        tangent_from_first: bool = True,
        # mode: Mode = Mode.ADDITION,
        tag: Optional[str] = None,
        for_construction: bool = False,
    ):
        """Tangent Arc
    
        Create an arc defined by the provided points and a tangent
    
        Examples::
    
            tangent_arc = (
                cq.Sketch()
                .center_arc(center=(0, 0), radius=10, start_angle=0, arc_size=90, tag="c")
                .tangent_arc("c@0.5", (10, 10), tag="t")
            )
    
        Args:
            pts (Union[Point,str]): start and end point or snap of arc
            tangent (Point, optional): tangent value if snaps aren't used. Defaults to None.
            tangent_from_first (bool, optional) point to align tangent to. Note that
                using a value of False will build the arc in the reverse direction. Defaults to True.
            tag (str, optional): feature label. Defaults to None.
            for_construction (bool, optional): edge used to build other geometry. Defaults to False.
    
        Raises:
            ValueError: tangentArc requires two points
            ValueError: no tangent provided
    
        Returns:
            Updated sketch
        """
    def push_points(
        self: T,
        *pts: Union[Union[Point, str], Location],
        tag: Optional[str] = None,
    ) -> T:
        """Select the provided points
    
        Add the provided points, locations or snaps to current selections
    
        Examples::
    
            circles_on_arc = (
                cq.Sketch()
                .center_arc(center=(0, 0), radius=10, start_angle=0, arc_size=90, tag="c")
                .push_points("c@0.1", "c@0.5", "c@0.9")
                .circle(1)
            )
    
        Args:
            pts (Union[Point,str,Location]): points to add
            tag (str, optional): feature label. Defaults to None.
    
        Returns:
            Updated sketch
        """
    def bounding_box(
        self: T,
        mode: "Modes" = "a",
        # mode: Mode = Mode.ADDITION,
        tag: Optional[str] = None,
    ) -> T:
        """Bounding Box
    
        Create bounding box(s) around selected features. These bounding boxes can
        be used to directly construct shapes or to locate other shapes.
    
        Examples::
    
            mickey = (
                cq.Sketch()
                .circle(10)
                .faces()
                .bounding_box(tag="bb", mode="c")
                .faces(tag="bb")
                .vertices(">Y")
                .circle(7)
                .clean()
            )
    
            bounding_box_center = (
                cq.Sketch()
                .segment((0, 0), (10, 0))
                .segment((0, 5))
                .close()
                .assemble(tag="t")
                .faces(tag="t")
                .circle(0.5, mode="s")
                .faces(tag="t")
                .bounding_box(tag="bb", mode="c")
                .faces(tag="bb")
                .rect(1, 1, mode="s")
            )
    
            circles = (
                cq.Sketch()
                .rarray(40, 40, 2, 2)
                .circle(10)
                .reset()
                .faces()
                .bounding_box(tag="bb", mode="c")
                .vertices(tag="bb")
                .circle(7)
                .clean()
            )
    
        Args:
            tag (Optional[str], optional): feature label. Defaults to None.
    
        Returns:
            Updated sketch
        """
class Wire(object):
    def makeRect(
        width: float, height: float, center: Vector, normal: Vector, xDir: Vector = None
    ) -> "Wire":
        """Make Rectangle
    
        Make a Rectangle centered on center with the given normal
    
        Args:
            width (float): width (local X)
            height (float): height (local Y)
            center (Vector): rectangle center point
            normal (Vector): rectangle normal
            xDir (Vector, optional): x direction. Defaults to None.
    
        Returns:
            Wire: The centered rectangle
        """
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
    def sortedEdges(self, tolerance: float = 1e-5):
        """Edges sorted by position
    
        Extract the edges from the wire and sort them such that the end of one
        edge is within tolerance of the start of the next edge
    
        Args:
            tolerance (float, optional): Max separation between sequential edges.
                Defaults to 1e-5.
    
        Raises:
            ValueError: Wire is disjointed
    
        Returns:
            list(Edge): Edges sorted by position
        """
class Edge(object):
    def distributeLocations(
        self: Union["Wire", "Edge"],
        count: int,
        start: float = 0.0,
        stop: float = 1.0,
        positions_only: bool = False,
    ) -> list[Location]:
        """Distribute Locations
    
        Distribute locations along edge or wire.
    
        Args:
            count (int): Number of locations to generate
            start (float, optional): position along Edge|Wire to start. Defaults to 0.0.
            stop (float, optional): position along Edge|Wire to end. Defaults to 1.0.
            positions_only (bool, optional): only generate position not orientation. Defaults to False.
    
        Raises:
            ValueError: count must be two or greater
    
        Returns:
            list[Location]: locations distributed along Edge|Wire
        """
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
    def transformed(
        self, rotate: VectorLike = (0, 0, 0), offset: VectorLike = (0, 0, 0)
    ) -> "Shape":
        """Transform Shape
    
        Rotate and translate the Shape by the three angles (in degrees) and offset.
        Functions exactly like the Workplane.transformed() method but for Shapes.
    
        Args:
            rotate (VectorLike, optional): 3-tuple of angles to rotate, in degrees. Defaults to (0, 0, 0).
            offset (VectorLike, optional): 3-tuple to offset. Defaults to (0, 0, 0).
    
        Returns:
            Shape: transformed object
        """
    def _apply_transform(self: "Shape", Tr: gp_Trsf) -> "Shape":
        """_apply_transform
    
        Apply the provided transformation matrix to a copy of Shape
    
        Args:
            Tr (gp_Trsf): transformation matrix
    
        Returns:
            Shape: copy of transformed Shape
        """
    def copy(self: "Shape") -> "Shape":
        """
        Creates a new object that is a copy of this object.
        """
    def clean(self: "Shape") -> "Shape":
        """clean - remove internal edges"""
    
        upgrader = ShapeUpgrade_UnifySameDomain(self.wrapped, True, True, True)
        upgrader.AllowInternalEdges(False)
        upgrader.Build()
        shape_copy: "Shape" = self.copy()
        shape_copy.wrapped = downcast(upgrader.Shape())
        return shape_copy
    
    
    
    def fix(self: "Shape") -> "Shape":
        """fix - try to fix shape if not valid"""
        if not self.isValid():
            shape_copy: "Shape" = self.copy()
            shape_copy.wrapped = fix(self.wrapped)
    
            return shape_copy
    
        return self
    
    
    
    def located(self: "Shape", loc: Location) -> "Shape":
        """located
    
        Apply a location in absolute sense to a copy of self
    
        Args:
            loc (Location): new absolute location
    
        Returns:
            Shape: copy of Shape at location
        """
    def moved(self: "Shape", loc: Location) -> "Shape":
        """moved
    
        Apply a location in relative sense (i.e. update current location) to a copy of self
    
        Args:
            loc (Location): new location relative to current location
    
        Returns:
            Shape: copy of Shape moved to relative location
        """
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
        tolerance: float = 0.1,
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
    def makeFingerJointFaces(
        self: "Shape",
        fingerJointEdges: list["Edge"],
        materialThickness: float,
        targetFingerWidth: float,
        kerfWidth: float = 0.0,
    ) -> list["Face"]:
        """makeFingerJointFaces
    
        Extract Faces from the given Shape (Solid or Compound) and create Faces with finger
        joints cut into the given Edges.
    
        Args:
            self (Shape): the base shape defining the finger jointed object
            fingerJointEdges (list[Edge]): the Edges to convert to finger joints
            materialThickness (float): thickness of the notch from edge
            targetFingerWidth (float): approximate with of notch - actual finger width
                will be calculated such that there are an integer number of fingers on Edge
            kerfWidth (float, optional): Extra size to add (or subtract) to account
                for the kerf of the laser cutter. Defaults to 0.0.
    
        Raises:
            ValueError: provide Edge is not shared by two Faces
    
        Returns:
            list[Face]: faces with finger joint cut into selected edges
        """
    def maxFillet(
        self: "Shape",
        edgeList: Iterable["Edge"],
        tolerance=0.1,
        maxIterations: int = 10,
    ) -> float:
        """Find Maximum Fillet Size
    
        Find the largest fillet radius for the given Shape and Edges with a
        recursive binary search.
    
        Args:
            edgeList (Iterable[Edge]): a list of Edge objects, which must belong to this solid
            tolerance (float, optional): maximum error from actual value. Defaults to 0.1.
            maxIterations (int, optional): maximum number of recursive iterations. Defaults to 10.
    
        Raises:
            RuntimeError: failed to find the max value
            ValueError: the provided Shape is invalid
    
        Returns:
            float: maximum fillet radius
    
        As an example:
            max_fillet_radius = my_shape.maxFillet(shape_edges)
        or:
            max_fillet_radius = my_shape.maxFillet(shape_edges, tolerance=0.5, maxIterations=8)
    
        """
class Location(object):
    def __repr__(self):
        """To String
    
        Convert Location to String for display
    
        Returns:
            Location as String
        """
    def position(self):
        """Extract Position component
    
        Returns:
            Vector: Position part of Location
        """
    def rotation(self):
        """Extract Rotation component
    
        Returns:
            Vector: Rotation part of Location
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
