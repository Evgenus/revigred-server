import unittest
import uuid
from revigred.model.graph.fs import (
    FSGraph, 
    FSGraphModel,
    )
from revigred.model import (
    Node, 
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

class FakeGraph(FSGraph):
    node_factory = FakeNode

class FakeModelGraph(FSGraphModel):
    user_factory = FakeUser
    graph_factory = FakeGraph

class TestGraphModel(unittest.TestCase):
    def setUp(self):
        self.model = FakeModelGraph()
        self.graph = self.model.graph
        self.user = self.model.create_new_user()
        #self.observer = self.model.create_new_user()

    def test_create_single_node(self):
        self.id = make_node_id()
        test = Counter()
        self.user.dispatch("nodeCreated", self.id, rev=test.rev)
        self.user.dispatch("nodeStateChanged", self.id, {"path": "./revigred"}, rev=test.rev)

        rev = Counter()
        origin = Counter()
        self.assertSequenceEqual(self.user.messages, [
            ('createNode', (self.id,), {'rev': rev.rev, 'origin': origin.rev}),
            ('changeState', (self.id, {}), {'rev': rev.rev}),
            ])

        # rev = Counter()
        # self.assertSequenceEqual(self.observer.messages, [
        #     ('createNode', (self.id,), {'rev': rev.rev}),
        #     ('changeState', (self.id, {}), {'rev': rev.rev}),
        #     ])
