import networkx as nx

from networkx.classes.multidigraph import MultiDiGraph
from networkx.drawing.nx_pydot import write_dot


class Cfg(MultiDiGraph):
    def get_info(self, key=None):
        if key:
            return self.graph[key]
        return self.graph

    def set_info(self, key, value):
        self.graph[key] = value

    def add_edge(self, source, target, name, **kwargs):
        color = ["#3366CC", "#3B3EAC", "#DC3912", "#FF9900", "#109618",
                 "#990099", "#3B8EAC", "#0099C6", "#DD4477", "#66AA00",
                 "#B82E2E", "#316395", "#994499", "#22AA99", "#AAAA11",
                 "#6633CC", "#E67300", "#8B0707", "#329262", "#5574A6"]

        if not("color" in kwargs):
            c = color[self.number_of_edges() % len(color)]
            kwargs["color"] = c
            kwargs["fontcolor"] = c

        if not("label" in kwargs):
            label = name
            if "constraints" in kwargs:
                label += " {\n"
                for c in kwargs["constraints"]:
                    label += str(c) + "\n"
                label += "}"
            kwargs["label"] = label

        kwargs["source"] = source
        kwargs["target"] = target
        kwargs["name"] = name

        return MultiDiGraph.add_edge(self, source, target, key=name, **kwargs)

    def get_edges(self, source=None, target=None, name=None):
        edges = []
        for s in self:
            if source is None or source == s:
                for t in self[s]:
                    if target is None or target == t:
                        for n in self[s][t]:
                            if name is None or name == n:
                                edges.append(self[s][t][n])
        return sorted(edges, key=lambda tr: tr["name"])

    def set_edge_info(self, key, value, source=None, target=None, name=None):
        """Add or Replace a some edge information (``key``, ``value``)
        """
        for s in self:
            if source is None or source == s:
                for t in self[s]:
                    if target is None or target == t:
                        for n in self[s][t]:
                            if name is None or name == n:
                                self[s][t][n][key] = value

    def neighbors(self, node):
        return nx.all_neighbors(self, node)

    def get_strongly_connected_component(self):
        """Generate Strongly connected components as subgraphs.
        Return a list of control flow graphs
        """
        subgs = [Cfg(self.subgraph(c))
                 for c in nx.strongly_connected_components(self)]
        subgs.sort(key=len)
        return subgs

    def get_scc(self):
        return self.get_strongly_connected_component()

    def has_cycle(self):
        """Returns if the CFG has cycle or not.
        """
        try:
            nx.find_cycle(self)
            return True
        except nx.exception.NetworkXNoCycle:
            return False

    def simple_cycles(self):
        """Returns a list of cycles which form a basis for cycles of G.
        """
        return nx.simple_cycles(self)

    def toDot(self, outfile="graph.dot", minimize=False, invariants=False):
        """
        """
        if invariants:
            n_labels = {}
            for n in self.nodes():
                try:
                    invariant = self.nodes[n]["invariant"].get_constraints()
                except Exception:
                    invariant = []
                n_labels[n] = ("" + str(n) + "\n" +
                               "" #+ OM.tostr(invariant)
                               + "")
            g = nx.relabel_nodes(self, n_labels)
        else:
            g = self.copy()
        g.add_edge(source="", target=self.graph["init_node"], name="")
        edg = g.edges(keys=True)
        for (u, v, k) in edg:
            if u == "":
                continue
            tr_poly = g[u][v][k]["constraints"]
            tr_linear = g[u][v][k]["linear"]
            #if minimize:
            #    tr_poly.minimized_constraints()
            name = str(k)
            if not tr_linear:
                name += " removed no linear constraint"
            g[u][v][k]["label"] = name
            g[u][v][k]["tooltip"] = "\"" + name + " "+ str(tr_poly) + "\""
        write_dot(g, outfile)

    def toProlog(self, outfile=None):
        def saveName(word):
            import re
            return re.sub('[\'\?\!\^]', '_X_', word)
        import sys
        if outfile:
            sys.stdout = open(outfile, "w")
        global_vars = self.graph["global_vars"]
        N = int(len(global_vars)/2)
        vs = ", ".join(["V"+saveName(v) for v in global_vars[:N]])
        pvs = ", ".join(["V"+saveName(v) for v in global_vars[N:]])

        # print startpoint
        init = "n_{}({})".format(saveName(self.graph["init_node"]),vs)
        print("% initial point\n")
        print("startpoint :- {}.".format(init))

        # print transitions
        for s in self: # source node
            print("\n% transitions from node {}\n".format(s))
            source = "n_{}({})".format(saveName(s),vs)
            for t in self[s]: # target node
                target = "n_{}({})".format(saveName(t),pvs)
                for name in self[s][t]: # concrete edge
                    cons = self[s][t][name]["constraints"]
                    local_vars = self[s][t][name]["local_vars"]
                    all_vars = global_vars + local_vars
                    renamevars = {v:"V"+saveName(v) for v in all_vars}
                    phi = ",".join([c.toString(renamevars) for c in cons])
                    phi = phi.replace("<=", "=<")
                    phi = phi.replace("==", "=")
                    print("{} :- {}, {}.\n".format(source, phi, target))
        if outfile:
            sys.stdout = sys.__stdout__

    def edge_data_subgraph(self, edges):
        edges_ref = [(e["source"],e["target"],e["name"])
                     for e in edges]
        subg = Cfg(nx.edge_subgraph(self, edges_ref))
        for e in edges:
            for key in e:
                subg.set_edge_info(key, e[key],
                                   e["source"], e["target"], e["name"])
        return subg

    def __lt__(self, other):
        return self.number_of_edges() < other.number_of_edges()

    def __repr__(self):
        try:
            import pprint
            cat = "Control Flow Graph"
            cat += "\n"
            cat += pprint.pformat(self.graph)
            cat += "\n"
            cat += pprint.pformat(self.edges(data=True))
            cat += "\n"
            cat += pprint.pformat(self.nodes(data=True))
            return cat
        except Exception:
            return super(Cfg, self).__repr__()

    def __str__(self):
        try:
            import pprint
            cat = "Control Flow Graph"
            cat += "\n"
            cat += pprint.pformat(self.graph)
            cat += "\n"
            cat += pprint.pformat(self.edges(data=True))
            cat += "\n"
            cat += pprint.pformat(self.nodes(data=True))
            return cat
        except Exception:
            return super(Cfg, self).__str__()
