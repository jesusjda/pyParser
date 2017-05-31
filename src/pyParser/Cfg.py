import random
import networkx as nx
from networkx.drawing.nx_pydot import write_dot


class Edge:
    """Edge Class contains source and target node, and all the
    constraints between them.
    """
    _name = None
    _src = None
    _trg = None
    _cons = []

    def __init__(self, name, src, trg, constraints=[]):
        """

        :param name: transition name
        :type name: str
        :param src: Source node name
        :type src: str
        :param trg: Target node name
        :type trg: str
        :param constraints: initial set of constraints
        :type constraints: :obj:`list` of :obj:`ppl.Constraint`,optional
        """
        self._name = name
        self._src = src
        self._trg = trg
        self._cons = constraints

    def add_constraint(self, constraint):
        """Adds a contraint to the edge.

        :param constrain: Constraint to be added.
        :type: `ppl.Constraint`
        """
        self._cons.append(constraint)

    def get_source(self):
        """Returns source node name
        """
        return self._src

    def get_target(self):
        """Returns target node name
        """
        return self._trg

    def get_name(self):
        """Returns edge name
        """
        return self._name

    def __repr__(self):
        strr = self._name+" {\n"
        for c in self._cons:
            strr = strr + "\t"+c.__repr__()+"\n"
        strr = strr + "}"
        return strr
        print(self._cons[0])
        return self._name + " {\n\t" + ','.join(self._cons) + "\n}"


class Cfg:
    _graph = None

    def __init__(self):
        self._graph = nx.MultiDiGraph()

    def add_edge(self, edge):
        """Add an edge.

        :param edge::Edge to be added.
        :type edge: :obj:`Edge`
        """
        c = "#%06x" % random.randint(0, 0xFFFFFF)
        self._graph.add_edge(edge.get_source(), edge.get_target(), object=edge,
                             label=edge, color=c, fontcolor=c)

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
