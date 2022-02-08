"""
Parametric Sprockets and Chains Unit Tests

name: sprocket_and_chain_tests.py
by:   Gumyr
date: July 13th 2021

desc: Unit tests for the sprocket and chain sub-package of cq_warehouse
Name                                            Stmts   Miss  Cover
-------------------------------------------------------------------
.../cq_warehouse/src/cq_warehouse/__init__.py       1      0   100%
.../cq_warehouse/src/cq_warehouse/chain.py        203      0   100%
.../cq_warehouse/src/cq_warehouse/sprocket.py     104      0   100%
sprocket_and_chain_tests.py                       141      1    99%
"""
import math
import unittest
from cadquery import Vector
from cq_warehouse.sprocket import Sprocket
from cq_warehouse.chain import Chain

MM = 1
INCH = 25.4 * MM


def _assertTupleAlmostEquals(self, expected, actual, places, msg=None):
    """Check Tuples"""
    for i, j in zip(actual, expected):
        self.assertAlmostEqual(i, j, places, msg=msg)


unittest.TestCase.assertTupleAlmostEquals = _assertTupleAlmostEquals


class TestParsing(unittest.TestCase):
    """Validate input parsing of the Sprocket and Chain classes"""

    def test_sprocket_input_parsing(self):
        """Validate Sprocket input validation"""
        with self.assertRaises(ValueError):  # Insufficient tooth count
            Sprocket(num_teeth=2)
        with self.assertRaises(ValueError):  # Invalid chain
            Sprocket(num_teeth=32, chain_pitch=4, roller_diameter=5)

    def test_chain_input_parsing(self):
        """Validate Chain input validation"""
        with self.assertRaises(ValueError):  # Invalid chain
            Chain(
                spkt_teeth=[10, 10],
                spkt_locations=[(0, 0, 0), (100, 0, 0)],
                positive_chain_wrap=[True, True],
                chain_pitch=4,
                roller_diameter=5,
            )
        with self.assertRaises(ValueError):  # Unequal list lengths
            Chain(
                spkt_teeth=[10, 10],
                spkt_locations=[(0, 0), (1, 1)],
                positive_chain_wrap=[True],
            )
        with self.assertRaises(ValueError):  # Invalid locations
            Chain(
                spkt_teeth=[10, 10],
                spkt_locations=[(0, 0), 1],
                positive_chain_wrap=[True, False],
            )
        with self.assertRaises(ValueError):  # Same locations
            Chain(
                spkt_teeth=[10, 10],
                spkt_locations=[(0, 0), (0, 0)],
                positive_chain_wrap=[True, False],
            )
        with self.assertRaises(ValueError):  # Invalid teeth
            Chain(
                spkt_teeth=[12.5, 6],
                spkt_locations=[(0, 0), (1, 0)],
                positive_chain_wrap=[True, False],
            )
        with self.assertRaises(ValueError):  # Too few sprockets
            Chain(
                spkt_teeth=[16],
                spkt_locations=[(0, 0), (1, 0)],
                positive_chain_wrap=[True, False],
            )
        with self.assertRaises(ValueError):  # Teeth not list
            Chain(
                spkt_teeth=12,
                spkt_locations=[(0, 0), (1, 0)],
                positive_chain_wrap=[True, False],
            )
        with self.assertRaises(ValueError):  # Too few locations
            Chain(
                spkt_teeth=[12, 12],
                spkt_locations=Vector(0, 0, 0),
                positive_chain_wrap=[True, False],
            )
        with self.assertRaises(ValueError):  # Wrap not a list
            Chain(
                spkt_teeth=[12, 12],
                spkt_locations=Vector(0, 0, 0),
                positive_chain_wrap=True,
            )
        with self.assertRaises(ValueError):  # Wrap not bool
            Chain(
                spkt_teeth=[12, 12],
                spkt_locations=Vector(0, 0, 0),
                positive_chain_wrap=["yes", "no"],
            )
        with self.assertRaises(ValueError):  # Length mismatch
            Chain(
                spkt_teeth=[20, 20],
                spkt_locations=[Vector(0, 0, 0), Vector(20, 0, 0)],
                positive_chain_wrap=[True],
            )
        with self.assertRaises(ValueError):  # Overlapping sprockets
            Chain(
                spkt_teeth=[12, 12],
                spkt_locations=[Vector(0, 0, 0), Vector(0, 0, 0)],
                positive_chain_wrap=[True, True],
            )


