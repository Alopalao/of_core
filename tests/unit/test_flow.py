"""Tests for high-level Flow of OpenFlow 1.3."""
from unittest import TestCase
from unittest.mock import MagicMock, patch

import pytest

from kytos.lib.helpers import get_connection_mock, get_switch_mock
from napps.kytos.of_core.v0x04.flow import Flow as Flow04
from napps.kytos.of_core.v0x04.flow import Match as Match04


@pytest.mark.parametrize(
    "flow1_dict, flow2_dict",
    [
        (
            {"match": {"in_port": 1, "dl_vlan": 105}, "actions": []},
            {"match": {"in_port": 1, "dl_vlan": 105}},
        ),
        (
            {
                "match": {},
                "cookie": 0,
                "table_id": 0,
                "priority": 0x8000,
                "idle_timeout": 0,
                "hard_timeout": 0,
            },
            {"match": {}},
        )
    ],
)
def test_equivalent_flow_ids(flow1_dict, flow2_dict):
    """Test equivalent flow ids."""
    switch = MagicMock()
    dpid = "00:00:00:00:00:00:00:01"
    switch.id = dpid
    flow1 = Flow04.from_dict(flow1_dict, switch)
    flow2 = Flow04.from_dict(flow2_dict, switch)
    assert flow1.as_dict(include_id=False) == flow2.as_dict(include_id=False)
    assert flow1.id == flow2.id


class TestFlowFactory(TestCase):
    """Test the FlowFactory class."""

    def setUp(self):
        """Execute steps before each tests.
        Set the server_name_url from kytos/of_core
        """
        self.switch_v0x04 = get_switch_mock("00:00:00:00:00:00:00:02", 0x04)
        self.switch_v0x04.connection = get_connection_mock(
            0x04, get_switch_mock("00:00:00:00:00:00:00:04"))

        patch('kytos.core.helpers.run_on_thread', lambda x: x).start()
        # pylint: disable=import-outside-toplevel
        from napps.kytos.of_core.flow import FlowFactory
        self.addCleanup(patch.stopall)

        self.factory = FlowFactory()

    @patch('napps.kytos.of_core.flow.v0x04')
    def test_from_of_flow_stats(self, mock_flow_v0x04):
        """Test from_of_flow_stats."""
        mock_stats = MagicMock()
        self.factory.from_of_flow_stats(mock_stats, self.switch_v0x04)
        mock_flow_v0x04.flow.Flow.from_of_flow_stats.assert_called()

    def test_get_class(self) -> None:
        """Test get_class."""
        assert self.factory.get_class(self.switch_v0x04) == Flow04
        switch = MagicMock(connection=None)
        assert self.factory.get_class(switch, Flow04) == Flow04


class TestFlow(TestCase):
    """Test OF flow abstraction."""

    mock_switch = get_switch_mock("00:00:00:00:00:00:00:01")
    mock_switch.id = "00:00:00:00:00:00:00:01"
    requested = {
        'switch': mock_switch.id,
        'table_id': 1,
        'match': {
            'dl_src': '11:22:33:44:55:66'
        },
        'priority': 2,
        'idle_timeout': 3,
        'hard_timeout': 4,
        'cookie': 5,
        'actions': [{
            'action_type': 'set_vlan',
            'vlan_id': 6
        }]
    }
    expected_13 = {
        'switch': mock_switch.id,
        'table_id': 1,
        'match': {
            'dl_src': '11:22:33:44:55:66'
        },
        'priority': 2,
        'idle_timeout': 3,
        'hard_timeout': 4,
        'cookie': 5,
        'cookie_mask': 0,
        'instructions': [{
            'instruction_type': 'apply_actions',
            'actions': [{
                'action_type': 'set_vlan',
                'vlan_id': 6
                }]
            }],
        'stats': {}
    }
    requested_instructions = {
        'switch': mock_switch.id,
        'table_id': 1,
        'match': {
            'dl_src': '11:22:33:44:55:66'
        },
        'priority': 2,
        'idle_timeout': 3,
        'hard_timeout': 4,
        'cookie': 5,
        'cookie_mask': 0,
        'instructions': [
            {
                'instruction_type': 'apply_actions',
                'actions': [{
                    'action_type': 'set_vlan',
                    'vlan_id': 2
                }]
            },
            {
                'instruction_type': 'goto_table',
                'table_id': 1
            }

        ]
    }

    @patch('napps.kytos.of_core.flow.v0x04')
    @patch('napps.kytos.of_core.flow.json.dumps')
    def test_flow_mod_goto(self, *args):
        """Convert a dict to flow and vice-versa."""
        (mock_json, _) = args
        dpid = "00:00:00:00:00:00:00:01"
        mock_json.return_value = str(self.requested_instructions)
        mock_switch = get_switch_mock(dpid, 0x04)
        mock_switch.id = dpid
        flow = Flow04.from_dict(self.requested_instructions, mock_switch)
        actual = flow.as_dict()
        del actual['id']
        del actual['stats']
        self.assertDictEqual(self.requested_instructions, actual)

    @patch('napps.kytos.of_core.flow.v0x04')
    @patch('napps.kytos.of_core.flow.json.dumps')
    def test_flow_mod(self, *args):
        """Convert a dict to flow and vice-versa."""
        (mock_json, _,) = args
        dpid = "00:00:00:00:00:00:00:01"
        mock_json.return_value = str(self.requested)
        for flow_class, version, expected in \
            [
                (Flow04, 0x04, self.expected_13)]:
            with self.subTest(flow_class=flow_class):
                mock_switch = get_switch_mock(dpid, version)
                mock_switch.id = dpid
                flow = flow_class.from_dict(self.requested, mock_switch)
                actual = flow.as_dict()
                del actual['id']
                self.assertDictEqual(expected, actual)

    @patch('napps.kytos.of_core.flow.FlowBase._as_of_flow_mod')
    def test_of_flow_mod(self, mock_flow_mod):
        """Test convertion from Flow to OFFlow."""
        with self.subTest(flow_class=Flow04):
            flow = Flow04.from_dict(self.requested, self.mock_switch)
            flow.as_of_add_flow_mod()
            mock_flow_mod.assert_called()
            flow.as_of_delete_flow_mod()
            mock_flow_mod.assert_called()

    # pylint: disable = protected-access
    def test_as_of_flow_mod(self):
        """Test _as_of_flow_mod."""
        mock_command = MagicMock()
        with self.subTest(flow_class=Flow04):
            flow_mod = Flow04.from_dict(self.requested, self.mock_switch)
            response = flow_mod._as_of_flow_mod(mock_command)
            self.assertEqual(response.cookie, self.requested['cookie'])
            self.assertEqual(response.idle_timeout,
                             self.requested['idle_timeout'])
            self.assertEqual(response.hard_timeout,
                             self.requested['hard_timeout'])

    @staticmethod
    def test_match_id():
        """Test match_id."""
        dpid = "00:00:00:00:00:00:00:01"
        mock_switch = get_switch_mock(dpid, 0x04)
        mock_switch.id = dpid
        flow_one = {"match": Match04(**{"in_port": 1, "dl_vlan": 2})}
        flow_two = {"match": Match04(**{"in_port": 1, "dl_vlan": 2})}
        flow_three = {"match": Match04(**{"in_port": 1, "dl_vlan": 3})}

        assert Flow04(mock_switch, **flow_one).match_id == Flow04(
            mock_switch, **flow_two
        ).match_id
        assert Flow04(mock_switch, **flow_one).match_id != Flow04(
            mock_switch, **flow_three
        ).match_id

        flow_two["cookie"] = 0x10
        assert Flow04(mock_switch, **flow_one).match_id != Flow04(
            mock_switch, **flow_two
        ).match_id


