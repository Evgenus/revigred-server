from functools import partial
from enum import Enum
from sentinels import NOTHING

class InvalidCommand(DocDescribed, ValueError):
    "Command {name} was not found"
    def __init__(self, name):
        self.name = name

class InvalidRevision(DocDescribed, Exception):
    "Expected {expected} revision but got {got}"
    def __init__(self, got, expected):
        self.got = got
        self.expected = expected

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
        self._unresolved = deque()
        self._receivers = []

    def resolve(self, rev, origin, value):
        self._their.add(rev, value)
        expected = self._unresolved.popleft()
        if expected != origin:
            raise InvalidRevision(origin, expected)

    def initiate(self, rev, value):
        self._conflict.add(rev, value)
        self._unresolved.append(rev)

    def store(self, rev, value):
        self._their.add(rev, value)

    def _publish(self, event, *args, **kwargs):
        for callback in self._receivers:
            callback(this, event, *args, **kwargs)

    def subscribe(self, callback):
        if callback in self._receivers:
            return
        self._receivers.append(callback)

    def unsubscribe(self, callback):
        if callback not in self._receivers:
            return
        self._receivers.remove(callback)

class ClientGraph(object):
    repo_factory = Repo
    def __init__(self):
        self._rev = 0
        self._nodes = defaultdict(self.repo_factory)
        self._ports = defaultdict(self.repo_factory)
        self._states = defaultdict(self.repo_factory)
        self._links = defaultdict(self.repo_factory)

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
    graph_factory = ClientGraph
    def __init__(self):
        self._graph = self.graph_factory()
        self._server_rev = 0

    @property
    def graph(self):
        return self._graph

    def dispatch(self, name, *args, **kwargs):
        func = getattr(self, "on_" + name, None)
        if func is None:
            raise InvalidCommand(name)
        func(*args, **kwargs)

    def _check_rev(self, rev):
        if rev != self._server_rev:
            raise InvalidRevision(rev, self._server_rev)
        self._server_rev = rev + 1

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
