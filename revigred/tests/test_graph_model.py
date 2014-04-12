import unittest
import uuid
from revigred.model import Graph

class FakeUser(object):
    def __init__(self, model):
        self.id = "USER-" + uuid.uuid4().hex
        self._message_pool = []
    def send(self, name, *args, **kwargs):
        message = (name, args, kwargs)
        print(*message)
        self._message_pool.append(message)
    @property
    def messages(self):
        return self._message_pool

class FakeOrigin(object):
    def __init__(self, user, rev):
        self.user = user
        self.rev = rev

class FakeGraph(Graph):
    user_factory = FakeUser

class TestGraphModel(unittest.TestCase):
    def make_origin(self):
        origin = FakeOrigin(self.user, self.rev)
        self.rev += 1
        return origin

    def make_node_id(self):
        return "NODE-" + uuid.uuid4().hex

    def setUp(self):
        self.graph = FakeGraph()
        self.user = self.graph.create_new_user()
        self.rev = 0

    def test_on_createNode_success(self):
        node_id = self.make_node_id()
        self.graph.on_nodeCreated(self.make_origin(), node_id)

        self.assertSequenceEqual(self.user.messages, [
            ('changePorts', (node_id, []), {'rev': 0}),
            ('createNode', (node_id,), {'rev': 1, 'origin': 0}),
            ])

    def test_on_createNode_fail_conflict(self):
        node_id = self.make_node_id()
        self.graph.on_nodeCreated(self.make_origin(), node_id)
        self.graph.on_nodeCreated(self.make_origin(), node_id)

        self.assertSequenceEqual(self.user.messages, [
            ('changePorts', (node_id, []), {'rev': 0}),
            ('createNode', (node_id,), {'rev': 1, 'origin': 0}),
            ('createNode', (node_id,), {'rev': 2, 'origin': 1}),
            ])