class TestFlowBase(TestCase):
    """Test FlowBase Class."""

    def test__eq__success_with_equal_flows(self):
        """Test success case to __eq__ override with equal flows."""
        mock_switch = get_switch_mock("00:00:00:00:00:00:00:01")

        flow_dict = {'switch': mock_switch.id,
                     'table_id': 1,
                     'match': {
                         'dl_src': '11:22:33:44:55:66'
                     },
                     'priority': 2,
                     'idle_timeout': 3,
                     'hard_timeout': 4,
                     'cookie': 5,
                     'actions': [
                         {'action_type': 'set_vlan',
                          'vlan_id': 6}],
                     'stats': {}
                     }

        with self.subTest(flow_class=Flow04):
            flow_1 = Flow04.from_dict(flow_dict, mock_switch)
            flow_2 = Flow04.from_dict(flow_dict, mock_switch)
            self.assertEqual(flow_1 == flow_2, True)

    def test__eq__success_with_different_flows(self):
        """Test success case to __eq__ override with different flows."""
        mock_switch = get_switch_mock("00:00:00:00:00:00:00:01")

        flow_dict_1 = {'switch': mock_switch.id,
                       'table_id': 1,
                       'match': {
                           'dl_src': '11:22:33:44:55:66'
                       },
                       'priority': 2,
                       'idle_timeout': 3,
                       'hard_timeout': 4,
                       'cookie': 5,
                       'actions': [
                           {'action_type': 'set_vlan',
                            'vlan_id': 6}],
                       'stats': {}
                       }

        flow_dict_2 = {'switch': mock_switch.id,
                       'table_id': 1,
                       'match': {
                           'dl_src': '11:22:33:44:55:66'
                       },
                       'priority': 1000,
                       'idle_timeout': 3,
                       'hard_timeout': 4,
                       'cookie': 5,
                       'actions': [
                           {'action_type': 'set_vlan',
                            'vlan_id': 6}],
                       'stats': {}
                       }

        with self.subTest(flow_class=Flow04):
            flow_1 = Flow04.from_dict(flow_dict_1, mock_switch)
            flow_2 = Flow04.from_dict(flow_dict_2, mock_switch)
            self.assertEqual(flow_1 == flow_2, False)

    def test__eq__fail(self):
        """Test the case where __eq__ receives objects with different types."""
        mock_switch = get_switch_mock("00:00:00:00:00:00:00:01")

        flow_dict = {'switch': mock_switch.id,
                     'table_id': 1,
                     'match': {
                         'dl_src': '11:22:33:44:55:66'
                     },
                     'priority': 2,
                     'idle_timeout': 3,
                     'hard_timeout': 4,
                     'cookie': 5,
                     'actions': [
                         {'action_type': 'set_vlan',
                          'vlan_id': 6}],
                     'stats': {}
                     }

        with self.subTest(flow_class=Flow04):
            flow_1 = Flow04.from_dict(flow_dict, mock_switch)
            flow_2 = "any_string_object"
            with self.assertRaises(ValueError):
                return flow_1 == flow_2