class TestSprocketShape(unittest.TestCase):
    """Validate the Sprocket object"""

    def test_flat_sprocket_shape(self):
        """Normal Sprockets"""
        spkt = Sprocket(
            num_teeth=32,
            bolt_circle_diameter=104 * MM,
            num_mount_bolts=4,
            mount_bolt_diameter=8 * MM,
            bore_diameter=80 * MM,
        )
        spkt_object = spkt.cq_object
        self.assertTrue(spkt_object.val().isValid())
        # self.assertEqual(spkt.hashCode(),2035876455)  # hashCode() isn't consistent
        self.assertAlmostEqual(spkt_object.val().Area(), 16935.40667143173)
        self.assertAlmostEqual(spkt_object.val().Volume(), 15851.936489869417)
        self.assertEqual(len(spkt_object.val().Edges()), 591)
        self.assertAlmostEqual(spkt.pitch_radius, 64.78458745735234)
        self.assertAlmostEqual(spkt.outer_radius, 66.76896245735234)
        self.assertAlmostEqual(spkt.pitch_circumference, 407.0535680437272)

    def test_spiky_sprocket_shape(self):
        """Create sprockets with no flat/chamfered top"""
        spkt = Sprocket(
            num_teeth=16, chain_pitch=0.5 * INCH, roller_diameter=0.49 * INCH
        )
        spkt_object = spkt.cq_object
        self.assertTrue(spkt_object.val().isValid())
        self.assertAlmostEqual(spkt_object.val().Area(), 5475.870128515104)
        self.assertAlmostEqual(spkt_object.val().Volume(), 5124.246302618558)
        self.assertEqual(len(spkt_object.val().Edges()), 144)
        self.assertAlmostEqual(spkt.pitch_radius, 32.54902618631712)
        self.assertAlmostEqual(spkt.outer_radius, 33.19993997888148)
        self.assertAlmostEqual(spkt.pitch_circumference, 204.51156309687133)


