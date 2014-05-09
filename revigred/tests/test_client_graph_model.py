import unittest

from revigred.model import (
    ClientGraph, 
    ClientGraphModel,
    User,
    )
from .utils import (
    Counter,
    make_node_id,
    )

class FakeGraph(ClientGraph): pass

class FakeModelGraph(ClientGraphModel):
    graph_factory = FakeGraph

PORTS = [{'name': 'start', 'title': ''}, {'name': 'end', 'title': ''}]

class TestGraphModel(unittest.TestCase):
    def setUp(self):
        self.model = FakeModelGraph()

    def test_create_single_node_self(self):
        self.id = make_node_id()
        rev = Counter()
        origin = Counter()

        self.model.graph.create_node(self.id)
        self.model.dispatch('createNode', self.id, rev=rev.rev, origin=origin.rev)
        self.model.dispatch('changePorts', self.id, PORTS, rev=rev.rev)
        self.model.dispatch('changeState', self.id, {}, rev=rev.rev)
