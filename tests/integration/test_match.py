"""Test Match abstraction for v0x04."""
import unittest

from pyof.v0x04.common.flow_match import Match as OFMatch04

from napps.kytos.of_core.v0x04.flow import Match as Match04


class TestMatch(unittest.TestCase):
    """Tests for the Match class."""

    EXPECTED = {'in_port': 1,
                'dl_src': '11:22:33:44:55:66',
                'dl_dst': 'aa:bb:cc:dd:ee:ff',
                'dl_vlan': 2,
                'dl_vlan_pcp': 3,
                'dl_type': 4,
                'nw_proto': 5,
                'nw_src': '1.2.3.4/32',
                'nw_dst': '5.6.7.0/24',
                'tp_src': 6,
                'tp_dst': 7}

    def test_all_fields(self):
        """Test all match fields from and to dict."""
        with self.subTest(match_class=Match04):
            match = Match04.from_dict(self.EXPECTED)
            actual = match.as_dict()
            self.assertDictEqual(self.EXPECTED, actual)

    def test_of_match(self):
        """Test convertion between Match and OFMatch."""
        match_04 = Match04.from_dict(self.EXPECTED)
        of_match_04 = match_04.as_of_match()
        match_04_converted = Match04.from_of_match(of_match_04)
        self.assertIsInstance(of_match_04, OFMatch04)
        self.assertIsInstance(match_04_converted, Match04)
