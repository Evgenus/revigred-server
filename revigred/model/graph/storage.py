import weakref
from copy import deepcopy
from collections import defaultdict

from revigred.record import Record

from .events import *

__all__ = [
    "Port",
    "Node",
    "Link",
    "Graph",
    "NodeExists",
    "NoSuchNode",
    "NoSuchPort",
    "LinkExists",
    "NoSuchLink",
    ]

class MethodsWeakSet(set):
    def add(self, method):
        set.add(self, weakref.WeakMethod(method, self.remove))

class EventEmmiter(object):
    def __init__(self):
        super().__init__()
        self._listeners = defaultdict(MethodsWeakSet)

    def on(self, name, method):
        self._listeners[name].add(method)

    def notify(self, name, *args, **kwargs):
        for method in self._listeners.get(name, ()):
            method()(*args, **kwargs)

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

# ____________________________________________________________________________ #

class Port(object):
    def __init__(self, name, title):
        super().__init__()
        self._name = name
        self._title = title

    @property
    def name(self): 
        return self._name

    @property
    def title(self):
        return self._title

    def serialize(self):
        return Record(
            name=self._name,
            title=self._title,
            )

class Node(EventEmmiter):
    port_factory = Port

    def __init__(self, id):
        super().__init__()
        self._id = id
        self._state = {}
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
        self.notify("change:ports", self.id)

    def remove_port(self, name):
        port = self._ports_by_name[name]
        self._ports.remove(port)
        self.notify("change:ports", self.id)

    def get_ports(self):
        return [port.serialize() for port in self._ports]

    def set_ports(self, ports):
        self._ports = deepcopy(ports)
        self.notify("change:ports", self.id)

    def get_state(self):
        return deepcopy(self._state)

    def set_state(self, state):
        self._state = state
        self.notify("change:state", self.id)

class Link(object):
    def __init__(self, start_id, start_name, end_id, end_name):
        super().__init__()
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

class Graph(EventEmmiter):
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
        self.notify("node:add", node.id)

    def remove_node(self, id):
        del self._nodes_by_id[id]
        self.notify("node:remove", id)

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
        self.notify("link:add", key)

    def remove_link(self, start_id, start_name, end_id, end_name):
        key = (start_id, start_name, end_id, end_name)
        del self._links_by_key[key]
        del self._links_by_start_id[start_id][key]
        del self._links_by_end_id[end_id][key]
        self.notify("link:remove", key)

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