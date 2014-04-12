from collections import defaultdict

__all__ = [
    "Port",
    "Node",
    "Link",
    "Graph",
    "ResultException",
    "ConflictOccured",
    "InvalidOperation",
    "NodeAlreadyExistsConflict",
    "PortAlreadyRemovedConflict",
    "NodeAlreadyRemovedConflict",
    "LinkAlreadyExistsConflict",
    "LinkAlreadyRemovedConflict",
    "NoSuchNodeError",
    "NoSuchPortError",
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

class Node(object):
    def __init__(self, id):
        self._id = id
        self._ports = []
        self._ports_by_name = {}

    @property
    def ports(self):
        yield from self._ports

    def has_port(self, name):
        return name in self._ports_by_name

    def get_port(self, name):
        return self._ports_by_name.get(name)

    def add_port(self, port, index=None):
        if index is None:
            index = len(self._ports)
        self._ports.insert(port)
        self._ports_by_name[port.name] = port

    def remove_port(self, name):
        port = self._ports_by_name[name]
        self._ports.remove(port)

    def get_ports(self):
        return [port.serialize() for port in self._ports]

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
class ConflictOccured(ResultException): pass
class InvalidOperation(ResultException): pass

class NodeAlreadyExistsConflict(ConflictOccured):
    def __init__(self, id):
        self.id = id

class PortAlreadyRemovedConflict(ConflictOccured):
    def __init__(self, id, name):
        self.id = id
        self.name = name

class NodeAlreadyRemovedConflict(ConflictOccured):
    def __init__(self, id):
        self.id = id

class LinkAlreadyExistsConflict(ConflictOccured):
    def __init__(self, start_id, start_name, end_id, end_name):
        self.start_id = start_id
        self.start_name = start_name
        self.end_id = end_id
        self.end_name = end_name

class LinkAlreadyRemovedConflict(ConflictOccured):
    def __init__(self, start_id, start_name, end_id, end_name):
        self.start_id = start_id
        self.start_name = start_name
        self.end_id = end_id
        self.end_name = end_name

class NoSuchNodeError(InvalidOperation):
    def __init__(self, id):
        self.id = id

class NoSuchPortError(InvalidOperation):
    def __init__(self, id, name):
        self.id = id
        self.name = name

# ____________________________________________________________________________ #

class Graph(object):
    node_factory = Node
    link_factory = Link

    def __init__(self):
        self._rev = 0
        self._nodes_by_name = {}
        self._links_by_key = {}
        self._links_by_start_id = defaultdict(dict)
        self._links_by_end_id = defaultdict(dict)

    def has_node(self, id):
        return id in self._nodes_by_name

    def get_node(self, id):
        return self._nodes_by_name[id]

    def add_node(self, node):
        self._nodes_by_name[node.id] = node

    def remove_node(self, id):
        del self._nodes_by_name[id]

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
            raise NodeAlreadyExistsConflict(id)

    def check_remove_node(self, id):
        if not self.has_node(id): 
            raise NodeAlreadyRemovedConflict(id)

    def check_add_link(self, start_id, start_name, end_id, end_name):
        if not self.has_node(start_id): 
            raise NoSuchNodeError(start_id)

        if not self.has_node(end_id): 
            raise NoSuchNodeError(end_id)

        if not self.get_node(start_id).has_port(start_name): 
            raise NoSuchPortError(start_id, start_name)

        if not self.get_node(end_id).has_port(end_name): 
            raise NoSuchPortError(end_id, end_name)

        if self.has_link(start_id, start_name, end_id, end_name):
            raise LinkAlreadyExistsConflict(start_id, start_name, end_id, end_name)

    def check_remove_link(self, start_id, start_name, end_id, end_name):
        if not self.has_node(start_id): 
            raise NodeAlreadyRemovedConflict(start_id)

        if not self.has_node(end_id): 
            raise NodeAlreadyRemovedConflict(end_id)

        if not self.get_node(start_id).has_port(start_name): 
            raise PortAlreadyRemovedConflict(start_id, start_name)

        if not self.get_node(end_id).has_port(end_name): 
            raise PortAlreadyRemovedConflict(end_id, end_name)

        if not self.has_link(start_id, start_name, end_id, end_name):
            raise LinkAlreadyRemovedConflict(start_id, start_name, end_id, end_name)

    # ======================================================================== #

    def on_nodeCreated(self, origin, id):
        try:
            self.check_create_node(id)
        except ConflictOccured:
            self.createNodeSelf(origin, id)
        except InvalidOperation:
            self.removeNodeSelf(origin, id)
        else:
            node = self.node_factory(id)
            self.add_node(node)
            self.changePortsAll(node.get_ports())
            self.changeStateAll(node.set_state())
            self.createNodeAll(origin, id)

    def on_nodeRemoved(self, origin, id):
        try:
            self.check_remove_node(id)
        except ConflictOccured:
            self.removeNodeSelf(origin, id)
        except InvalidOperation:
            self.createNodeSelf(origin, id)
        else:
            for link in self.find_links_startswith(id):
                self.remove_link(link)
                self.removeLinkAll(None,
                    link.start_id, link.start_name, 
                    link.end_id, link.end_name)

            for link in self.find_links_endswith(id):
                self.remove_link(link)
                self.removeLinkAll(None,
                    link.start_id, link.start_name, 
                    link.end_id, link.end_name)

            self.remove_node(id)
            self.removeNodeAll(origin, id)

    #def on_nodeStateChanged(self, origin, id, state): pass

    def on_linkAdded(self, origin, start_id, start_name, end_id, end_name):
        try:
            self.check_add_link(start_id, start_name, end_id, end_name)
        except ConflictOccured:
            self.addLinkSelf(origin, start_id, start_name, end_id, end_name)
        except InvalidOperation:
            self.removeLinkSelf(origin, start_id, start_name, end_id, end_name)
        else:
            link = self.link_factory(start_id, start_name, end_id, end_name)
            self.add_link(link)
            self.addLinkAll(origin, start_id, start_name, end_id, end_name)

    def on_linkRemoved(self, origin, start_id, start_name, end_id, end_name):
        try:
            self.check_remove_link(start_id, start_name, end_id, end_name)
        except ConflictOccured:
            self.removeLinkSelf(origin, start_id, start_name, end_id, end_name)
        except InvalidOperation:
            self.addLinkSelf(origin, start_id, start_name, end_id, end_name)
        else:
            self.remove_link(start_id, start_name, end_id, end_name)
            self.removeLinkAll(origin, start_id, start_name, end_id, end_name)

    # ======================================================================== #

    def _increv(self):
        old = self._rev
        self._rev += 1
        return old

    def _callSelf(self, name, origin, *args, **kwargs):
        rev = self._increv()
        origin.user.send(name, *args, rev=rev, origin=origin.rev, **kwargs)

    def _callAll(self, name, origin, *args, **kwargs):
        rev = self._increv()
        for user in self._users.values():
            if origin.user is user:
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

    def changeStateSelf(self, origin):
        self._callSelf("changeState", origin, id, state)

    def changeStateAll(self, origin):
        self._callAll("changeState", origin, id, state)

    def changePortsSelf(self, origin):
        self._callSelf("changePorts", origin, id, ports)

    def changePortsAll(self, origin):
        self._callAll("changePorts", origin, id, ports)

    def addLinkSelf(self, origin, start_id, start_name, end_id, end_name):
        self._callSelf("addLink", origin, start_id, start_name, end_id, end_name)

    def addLinkAll(self, origin, start_id, start_name, end_id, end_name):
        self._callAll("addLink", origin, start_id, start_name, end_id, end_name)

    def removeLinkSelf(self, origin, start_id, start_name, end_id, end_name):
        self._callSelf("removeLink", origin, start_id, start_name, end_id, end_name)
    
    def removeLinkAll(self, origin, start_id, start_name, end_id, end_name):
        self._callAll("removeLink", origin, start_id, start_name, end_id, end_name)
