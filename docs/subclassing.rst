#############################
Sub-classing CadQuery Objects
#############################
As CadQuery is a python CAD library it is based on the concept of classes. One
of the most important CadQuery base class is Shape which provides both an
OpenCascade object contained in the ``wrapped`` attribute and pure python
attributes such as ``forConstruction`` (a bool) and ``label`` (a str).  Shape provides
a wealth of python methods to manipulate Shapes, such as ``rotate()`` and ``mirror()``.

Solid and Edge are two of the many sub-classes of Shape - more formally
Solid is a derived class of the Shape base class - which inherit the
methods of Shape. The cq_warehouse.extensions package contains
changes to the CadQuery core functionality which allows users to also create
derived classes from the Shape base class. These user derived classes also
inherit the wealth of Shape methods (also note that future additions to Shape
will automatically apply to user derived classes).

The cq_warehouse.fastener ``Nut`` class is an example of a derived class - specifically
of Solid and is defined as follows:

.. code-block:: python

    class Nut(ABC, Solid):

and therefore inherits the methods of Solid and Shape. ``Nut`` is itself
a base class for a whole series of different classes of nuts like ``DomedCapNut``
which is defined as follows:

.. code-block:: python

    class DomedCapNut(Nut):

Expressed as a diagram, the inheritance looks like this:

.. graphviz::

    digraph {
        splines=false;
        Shape -> Solid;
        Mixin3D -> Solid;
        Solid -> Nut;
        ABC -> Nut;
        Nut -> BradTeeNut;
        Nut -> DomedCapNut;
        Nut -> HexNut;
        Ellipsis [shape=none  label="&#8230;" fontsize=30];
        Nut -> SquareNut;
        {rank=same BradTeeNut DomedCapNut HexNut Ellipsis SquareNut}       // align on same rank
        // invisible edges to order nodes
        edge[style=invis]
        BradTeeNut->DomedCapNut->HexNut->Ellipsis->SquareNut
    }

.. note::
    ``Nut`` is also a sub-class of ``ABC`` the Abstract Base Class which provides
    many useful features when creating derived classes. ``Mixin3D`` provides
    a set of methods specific to 3D objects like ``chamfer()``.

Instantiation of one of the nut sub-classes is done as follows:

.. code-block:: python

    nut = DomedCapNut(size="M6-1", fastener_type="din1587")

where ``nut`` is a subclass of Solid and therefore the many Solid methods
apply to ``nut`` like this:

.. code-block:: python

    nut_translated = nut.translate((20, 20, 10))

Creating Custom Sub-Classes
===========================
To create custom sub-classes of Shape, there are three necessary steps and
one extra step for complex classes:

1. The class definition must include the base class, e.g: ``class MyCustomShape(Solid):``.
2. All parameters must be stored as instance attributes so a copy can be created.
3. The class' ``__init__`` method must initialize the base class
   object: ``super().__init__(obj.wrapped)``. Recall that the Shape
   class stores the OpenCascade CAD object in the ``wrapped`` attribute
   which is what is passed into the ``__init__`` method.
4. Create a custom ``copy()`` method for complex classes only (see below).

Here is a working example of a ``FilletBox`` (i.e.a box with rounded corners)
that is a sub-class of Solid:

.. code-block:: python

    class FilletBox(Solid):
        """A filleted box

        A box of the given dimensions with all of the edges filleted.

        Args:
            length (float): box length
            width (float): box width
            height (float): box height
            radius (float): edge radius
            pnt (VectorLike, optional): minimum x,y,z point. Defaults to (0, 0, 0).
            dir (VectorLike, optional): direction of height. Defaults to (0, 0, 1).
        """

        def __init__(
            self,
            length: float,
            width: float,
            height: float,
            radius: float,
            pnt: VectorLike = (0, 0, 0),
            dir: VectorLike = (0, 0, 1),
        ):
            # Store the attributes so the object can be copied
            self.length = length
            self.width = width
            self.height = height
            self.radius = radius
            self.pnt = pnt
            self.dir = dir

            # Create the object
            obj = Solid.makeBox(length, width, height, pnt, dir)
            obj = obj.fillet(radius, obj.Edges())
            # Initialize the Solid class with the new OCCT object
            super().__init__(obj.wrapped)

Internally, Shape has a ``copy()`` method that is able copy derived
classes with a single OpenCascade object stored in the ``wrapped`` attribute.
If a custom class contains attributes that can't be copied with the python
``copy.deepcopy()`` method, that class will need to contain a custom ``copy()``
method. This custom copy method can be based off the cq_warehouse extended
copy method shown here:

.. code-block:: python

    from OCP.BRepBuilderAPI import BRepBuilderAPI_Copy

    def copy(self: "Shape") -> "Shape":
        """
        Creates a new object that is a copy of this object.
        """
        # The wrapped object is a OCCT TopoDS_Shape which can't be pickled or copied
        # with the standard python copy/deepcopy, so create a deepcopy 'memo' with this
        # value already copied which causes deepcopy to skip it.
        memo = {id(self.wrapped): BRepBuilderAPI_Copy(self.wrapped).Shape()}
        copy_of_shape = copy.deepcopy(self, memo)
        return copy_of_shape

Converting Compound to Solid
============================
When creating custom Solid sub-classed objects one my find that a Compound object
has been created instead of the desired Solid object (use the ``type(<my_object>)``
function to find the class of an object). As a Compound object is a fancy list
of other Shapes it is often possible to extract the desired Solid from the
Compound. The following code will check for this condition and extract the
Solid object for initialization of the base class:

.. code-block:: python

        if isinstance(obj, Compound) and len(obj.Solids()) == 1:
            super().__init__(obj.Solids()[0].wrapped)
        else:
            super().__init__(obj.wrapped)

where ``obj`` is the custom object created by this sub-class. If the Compound is
always generated by the custom class, the ``if`` check can be eliminated.

If the desired object is a Compound (e.g. cq_warehouse bearings) the class
should sub-class Compound and initialize the base (Compound) class in the
normal way.
