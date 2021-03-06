import unittest
import uuid
from revigred.model import (
    Node, 
    Graph, 
    GraphModel,
    User,
    )
from .utils import (
    Counter,
    make_node_id,
    )

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

class FakeUser(User):
    def __init__(self, model):
        super().__init__(model)
        self._message_pool = []

    def send(self, name, *args, **kwargs):
        message = (name, args, kwargs)
        print(*message)
        self._message_pool.append(message)

    @property
    def messages(self):
        return self._message_pool

    def drop(self):
        self._message_pool = []

    def dispatch(self, name, *args, **kwargs):
        rev = kwargs.pop("rev")
        func = getattr(self.model, "on_" + name, None)
        if func is None:
            raise ValueError("command {} was not found")
        origin = FakeOrigin(self, rev)
        func(origin, *args, **kwargs)

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

PORTS = [{'name': 'start', 'title': ''}, {'name': 'end', 'title': ''}]

class TestGraphModel(unittest.TestCase):
    def setUp(self):
        self.model = FakeModelGraph()
        self.graph = self.model.graph
        self.user = self.model.create_new_user()
        self.observer = self.model.create_new_user()

    def test_create_single_node(self):
        self.id = make_node_id()
        test = Counter()
        self.user.dispatch("nodeCreated", self.id, rev=test.rev)

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
        test = Counter()
        self.user.dispatch("nodeCreated", self.id, rev=test.rev)
        self.user.dispatch("nodeCreated", self.id, rev=test.rev)

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
        test = Counter()
        self.user.dispatch("nodeCreated", self.id, rev=test.rev)
        self.user.dispatch("nodeRemoved", self.id, rev=test.rev)

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
        test = Counter()
        self.user.dispatch("nodeRemoved", self.id, rev=test.rev)

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
        test = Counter()
        self.user.dispatch("nodeCreated", self.id, rev=test.rev)
        self.user.dispatch("nodeRemoved", self.id, rev=test.rev)
        self.user.dispatch("nodeRemoved", self.id, rev=test.rev)

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
        test = Counter()
        self.user.dispatch("nodeCreated", self.id, rev=test.rev)
        self.user.dispatch("nodeRemoved", self.id, rev=test.rev)
        self.user.dispatch("nodeCreated", self.id, rev=test.rev)

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
        test = Counter()
        self.user.dispatch("nodeCreated", self.id, rev=test.rev)
        self.user.dispatch("nodeStateChanged", self.id, {"state": True}, rev=test.rev)

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
        test = Counter()
        self.user.dispatch("nodeStateChanged", self.id, {"state": True}, rev=test.rev)

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
        test = Counter()
        self.user.dispatch("nodeCreated", self.id1, rev=test.rev)
        self.user.dispatch("nodeCreated", self.id2, rev=test.rev)
        self.user.drop()
        self.observer.drop()

    def test_create_link(self):
        test = Counter(2)
        self.user.dispatch("linkAdded", self.id1, "start", self.id2, "end", rev=test.rev)

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
        test = Counter(2)
        self.user.dispatch("linkAdded", self.id1, "start", self.id2, "end", rev=test.rev)
        self.user.dispatch("linkAdded", self.id1, "start", self.id2, "end", rev=test.rev)

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
        test = Counter(2)
        self.user.dispatch("linkAdded", self.id1, "start", self.id2, "end", rev=test.rev)
        self.user.dispatch("linkRemoved", self.id1, "start", self.id2, "end", rev=test.rev)

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
        test = Counter(2)
        self.user.dispatch("linkAdded", self.id1, "start", self.id2, "end", rev=test.rev)
        self.user.dispatch("linkRemoved", self.id1, "start", self.id2, "end", rev=test.rev)
        self.user.dispatch("linkRemoved", self.id1, "start", self.id2, "end", rev=test.rev)

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
        test = Counter(2)
        self.user.dispatch("linkRemoved", self.id1, "start", self.id2, "end", rev=test.rev)

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
        test = Counter(2)
        self.user.dispatch("linkRemoved", self.id1, "start", self.id2, "end_", rev=test.rev)

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
        test = Counter(2)
        self.user.dispatch("linkRemoved", self.id1, "start_", self.id2, "end", rev=test.rev)

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
        test = Counter(2)
        self.user.dispatch("linkRemoved", self.id3, "start", self.id2, "end", rev=test.rev)

        rev = Counter(6)
        origin = Counter(2)
        self.assertSequenceEqual(self.user.messages, [
            ('removeLink', (self.id3, "start", self.id2, "end"), {'rev': rev.rev, 'origin': origin.rev}),
            ])

        rev = Counter(6)
        self.assertSequenceEqual(self.observer.messages, [
            ('nop', (), {'rev': rev.rev}),
            ])

    def test_remove_inexist_link_5(self):
        test = Counter(2)
        self.user.dispatch("linkRemoved", self.id1, "start", self.id3, "end", rev=test.rev)

        rev = Counter(6)
        origin = Counter(2)
        self.assertSequenceEqual(self.user.messages, [
            ('removeLink', (self.id1, "start", self.id3, "end"), {'rev': rev.rev, 'origin': origin.rev}),
            ])

        rev = Counter(6)
        self.assertSequenceEqual(self.observer.messages, [
            ('nop', (), {'rev': rev.rev}),
            ])
