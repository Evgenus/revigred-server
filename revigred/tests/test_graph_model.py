import unittest
import uuid
from revigred.model import (
    Node, 
    Graph, 
    GraphModel,
    User,
    )

class FakeUser(User):
    def __init__(self, model):
        super().__init__(model)
        self._message_pool = []
        self._rev = 0

    def send(self, name, *args, **kwargs):
        message = (name, args, kwargs)
        print(*message)
        self._message_pool.append(message)

    @property
    def messages(self):
        return self._message_pool

    def make_origin(self):
        origin = FakeOrigin(self, self._rev)
        self._rev += 1
        return origin

    def drop(self):
        self._message_pool = []

class FakeOrigin(object):
    def __init__(self, user, rev):
        self._user = user
        self._rev = rev

    @property
    def user(self):
        return self._user

    @property
    def rev(self):
        return self._rev

class FakeNode(Node):
    def __init__(self, id):
        super().__init__(id)
        self.add_port(self.port_factory("start", ""))
        self.add_port(self.port_factory("end", ""))

class FakeGraph(Graph):
    node_factory = FakeNode

class FakeModelGraph(GraphModel):
    user_factory = FakeUser
    graph_factory = FakeGraph

class Counter(object):
    def __init__(self, start=0):
        self._value = start

    @property
    def rev(self):
        old = self._value
        self._value += 1
        return old

PORTS = [{'name': 'start', 'title': ''}, {'name': 'end', 'title': ''}]

def make_node_id():
    return "NODE-" + uuid.uuid4().hex

