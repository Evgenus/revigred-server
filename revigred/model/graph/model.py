from revigred.utils import DocDescribed
from revigred.model.users import (
    Users,
    User,
    Origin,
    )
from .storage import Graph
from .events import *

__all__ = [
    "GraphModel",
]

class GraphUser(User):
    def dispatch(self, name, *args, **kwargs):
        rev = kwargs.pop("rev")
        func = getattr(self.model, "on_" + name, None)
        if func is None:
            raise ValueError("command {} was not found")
        origin = Origin(self, rev)
        func(origin, *args, **kwargs)

class GraphModel(Users):
    graph_factory = Graph
    user_factory = GraphUser

    def __init__(self):
        super().__init__()
        self._graph = self.graph_factory()
        self._graph.on("node:add", self.node_added)
        self._graph.on("node:remove", self.node_removed)
        self._graph.on("link:add", self.link_added)
        self._graph.on("link:remove", self.link_removed)

    @property
    def graph(self):
        return self._graph

    # ======================================================================== #

    def node_added(self, id): pass
    def node_removed(self, id): pass
    def link_added(self, key): pass
    def link_removed(self, key): pass

    # ======================================================================== #

    def on_nodeCreated(self, origin, id):
        try:
            self.graph.check_create_node(id)
        except Confirm:
            self.createNodeSelf(origin, id)
        except Cancel:
            self.removeNodeSelf(origin, id)
        else:
            node = self.graph.node_factory(id)
            self.graph.add_node(node)
            self.createNodeAll(origin, id)
            self.changePortsAll(None, id, node.get_ports())
            self.changeStateAll(None, id, node.get_state())

    def on_nodeRemoved(self, origin, id):
        try:
            self.graph.check_remove_node(id)
        except Confirm:
            self.removeNodeSelf(origin, id)
        except Cancel:
            self.createNodeSelf(origin, id)
        else:
            for link in self.graph.find_links_startswith(id):
                self.remove_link(link)
                self.removeLinkAll(None,
                    link.start_id, link.start_name, 
                    link.end_id, link.end_name)

            for link in self.graph.find_links_endswith(id):
                self.remove_link(link)
                self.removeLinkAll(None,
                    link.start_id, link.start_name, 
                    link.end_id, link.end_name)

            self.graph.remove_node(id)
            self.removeNodeAll(origin, id)

    def on_nodeStateChanged(self, origin, id, state):
        try:
            self.graph.check_change_state(id, state)
        except Cancel:
            self.changeStateSelf(origin, id, None)
        else:
            node = self.graph.get_node(id)
            node.set_state(state)
            self.changeStateAll(origin, id, node.get_state())

    def on_linkAdded(self, origin, start_id, start_name, end_id, end_name):
        try:
            self.graph.check_add_link(start_id, start_name, end_id, end_name)
        except Confirm:
            self.addLinkSelf(origin, start_id, start_name, end_id, end_name)
        except Cancel:
            self.removeLinkSelf(origin, start_id, start_name, end_id, end_name)
        else:
            link = self.graph.link_factory(start_id, start_name, end_id, end_name)
            self.graph.add_link(link)
            self.addLinkAll(origin, start_id, start_name, end_id, end_name)

    def on_linkRemoved(self, origin, start_id, start_name, end_id, end_name):
        try:
            self.graph.check_remove_link(start_id, start_name, end_id, end_name)
        except Confirm:
            self.removeLinkSelf(origin, start_id, start_name, end_id, end_name)
        except Cancel:
            self.addLinkSelf(origin, start_id, start_name, end_id, end_name)
        else:
            self.graph.remove_link(start_id, start_name, end_id, end_name)
            self.removeLinkAll(origin, start_id, start_name, end_id, end_name)

    # ======================================================================== #

    def _callSelf(self, name, origin, *args, **kwargs):
        rev = self.graph.rev
        for user in self._users.values():
            if origin is not None and origin.user is user:
                user.send(name, *args, rev=rev, origin=origin.rev, **kwargs)
            else:
                user.send("nop", rev=rev)

    def _callAll(self, name, origin, *args, **kwargs):
        rev = self.graph.rev
        for user in self._users.values():
            if origin is not None and origin.user is user:
                user.send(name, *args, rev=rev, origin=origin.rev, **kwargs)
            else:
                user.send(name, *args, rev=rev, **kwargs)

    def createNodeSelf(self, origin, id):
        self._callSelf("createNode", origin, id)

    def createNodeAll(self, origin, id):
        self._callAll("createNode", origin, id)

    def removeNodeSelf(self, origin, id):
        self._callSelf("removeNode", origin, id)

    def removeNodeAll(self, origin, id):
        self._callAll("removeNode", origin, id)

    def changeStateSelf(self, origin, id, state):
        self._callSelf("changeState", origin, id, state)

    def changeStateAll(self, origin, id, state):
        self._callAll("changeState", origin, id, state)

    def changePortsSelf(self, origin, id, ports):
        self._callSelf("changePorts", origin, id, ports)

    def changePortsAll(self, origin, id, ports):
        self._callAll("changePorts", origin, id, ports)

    def addLinkSelf(self, origin, start_id, start_name, end_id, end_name):
        self._callSelf("addLink", origin, start_id, start_name, end_id, end_name)

    def addLinkAll(self, origin, start_id, start_name, end_id, end_name):
        self._callAll("addLink", origin, start_id, start_name, end_id, end_name)

    def removeLinkSelf(self, origin, start_id, start_name, end_id, end_name):
        self._callSelf("removeLink", origin, start_id, start_name, end_id, end_name)
    
    def removeLinkAll(self, origin, start_id, start_name, end_id, end_name):
        self._callAll("removeLink", origin, start_id, start_name, end_id, end_name)

# ____________________________________________________________________________ #
