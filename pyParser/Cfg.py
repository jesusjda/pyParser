import networkx as nx
from networkx.drawing.nx_pydot import write_dot


class Cfg:
    _graph = None
    _num_edges = 0
    _keys = {}

    def __init__(self):
        self._graph = nx.MultiDiGraph()
        self._num_edges = 0
        self._keys = {}

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
        print(kwargs)
        color = ["#3366CC", "#3366CC", "#DC3912", "#FF9900", "#109618",
                 "#990099", "#3B3EAC", "#0099C6", "#DD4477", "#66AA00",
                 "#B82E2E", "#316395", "#994499", "#22AA99", "#AAAA11",
                 "#6633CC", "#E67300", "#8B0707", "#329262", "#5574A6",
                 "#3B3EAC"]

        if "color" in kwargs:
            c = kwargs["color"]
        else:
            c = color[self._num_edges]

        kwargs["src"] = src
        kwargs["trg"] = trg
        kwargs["color"] = c
        kwargs["fontcolor"] = c
        kwargs["name"] = name

        print(kwargs)
        self._graph.add_edge(src, trg, key=name, **kwargs)
        self._keys[name] = (src, trg)
        self._num_edges += 1

    def get_edges(self, src=None, trg=None, name=None):
        """Returns a list of edges from `src` to `trg`
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
        return [self._graph.edge[s][t][k]
                for s in self._graph.edge if src is None or src == s
                for t in self._graph.edge[s] if trg is None or trg == t
                for k in self._graph.edge[s][t] if name is None or name == k]
        if src in self._graph.edge:
            if trg is None:
                return [self._graph.edge[src][t][k]
                        for t in self._graph.edge[src]
                        for k in self._graph.edge[src][t]]
            if trg in self._graph.edge[src]:
                return [self._graph.edge[src][trg][k]
                        for k in self._graph.edge[src][trg]]
        return []

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

    def _echo(self, outfile="graph.dot"):
        nx.drawing.nx_pydot.write_dot(self._graph, outfile)

    def __repr__(self):
        return "I'm a MultiDiGraph"

    def __str__(self):
        return "I'm a MultiDiGraph"