class TestNodes(unittest.TestCase):
    def setUp(self):
        self.model = FakeModelGraph()
        self.graph = self.model.graph
        self.user = self.model.create_new_user()
        self.observer = self.model.create_new_user()

    def test_create_single_node(self):
        self.id = make_node_id()
        self.model.on_nodeCreated(self.user.make_origin(), self.id)

        rev = Counter()
        origin = Counter()
        self.assertSequenceEqual(self.user.messages, [
            ('createNode', (self.id,), {'rev': rev.rev, 'origin': origin.rev}),
            ('changePorts', (self.id, PORTS), {'rev': rev.rev}),
            ('changeState', (self.id, {}), {'rev': rev.rev}),
            ])

        rev = Counter()
        self.assertSequenceEqual(self.observer.messages, [
            ('createNode', (self.id,), {'rev': rev.rev}),
            ('changePorts', (self.id, PORTS), {'rev': rev.rev}),
            ('changeState', (self.id, {}), {'rev': rev.rev}),
            ])

    def test_double_node_create_conflict(self):
        self.id = make_node_id()
        self.model.on_nodeCreated(self.user.make_origin(), self.id)
        self.model.on_nodeCreated(self.user.make_origin(), self.id)

        rev = Counter()
        origin = Counter()
        self.assertSequenceEqual(self.user.messages, [
            ('createNode', (self.id,), {'rev': rev.rev, 'origin': origin.rev}),
            ('changePorts', (self.id, PORTS), {'rev': rev.rev}),
            ('changeState', (self.id, {}), {'rev': rev.rev}),
            ('createNode', (self.id,), {'rev': rev.rev, 'origin': origin.rev}),
            ])

        rev = Counter()
        self.assertSequenceEqual(self.observer.messages, [
            ('createNode', (self.id,), {'rev': rev.rev}),
            ('changePorts', (self.id, PORTS), {'rev': rev.rev}),
            ('changeState', (self.id, {}), {'rev': rev.rev}),
            ('nop', (), {'rev': rev.rev}),
            ])

    def test_create_single_node_remove_node(self):
        self.id = make_node_id()
        self.model.on_nodeCreated(self.user.make_origin(), self.id)
        self.model.on_nodeRemoved(self.user.make_origin(), self.id)

        rev = Counter()
        origin = Counter()
        self.assertSequenceEqual(self.user.messages, [
            ('createNode', (self.id,), {'rev': rev.rev, 'origin': origin.rev}),
            ('changePorts', (self.id, PORTS), {'rev': rev.rev}),
            ('changeState', (self.id, {}), {'rev': rev.rev}),
            ('removeNode', (self.id,), {'rev': rev.rev, 'origin': origin.rev}),
            ])

        rev = Counter()
        self.assertSequenceEqual(self.observer.messages, [
            ('createNode', (self.id,), {'rev': rev.rev}),
            ('changePorts', (self.id, PORTS), {'rev': rev.rev}),
            ('changeState', (self.id, {}), {'rev': rev.rev}),
            ('removeNode', (self.id,), {'rev': rev.rev}),
            ])

    def test_remove_not_existant_node(self):
        self.id = make_node_id()
        self.model.on_nodeRemoved(self.user.make_origin(), self.id)

        rev = Counter()
        origin = Counter()
        self.assertSequenceEqual(self.user.messages, [
            ('removeNode', (self.id,), {'rev': rev.rev, 'origin': origin.rev}),
            ])

        rev = Counter()
        self.assertSequenceEqual(self.observer.messages, [
            ('nop', (), {'rev': rev.rev}),
            ])

    def test_create_single_node_double_remove_node_conflict(self):
        self.id = make_node_id()
        self.model.on_nodeCreated(self.user.make_origin(), self.id)
        self.model.on_nodeRemoved(self.user.make_origin(), self.id)
        self.model.on_nodeRemoved(self.user.make_origin(), self.id)

        rev = Counter()
        origin = Counter()
        self.assertSequenceEqual(self.user.messages, [
            ('createNode', (self.id,), {'rev': rev.rev, 'origin': origin.rev}),
            ('changePorts', (self.id, PORTS), {'rev': rev.rev}),
            ('changeState', (self.id, {}), {'rev': rev.rev}),
            ('removeNode', (self.id,), {'rev': rev.rev, 'origin': origin.rev}),
            ('removeNode', (self.id,), {'rev': rev.rev, 'origin': origin.rev}),
            ])

        rev = Counter()
        self.assertSequenceEqual(self.observer.messages, [
            ('createNode', (self.id,), {'rev': rev.rev}),
            ('changePorts', (self.id, PORTS), {'rev': rev.rev}),
            ('changeState', (self.id, {}), {'rev': rev.rev}),
            ('removeNode', (self.id,), {'rev': rev.rev}),
            ('nop', (), {'rev': rev.rev}),
            ])

    def test_create_remove_create_single(self):
        self.id = make_node_id()
        self.model.on_nodeCreated(self.user.make_origin(), self.id)
        self.model.on_nodeRemoved(self.user.make_origin(), self.id)
        self.model.on_nodeCreated(self.user.make_origin(), self.id)

        rev = Counter()
        origin = Counter()
        self.assertSequenceEqual(self.user.messages, [
            ('createNode', (self.id,), {'rev': rev.rev, 'origin': origin.rev}),
            ('changePorts', (self.id, PORTS), {'rev': rev.rev}),
            ('changeState', (self.id, {}), {'rev': rev.rev}),
            ('removeNode', (self.id,), {'rev': rev.rev, 'origin': origin.rev}),
            ('createNode', (self.id,), {'rev': rev.rev, 'origin': origin.rev}),
            ('changePorts', (self.id, PORTS), {'rev': rev.rev}),
            ('changeState', (self.id, {}), {'rev': rev.rev}),
            ])

        rev = Counter()
        self.assertSequenceEqual(self.observer.messages, [
            ('createNode', (self.id,), {'rev': rev.rev}),
            ('changePorts', (self.id, PORTS), {'rev': rev.rev}),
            ('changeState', (self.id, {}), {'rev': rev.rev}),
            ('removeNode', (self.id,), {'rev': rev.rev}),
            ('createNode', (self.id,), {'rev': rev.rev}),
            ('changePorts', (self.id, PORTS), {'rev': rev.rev}),
            ('changeState', (self.id, {}), {'rev': rev.rev}),
            ])

    def test_create_node_change_state(self):
        self.id = make_node_id()
        self.model.on_nodeCreated(self.user.make_origin(), self.id)
        self.model.on_nodeStateChanged(self.user.make_origin(), self.id, {"state": True})

        rev = Counter()
        origin = Counter()
        self.assertSequenceEqual(self.user.messages, [
            ('createNode', (self.id,), {'rev': rev.rev, 'origin': origin.rev}),
            ('changePorts', (self.id, PORTS), {'rev': rev.rev}),
            ('changeState', (self.id, {}), {'rev': rev.rev}),
            ('changeState', (self.id, {"state":True}), {'rev': rev.rev, 'origin': origin.rev}),
            ])

        rev = Counter()
        self.assertSequenceEqual(self.observer.messages, [
            ('createNode', (self.id,), {'rev': rev.rev}),
            ('changePorts', (self.id, PORTS), {'rev': rev.rev}),
            ('changeState', (self.id, {}), {'rev': rev.rev}),
            ('changeState', (self.id, {"state":True}), {'rev': rev.rev}),
            ])

    def test_change_state_no_node(self):
        self.id = make_node_id()
        self.model.on_nodeStateChanged(self.user.make_origin(), self.id, {"state": True})

        rev = Counter()
        origin = Counter()
        self.assertSequenceEqual(self.user.messages, [
            ('changeState', (self.id, None), {'rev': rev.rev, 'origin': origin.rev}),
            ])

        rev = Counter()
        self.assertSequenceEqual(self.observer.messages, [
            ('nop', (), {'rev': rev.rev}),
            ])

