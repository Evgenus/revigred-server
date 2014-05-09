from collections import defaultdict

from .users import Users

__all__ = [
    "Port",
    "Node",
    "Link",
    "Graph",
    "GraphModel",
    "ClientGraph",
    "ClientGraphModel",
    "NodeExists",
    "NoSuchNode",
    "NoSuchPort",
    "LinkExists",
    "NoSuchLink",
    "Merge",
    "Cancel",
    "Confirm",
    ]

class Port(object):
    def __init__(self, name, title):
        self._name = name
        self._title = title

    @property
    def name(self): 
        return self._name

    @property
    def title(self):
        return self._title

    def serialize(self):
        return dict(
            name=self._name,
            title=self._title,
            )

class State(object):
    def __init__(self):
        self._data = {}

    def serialize(self):
        return self._data

    def deserialize(self, data):
        self._data = data

class Node(object):
    state_factory = State
    port_factory = Port

    def __init__(self, id):
        self._id = id
        self._state = self.state_factory()
        self._ports = []
        self._ports_by_name = {}

    @property
    def id(self):
        return self._id

    def has_port(self, name):
        return name in self._ports_by_name

    def get_port(self, name):
        return self._ports_by_name.get(name)

    def add_port(self, port, index=None):
        if index is None:
            index = len(self._ports)
        self._ports.insert(index, port)
        self._ports_by_name[port.name] = port

    def remove_port(self, name):
        port = self._ports_by_name[name]
        self._ports.remove(port)

    def get_ports(self):
        return [port.serialize() for port in self._ports]

    def get_state(self):
        return self._state.serialize()

    def set_state(self, state):
        return self._state.deserialize(state)        

class Link(object):
    def __init__(self, start_id, start_name, end_id, end_name):
        self._start_id = start_id
        self._start_name = start_name
        self._end_id = end_id
        self._end_name = end_name

    @property
    def start_id(self): 
        return self._start_id

    @property
    def start_name(self): 
        return self._start_name

    @property
    def end_id(self): 
        return self._end_id

    @property
    def end_name(self): 
        return self._end_name

# ____________________________________________________________________________ #

class ResultException(Exception): pass
class NodeExists(ResultException):
    def __init__(self, id):
        self.id = id
class NoSuchNode(ResultException):
    def __init__(self, id):
        self.id = id
class NoSuchPort(ResultException):
    def __init__(self, id, name):
        self.id = id
        self.name = name
class LinkExists(ResultException):
    def __init__(self, start_id, start_name, end_id, end_name):
        self.start_id = start_id
        self.start_name = start_name
        self.end_id = end_id
        self.end_name = end_name
class NoSuchLink(ResultException):
    def __init__(self, start_id, start_name, end_id, end_name):
        self.start_id = start_id
        self.start_name = start_name
        self.end_id = end_id
        self.end_name = end_name

class ResultResolution(Exception): pass
class Merge(ResultResolution): pass
class Cancel(ResultException): pass
class Confirm(ResultException): pass

class Graph(object):
    node_factory = Node
    link_factory = Link

    def __init__(self):
        super().__init__()
        self._rev = 0
        self._nodes_by_id = {}
        self._links_by_key = {}
        self._links_by_start_id = defaultdict(dict)
        self._links_by_end_id = defaultdict(dict)

    @property
    def rev(self):
        old = self._rev
        self._rev += 1
        return old

    def has_node(self, id):
        return id in self._nodes_by_id

    def get_node(self, id):
        return self._nodes_by_id[id]

    def add_node(self, node):
        self._nodes_by_id[node.id] = node

    def remove_node(self, id):
        del self._nodes_by_id[id]

    def has_link(self, start_id, start_name, end_id, end_name):
        key = (start_id, start_name, end_id, end_name)
        return key in self._links_by_key

    def get_link(self, start_id, start_name, end_id, end_name):
        key = (start_id, start_name, end_id, end_name)
        return self._links_by_key[key]

    def add_link(self, link):
        key = (link.start_id, link.start_name, link.end_id, link.end_name)
        self._links_by_start_id[link.start_id][key] = link
        self._links_by_end_id[link.end_id][key] = link
        self._links_by_key[key] = link

    def remove_link(self, start_id, start_name, end_id, end_name):
        key = (start_id, start_name, end_id, end_name)
        del self._links_by_key[key]
        del self._links_by_start_id[start_id][key]
        del self._links_by_end_id[end_id][key]

    def find_links_startswith(self, start_id):
        yield from list(self._links_by_start_id[start_id].values())

    def find_links_endswith(self, end_id):
        yield from list(self._links_by_end_id[end_id].values())

    # ======================================================================== #

    def check_create_node(self, id):
        if self.has_node(id): 
            raise Confirm() from NodeExists(id)

    def check_remove_node(self, id):
        if not self.has_node(id): 
            raise Confirm() from NoSuchNode(id)

    def check_change_state(self, id, state):
        if not self.has_node(id): 
            raise Cancel() from NoSuchNode(id)

    def check_add_link(self, start_id, start_name, end_id, end_name):
        if not self.has_node(start_id): 
            raise Cancel() from NoSuchNode(start_id)

        if not self.has_node(end_id): 
            raise Cancel() from NoSuchNode(end_id)

        if not self.get_node(start_id).has_port(start_name): 
            raise Cancel() from NoSuchPort(start_id, start_name)

        if not self.get_node(end_id).has_port(end_name): 
            raise Cancel() from NoSuchPort(end_id, end_name)

        if self.has_link(start_id, start_name, end_id, end_name):
            raise Confirm() from LinkExists(start_id, start_name, end_id, end_name)

    def check_remove_link(self, start_id, start_name, end_id, end_name):
        if not self.has_node(start_id): 
            raise Confirm() from NoSuchNode(start_id)

        if not self.has_node(end_id): 
            raise Confirm() from NoSuchNode(end_id)

        if not self.get_node(start_id).has_port(start_name): 
            raise Confirm() from NoSuchPort(start_id, start_name)

        if not self.get_node(end_id).has_port(end_name): 
            raise Confirm() from NoSuchPort(end_id, end_name)

        if not self.has_link(start_id, start_name, end_id, end_name):
            raise Confirm() from NoSuchLink(start_id, start_name, end_id, end_name)