class TestChainShape(unittest.TestCase):
    """Chain shape verification"""

    def test_five_sprocket_chain(self):
        """Verify roller positions with a five sprocket configuration"""
        roller_pos = [
            (10.18715872390352, 222.87862587734543, 0.0),
            (-2.469786367915538, 223.63749243920552, 0.0),
            (-15.032122518458701, 221.91649041805948, 0.0),
            (-27.01863024307953, 217.7815454264499, 0.0),
            (-37.97014804499685, 211.39105285151325, 0.0),
            (-47.46716129814272, 202.98981027760766, 0.0),
            (-55.1458723960376, 192.89964014073198, 0.0),
            (-60.71213657508054, 181.50706182828947, 0.0),
            (-63.9527295792458, 169.24848546325475, 0.0),
            (-64.74351554107007, 156.59349454746925, 0.0),
            (-63.054202195766415, 144.02685784796165, 0.0),
            (-58.949501272721136, 132.02995958847876, 0.0),
            (-52.5866496138038, 121.06235929111907, 0.0),
            (-44.209385975842096, 111.54418764651639, 0.0),
            (-34.417283522603775, 103.46207713715292, 0.0),
            (-24.505824512547004, 95.52148646063736, 0.0),
            (-14.594365502490277, 87.58089578412186, 0.0),
            (-4.682906492433553, 79.64030510760635, 0.0),
            (5.2285525176232, 71.69971443109083, 0.0),
            (15.140011527679924, 63.75912375457532, 0.0),
            (25.051470537736677, 55.818533078059794, 0.0),
            (34.96292954779342, 47.87794240154427, 0.0),
            (44.87438855785015, 39.93735172502876, 0.0),
            (54.785847567906885, 31.99676104851325, 0.0),
            (64.6973065779636, 24.056170371997737, 0.0),
            (74.60876558802038, 16.115579695482197, 0.0),
            (84.5202245980771, 8.174989018966684, 0.0),
            (94.43168360813382, 0.23439834245118618, 0.0),
            (104.34314261819057, -7.706192334064326, 0.0),
            (114.25460162824731, -15.646783010579853, 0.0),
            (124.16606063830406, -23.58737368709538, 0.0),
            (134.07751964836078, -31.52796436361089, 0.0),
            (143.98897865841752, -39.468555040126404, 0.0),
            (153.90043766847427, -47.409145716641916, 0.0),
            (163.81189667853099, -55.34973639315743, 0.0),
            (173.72335568858776, -63.29032706967297, 0.0),
            (184.49526300952132, -69.797994158781, 0.0),
            (196.98516348377927, -69.32537692130084, 0.0),
            (206.89082176480787, -61.703112498603225, 0.0),
            (210.5475247587776, -49.75114596066792, 0.0),
            (206.60243280959895, -37.891245858957134, 0.0),
            (196.58394977859007, -30.352301961694447, 0.0),
            (185.16183484838712, -24.800249141229195, 0.0),
            (173.7397199181842, -19.248196320763938, 0.0),
            (162.31760498798135, -13.696143500298732, 0.0),
            (150.8954900577784, -8.144090679833472, 0.0),
            (139.47337512757557, -2.5920378593682614, 0.0),
            (128.17935413488252, 3.1912215382273708, 0.0),
            (120.62636980249249, 13.149806205975205, 0.0),
            (117.10019951704098, 25.349697399274334, 0.0),
            (113.61124119274426, 37.56105153431283, 0.0),
            (110.12228286844758, 49.77240566935122, 0.0),
            (106.63332454415087, 61.98375980438972, 0.0),
            (103.14436621985419, 74.1951139394281, 0.0),
            (99.76289104415392, 86.4331914608876, 0.0),
            (101.4396376126807, 98.8190504078871, 0.0),
            (109.98300537258243, 107.94219943818923, 0.0),
            (122.16645572507116, 111.2477354483829, 0.0),
            (134.6736270935342, 113.45242689162302, 0.0),
            (147.18079846199737, 115.65711833486316, 0.0),
            (159.68796983046056, 117.86180977810331, 0.0),
            (172.1951411989236, 120.06650122134342, 0.0),
            (184.7023125673868, 122.27119266458357, 0.0),
            (197.20948393584985, 124.47588410782367, 0.0),
            (209.716655304313, 126.68057555106382, 0.0),
            (221.6097114627239, 130.90791914125327, 0.0),
            (231.00827320966658, 139.329388606155, 0.0),
            (236.4972903657062, 150.6926980501538, 0.0),
            (237.25165788988997, 163.28972311553431, 0.0),
            (233.15797980817726, 175.22688821545123, 0.0),
            (224.8316148132517, 184.70980743005214, 0.0),
            (213.52417599627765, 190.31301528446517, 0.0),
            (201.01805763520213, 192.49309274067707, 0.0),
            (188.47605373377772, 194.49012507307776, 0.0),
            (175.93404983235322, 196.4871574054785, 0.0),
            (163.39204593092873, 198.48418973787923, 0.0),
            (150.85004202950435, 200.48122207027993, 0.0),
            (138.30803812807986, 202.47825440268065, 0.0),
            (125.76603422665546, 204.47528673508137, 0.0),
            (113.22403032523098, 206.4723190674821, 0.0),
            (100.68202642380648, 208.46935139988284, 0.0),
            (88.14002252238198, 210.46638373228356, 0.0),
            (75.59801862095773, 212.46341606468422, 0.0),
            (63.05601471953321, 214.46044839708497, 0.0),
            (50.514010818108716, 216.4574807294857, 0.0),
            (37.97200691668422, 218.45451306188642, 0.0),
            (25.43000301525973, 220.45154539428714, 0.0),
        ]
        chain = Chain(
            spkt_teeth=[32, 10, 10, 10, 16],
            positive_chain_wrap=[True, True, False, False, True],
            spkt_locations=[
                Vector(0, 158.9 * MM, 0),
                Vector(+190 * MM, -50 * MM, 0),
                Vector(+140 * MM, 20 * MM, 0),
                Vector(+120 * MM, 90 * MM, 0),
                Vector(+205 * MM, 158.9 * MM, 0),
            ],
        )
        self.assertEqual(chain.num_rollers, len(roller_pos))
        for i, roller_loc in enumerate(chain.roller_loc):
            self.assertTupleAlmostEquals(roller_loc.toTuple(), roller_pos[i], 7)

    def test_missing_link(self):
        """Validate the warning message generated when a gap in the chain is generated"""
        with self.assertWarns(Warning):
            Chain(
                spkt_teeth=[32, 32],
                spkt_locations=[
                    Vector(-4.9 * INCH, 0, 0),
                    Vector(+5 * INCH, 0, 0),
                ],
                positive_chain_wrap=[True, True],
            )


class TestSprocketMethods(unittest.TestCase):
    """Sprocket class methods"""

    def test_sprocket_pitch_radius(self):
        """Pitch radius verification"""
        self.assertAlmostEqual(
            Sprocket.sprocket_pitch_radius(32, 0.5 * INCH), 64.78458745735234
        )

    def test_sprocket_circumference(self):
        """Pitch circumference verification"""
        self.assertAlmostEqual(
            Sprocket.sprocket_circumference(32, 0.5 * INCH), 407.0535680437272
        )


