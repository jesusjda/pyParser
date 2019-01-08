import networkx as nx
from networkx.utils import open_file
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

    def get_nodes(self, data=False):
        return sorted(self.nodes(data=data))

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
                                if key in self[s][t][n]:
                                    del self[s][t][n][key]
                                self[s][t][n][key] = value

    def set_nodes_info(self, attrs, label=None):
        nx.set_node_attributes(self, attrs, label)

    @open_file(1, "w")
    def toSummary(self, path):
        """Writes a summary of the cfg such that:
        - num of nodes
        - num of transitions
        - avg constraints per transitions
        - max constraints per transitions
        - avg num transitions per scc
        - max num transitions per scc
        - num scc
        """
        summary = {}
        summary["#nodes"] = len(self.nodes())
        ntrs = len(self.get_edges())
        summary["#transitions"] = ntrs
        sccs = 0
        avgtrsscc = 0
        maxtrsscc = 0
        trsscc = []
        for s in self.get_scc():
            trs = len(s.get_edges())
            if trs > 0:
                sccs += 1
                trsscc.append(trs)
                avgtrsscc += trs
                if trs > maxtrsscc:
                    maxtrsscc = trs
        avgtrsscc = float(avgtrsscc) / float(sccs)
        summary["#sccs"] = sccs
        summary["avg_transitions_sccs"] = avgtrsscc
        summary["max_transitions_sccs"] = maxtrsscc
        summary["transitions_scc"] = trsscc
        avgcstrs = 0
        maxcstrs = 0
        cstrs = []
        for t in self.get_edges():
            cs = len(t["constraints"])
            avgcstrs += cs
            cstrs.append(cs)
            if cs > maxcstrs:
                maxcstrs = cs
        avgcstrs = float(avgcstrs) / float(ntrs)
        summary["avg_constraints_transitions"] = avgcstrs
        summary["max_constraints_transitions"] = maxcstrs
        summary["constraints_transition"] = cstrs
        import json
        json.dump(summary, path)
        return summary

    def build_polyhedrons(self):
        from ppl import Constraint_System
        from lpi import C_Polyhedron
        gvars = self.graph["global_vars"]
        for e in self.get_edges():
            if "tr_polyhedron" in e:
                continue
            all_vars = gvars + e["local_vars"]
            ppl_cons = [c.transform(all_vars, lib="ppl")
                        for c in e["constraints"] if c.is_linear()]
            e["tr_polyhedron"] = C_Polyhedron(Constraint_System(ppl_cons), len(all_vars))
            e["polyhedron"] = C_Polyhedron(Constraint_System(ppl_cons), len(all_vars))
            if e["tr_polyhedron"].is_empty():
                self.remove_edge(e["source"], e["target"], e["name"])

    def simplify_constraints(self, simplify=True):
        removed = []
        if simplify:
            self.build_polyhedrons()
            for e in self.get_edges():
                e["polyhedron"].minimized_constraints()
                if e["polyhedron"].is_empty():
                    self.remove_edge(e["source"], e["target"], e["name"])
                    removed.append(e["name"])
            isolate_node = list(nx.isolates(self))
            for n in isolate_node:
                self.remove_node(n)
        return removed

    def remove_unsat_edges(self):
        removed = []
        self.build_polyhedrons()
        for e in self.get_edges():
            if not e["polyhedron"].is_sat():
                self.remove_edge(e["source"], e["target"], e["name"])
                removed.append(e["name"])
        isolate_node = list(nx.isolates(self))
        for n in isolate_node:
            self.remove_node(n)
        return removed

    def neighbors(self, node):
        return nx.all_neighbors(self, node)

    def get_strongly_connected_component(self):
        """Generate Strongly connected components as subgraphs.
        Return a list of control flow graphs
        """
        self.simplify_constraints()
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
        return subgs

    def get_scc(self):
        return self.get_strongly_connected_component()

    def get_close_walks(self, max_length=5):
        def bt_cw(src, m_len, init, trs_cw=[]):
            trg = init if m_len == 1 else None
            for t in self.get_edges(source=src, target=trg):
                if t in trs_cw:
                    continue
                new_trs_cw = trs_cw + [t]
                if m_len == 1:
                    yield new_trs_cw
                    continue
                if t["target"] == init:
                    yield new_trs_cw
            for t in self.get_edges(source=src, target=trg):
                if t in trs_cw:
                    continue
                new_trs_cw = trs_cw + [t]
                yield from bt_cw(t["target"], m_len - 1, init, new_trs_cw)
        try:
            init_node = self.get_edges()[0]["source"]
        except Exception:
            return []
        return bt_cw(init_node, max_length, init_node)

    def remove_no_important_variables(self):
        def are_related_vars(vs, vas):
            if len(vs) != 2:
                return False
            N = int(len(vas) / 2)
            try:
                pos1 = vas.index(vs[0])
                pos2 = vas.index(vs[1])
            except Exception:
                return False
            return pos1 % N == pos2 % N

        gvars = self.get_info("global_vars")
        N = int(len(gvars) / 2)
        nivars = list(gvars[:N])
        for tr in self.get_edges():
            for c in tr["constraints"]:
                if c.isequality():
                    if c.get_independent_term() == 0 and are_related_vars(c.get_variables(), gvars):
                        continue
                for v in c.get_variables():
                    if v in tr["local_vars"]:
                        continue
                    pos = gvars.index(v)
                    vt = gvars[pos % N]
                    if vt in nivars:
                        nivars.remove(vt)

                if len(nivars) == 0:
                    break
            if len(nivars) == 0:
                break
        count = 0
        for v in nivars:
            pos = gvars.index(v)
            vp = gvars[pos + N]
            for tr in self.get_edges():
                for c in list(tr["constraints"]):
                    vs = c.get_variables()
                    if v in vs or vp in vs:
                        count += 1
                        tr["constraints"].remove(c)
            pos = gvars.index(v)
            gvars.pop(pos + N)
            gvars.pop(pos)
            N = int(len(gvars) / 2)
        return count, nivars

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

    def toDot(self, outfile, minimize=False, invariant_type="none"):
        """
        """
        edg = self.edges(keys=True)
        for (u, v, k) in edg:
            if u == "":
                continue
            tr_poly = self[u][v][k]["constraints"]
            tr_linear = self[u][v][k]["linear"]
            name = str(k)
            if not tr_linear:
                name += " no linear"
            cons = [str(c) for c in tr_poly]
            if invariant_type != "none":
                try:
                    invariants = self.nodes[u]["invariant_" + str(invariant_type)].toString(vars_name=self["global_variables"])
                except Exception:
                    invariants = []
                cons += invariants
            self[u][v][k]["label"] = name + "{{\n{}}}".format(",\n".join(cons))
            self[u][v][k]["tooltip"] = "\"" + name + " " + str(tr_poly) + "\""
        write_dot(self, outfile)

    @open_file(1, "w")
    def toEspecialProlog(self, path, number=1, idname="noname", invariant_type="none"):
        def saveName(word):
            import re
            return re.sub('[\'\?\!\^.]', '_P', word)

        def generate_pl_names(variables, pl_vars=[], related_vars={}):
            vs = variables.copy()
            out_pl_vars = pl_vars.copy()
            out_related_vars = related_vars.copy()
            for v in variables:
                vs.remove(v)
                i = 1
                new_v = saveName(v)
                rnew_v = "Var" + new_v
                while rnew_v in vs or rnew_v in out_pl_vars:
                    rnew_v = new_v + str(i)
                    i += 1
                out_related_vars[v] = rnew_v
                out_pl_vars.append(rnew_v)
            return out_pl_vars, out_related_vars

        global_vars = self.graph["global_vars"]
        pl_global_vars, related_vars = generate_pl_names(global_vars)

        N = int(len(global_vars) / 2)
        if N == 0:
            vs = ""
            pvs = ""
        else:
            vs = ", ".join([v for v in pl_global_vars[:N]])
            pvs = ", ".join([v for v in pl_global_vars[N:]])
            vs = "[" + vs + "]"
            pvs = "[" + pvs + "]"

        # print transitions
        trs = []
        for s in self.get_nodes():  # source node
            source = "n_{}".format(saveName(s))
            for t in self.get_nodes():  # target node
                target = "n_{}".format(saveName(t))
                for tr in self.get_edges(source=s, target=t):  # concrete edge
                    local_vars = tr["local_vars"]
                    __, tr_related_vars = generate_pl_names(local_vars, pl_global_vars, related_vars)
                    renamedvars = lambda v: tr_related_vars[v]
                    cons = [c.toString(renamedvars, int, eq_symb="=", leq_symb="=<")
                            for c in tr["constraints"]]
                    if invariant_type != "none":
                        try:
                            invariants = self.nodes[s]["invariant_" + str(invariant_type)].toString(vars_name=pl_global_vars, eq_symb="=")
                        except Exception:
                            invariants = []
                        cons += invariants
                    phi = ",".join(cons)
                    trs.append("\t\ttr({}, {}, {}, [{}])".format(tr["name"], source, target, phi))
        path.write("\n\ntest({},\n\t'{}',\n\t{},\n\t{},\n\t[\n{}\n\t]).\n".format(number, idname[2:], vs, pvs, ",\n".join(trs)))

    @open_file(1, "w")
    def toProlog(self, path=None, invariant_type="none"):
        def saveName(word):
            import re
            return re.sub('[\'\?\!\^.]', '_P', word)

        def generate_pl_names(variables, pl_vars=[], related_vars={}):
            vs = variables.copy()
            out_pl_vars = pl_vars.copy()
            out_related_vars = related_vars.copy()
            for v in variables:
                vs.remove(v)
                i = 1
                new_v = saveName(v)
                rnew_v = "Var" + new_v
                while rnew_v in vs or rnew_v in out_pl_vars:
                    rnew_v = new_v + str(i)
                    i += 1
                out_related_vars[v] = rnew_v
                out_pl_vars.append(rnew_v)
            return out_pl_vars, out_related_vars

        global_vars = self.graph["global_vars"]
        pl_global_vars, related_vars = generate_pl_names(global_vars)

        N = int(len(global_vars) / 2)
        if N == 0:
            vs = ""
            pvs = ""
        else:
            vs = ", ".join([v for v in pl_global_vars[:N]])
            pvs = ", ".join([v for v in pl_global_vars[N:]])
            vs = "(" + vs + ")"
            pvs = "(" + pvs + ")"

        # print transitions
        for s in self.get_nodes():  # source node
            path.write("\n% transitions from node {}\n".format(s))
            source = "n_{}{}".format(saveName(s), vs)
            for t in self.get_nodes():  # target node
                target = "n_{}{}".format(saveName(t), pvs)
                for tr in self.get_edges(source=s, target=t):  # concrete edge
                    local_vars = tr["local_vars"]
                    __, tr_related_vars = generate_pl_names(local_vars, pl_global_vars, related_vars)
                    renamedvars = lambda v: tr_related_vars[v]
                    cons = [c.toString(renamedvars, int, eq_symb="=", leq_symb="=<")
                            for c in tr["constraints"]]
                    if invariant_type != "none":
                        try:
                            invariants = self.nodes[s]["invariant_" + str(invariant_type)].toString(vars_name=pl_global_vars, eq_symb="=")
                        except Exception:
                            invariants = []
                        cons += invariants
                    phi = ",".join(cons)
                    if phi != "":
                        phi += ", "
                    path.write("{} :- {}{}.\n".format(source, phi, target))

    @open_file(1, "w")
    def toFc(self, path=None, invariant_type="none"):
        path.write("{\n")
        global_vars = self.graph["global_vars"]
        N = int(len(global_vars) / 2)
        path.write("  vars: [{}],\n".format(",".join(global_vars[:N])))
        path.write("  pvars: [{}],\n".format(",".join(global_vars[N:])))
        path.write("  initnode: {},\n".format(self.graph["init_node"]))
        path.write("  nodes: {\n")
        nodes = self.get_nodes(data=True)
        for n, data in nodes:
            path.write("    {}: {{\n".format(n))
            if "asserts" in data:
                path.write("      asserts: [\n")
                for p in data["asserts"]:
                    path.write("        {},\n".format(p))
                path.write("      ],\n")
            cfr_prop = "cfr_properties" in data or "cfr_cone_properties" in data or "cfr_project_properties" in data
            if cfr_prop:
                path.write("      cfr_properties: [\n")
                if "cfr_properties" in data:
                    path.write("        // User Properties\n")
                    for p in data["cfr_properties"]:
                        path.write("        {},\n".format(p))
                if "cfr_cone_properties" in data:
                    path.write("        // Cone Properties\n")
                    for p in data["cfr_cone_properties"]:
                        path.write("        {},\n".format(p))
                if "cfr_project_properties" in data:
                    path.write("        // Projection Properties\n")
                    for p in data["cfr_project_properties"]:
                        path.write("        {},\n".format(p))
                path.write("      ],\n")
            if "invariant_polyhedra" in data:
                path.write("      inv_polyhedra: [{}],\n".format(", ".join(data["invariant_polyhedra"].toString(vars_name=global_vars))))
            if "invariant_interval" in data:
                path.write("      inv_interval: [{}],\n".format(", ".join(data["invariant_interval"].toString(vars_name=global_vars))))
            path.write("    },\n")
        path.write("  },\n")
        trs = []
        for tr in self.get_edges():
            cons = [c.toString(lambda v:v, int, eq_symb="=", leq_symb="=<")
                    for c in tr["constraints"]]
            if invariant_type != "none":
                try:
                    invariants = self.nodes[tr["source"]]["invariant_" + str(invariant_type)].toString(vars_name=global_vars)
                except Exception:
                    invariants = []
                cons += invariants
            c = ", ".join(cons)
            trs.append("{{\n\tsource: {},\n\ttarget: {},".format(tr["source"], tr["target"]) +
                       "\n\tname: {},\n\tconstraints: [{}]\n    }}".format(tr["name"], c))
        ts = ",\n    ".join(trs)
        path.write("  transitions: [\n    {}\n  ]\n".format(ts))
        path.write("}\n")

    @open_file(1, "w")
    def toKoat(self, path=None, goal_complexity=False, invariant_type="none"):
        if goal_complexity:
            goal = "COMPLEXITY"
        else:
            goal = "TERMINATION"
        path.write("(GOAL {})\n".format(goal))
        path.write("(STARTTERM (FUNCTIONSYMBOLS pyRinit))\n")
        rules, str_vars = self._toKoat_rules(invariant_type)
        path.write("(VAR {})\n".format(str_vars))
        path.write("(RULES {})\n".format(rules))

    def _toKoat_rules(self, invariant_type):
        def isolate(cons, pvars):
            from lpi import ExprTerm
            result = cons[:]
            pvar_exps = []
            lvars = []
            lvars_count = 0
            for v in pvars:
                v_exp = None
                try:
                    toremove = []
                    for c in result[:]:
                        if str(c) == "0 == 0":
                            toremove.append(c)
                            continue
                        if not(v in c.get_variables()):
                            continue
                        v_exp_isolate = c.isolate(v)
                        if v_exp is not None:
                            if str(v_exp) == str(v_exp_isolate):
                                continue
                            raise ValueError("Transition is false.")
                        v_exp = v_exp_isolate
                        for v2 in pvars:
                            if v2 in v_exp.get_variables():
                                raise ValueError("Multiple pvars on the same constraint.")
                        toremove.append(c)
                    for c in toremove:
                        result.remove(c)
                except ValueError:
                    v_exp = ExprTerm(v)
                if not v_exp:
                    lvars.append("NoDet{}".format(lvars_count))
                    v_exp = ExprTerm(lvars[lvars_count])
                    lvars_count += 1
                pvar_exps.append(v_exp)
            pvar_str = ", ".join([str(e) for e in pvar_exps])
            return result, pvar_str, lvars
        global_vars = self.graph["global_vars"]
        N = int(len(global_vars) / 2)
        str_vars = ",".join(global_vars[:N])
        rules = "\n  pyRinit({}) -> Com_1({}({}))\n".format(str_vars, self.graph["init_node"], str_vars)
        # lpvars = ",".join(global_vars[N:])
        localV = set()
        for src in self.get_nodes():
            for trg in self.get_nodes():
                for tr in self.get_edges(source=src, target=trg):
                    cons = tr["constraints"]
                    local_vars = tr["local_vars"]
                    localV = localV.union(local_vars)
                    cons, pvalues, local_vars = isolate(cons, global_vars[N:])
                    localV = localV.union(local_vars)
                    renamedvars = lambda v: str(v)
                    cons_str = [c.toString(renamedvars, int, eq_symb="=")
                                for c in cons]
                    if invariant_type != "none":
                        try:
                            new_globals = [renamedvars(v) for v in global_vars]
                            invariants = self.nodes[src]["invariant_" + str(invariant_type)].toString(vars_name=new_globals, eq_symb="=")
                        except Exception:
                            invariants = []
                        cons_str += invariants
                    if len(cons_str) > 0:
                        phi = " :|: " + " && ".join(cons_str)
                    else:
                        phi = ""
                    rules += "  {}({}) -> Com_1({}({})){}\n".format(src, str_vars, trg, pvalues, phi)
        return rules, " ".join(global_vars + list(localV))

    def edge_data_subgraph(self, edges):
        edges_ref = [(e["source"], e["target"], e["name"])
                     for e in edges]
        subg = Cfg(nx.edge_subgraph(self, edges_ref))
        for e in edges:
            for key in e:
                subg.set_edge_info(key, e[key],
                                   e["source"], e["target"], e["name"])
        return subg

    def get_minimum_node_cut(self, s):
        return nx.minimum_node_cut(self, s)

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
