import unittest
import uuid
from revigred.model import GraphModel
from revigred.model import User

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

class FakeModelGraph(GraphModel):
    user_factory = FakeUser

class TestGraphModel(unittest.TestCase):
    def make_node_id(self):
        return "NODE-" + uuid.uuid4().hex

    def setUp(self):
        self.model = FakeModelGraph()
        self.graph = self.model.graph
        self.user = self.model.create_new_user()
        self.observer = self.model.create_new_user()

    def test_creating_single_node(self):
        node_id = self.make_node_id()
        self.model.on_nodeCreated(self.user.make_origin(), node_id)

        self.assertSequenceEqual(self.user.messages, [
            ('changePorts', (node_id, []), {'rev': 0}),
            ('changeState', (node_id, {}), {'rev': 1}),
            ('createNode', (node_id,), {'rev': 2, 'origin': 0}),
            ])

        self.assertSequenceEqual(self.observer.messages, [
            ('changePorts', (node_id, []), {'rev': 0}),
            ('changeState', (node_id, {}), {'rev': 1}),
            ('createNode', (node_id,), {'rev': 2}),
            ])

    def test_double_node_create_conflict(self):
        node_id = self.make_node_id()
        self.model.on_nodeCreated(self.user.make_origin(), node_id)
        self.model.on_nodeCreated(self.user.make_origin(), node_id)

        self.assertSequenceEqual(self.user.messages, [
            ('changePorts', (node_id, []), {'rev': 0}),
            ('changeState', (node_id, {}), {'rev': 1}),
            ('createNode', (node_id,), {'rev': 2, 'origin': 0}),
            ('createNode', (node_id,), {'rev': 3, 'origin': 1}),
            ])

        self.assertSequenceEqual(self.observer.messages, [
            ('changePorts', (node_id, []), {'rev': 0}),
            ('changeState', (node_id, {}), {'rev': 1}),
            ('createNode', (node_id,), {'rev': 2}),
            ])

    def test_creating_single_node_remove_node(self):
        node_id = self.make_node_id()
        self.model.on_nodeCreated(self.user.make_origin(), node_id)
        self.model.on_nodeRemoved(self.user.make_origin(), node_id)

        self.assertSequenceEqual(self.user.messages, [
            ('changePorts', (node_id, []), {'rev': 0}),
            ('changeState', (node_id, {}), {'rev': 1}),
            ('createNode', (node_id,), {'rev': 2, 'origin': 0}),
            ('removeNode', (node_id,), {'rev': 3, 'origin': 1}),
            ])

        self.assertSequenceEqual(self.observer.messages, [
            ('changePorts', (node_id, []), {'rev': 0}),
            ('changeState', (node_id, {}), {'rev': 1}),
            ('createNode', (node_id,), {'rev': 2}),
            ('removeNode', (node_id,), {'rev': 3}),
            ])

    def test_remove_not_existant_node(self):
        node_id = self.make_node_id()
        self.model.on_nodeRemoved(self.user.make_origin(), node_id)

        self.assertSequenceEqual(self.user.messages, [
            ('removeNode', (node_id,), {'rev': 0, 'origin': 0}),
            ])

        self.assertSequenceEqual(self.observer.messages, [
            ])

    def test_creating_single_node_double_remove_node_conflict(self):
        node_id = self.make_node_id()
        self.model.on_nodeCreated(self.user.make_origin(), node_id)
        self.model.on_nodeRemoved(self.user.make_origin(), node_id)
        self.model.on_nodeRemoved(self.user.make_origin(), node_id)

        self.assertSequenceEqual(self.user.messages, [
            ('changePorts', (node_id, []), {'rev': 0}),
            ('changeState', (node_id, {}), {'rev': 1}),
            ('createNode', (node_id,), {'rev': 2, 'origin': 0}),
            ('removeNode', (node_id,), {'rev': 3, 'origin': 1}),
            ('removeNode', (node_id,), {'rev': 4, 'origin': 2}),
            ])

        self.assertSequenceEqual(self.observer.messages, [
            ('changePorts', (node_id, []), {'rev': 0}),
            ('changeState', (node_id, {}), {'rev': 1}),
            ('createNode', (node_id,), {'rev': 2}),
            ('removeNode', (node_id,), {'rev': 3}),
            ])

    def test_creating_remove_create_single(self):
        node_id = self.make_node_id()
        self.model.on_nodeCreated(self.user.make_origin(), node_id)
        self.model.on_nodeRemoved(self.user.make_origin(), node_id)
        self.model.on_nodeCreated(self.user.make_origin(), node_id)

        self.assertSequenceEqual(self.user.messages, [
            ('changePorts', (node_id, []), {'rev': 0}),
            ('changeState', (node_id, {}), {'rev': 1}),
            ('createNode', (node_id,), {'rev': 2, 'origin': 0}),
            ('removeNode', (node_id,), {'rev': 3, 'origin': 1}),
            ('changePorts', (node_id, []), {'rev': 4}),
            ('changeState', (node_id, {}), {'rev': 5}),
            ('createNode', (node_id,), {'rev': 6, 'origin': 2}),
            ])

        self.assertSequenceEqual(self.observer.messages, [
            ('changePorts', (node_id, []), {'rev': 0}),
            ('changeState', (node_id, {}), {'rev': 1}),
            ('createNode', (node_id,), {'rev': 2}),
            ('removeNode', (node_id,), {'rev': 3}),
            ('changePorts', (node_id, []), {'rev': 4}),
            ('changeState', (node_id, {}), {'rev': 5}),
            ('createNode', (node_id,), {'rev': 6}),
            ])
