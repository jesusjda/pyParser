from networkx.drawing.nx_pydot import write_dot

import networkx as nx


class Cfg:
    _graph = None
    _num_edges = 0
    _keys = {}
    _vars = []
    _nodes = {}

    def __init__(self, graph=None, vars_name=[],
                 nodes_info={}, init_node=None):
        if graph is None:
            self._graph = nx.MultiDiGraph()
            self._num_edges = 0
            self._keys = {}
            self._vars = vars_name
            self._nodes = nodes_info
            self._init_node = init_node
        elif isinstance(graph, list):
            self._graph = nx.MultiDiGraph()
            self._num_edges = 0
            self._keys = {}
            self._nodes = nodes_info
            self._vars = vars_name
            self._init_node = init_node
            for edge in graph:
                self.add_edge(**edge)
        else:
            self._graph = graph
            self._num_edges = self._graph.number_of_edges()
            self._vars = vars_name
            self._keys = {}
            self._nodes = nodes_info
            self._init_node = init_node
            for src in self._graph:
                for trg in self._graph[src]:
                    for name in self._graph[src][trg]:
                        self._keys[name] = (src, trg)

    def add_var_name(self, vars_name):
        self._vars = vars_name

    def get_var_name(self, idx=None):
        if idx is None:
            return self._vars
        return self._vars[idx]

    def add_edge(self, name, source, target, **kwargs):
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
            c = color[self._num_edges % 20]

        kwargs["source"] = source
        kwargs["target"] = target
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

        self._graph.add_edge(source, target, key=name, **kwargs)
        self._keys[name] = (source, target)
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
        for s in self._graph:
            if src is None or src == s:
                for t in self._graph[s]:
                    if trg is None or trg == t:
                        for n in self._graph[s][t]:
                            if name is None or name == n:
                                edges.append(self._graph[s][t][n])
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
        return [n for n in nx.nodes(self._graph)]

    def set_init_node(self, node):
        """Sets the initial node
        """
        if node in self.nodes():
            self._init_node = node
        else:
            raise Exception("No such node (" + str(node) + ") in the graph")

    def get_init_node(self):
        """Returns the initial node
        """
        return self._init_node

    def add_node_info(self, nodeid, key, value):
        """Add or Replace a some node information (``key``, ``value``)
        """
        if not(nodeid in self.nodes()):
            raise Exception("The node '" + nodeid + "' does not exists.")
        elif not(nodeid in self._nodes):
            self._nodes[nodeid] = {"id": nodeid}
        self._nodes[nodeid][key] = value

    def set_node_info(self, nodeid, info):
        """Replace all the information
        """
        if not("id" in info):
            info["id"] = nodeid
        self._nodes[nodeid] = info

    def get_node_info(self, nodeid=None, key=None):
        """Returns the information of the node with id: ``nodeid``,
        if a ``key`` is specified only the corresponding value is returned.
        """
        if nodeid is None:
            if key is None:
                return self._nodes
            else:
                return {node: {"id": node, key: self._nodes[node][key]}
                        for node in self._nodes}
        if not(nodeid in self.nodes()):
            raise Exception("The node '" + nodeid + "' does not exists.")
        elif not(nodeid in self._nodes):
            self._nodes[nodeid] = {"id": nodeid}
        if key is None:
            return self._nodes[nodeid]
        else:
            if key in self._nodes[nodeid]:
                return self._nodes[nodeid][key]
            else:
                return None

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
        if copy:
            subcfgs = [Cfg(Gc, self._vars,
                           nodes_info=self._nodes, init_node=self._init_node)
                       for Gc in subgs]
        else:
            subcfgs = [Cfg(Gc, self._vars) for Gc in subgs]
        return subcfgs

    def get_sccs(self, copy=True):
        """Generate Strongly connected components as subgraphs.

        :param copy: if copy is True, Graph, node and edge attributes
        are copied to the subgraphs.
        :type copy: boolean

        Return a list of control flow graphs
        """
        return self.get_strongly_connected_component_subgraphs(copy)

    def has_cycle(self):
        """Returns if the CFG has cycle or not.
        """
        try:
            nx.find_cycle(self._graph)
            return True
        except nx.exception.NetworkXNoCycle:
            return False

    def toDot(self, OM, outfile="graph.dot"):
        """
        """
        n_labels = {}
        for n in self.nodes():
            n_labels[n] = ("" + str(n) + "\n" +
                           OM.tostr(self._nodes[n]["invariant"].get_constraints())
                           + "")
        g = nx.relabel_nodes(self._graph, n_labels)
        edg = g.edges(keys=True)
        for (u, v, k) in edg:
            g[u][v][k]["label"] = str(k) + OM.tostr(g[u][v][k]["tr_polyhedron"].get_constraints())

        write_dot(g, outfile)

    def __repr__(self):
        return "I'm a MultiDiGraph"

    def __str__(self):
        return "I'm a MultiDiGraph"