class TestLinks(unittest.TestCase):
    def setUp(self):
        self.model = FakeModelGraph()
        self.graph = self.model.graph
        self.user = self.model.create_new_user()
        self.observer = self.model.create_new_user()
        self.id1 = make_node_id()
        self.id2 = make_node_id()
        self.id3 = make_node_id()
        self.model.on_nodeCreated(self.user.make_origin(), self.id1)
        self.model.on_nodeCreated(self.user.make_origin(), self.id2)
        self.user.drop()
        self.observer.drop()

    def test_create_link(self):
        self.model.on_linkAdded(self.user.make_origin(), self.id1, "start", self.id2, "end")

        rev = Counter(6)
        origin = Counter(2)
        self.assertSequenceEqual(self.user.messages, [
            ('addLink', (self.id1, "start", self.id2, "end"), {'rev': rev.rev, 'origin': origin.rev}),
            ])

        rev = Counter(6)
        self.assertSequenceEqual(self.observer.messages, [
            ('addLink', (self.id1, "start", self.id2, "end"), {'rev': rev.rev}),
            ])

    def test_double_create_link(self):
        self.model.on_linkAdded(self.user.make_origin(), self.id1, "start", self.id2, "end")
        self.model.on_linkAdded(self.user.make_origin(), self.id1, "start", self.id2, "end")

        rev = Counter(6)
        origin = Counter(2)
        self.assertSequenceEqual(self.user.messages, [
            ('addLink', (self.id1, "start", self.id2, "end"), {'rev': rev.rev, 'origin': origin.rev}),
            ('addLink', (self.id1, "start", self.id2, "end"), {'rev': rev.rev, 'origin': origin.rev}),
            ])

        rev = Counter(6)
        self.assertSequenceEqual(self.observer.messages, [
            ('addLink', (self.id1, "start", self.id2, "end"), {'rev': rev.rev}),
            ('nop', (), {'rev': rev.rev}),
            ])

    def test_create_remove_link(self):
        self.model.on_linkAdded(self.user.make_origin(), self.id1, "start", self.id2, "end")
        self.model.on_linkRemoved(self.user.make_origin(), self.id1, "start", self.id2, "end")

        rev = Counter(6)
        origin = Counter(2)
        self.assertSequenceEqual(self.user.messages, [
            ('addLink', (self.id1, "start", self.id2, "end"), {'rev': rev.rev, 'origin': origin.rev}),
            ('removeLink', (self.id1, "start", self.id2, "end"), {'rev': rev.rev, 'origin': origin.rev}),
            ])

        rev = Counter(6)
        self.assertSequenceEqual(self.observer.messages, [
            ('addLink', (self.id1, "start", self.id2, "end"), {'rev': rev.rev}),
            ('removeLink', (self.id1, "start", self.id2, "end"), {'rev': rev.rev}),
            ])

    def test_create_double_remove_link(self):
        self.model.on_linkAdded(self.user.make_origin(), self.id1, "start", self.id2, "end")
        self.model.on_linkRemoved(self.user.make_origin(), self.id1, "start", self.id2, "end")
        self.model.on_linkRemoved(self.user.make_origin(), self.id1, "start", self.id2, "end")

        rev = Counter(6)
        origin = Counter(2)
        self.assertSequenceEqual(self.user.messages, [
            ('addLink', (self.id1, "start", self.id2, "end"), {'rev': rev.rev, 'origin': origin.rev}),
            ('removeLink', (self.id1, "start", self.id2, "end"), {'rev': rev.rev, 'origin': origin.rev}),
            ('removeLink', (self.id1, "start", self.id2, "end"), {'rev': rev.rev, 'origin': origin.rev}),
            ])

        rev = Counter(6)
        self.assertSequenceEqual(self.observer.messages, [
            ('addLink', (self.id1, "start", self.id2, "end"), {'rev': rev.rev}),
            ('removeLink', (self.id1, "start", self.id2, "end"), {'rev': rev.rev}),
            ('nop', (), {'rev': rev.rev}),
            ])

    def test_remove_inexist_link_1(self):
        self.model.on_linkRemoved(self.user.make_origin(), self.id1, "start", self.id2, "end")

        rev = Counter(6)
        origin = Counter(2)
        self.assertSequenceEqual(self.user.messages, [
            ('removeLink', (self.id1, "start", self.id2, "end"), {'rev': rev.rev, 'origin': origin.rev}),
            ])

        rev = Counter(6)
        self.assertSequenceEqual(self.observer.messages, [
            ('nop', (), {'rev': rev.rev}),
            ])

    def test_remove_inexist_link_2(self):
        self.model.on_linkRemoved(self.user.make_origin(), self.id1, "start", self.id2, "end_")

        rev = Counter(6)
        origin = Counter(2)
        self.assertSequenceEqual(self.user.messages, [
            ('removeLink', (self.id1, "start", self.id2, "end_"), {'rev': rev.rev, 'origin': origin.rev}),
            ])

        rev = Counter(6)
        self.assertSequenceEqual(self.observer.messages, [
            ('nop', (), {'rev': rev.rev}),
            ])

    def test_remove_inexist_link_3(self):
        self.model.on_linkRemoved(self.user.make_origin(), self.id1, "start_", self.id2, "end")

        rev = Counter(6)
        origin = Counter(2)
        self.assertSequenceEqual(self.user.messages, [
            ('removeLink', (self.id1, "start_", self.id2, "end"), {'rev': rev.rev, 'origin': origin.rev}),
            ])

        rev = Counter(6)
        self.assertSequenceEqual(self.observer.messages, [
            ('nop', (), {'rev': rev.rev}),
            ])

    def test_remove_inexist_link_4(self):
        self.model.on_linkRemoved(self.user.make_origin(), self.id3, "start", self.id2, "end")

        rev = Counter(6)
        origin = Counter(2)
        self.assertSequenceEqual(self.user.messages, [
            ('removeLink', (self.id3, "start", self.id2, "end"), {'rev': rev.rev, 'origin': origin.rev}),
            ])

        rev = Counter(6)
        self.assertSequenceEqual(self.observer.messages, [
            ('nop', (), {'rev': rev.rev}),
            ])

    def test_remove_inexist_link_1(self):
        self.model.on_linkRemoved(self.user.make_origin(), self.id1, "start", self.id3, "end")

        rev = Counter(6)
        origin = Counter(2)
        self.assertSequenceEqual(self.user.messages, [
            ('removeLink', (self.id1, "start", self.id3, "end"), {'rev': rev.rev, 'origin': origin.rev}),
            ])

        rev = Counter(6)
        self.assertSequenceEqual(self.observer.messages, [
            ('nop', (), {'rev': rev.rev}),
            ])