class TestChainMethods(unittest.TestCase):
    """Chain class methods"""

    def test_gen_mix_sum_list(self):
        """Validate custom list function"""
        with self.assertRaises(ValueError):
            Chain._gen_mix_sum_list([1, 2], [1, 2, 3])
        self.assertEqual(
            Chain._gen_mix_sum_list([1, 2, 3, 4], [3, 4, 1, 2]),
            [1, 4, 6, 10, 13, 14, 18, 20],
        )

    def test_interleave_lists(self):
        """Validate custom list function"""
        with self.assertRaises(ValueError):
            Chain._interleave_lists([1, 2], [1, 2, 3])
        self.assertEqual(
            Chain._interleave_lists([1, 2, 3, 4], [3, 4, 1, 2]),
            [1, 3, 2, 4, 3, 1, 4, 2],
        )

    def test_find_segment(self):
        """Validate custom list function"""
        self.assertEqual(Chain._find_segment(3.5, [1, 2, 3, 4]), 3)
        self.assertTrue(math.isnan(Chain._find_segment(13.5, [1, 2, 3, 4])))

    def test_make_link(self):
        """Validate the creation of inner and outer link objects"""
        inner_link = Chain.make_link(inner=True).val()
        self.assertTrue(inner_link.isValid())
        self.assertAlmostEqual(inner_link.Area(), 577.0049729508926)
        self.assertAlmostEqual(inner_link.Volume(), 510.0011770079004)
        self.assertEqual(len(inner_link.Edges()), 30)
        outer_link = Chain.make_link(inner=False).val()
        self.assertTrue(outer_link.isValid())
        self.assertAlmostEqual(outer_link.Area(), 665.0791957450477)
        self.assertAlmostEqual(outer_link.Volume(), 279.06641583265633)
        self.assertEqual(len(outer_link.Edges()), 36)

    def test_assemble_chain_transmission(self):
        """Validate input parsing"""
        spkt0 = Sprocket(num_teeth=16)
        spkt1 = Sprocket(num_teeth=16)

        chain = Chain(
            spkt_teeth=[16, 16],
            spkt_locations=[Vector(-3 * INCH, 40, 50), Vector(+3 * INCH, 40, 50)],
            positive_chain_wrap=[True, True],
        )
        with self.assertRaises(ValueError):
            chain.assemble_chain_transmission(spkt0.cq_object)
        with self.assertRaises(ValueError):
            chain.assemble_chain_transmission([spkt0, spkt1.cq_object])

        """ Validate a transmission assembly composed of two sprockets and a chain """
        chain = Chain(
            spkt_teeth=[16, 16],
            spkt_locations=[(-3 * INCH, 40), (+3 * INCH, 40)],
            positive_chain_wrap=[True, True],
            chain_pitch=(1 / 2) * INCH,
            roller_diameter=(5 / 16) * INCH,
        )
        self.assertEqual(chain.cq_object.name, "chain_links")
        self.assertAlmostEqual(chain.chain_links, 40.10327268479302, 7)
        self.assertEqual(len(chain.cq_object.children), 40)
        self.assertTupleAlmostEquals(chain.chain_angles[0], (0, 180), 7)
        self.assertAlmostEqual(chain.spkt_initial_rotation[0], 11.25, 7)
        transmission = (
            chain.assemble_chain_transmission([spkt0.cq_object, spkt1.cq_object])
            .rotate((1, 0, 0), 90)
            .translate((0, 0, -40))
        )
        self.assertEqual(transmission.name, "transmission")
        self.assertEqual(len(transmission.children), 3)
        self.assertEqual(transmission.children[0].name, "spkt0")
        self.assertEqual(transmission.children[1].name, "spkt1")
        self.assertEqual(transmission.children[2].name, "chain")


class TestVectorMethods(unittest.TestCase):
    """Extensions to the Vector class"""

    def test_vector_rotate(self):
        """Validate vector rotate methods"""
        vector_x = Vector(1, 0, 1).rotateX(45)
        vector_y = Vector(1, 2, 1).rotateY(45)
        vector_z = Vector(-1, -1, 3).rotateZ(45)
        self.assertTupleAlmostEquals(
            vector_x.toTuple(), (1, -math.sqrt(2) / 2, math.sqrt(2) / 2), 7
        )
        self.assertTupleAlmostEquals(vector_y.toTuple(), (math.sqrt(2), 2, 0), 7)
        self.assertTupleAlmostEquals(vector_z.toTuple(), (0, -math.sqrt(2), 3), 7)

    def test_vector_flip_y(self):
        """Validate vector flip of the xz plane method"""
        self.assertTupleAlmostEquals(Vector(1, 2, 3).flipY().toTuple(), (1, -2, 3), 7)


if __name__ == "__main__":
    unittest.main()
