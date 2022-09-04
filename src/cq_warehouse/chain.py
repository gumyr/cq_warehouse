"""

Parametric Chains

name: chain.py
by:   Gumyr
date: July 9th 2021

desc:

		This python/cadquery code is a parameterized chain generator.  Given an
array of sprockets data and sprocket locations, a chain can be generated that
wraps around the sprockets - counter clockwise (positive_chain_wrap=True) or
clock wise (positive_chain_wrap=False) - meshing with the teeth of the
sprockets.

		Note that the chain is perfectly tight as it wraps around the sprockets and
does not support any slack. Therefore, as the chain wraps back around to the
first link it will either overlap or gap this link. Control this by changing the
locations of the sprockets.

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
from math import asin, pi, degrees, sqrt, atan2, floor, nan
import warnings
from functools import cache
from typing import Union, Tuple, List
from cadquery import Vector, Location, Workplane, Assembly, Plane, Shape
from cadquery.occ_impl.shapes import VectorLike
import cq_warehouse.extensions
from cq_warehouse.sprocket import Sprocket


MM = 1
INCH = 25.4 * MM
ENTRY = 0  # chain_angles tuple index for sprocket ..
EXIT = 1  # .. entry and exit angles

#
#  =============================== CLASSES ===============================
#
class Chain:
    """Roller Chain

    Create a new chain object as defined by the given parameters. The input parameter
    defaults are appropriate for a standard bicycle chain.

    Args:
        spkt_teeth (list[int]): list of the number of teeth on each sprocket the chain will wrap around
        spkt_locations (list[VectorLike]): location of the sprocket centers
        positive_chain_wrap (list[bool]): the direction chain wraps around the sprockets, True for counter
            clockwise viewed from positive Z
        chain_pitch (float): distance between two adjacent pins in a single link. Defaults to 1/2 inch.
        roller_diameter (float): size of the cylindrical rollers within the chain. Defaults to 5/16 inch.
        roller_length (float): distance between the inner links, i.e. the length of the link rollers.
            Defaults to 3/32 inch.
        link_plate_thickness (float): thickness of the link plates (both inner and outer link plates).
            Defaults to 1 mm.
        spkt_normal (VectorLike): direction of the sprocket axes - only required for two sprocket configurations.
            Defaults to (0, 0, 1).

    Attributes:
        pitch_radii (float): radius of the circle formed by the center of the chain rollers on each sprocket
        chain_links (int): length of the chain in links
        num_rollers (int): number of link rollers in the entire chain
        roller_loc (list[Vector]): location of each roller in the chain
        chain_angles (list[tuple[float,float]]): chain entry and exit angles in degrees for each sprocket
        spkt_initial_rotation (list[float]): angle in degrees to rotate each sprocket in-order to align the
            teeth with the gaps in the chain
        chain_plane (Plane): the plane defined by the location of the sprockets
        cq_object: cadquery chain object

    Raises:
        ValueError: invalid roller diameter
        ValueError: length of spkt_teeth, spkt_locations, positive_chain_wrap not equal
        ValueError: sprockets in the same location

    Examples:

        .. code-block:: python

            c = Chain(
                spkt_teeth=[32, 32],
                spkt_locations=[(-300, 0), (300, 0)],
                positive_chain_wrap=[True, True]
            )

            print(c.spkt_initial_rotation)       # [5.625, 193.82627377380086]

            c.cq_object.save('chain.step')       # save the cadquery assembly as a STEP file

    """

    @property
    def pitch_radii(self) -> List[float]:
        """The radius of the circle formed by the center of the chain rollers on each sprocket"""
        return [
            Sprocket.sprocket_pitch_radius(n, self.chain_pitch) for n in self.spkt_teeth
        ]

    @property
    def chain_links(self) -> float:
        """the length of the chain in links"""
        return self._chain_links

    @property
    def num_rollers(self) -> int:
        """the number of link rollers in the entire chain"""
        return self._num_rollers

    @property
    def roller_loc(self) -> List[Vector]:
        """the location of each roller in the chain"""
        roller_world_locations = [
            self._chain_plane.fromLocalCoords(l.toTuple()) for l in self._roller_loc
        ]
        return roller_world_locations

    @property
    def chain_angles(self) -> "List[Tuple(float,float)]":
        """the chain entry and exit angles in degrees for each sprocket"""
        return self._chain_angles

    @property
    def spkt_initial_rotation(self) -> List[float]:
        """a in degrees to rotate each sprocket in-order to align the teeth with the gaps
        in the chain"""
        return self._spkt_initial_rotation

    @property
    def chain_plane(self) -> Plane:
        """the plane defined by the location of the sprockets"""
        return self._chain_plane

    @property
    def cq_object(self) -> Assembly:
        """the cadquery chain object"""
        return self._cq_object

    def __init__(
        self,
        spkt_teeth: list[int],
        spkt_locations: list[VectorLike],
        positive_chain_wrap: list[bool],
        chain_pitch: float = (1 / 2) * INCH,
        roller_diameter: float = (5 / 16) * INCH,
        roller_length: float = (3 / 32) * INCH,
        link_plate_thickness: float = 1.0 * MM,
        spkt_normal: VectorLike = (0, 0, 1),
    ):
        """Validate inputs and create the chain assembly object"""
        self.spkt_teeth = spkt_teeth
        self.spkt_locations = spkt_locations
        self.positive_chain_wrap = positive_chain_wrap
        self.chain_pitch = chain_pitch
        self.roller_diameter = roller_diameter
        self.roller_length = roller_length
        self.link_plate_thickness = link_plate_thickness
        self.spkt_normal = spkt_normal

        if not (
            isinstance(spkt_teeth, list) and all(isinstance(s, int) for s in spkt_teeth)
        ):
            raise ValueError("spkt_teeth must be a list of int")
        if not (
            isinstance(spkt_locations, list)
            and all(isinstance(v, (Vector, tuple)) for v in spkt_locations)
        ):
            raise ValueError("spkt_locations must be a list")
        if not (
            isinstance(positive_chain_wrap, list)
            and all(isinstance(b, bool) for b in positive_chain_wrap)
        ):
            raise ValueError("positive_chain_wrap must be a list")
        if not (len(spkt_teeth) == len(spkt_locations) == len(positive_chain_wrap)):
            raise ValueError(
                "Length of spkt_teeth, spkt_locations, positive_chain_wrap not equal"
            )
        if len(spkt_teeth) < 2:
            raise ValueError("At least two sprockets are required")
        """Ensure that the roller would fit in the chain"""
        if self.roller_diameter >= self.chain_pitch:
            raise ValueError(
                f"roller_diameter {self.roller_diameter} is too large for chain_pitch {self.chain_pitch}"
            )
        if len(set(Vector(loc).toTuple() for loc in spkt_locations)) != len(
            spkt_locations
        ):
            raise ValueError("At least two sprockets are in the same location")

        # Store the number of sprockets in this chain
        self._num_spkts = len(self.spkt_teeth)

        self.x_direction = (
            Vector(self.spkt_locations[1]) - Vector(self.spkt_locations[0])
        ).normalized()
        if self._num_spkts > 2:
            self.spkt_normal = self.x_direction.cross(
                (
                    Vector(self.spkt_locations[2]) - Vector(self.spkt_locations[0])
                ).normalized()
            )
        self._chain_plane = Plane(
            origin=Vector(0, 0, 0),
            xDir=self.x_direction,
            normal=self.spkt_normal,
        )

        # Store the locations of the sprockets as a list of Vector in local coordinates
        # as defined by the plane the sprocket locations create
        self._spkt_locs = [
            self._chain_plane.toLocalCoords(Vector(l)) for l in self.spkt_locations
        ]

        self._calc_entry_exit_angles()  # Determine critical chain angles
        self._calc_segment_lengths()  # Determine the chain segment lengths
        self._calc_roller_locations()  # Determine the location of each chain roller
        self._assemble_chain()  # Build the Assembly for the chain

    def _calc_spkt_separation(self) -> List[float]:
        """Determine the distance between sprockets"""
        return [
            (self._spkt_locs[(s + 1) % self._num_spkts] - self._spkt_locs[s]).Length
            for s in range(self._num_spkts)
        ]

    def _calc_entry_exit_angles(self):
        """
        Calculate the angle that the chain enters and departs the sprockets
        1- determine the angle between the sprocket centers
        2- determine the extra angle resulting from different sized sprockets:
           asin((Rn+Rn-1)/separation)
        3- based on the relative rotational direction of the two sprockets,
           determine the angle the chain will exit the first sprocket
        """
        spkt_sep = self._calc_spkt_separation()

        base_a = [
            90
            + degrees(
                atan2(
                    self._spkt_locs[s].y - self._spkt_locs[(s + 1) % self._num_spkts].y,
                    self._spkt_locs[s].x - self._spkt_locs[(s + 1) % self._num_spkts].x,
                )
            )
            for s in range(self._num_spkts)
        ]

        exit_a = []
        for s in range(self._num_spkts):
            if (
                self.positive_chain_wrap[s]
                and self.positive_chain_wrap[(s + 1) % self._num_spkts]
            ):
                exit_a.append(
                    base_a[s]
                    - 90
                    + degrees(
                        asin(
                            (
                                self.pitch_radii[s]
                                - self.pitch_radii[(s + 1) % self._num_spkts]
                            )
                            / spkt_sep[s]
                        )
                    )
                )
            elif (
                self.positive_chain_wrap[s]
                and not self.positive_chain_wrap[(s + 1) % self._num_spkts]
            ):
                exit_a.append(
                    base_a[s]
                    - 90
                    + degrees(
                        asin(
                            (
                                self.pitch_radii[s]
                                + self.pitch_radii[(s + 1) % self._num_spkts]
                            )
                            / spkt_sep[s]
                        )
                    )
                )
            elif (
                not self.positive_chain_wrap[s]
                and self.positive_chain_wrap[(s + 1) % self._num_spkts]
            ):
                exit_a.append(
                    base_a[s]
                    + 90
                    - degrees(
                        asin(
                            (
                                self.pitch_radii[s]
                                + self.pitch_radii[(s + 1) % self._num_spkts]
                            )
                            / spkt_sep[s]
                        )
                    )
                )
            else:
                exit_a.append(
                    base_a[s]
                    + 90
                    - degrees(
                        asin(
                            (
                                self.pitch_radii[s]
                                - self.pitch_radii[(s + 1) % self._num_spkts]
                            )
                            / spkt_sep[s]
                        )
                    )
                )

        # The entry a of a sprocket is the same the exit a of the previous sprocket
        entry_a = [
            exit_a[(s - 1) % self._num_spkts] + 180
            if self.positive_chain_wrap[s]
            != self.positive_chain_wrap[(s - 1) % self._num_spkts]
            else exit_a[(s - 1) % self._num_spkts]
            for s in range(self._num_spkts)
        ]

        # Record the entry and exit angles as tuples per sprocket
        self._chain_angles = [*zip(entry_a, exit_a)]

    def _calc_segment_lengths(self):
        """Determine the length of the chain between and in contact with the sprockets"""

        # Determine the distance between sprockets
        spkt_sep = self._calc_spkt_separation()

        # Calculate the distance the chain spans between two sprockets
        line_l = [
            sqrt(
                pow(spkt_sep[s], 2)
                - pow(
                    self.pitch_radii[s] - self.pitch_radii[(s + 1) % self._num_spkts], 2
                )
            )
            if self.positive_chain_wrap[s]
            == self.positive_chain_wrap[(s + 1) % self._num_spkts]
            else sqrt(
                pow(spkt_sep[s], 2)
                - pow(
                    self.pitch_radii[s] + self.pitch_radii[(s + 1) % self._num_spkts], 2
                )
            )
            for s in range(self._num_spkts)
        ]

        # Calculate the length of the arc where the chain is in contact with the sprocket
        self._arc_a = [
            (self._chain_angles[s][EXIT] - self._chain_angles[s][ENTRY] + 360) % 360
            if self.positive_chain_wrap[s]
            else (self._chain_angles[s][ENTRY] - self._chain_angles[s][EXIT] + 360)
            % 360
            for s in range(self._num_spkts)
        ]
        arc_l = [
            abs(self._arc_a[s] * 2 * pi * self.pitch_radii[s] / 360)
            for s in range(self._num_spkts)
        ]

        # Generate a list of all the chain segment lengths [arc,line,arc,...]
        self._segment_lengths = Chain._interleave_lists(arc_l, line_l)

        # Generate a list of the sum of the chain segment lengths [arc,line,arc,...]
        self._segment_sums = Chain._gen_mix_sum_list(arc_l, line_l)

        # The chain length is the last of the segment sums
        self._chain_length = self._segment_sums[-1]

        # Length of the chain in links
        self._chain_links = self._chain_length / self.chain_pitch

        #
        # Warn the user if the length in links creates a gap
        # (The user needs to repositioning the ..
        # .. sprockets to achieve a near integer number of links)
        if self._chain_links - floor(self._chain_links) > 0.5:
            warnings.warn(message="Chain has missing links", category=Warning)

        # Round to the nearest number of rollers - note, should be close to ..
        # .. an integer to avoid gaps in the chain and positioning errors
        self._num_rollers = floor(self._chain_length / self.chain_pitch)

    def _calc_roller_locations(self):
        """Determine the location of all the chain rollers"""

        # Calculate the 2D point where the chain enters and exits the sprockets
        spkt_entry_exit_loc = [
            [
                self._spkt_locs[s]
                + Vector(0, self.pitch_radii[s]).rotateZ(self._chain_angles[s][ENTRY]),
                self._spkt_locs[s]
                + Vector(0, self.pitch_radii[s]).rotateZ(self._chain_angles[s][EXIT]),
            ]
            for s in range(self._num_spkts)
        ]

        self._roller_loc = []
        roller_a_per_spkt = []
        for i in range(self._num_rollers):
            roller_distance = (i * self.chain_pitch) % self._chain_length
            roller_segment = Chain._find_segment(roller_distance, self._segment_sums)
            roller_spkt = floor(roller_segment / 2)
            along_segment = (
                1
                - (self._segment_sums[roller_segment] - roller_distance)
                / self._segment_lengths[roller_segment]
            )
            if roller_segment % 2 == 0 and self.positive_chain_wrap[roller_spkt]:
                roller_a = (
                    self._chain_angles[roller_spkt][ENTRY]
                    + self._arc_a[roller_spkt] * along_segment
                )
            elif roller_segment % 2 == 0 and not self.positive_chain_wrap[roller_spkt]:
                roller_a = (
                    self._chain_angles[roller_spkt][ENTRY]
                    - self._arc_a[roller_spkt] * along_segment
                )
            else:
                roller_a = nan

            if roller_segment % 2 == 0:  # on a sprocket
                self._roller_loc.append(
                    self._spkt_locs[roller_spkt]
                    + Vector(0, self.pitch_radii[roller_spkt]).rotateZ(roller_a)
                )
            else:  # between two sprockets
                self._roller_loc.append(
                    (
                        spkt_entry_exit_loc[(roller_spkt + 1) % self._num_spkts][0]
                        - spkt_entry_exit_loc[roller_spkt][1]
                    )
                    * along_segment
                    + spkt_entry_exit_loc[roller_spkt][1]
                )
            # For the rollers that are in contact with a sprocket, record their angles
            if roller_segment % 2 == 0:
                roller_a_per_spkt.append([roller_spkt, roller_a])

        # Filter the roller as to just the first one per sprocket
        first_roller_a_per_spkt = [
            roller_a_per_spkt[
                [roller_a_per_spkt[i][0] for i in range(len(roller_a_per_spkt))].index(
                    s
                )
            ][1]
            for s in range(self._num_spkts)
        ]
        #
        # Calculate the angle to rotate the sprockets such that the teeth are between the rollers
        self._spkt_initial_rotation = [
            first_roller_a_per_spkt[s] + 180 / self.spkt_teeth[s]
            for s in range(self._num_spkts)
        ]

    def _assemble_chain(self):
        """Given the roller locations assemble the chain"""
        #
        # Initialize the chain assembly
        self._cq_object = Assembly(None, name="chain_links")

        #
        # Add the links to the chain assembly
        for i in range(self._num_rollers):
            # Calculate the bend in the chain at each roller
            link_rotation_a_d = degrees(
                atan2(
                    self._roller_loc[(i + 1) % self._num_rollers].y
                    - self._roller_loc[i].y,
                    self._roller_loc[(i + 1) % self._num_rollers].x
                    - self._roller_loc[i].x,
                )
            )
            link_location = Location(
                self._chain_plane.fromLocalCoords(self._roller_loc[i].toTuple())
            )
            # Add the link after aligning it with the world coordinate system
            self._cq_object.add(
                self._chain_plane.fromLocalCoords(
                    Chain.make_link(inner=i % 2 == 0)
                    .val()
                    .rotate((0, 0, 0), Vector(0, 0, 1), link_rotation_a_d)
                ),
                name="link" + str(i),
                loc=link_location,
            )

    def assemble_chain_transmission(
        self, spkts: list[Sprocket]
    ) -> Assembly:
        """Build Socket/Chain Assembly

        Create the transmission assembly from sprockets for a chain

        Args:
            spkts: sprockets to include in transmission

        Returns:
            Chain wrapped around sprockets
        """
        if not isinstance(spkts, list) or not all(
            isinstance(s, Sprocket) for s in spkts
        ):
            raise ValueError("spkts must be a list of Sprocket")

        transmission = Assembly(None, name="transmission")

        for spkt_num, spkt in enumerate(spkts):
            spktname = "spkt" + str(spkt_num)
            transmission.add(
                spkt.rotate(
                    (0, 0, 0),
                    self.spkt_normal,
                    self._spkt_initial_rotation[spkt_num],
                ).translate(self.spkt_locations[spkt_num]),
                name=spktname,
            )
        transmission.add(self._cq_object, name="chain")
        return transmission

    @staticmethod
    @cache
    def make_link(
        chain_pitch: float = 0.5 * INCH,
        link_plate_thickness: float = 1 * MM,
        inner: bool = True,
        roller_length: float = (3 / 32) * INCH,
        roller_diameter: float = (5 / 16) * INCH,
    ) -> Workplane:
        """Create roller chain link pair

        Create either inner or outer link pairs.  Inner links include rollers while
        outer links include fake roller pins.

        Args:
            chain_pitch: distance between roller pin centers. Defaults to 0.5*INCH.
            link_plate_thickness: thickness of single plate connecting rollers. Defaults to 1*MM.
            inner: is this an inner (or outer) chain link?. Defaults to True.
            roller_length: length of the internal roller. Defaults to (3 / 32)*INCH.
            roller_diameter: diameter of the internal roller. Defaults to (5 / 16)*INCH.

        Returns:
            A single link pair
        """

        def link_plates(chain_pitch, thickness, inner=False):
            """Create a single chain link, either inner or outer"""
            plate_scale = chain_pitch / (0.5 * INCH)
            neck = plate_scale * 4.5 * MM / 2
            plate_r = plate_scale * 8.5 * MM / 2
            neck_r = (pow(chain_pitch / 2, 2) + pow(neck, 2) - pow(plate_r, 2)) / (
                2 * plate_r - 2 * neck
            )
            plate_cen_pt = Vector(chain_pitch / 2, 0)
            plate_neck_intersection_a = degrees(atan2(neck + neck_r, chain_pitch / 2))
            neck_tangent_pt = (
                Vector(plate_r, 0).rotateZ(180 - plate_neck_intersection_a)
                + plate_cen_pt
            )

            # Create a dog boned link plate
            plate = (
                Workplane("XY")
                .hLine(chain_pitch / 2 + plate_r, forConstruction=True)
                .threePointArc((chain_pitch / 2, plate_r), neck_tangent_pt.toTuple())
                .radiusArc((0, neck), neck_r)
                .mirrorX()
                .mirrorY()
                .extrude(thickness / 2, both=True)
            )
            # Add roller pins
            if not inner:
                plate = (
                    plate.faces(">Z")
                    .workplane()
                    .tag("Outside")
                    .center(-chain_pitch / 2, 0)
                    .circle(plate_r / 4)
                    .extrude(thickness / 3)
                    .workplaneFromTagged("Outside")
                    .center(+chain_pitch / 2, 0)
                    .circle(plate_r / 4)
                    .extrude(thickness / 3)
                )
            return plate

        def roller(roller_diameter=(5 / 16) * INCH, roller_length=(3 / 32) * INCH):
            roller = (
                Workplane("XY")
                .circle(roller_diameter / 2)
                .extrude(roller_length / 2, both=True)
            )
            return roller

        if inner:
            # Link Plates
            link = link_plates(chain_pitch, link_plate_thickness, inner=True).translate(
                (chain_pitch / 2, 0, (roller_length + link_plate_thickness) / 2.0)
            )
            link = link.union(
                (
                    link_plates(
                        chain_pitch, link_plate_thickness, inner=True
                    ).translate(
                        (
                            chain_pitch / 2,
                            0,
                            -(roller_length + link_plate_thickness) / 2,
                        )
                    )
                )
            )
            # Link Rollers
            link = link.union(roller(roller_diameter, roller_length))
            link = link.union(
                roller(roller_diameter, roller_length).translate((chain_pitch, 0, 0))
            )
        else:
            link = link_plates(
                chain_pitch, link_plate_thickness, inner=False
            ).translate(
                (chain_pitch / 2, 0, (roller_length + 3 * link_plate_thickness) / 2)
            )
            link = link.union(
                (
                    link_plates(chain_pitch, link_plate_thickness, inner=False)
                    .translate(
                        (
                            chain_pitch / 2,
                            0,
                            (roller_length + 3 * link_plate_thickness) / 2,
                        )
                    )
                    .rotate((0, 0, 0), (1, 0, 0), 180)
                )
            )

        return link

    @staticmethod
    def _gen_mix_sum_list(list_a: list, list_b: list) -> list:
        """
        Return the sum the values of two interleaving arrays
        print(_gen_mix_sum_list([1,2,3,4],[3,4,1,2]))  #  [1, 4, 6, 10, 13, 14, 18, 20]
        """
        if len(list_a) != len(list_b):
            raise ValueError("_gen_mix_sum_list require two lists of equal size")
        array_sum = [list_a[0], list_a[0] + list_b[0]]
        for i in range(1, len(list_a)):
            array_sum.append(array_sum[-1] + list_a[i])
            array_sum.append(array_sum[-1] + list_b[i])
        return array_sum

    @staticmethod
    def _interleave_lists(list_a: list, list_b: list) -> list:
        """
        Return a single interleaved array given two equal sized lists
        print(_interleave_lists([1,2,3,4],[3,4,1,2]))  #  [1, 3, 2, 4, 3, 1, 4, 2]
        """
        if len(list_a) != len(list_b):
            raise ValueError("_interleave_lists require two lists of equal size")
        return_list = (
            [None] * 2 * len(list_a)
        )  # Create an empty list of the correct size
        return_list[::2] = list_a  # Assign a to the even-numbered indices
        return_list[1::2] = list_b  # Assign b to the odd-numbered indices
        return return_list

    @staticmethod
    def _find_segment(len_value: float, len_array: list[float]) -> int:
        """
        Return a position in a length array given a length value
        """
        return_value = nan
        for i, len_array_value in enumerate(len_array):
            if len_value < len_array_value:
                return_value = i
                break
        return return_value
