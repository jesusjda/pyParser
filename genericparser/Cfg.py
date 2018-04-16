import networkx as nx
from networkx.utils import open_file
from networkx.classes.multidigraph import MultiDiGraph
from networkx.drawing.nx_pydot import write_dot
from genericparser.expressions import ExprTerm


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

    def get_nodes(self, name=None):
        if name is None:
            return self.nodes()

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
        # update entry_points
        for s in subgs:
            subg_nodes = list(s.nodes())
            entries = [n for n in self.get_info("entry_nodes")
                       if n in subg_nodes]
            for u, v in self.in_edges(nbunch=s.nodes()):
                if u not in s.nodes() and v not in entries:
                    entries.append(v)
            s.set_info("entry_nodes", entries)
        #for i, s in enumerate(subgs):
        #    print("{} - scc: {} nodes({}) \n {} entries({}).".format(i,s.nodes(),len(s.nodes()),s.get_info("entry_nodes"),len(s.get_info("entry_nodes"))))
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

    def toDot(self, outfile, minimize=False, invariants=False):
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
            g = self#.copy()
        #g.add_edge("", self.graph["init_node"], "")
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

    @open_file(1,"w")
    def toProlog(self, path=None):
        def saveName(word):
            import re
            return re.sub('[\'\?\!\^]', 'P', word)
        global_vars = self.graph["global_vars"]
        N = int(len(global_vars)/2)
        if N == 0:
            vs = ""
            pvs = ""
        else:
            vs = ", ".join(["V"+saveName(v) for v in global_vars[:N]])
            pvs = ", ".join(["V"+saveName(v) for v in global_vars[N:]])
            vs = "("+vs+")"
            pvs = "("+pvs+")"

        # print startpoint
        if "entry_nodes" in self.graph:
            entries = self.graph["entry_nodes"]
        else:
            entries = [self.graph["init_node"]]
        epoints = ["n_{}{}".format(saveName(e),vs) for e in entries]
        path.write("% initial point\n")
        for e in epoints:
            path.write("startpoint :- {}.\n".format(e))

        # print transitions
        for s in self: # source node
            path.write("\n% transitions from node {}\n".format(s))
            source = "n_{}{}".format(saveName(s),vs)
            for t in self[s]: # target node
                target = "n_{}{}".format(saveName(t),pvs)
                for name in self[s][t]: # concrete edge
                    cons = self[s][t][name]["constraints"]
                    renamedvars = lambda v: "V"+saveName(v)
                    phi = ",".join([c.toString(renamedvars, int, eq_symb="=", leq_symb="=<") for c in cons])
                    path.write("{} :- {}, {}.\n".format(source, phi, target))

    @open_file(1,"w")
    def toKoat(self, path=None, goal_complexity=False):
        def eq2ineqs(cons):
            result = []
            for c in cons:
                if not c.isequality():
                    result.append(c)
                    continue
                a = (c._exp <= 0)
                b = (c._exp >= 0)
                result.append(a)
                result.append(b)
            return result
        def isolate(cons, pvars, lvars):
            result = cons[:]
            pvar_exps = []
            lvars_count = 0
            for v in pvars:
                v_exp = None
                for c in result[:]:
                    if not(v in c.get_variables()):
                        if str(c) == "0 == 0":
                            result.remove(c)
                        continue
                    if v_exp:
                        raise ValueError("unable to handle this example")
                    v_exp = c.isolate(v)
                    for v2 in pvars:
                        if v2 in v_exp.get_variables():
                            raise ValueError("unable to handle this example...")
                    result.remove(c)
                if not v_exp:
                    if lvars_count < len(lvars):
                        v_exp = ExprTerm(lvars[lvars_count])
                        lvars_count += 1
                    else:
                        raise ValueError("unable to handle this example... puff")
                pvar_exps.append(v_exp)
            pvar_str = ", ".join([str(e) for e in pvar_exps])
            return result, pvar_str
        if goal_complexity:
            goal = "COMPLEXITY"
        else:
            goal = "TERMINATION"
        path.write("(GOAL {})\n".format(goal))
        path.write("(STARTTERM (FUNCTIONSYMBOLS pyRinit))\n")
        global_vars = self.graph["global_vars"]
        N = int(len(global_vars)/2)
        lvars = ",".join(global_vars[:N])
        rules = "\n  pyRinit({}) -> Com_1({}({}))\n".format(lvars,self.graph["init_node"], lvars)
        #lpvars = ",".join(global_vars[N:])
        localV = set()
        for src in self:
            for trg in self[src]:
                for name in self[src][trg]:
                    cons = self[src][trg][name]["constraints"]
                    local_vars = self[src][trg][name]["local_vars"]
                    localV = localV.union(local_vars)
                    #cons = eq2ineqs(cons)
                    cons, pvalues = isolate(cons, global_vars[N:],local_vars)
                    renamedvars = lambda v: str(v)
                    if len(cons) > 0:
                        phi = " :|: "+ " && ".join([c.toString(renamedvars, int, eq_symb="=")
                                                    for c in cons])
                    else:
                        phi = ""
                    rules += "  {}({}) -> Com_1({}({})){}\n".format(src,lvars,trg,pvalues,phi)
        str_vars = " ".join(global_vars[:N]+list(localV))
        path.write("(VAR {})\n".format(str_vars))
        path.write("(RULES {})\n".format(rules))

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
