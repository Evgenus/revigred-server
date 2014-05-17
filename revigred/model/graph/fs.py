from .storage import Graph, Port, Link
from .model import GraphModel

import os
import os.path
import uuid

class FSGraph(Graph):
    def check_change_state(self, id, state):
        super().check_change_state(id, state)
        node = self.get_node(id)
        old = node.get_state()
        if old["__type__"] != "Root":
            raise Cancel()
        if "__type__" in state:
            raise Cancel()
        if "path" not in state:
            raise Cancel()

    def walk(self, node, nodes, links):
        if node.id in nodes:
            return
        nodes[node.id] = node
        for link in self.find_links_startswith(node.id):
            key = (link.start_id, link.start_name, link.end_id, link.end_name)
            links[key] = link
            self.walk(link.end_id, nodes, links)

class FSGraphModel(GraphModel):
    graph_factory = FSGraph
    
    def on_nodeCreated(self, origin, id):
        node = self.graph.node_factory(id)
        node.set_state({
            "__type__": "Root",
            "path": None,
            })
        node.set_ports([])
        self.graph.add_node(node)
        self.createNodeAll(origin, id)
        self.changePortsAll(None, id, node.get_ports())
        self.changeStateAll(None, id, node.get_state())

    def fill_node(self, path, root):
        for name in os.listdir(path):
            node = self.graph.node_factory("NODE-" + uuid.uuid4().hex)
            self.createNodeAll(None, node.id)
            subpath = os.path.join(path, name)
            if os.path.isdir(subpath): 
                node.set_state({
                    "__type__": "Folder",
                    "path": subpath,
                    })
                self.fill_node(subpath, node)
            else:
                node.set_state({
                    "__type__": "File",
                    "path": subpath,
                    })
            self.changeStateAll(None, node.id, node.get_state())

            node.add_port(Port("in", ""))
            root.add_port(Port(name, name))
            self.changePortsAll(None, node.id, node.get_ports())
            self.graph.add_link(Link(root.id, name, node.id, "in"))
            self.addLinkAll(None, root.id, name, node.id, "in")

    def on_nodeStateChanged(self, origin, id, state):
        try:
            self.graph.check_change_state(id, state)
        except Cancel:
            self.changeStateSelf(origin, id, None)
        else:
            node = self.graph.get_node(id)
            old = node.get_state()
            old["path"] = state["path"]
            subnodes = {}
            sublinks = {}
            self.graph.walk(node, subnodes, sublinks)
            for sublink in sublinks:
                self.graph.remove_link(sublink.start_id, sublink.start_name, sublink.end_id, sublink.end_name)
                self.removeLinkAll(None, sublink.start_id, sublink.start_name, sublink.end_id, sublink.end_name)
            for sub_id in subnodes:
                if sub_id == id: continue
                self.graph.remove_node(sub_id)
                self.removeNodeAll(None, sub_id)

            self.fill_node(state["path"], node)

            self.changePortsAll(None, node.id, node.get_ports())
            node.set_state(old)
            self.changeStateAll(origin, id, node.get_state())
