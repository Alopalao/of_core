"""Test v0x04.utils methods."""
from unittest import TestCase
from unittest.mock import MagicMock, patch

import pytest
from pyof.v0x04.common.port import PortNo, PortState

from kytos.lib.helpers import (get_connection_mock, get_controller_mock,
                               get_switch_mock)
from napps.kytos.of_core.v0x04.utils import (handle_features_reply,
                                             handle_port_desc, say_hello,
                                             send_desc_request, send_echo,
                                             send_port_request,
                                             send_set_config,
                                             try_to_activate_interface)


@patch('napps.kytos.of_core.v0x04.utils.aemit_message_out')
async def test_say_hello(mock_aemit_message_out, controller, switch_one):
    """Test say_hello."""
    await say_hello(controller, switch_one)
    mock_aemit_message_out.assert_called()


@patch('kytos.core.buffers.KytosEventBuffer.aput')
async def test_handle_port_desc(mock_event_buffer, controller, switch_one):
    """Test Handle Port Desc."""
    mock_port = MagicMock()
    mock_port.port_no.value = PortNo.OFPP_LOCAL.value
    mock_intf = MagicMock()
    switch_one.update_or_create_interface.return_value = mock_intf
    await handle_port_desc(controller, switch_one, [mock_port])
    assert switch_one.update_or_create_interface.call_count == 1
    mock_event_buffer.assert_called()
    mock_intf.activate.assert_called()
    assert controller.buffers.app.aput.call_count == 3


@patch('kytos.core.buffers.KytosEventBuffer.aput')
async def test_handle_port_desc_inactive(mock_event_buffer, controller,
                                         switch_one):
    """Test Handle Port Desc inactive interface."""
    mock_port = MagicMock()
    mock_port.port_no.value = 1
    mock_port.state.value = PortState.OFPPS_LINK_DOWN
    mock_intf = MagicMock()
    switch_one.update_or_create_interface.return_value = mock_intf
    await handle_port_desc(controller, switch_one, [mock_port])
    assert switch_one.update_or_create_interface.call_count == 1
    mock_event_buffer.assert_called()
    mock_intf.deactivate.assert_called()
    assert controller.buffers.app.aput.call_count == 3


@pytest.mark.parametrize(
    "state,port_no,should_activate",
    [
     (PortState.OFPPS_LIVE, 1, True),
     (PortState.OFPPS_LINK_DOWN, PortNo.OFPP_LOCAL, True),
     (PortState.OFPPS_LINK_DOWN, 2, False)
    ],
)
def test_try_to_activate_interface(state, port_no, should_activate) -> None:
    """test test_try_to_activate_interface."""
    interface = MagicMock()
    port = MagicMock()
    port.state.value = state
    port.port_no.value = port_no
    try_to_activate_interface(interface, port)

    if should_activate:
        interface.activate.assert_called()
    else:
        interface.deactivate.assert_called()


class TestUtils(TestCase):
    """Test utils."""

    def setUp(self):
        """Execute steps before each tests."""
        self.mock_controller = get_controller_mock()
        self.mock_switch = get_switch_mock('00:00:00:00:00:00:00:01', 0x04)
        self.mock_connection = get_connection_mock(0x04, self.mock_switch)

    @patch('napps.kytos.of_core.v0x04.utils.emit_message_out')
    def test_send_desc_request(self, mock_emit_message_out):
        """Test send_desc_request."""
        send_desc_request(self.mock_controller, self.mock_switch)
        mock_emit_message_out.assert_called()

    @patch('napps.kytos.of_core.v0x04.utils.emit_message_out')
    def test_port_request(self, mock_emit_message_out):
        """Test send_desc_request."""
        send_port_request(self.mock_controller, self.mock_switch)
        mock_emit_message_out.assert_called()

    def test_handle_features_reply(self):
        """Test Handle features reply."""
        mock_controller = MagicMock()
        mock_event = MagicMock()
        mock_controller.get_switch_or_create.return_value = self.mock_switch
        response = handle_features_reply(mock_controller, mock_event)
        self.assertEqual(self.mock_switch, response)
        self.assertEqual(self.mock_switch.update_features.call_count, 1)

    @patch('napps.kytos.of_core.v0x04.utils.emit_message_out')
    def test_send_echo(self, mock_emit_message_out):
        """Test send_echo."""
        send_echo(self.mock_controller, self.mock_switch)
        mock_emit_message_out.assert_called()

    @patch('napps.kytos.of_core.v0x04.utils.emit_message_out')
    def test_set_config(self, mock_emit_message_out):
        """Test set_config."""
        send_set_config(self.mock_controller, self.mock_switch)
        mock_emit_message_out.assert_called()
