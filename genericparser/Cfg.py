import networkx as nx
from networkx.drawing.nx_pydot import write_dot


class Cfg:
    _graph = None
    _num_edges = 0
    _keys = {}
    _vars = []

    def __init__(self, graph=None, vars_name=[]):
        if graph is None:
            self._graph = nx.MultiDiGraph()
            self._num_edges = 0
            self._keys = {}
            self._vars = []
        else:
            self._graph = graph
            self._num_edges = self._graph.number_of_edges()
            self._vars = vars_name
            self._keys = {}
            for ed in self._graph.edges():
                self._keys[ed.name] = (ed.src, ed.trg)

    def add_var_name(self, vars_name):
        self._vars = vars_name

    def get_var_name(self, idx=None):
        if idx is None:
            return self._vars
        return self._vars[idx]

    def add_edge(self, name, src, trg, **kwargs):
        """Add an edge.

        :param name: transition name
        :type name: str
        :param src: Source node name
        :type src: str
        :param trg: Target node name
        :type trg: str
        :param \**kwargs: Properties or attributes of the edge.
            `src`, `trg`, `key` and `name` tags will be ignored.

        """
        color = ["#3366CC", "#3B3EAC", "#DC3912", "#FF9900", "#109618",
                 "#990099", "#3B8EAC", "#0099C6", "#DD4477", "#66AA00",
                 "#B82E2E", "#316395", "#994499", "#22AA99", "#AAAA11",
                 "#6633CC", "#E67300", "#8B0707", "#329262", "#5574A6"]

        if "color" in kwargs:
            c = kwargs["color"]
        else:
            c = color[self._num_edges]

        kwargs["source"] = src
        kwargs["target"] = trg
        kwargs["color"] = c
        kwargs["fontcolor"] = c
        label = name
        if "tr_polyhedron" in kwargs:
            label += " {\n"
            for c in kwargs["tr_polyhedron"].get_constraints():
                label += str(c) + "\n"
            label += "}"
        kwargs["label"] = label
        kwargs["name"] = name

        self._graph.add_edge(src, trg, key=name, **kwargs)
        self._keys[name] = (src, trg)
        self._num_edges += 1

    def get_edges(self, src=None, trg=None, name=None):
        """Returns a list of edges from `src` to `trg` with format
        { src: src, trg: trg, name: name , other_options }

        :param src: Source Node, optional, Defaults None
        :type src: `str`
        :param trg: Target Node, optional, Defaults None
        :type trg: `str`
        :param name: hashable identifier, optional, Defaults None
            Used to distinguish multiple edges between a pair of nodes.
        :type name: `str`

        if src, trg or name are None all values of them are suitables.
        """
        if src is None and trg is None and not(name is None):
            return [self.get_edge(name)]
        edges = []
        for e in self._graph.edges:
            if src is None or src == e["source"]:
                if trg is None or trg == e["target"]:
                    if name is None or name == e["name"]:
                        edges.append(e)
        return edges

    def get_edge(self, name):
        """Returns the edge identified by the name

        :param name: hashable identifier
        :type name: `str`
        """
        if name in self._keys:
            src, trg = self._keys[name]
            if src in self._graph and trg in self._graph[src]:
                return self._graph[src][trg][name]
        return None

    def remove_edge(self, src, trg, name=None):
        """Remove an edge between src and trg.

        :param src: Source Node
        :type src: `str`
        :param trg: Target Node
        :type trg: `str`
        :param name: hashable identifier, optional (default=None)
            Used to distinguish multiple edges between a pair of nodes.
            If None remove a single (abritrary) edge between src and trg.
        :type name: `str`
        """
        self._graph.remove_edge(src, trg, name)

    def nodes(self):
        """Return a copy of the graph nodes in a list.
        """
        return nx.nodes(self._graph)

    def number_of_nodes(self):
        """Return the number of nodes in the graph.
        """
        return nx.number_of_nodes(self._graph)

    def neighbors(self, node):
        """Returns all of the neighbors of a node in the graph.

        :param node: Node.
        :type node: str
        """
        return nx.all_neighbors(self._graph, node)

    def edges(self):
        """Return list of edges
        """
        return nx.edges(self._graph)

    def number_of_edges(self):
        """Return the number of edges in the graph.
        """
        return nx.number_of_edges(self._graph)

    def get_strongly_connected_component_subgraphs(self, copy=True):
        """Generate Strongly connected components as subgraphs.

        :param copy: if copy is True, Graph, node and edge attributes
        are copied to the subgraphs.
        :type copy: boolean

        Return a list of control flow graphs
        """
        subgs = sorted(nx.strongly_connected_component_subgraphs(self._graph),
                       key=len)
        subcfgs = [Cfg(Gc, self._vars.copy()) for Gc in subgs]
        return subcfgs

    def get_sccs(self, copy=True):
        """Generate Strongly connected components as subgraphs.

        :param copy: if copy is True, Graph, node and edge attributes
        are copied to the subgraphs.
        :type copy: boolean

        Return a list of control flow graphs
        """
        return self.get_strongly_connected_component_subgraphs(self, copy)

    def toDot(self, outfile="graph.dot"):
        nx.drawing.nx_pydot.write_dot(self._graph, outfile)

    def __repr__(self):
        return "I'm a MultiDiGraph"

    def __str__(self):
        return "I'm a MultiDiGraph"
