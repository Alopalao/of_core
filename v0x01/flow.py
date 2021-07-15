"""Deal with OpenFlow 1.0 specificities related to flows."""
from pyof.v0x01.common.action import ActionOutput as OFActionOutput
from pyof.v0x01.common.action import ActionVlanVid as OFActionVlanVid
from pyof.v0x01.common.flow_match import Match as OFMatch
from pyof.v0x01.controller2switch.flow_mod import FlowMod

from napps.kytos.of_core.flow import (ActionBase, ActionFactoryBase, FlowBase,
                                      FlowStats, MatchBase, PortStats)

__all__ = ('ActionOutput', 'ActionSetVlan', 'Action', 'Flow', 'FlowStats',
           'PortStats')


class Match(MatchBase):
    """High-level Match for OpenFlow 1.0."""

    @classmethod
    def from_of_match(cls, of_match):
        """Return an instance from a pyof Match."""
        match = cls(in_port=of_match.in_port,
                    dl_src=of_match.dl_src.value,
                    dl_dst=of_match.dl_dst.value,
                    dl_vlan=of_match.dl_vlan,
                    dl_vlan_pcp=of_match.dl_vlan_pcp,
                    dl_type=of_match.dl_type,
                    nw_proto=of_match.nw_proto,
                    nw_src=of_match.nw_src.value,
                    nw_dst=of_match.nw_dst.value,
                    tp_src=of_match.tp_src,
                    tp_dst=of_match.tp_dst)
        return match

    def as_of_match(self):
        """Return a pyof Match instance with current contents."""
        match = OFMatch()
        for field, value in self.__dict__.items():
            if value is not None:
                setattr(match, field, value)
        return match


class ActionOutput(ActionBase):
    """Action with an output port."""

    def __init__(self, port):
        """Require an output port.

        Args:
            port (int): Specific port number.
        """
        self.port = port
        self.action_type = 'output'

    @classmethod
    def from_of_action(cls, of_action):
        """Return a high-level ActionOuput instance from pyof ActionOutput."""
        return ActionOutput(port=of_action.port.value)

    def as_of_action(self):
        """Return a pyof ActionOuput instance."""
        return OFActionOutput(port=self.port)


class ActionSetVlan(ActionBase):
    """Action to set VLAN ID."""

    def __init__(self, vlan_id):
        """Require a VLAN ID."""
        self.vlan_id = vlan_id
        self.action_type = 'set_vlan'

    @classmethod
    def from_of_action(cls, of_action):
        """Return a high-level ActionSetVlan object from pyof ActionVlanVid."""
        return cls(vlan_id=of_action.vlan_id.value)

    def as_of_action(self):
        """Return a pyof ActionVlanVid instance."""
        return OFActionVlanVid(vlan_id=self.vlan_id)


class Action(ActionFactoryBase):
    """An action to be executed once a flow is activated.

    This class behavies like a factory but has no "Factory" suffix for end-user
    usability issues.
    """

    # Set v0x01 classes for action types and pyof classes
    _action_class = {
        'output': ActionOutput,
        'set_vlan': ActionSetVlan,
        OFActionOutput: ActionOutput,
        OFActionVlanVid: ActionSetVlan
    }


class Flow(FlowBase):
    """High-level flow representation for OpenFlow 1.0.

    This is a subclass that only deals with 1.0 flow actions.
    """

    _action_factory = Action
    _flow_mod_class = FlowMod
    _match_class = Match

    def __init__(self, *args, **kwargs):
        """Create a flow with actions."""
        actions = kwargs.pop('actions', None)
        super().__init__(*args, **kwargs)
        self.actions = actions or []

    def as_dict(self, include_id=True):
        """Representation of this flow as a dictionary."""
        flow_dict = super().as_dict(include_id=include_id)
        flow_dict['actions'] = [action.as_dict() for action in self.actions]

        return flow_dict

    @classmethod
    def from_dict(cls, flow_dict, switch):
        """Create a flow from a dictionary."""
        flow = super().from_dict(flow_dict, switch)
        if 'actions' in flow_dict:
            flow.actions = []
            for action_dict in flow_dict['actions']:
                action = cls._action_factory.from_dict(action_dict)
                if action:
                    flow.actions.append(action)
        return flow

    @staticmethod
    def _get_of_actions(of_flow_stats):
        """Return the pyof actions from pyof ``FlowStats.actions``."""
        return of_flow_stats.actions

    def _as_of_flow_mod(self, command):
        """Return pyof FlowMod with a ``command`` to add or delete a flow."""
        flow_mod = super()._as_of_flow_mod(command)
        flow_mod.actions = [action.as_of_action() for action in self.actions]
        return flow_mod

    @classmethod
    def from_of_flow_stats(cls, of_flow_stats, switch):
        """Create a flow with latest stats based on pyof FlowStats."""
        of_actions = cls._get_of_actions(of_flow_stats)
        actions = (cls._action_factory.from_of_action(of_action)
                   for of_action in of_actions)
        non_none_actions = [action for action in actions if action]
        flow = super().from_of_flow_stats(of_flow_stats, switch)
        flow.actions = non_none_actions
        return flow