# ____________________________________________________________________________ #

class GraphModel(Users):
    graph_factory = Graph

    def __init__(self):
        super().__init__()
        self._graph = self.graph_factory()

    @property
    def graph(self):
        return self._graph

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

from functools import partial
from enum import Enum
from sentinels import NOTHING

class Existence(Enum):
    """
    I've used this instead of True and False only for clarification reason,
    because booleans are not self-described.
    """
    CREATED = True
    REMOVED = False

class Cell(object):
    def __init__(self):
        self._value = NOTHING

    @property
    def empty(self):
        return self._value is NOTHING

    def set(self, value):
        self._value = value

    def get(self):
        return self._value

class Branch(object):
    cell_factory = Cell
    def __init__(self):
        self._cells = defaultdict(self.cell_factory)

    def add(self, rev, value):
        assert self._cells[rev].empty
        self._cells[rev].set(value)

    def get(self, rev):
        assert not self._cells[rev].empty
        return self._cells[rev].get()

    def top(self):
        return max(self._cells)

class Repo(object):
    branch_factory = Branch
    def __init__(self):
        self._their = self.branch_factory()
        self._conflict = self.branch_factory()
        self._unresolved = set()

    def resolve(self, rev, origin, value):
        self._unresolved.remove(origin)
        self._their.add(rev, value)

    def initiate(self, rev, value):
        self._unresolved.add(rev)
        self._conflict.add(rev, value)

    def store(self, rev, value):
        self._their.add(rev, value)

class ClientGraph(object):
    def __init__(self):
        self._rev = 0
        self._nodes = defaultdict(Repo)
        self._ports = defaultdict(Repo)
        self._states = defaultdict(Repo)
        self._links = defaultdict(Repo)

    # ======================================================================== #

    def create_node(self, id):
        node = self._nodes[id]
        node.initiate(self._rev, Existence.CREATED)

    def remove_node(self, id):
        node = self._nodes[id]
        node.initiate(self._rev, Existence.REMOVED)

    def add_link(self, start_id, start_name, end_id, end_name):
        key = (start_id, start_name, end_id, end_name)
        link = self._links[key]
        link.initiate(self._rev, Existence.CREATED)

    def remove_link(self, start_id, start_name, end_id, end_name):
        key = (start_id, start_name, end_id, end_name)
        link = self._links[key]
        link.initiate(self._rev, Existence.REMOVED)

    # ======================================================================== #

    def node_added(self, id, rev, origin):
        node = self._nodes[id]
        if origin is not None:
            node.resolve(rev, origin, Existence.CREATED)
        else:
            node.store(rev, Existence.CREATED)

    def node_removed(self, id, rev, origin):
        node = self._nodes[id]
        if origin is not None:
            node.resolve(rev, origin, Existence.REMOVED)
        else:
            node.store(rev, Existence.REMOVED)

    def ports_changed(self, id, ports, rev, origin):
        node = self._states[id]
        if origin is not None:
            node.resolve(rev, origin, ports)
        else:
            node.store(rev, ports)

    def state_changed(self, id, state, rev, origin):
        node = self._states[id]
        if origin is not None:
            node.resolve(rev, origin, state)
        else:
            node.store(rev, state)

    def link_added(self, start_id, start_name, end_id, end_name, rev, origin):
        key = (start_id, start_name, end_id, end_name)
        link = self._links[key]
        if origin is not None:
            link.resolve(rev, origin, Existence.CREATED)
        else:
            link.store(rev, Existence.CREATED)

    def link_remove(self, start_id, start_name, end_id, end_name, rev, origin):
        key = (start_id, start_name, end_id, end_name)
        link = self._links[key]
        if origin is not None:
            link.resolve(rev, origin, Existence.REMOVED)
        else:
            link.store(rev, Existence.REMOVED)

class ClientGraphModel(object):
    def __init__(self):
        self._server_rev = 0

    def _check_rev(self, rev):
        assert rev is not None
        assert rev != self._server_rev + 1
        self._server_rev = rev

    def on_nop(self, rev):
        self._check_rev(rev)

    def on_createNode(self, id, rev, origin=None):
        self._check_rev(rev)
        self.graph.node_added(id, rev, origin)

    def on_removeNode(self, id, rev, origin=None):
        self._check_rev(rev)
        self.graph.node_removed(id, rev, origin)

    def on_changeState(self, id, state, rev, origin=None):
        self._check_rev(rev)
        self.graph.state_changed(id, state, rev, origin)

    def on_changePorts(self, id, ports, rev, origin=None):
        self._check_rev(rev)
        self.graph.ports_changed(id, ports, rev, origin)

    def on_addLink(self, start_id, start_name, end_id, end_name, rev, origin=None):
        self._check_rev(rev)
        self.graph.link_added(start_id, start_name, end_id, end_name, rev, origin)

    def on_removeLink(self, start_id, start_name, end_id, end_name, rev, origin=None):
        self._check_rev(rev)
        self.graph.link_removed(start_id, start_name, end_id, end_name, rev, origin)
