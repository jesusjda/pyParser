import networkx as nx
from networkx.utils import open_file
from networkx.classes.multidigraph import MultiDiGraph
from networkx.drawing.nx_pydot import write_dot
import genericparser.constants as constants


class Cfg(MultiDiGraph):
    def get_info(self, key=None):
        return self.graph[key] if key is not None else self.graph

    def set_info(self, key, value):
        self.graph[key] = value

    def add_edge(self, source, target, name, **kwargs):
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
            cs = len(t[constants.transition.constraints])
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

    def build_polyhedrons(self, update=False):
        from lpi import C_Polyhedron
        gvars = self.graph[constants.variables]
        for e in self.get_edges():
            if constants.transition.polyhedron in e:
                if update:
                    del e[constants.transition.polyhedron]
                else:
                    continue
            all_vars = gvars + e[constants.transition.localvariables]
            cons = [c for c in e[constants.transition.constraints] if c.is_linear()]
            e[constants.transition.polyhedron] = C_Polyhedron(constraints=cons, variables=all_vars)
        self.remove_unsat_edges()

    def remove_unsat_edges(self):
        removed = []
        from lpi import Solver
        for e in self.get_edges():
            s = Solver()
            s.add(e[constants.transition.polyhedron].get_constraints())
            if not s.is_sat():
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
        subgs = [Cfg(self.subgraph(c))
                 for c in nx.strongly_connected_components(self)]
        # update entry_points
        final_subgs = []
        for s in subgs:
            subg_nodes = list(s.nodes())
            entries = [n for n in self.get_info(constants.entries)
                       if n in subg_nodes]
            for u, v in self.in_edges(nbunch=subg_nodes):
                if u not in subg_nodes and v not in entries:
                    entries.append(v)
            if len(entries) == 0:
                continue
                raise Exception("The scc has not got entry points.")
            s.set_info(constants.entries, entries)
            s.set_info(constants.initnode, entries[0])
            s.set_info(constants.variables, list(self.get_info(constants.variables)))
            final_subgs.append(s)
        final_subgs.sort(key=len)
        return final_subgs

    def get_scc(self):
        return self.get_strongly_connected_component()

    def get_close_walks(self, max_length=5, max_appears=2, linear=False):
        def bt_cw(src, m_len, init, trs_cw=[], trs_count={}):
            trg = init if m_len == 1 else None
            for t in self.get_edges(source=src, target=trg):
                if linear and not t["linear"]:
                    continue
                if trs_count.get(t["name"], 0) >= max_appears:
                    continue
                new_trs_cw = trs_cw + [t]
                if m_len == 1:
                    yield new_trs_cw
                    continue
                if t["target"] == init:
                    yield new_trs_cw
            if m_len > 1:
                for t in self.get_edges(source=src, target=trg):
                    if linear and not t["linear"]:
                        continue
                    if trs_count.get(t["name"], 0) >= max_appears:
                        continue
                    new_trs_cw = trs_cw + [t]
                    trs_count[t["name"]] = trs_count.get(t["name"], 0) + 1
                    yield from bt_cw(t["target"], m_len - 1, init, new_trs_cw, trs_count)
                    trs_count[t["name"]] -= 1
        entries = self.get_info(constants.entries)
        for init in entries:
            yield from bt_cw(init, max_length, init)

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
        gvars = self.get_info(constants.variables)
        N = int(len(gvars) / 2)
        nivars = list(gvars[:N])
        count = 0
        for tr in self.get_edges():
            lvars = tr[constants.transition.localvariables]
            dependencies = { v: [] for v in gvars}
            needed = {v: True for v in gvars}
            for v in lvars:
                dependencies[v] = []
                needed[v] = False
            for c in tr[constants.transition.constraints]:
                if c.is_equality():
                    if c.get_independent_term() == 0 and are_related_vars(c.get_variables(), gvars):
                        continue
                c_vars = c.get_variables()
                for v in c_vars:
                    dependencies[v] = dependencies[v] + c_vars
                    if v in lvars:
                        continue
                    pos = gvars.index(v)
                    vt = gvars[pos % N]
                    if vt in nivars:
                        nivars.remove(vt)
                # if len(nivars) == 0:
                #     break
            q = list(gvars)
            while len(q) > 0:
                v = q.pop()
                for vi in dependencies[v]:
                    if needed[vi]:
                        continue
                    needed[vi] = True
                    q.append(vi)
            # if len(nivars) == 0:
            #    break
            for v in lvars:
                if needed[v]:
                    continue
                for c in tr[constants.transition.constraints]:
                    if v in c.get_variables():
                        count += 1
                        tr[constants.transition.constraints].remove(c)
        for v in nivars:
            pos = gvars.index(v)
            vp = gvars[pos + N]
            for tr in self.get_edges():
                for c in list(tr[constants.transition.constraints]):
                    vs = c.get_variables()
                    if v in vs or vp in vs:
                        count += 1
                        tr[constants.transition.constraints].remove(c)
            pos = gvars.index(v)
            gvars.pop(pos + N)
            gvars.pop(pos)
            N = int(len(gvars) / 2)
        if count > 0:
            self.build_polyhedrons(update=True)
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

    def toDot(self, outfile, invariant_type="none"):
        """
        """
        color = ["#3366CC", "#3B3EAC", "#DC3912", "#FF9900", "#109618",
                 "#990099", "#3B8EAC", "#0099C6", "#DD4477", "#66AA00",
                 "#B82E2E", "#316395", "#994499", "#22AA99", "#AAAA11",
                 "#6633CC", "#E67300", "#8B0707", "#329262", "#5574A6"]

        edg = self.edges(keys=True)
        count = 0
        for (u, v, k) in edg:
            if u == "":
                continue
            tr_poly = self[u][v][k][constants.transition.constraints]
            tr_linear = self[u][v][k][constants.transition.islinear]
            name = str(k)
            if not tr_linear:
                name += " no linear"
            cons = tr_poly
            if invariant_type != "none":
                try:
                    invariants = self.nodes[u]["invariant_" + str(invariant_type)].get_constraints()
                    cons += invariants
                except KeyError:
                    pass
            str_cs = [str(c) for c in cons]
            self[u][v][k]["label"] = name  # + "{{\n{}}}".format(",\n".join(str_cs))
            endl = '&#13;&#10;'
            tab = '&#09;'
            tooltip = "\"" + name + " {" + endl + tab + ("," + endl + tab).join(str_cs) + endl + "}\""
            self[u][v][k]["tooltip"] = tooltip
            self[u][v][k]["labeltooltip"] = tooltip
            self[u][v][k]["edgetooltip"] = tooltip
            self[u][v][k]["title"] = tooltip
            self[u][v][k]["color"] = color[count % len(color)]
            self[u][v][k]["fontcolor"] = color[count % len(color)]
            count += 1

        entries = self.get_info(constants.entries)
        for n in self.get_nodes():
            if n in entries:
                self.nodes[n]["fillcolor"] = "darkolivegreen1"
                self.nodes[n]["style"] = "filled"
            else:
                self.nodes[n]["fillcolor"] = "transparent"
                self.nodes[n]["style"] = ""
            if invariant_type != "none":
                try:
                    self.nodes[n]["tooltip"] = str(self.nodes[u]["invariant_" + str(invariant_type)].get_constraints())
                except KeyError:
                    pass
        write_dot(self, outfile)

    @open_file(1, "w")
    def toSMT2(self, path=None, invariant_type="none"):
        path.write("(declare-sort Loc 0)\n")
        # declare nodes
        for n in self.get_nodes():
            path.write("(declare-const {} Loc)\n".format(n))
        path.write("(assert (distinct {}))\n".format(" ".join(self.get_nodes())))
        # define how a transition works
        path.write("(define-fun cfg_init ( (pc Loc) (src Loc) (rel Bool) ) Bool (and (= pc src) rel))\n")
        path.write("(define-fun cfg_trans2 ( (pc Loc) (src Loc) (pc1 Loc) (dst Loc) (rel Bool) ) Bool\n")
        path.write("                       (and (= pc src) (= pc1 dst) rel))\n")
        path.write("(define-fun cfg_trans3 ( (pc Loc) (exit Loc) (pc1 Loc) (call Loc) (pc2 Loc) (return Loc)\n")
        path.write("                         (rel Bool) ) Bool (and (= pc exit) (= pc1 call) (= pc2 return) rel))\n")
        global_vars = self.graph[constants.variables]
        N = int(len(global_vars) / 2)
        vs_str = " ".join(["({} Int)".format(v) for v in global_vars[:N]])
        pvs_str = " ".join(["({} Int)".format(v) for v in global_vars[N:]])
        # define init node with the global variables
        path.write("(define-fun init_main ( (pc Loc) {} ) Bool (cfg_init pc {} true))\n".format(vs_str, self.graph[constants.initnode]))
        # define transitions with the global variables
        path.write("(define-fun next_main ( (pc Loc) {} (pc1 Loc) {}) Bool (or\n".format(vs_str, pvs_str))

        def toprefixformat(c):
            return c.toString(str, int, eq_symb="=", opformat="prefix")
        self.build_polyhedrons()
        for tr in self.get_edges():
            cons = tr[constants.transition.constraints]
            if invariant_type != "none":
                try:
                    invariants = self.nodes[tr["source"]]["invariant_" + str(invariant_type)].get_constraints()
                    cons += invariants
                except KeyError:
                    pass
            if len(cons) == 0:
                prefix_cons = "true"
            else:
                prefix_cons = toprefixformat(cons[0])
                for c in cons[1:]:
                    prefix_cons = "(and {} {})".format(prefix_cons, toprefixformat(c))
            if len(tr[constants.transition.localvariables]) > 0:
                prefix_cons = "(exists ({}) {})".format(" ".join(["({} Int)".format(v) for v in tr[constants.transition.localvariables]]), prefix_cons)

            path.write("    (cfg_trans2 pc {} pc1 {} {})\n".format(tr["source"], tr["target"], prefix_cons))
        path.write("  )\n)\n")

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

        global_vars = self.graph[constants.variables]
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
                    local_vars = tr[constants.transition.localvariables]
                    __, tr_related_vars = generate_pl_names(local_vars, pl_global_vars, related_vars)
                    renamedvars = lambda v: tr_related_vars[v]
                    cons = [c for c in tr[constants.transition.constraints] if c.is_linear()]
                    if invariant_type != "none":
                        try:
                            invariants = self.nodes[s]["invariant_" + str(invariant_type)].get_constraints()
                            cons += invariants
                        except KeyError:
                            pass
                    str_cs = [c.toString(renamedvars, int, eq_symb="=", leq_symb="=<")
                              for c in cons]
                    phi = ",".join(str_cs)
                    trs.append("\t\ttr({}, {}, {}, [{}])".format(tr["name"], source, target, phi))
        path.write("\n\ntest({},\n\t'{}',\n\t{},\n\t{},\n\t[\n{}\n\t]).\n".format(number, idname[2:], vs, pvs, ",\n".join(trs)))

    @open_file(1, "w")
    def toProlog(self, path=None, invariant_type="none", with_cost=False):
        from lpi import Expression
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

        
        global_vars = self.graph[constants.variables]
        N = int(len(global_vars) / 2)
        cost_var, cost_pvar = (None, None)
        if with_cost:
            cost_var = "_COST_"
            idx = 0
            while cost_var+str(idx) in global_vars or cost_var+str(idx+1) in global_vars:
                idx = idx + 2
            cost_var = cost_var+str(idx)
            cost_pvar = cost_var+str(idx+1)
            global_vars = global_vars[:N] +[cost_var]+ global_vars[N:]+[cost_pvar]
            N= N + 1

        pl_global_vars, related_vars = generate_pl_names(global_vars)
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
                    cons = [c for c in tr[constants.transition.constraints] if c.is_linear()]
                    if with_cost:
                        c = tr.get("cost", 1)
                        cons.append(Expression(cost_pvar) == Expression(cost_var)+c)
                    if invariant_type != "none":
                        try:
                            invariants = self.nodes[tr["source"]]["invariant_" + str(invariant_type)].get_constraints()
                            cons += invariants
                        except KeyError:
                            pass
                    local_vars = tr[constants.transition.localvariables]
                    __, tr_related_vars = generate_pl_names(local_vars, pl_global_vars, related_vars)
                    renamedvars = lambda v: tr_related_vars[v]
                    str_cs = [c.toString(renamedvars, int, eq_symb="=", leq_symb="=<")
                              for c in cons]
                    phi = ",".join(str_cs)
                    if phi != "":
                        phi += ", "
                    path.write("{} :- {}{}.\n".format(source, phi, target))
        return cost_var, cost_pvar

    @open_file(1, "w")
    def toFc(self, path=None, invariant_type="none"):
        path.write("{\n")
        global_vars = self.graph[constants.variables]
        N = int(len(global_vars) / 2)
        path.write("  vars: [{}],\n".format(",".join(global_vars[:N])))
        path.write("  pvars: [{}],\n".format(",".join(global_vars[N:])))
        path.write("  initnode: {},\n".format(self.graph[constants.initnode]))
        path.write("  nodes: {\n")
        nodes = self.get_nodes(data=True)
        for n, data in nodes:
            path.write("    {}: {{\n".format(n))
            if "asserts" in data:
                path.write("      asserts: [\n")
                for p in data["asserts"]:
                    path.write("        {},\n".format(p))
                path.write("      ],\n")
            cfr_prop = ("cfr_properties" in data or "cfr_cone_properties" in data or
                        "cfr_project_properties" in data or "cfr_auto_properties" in data or
                        "cfr_rfs_properties" in data)
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
                if "cfr_auto_properties" in data:
                    path.write("        // John Properties\n")
                    for p in data["cfr_auto_properties"]:
                        path.write("        {},\n".format(p))
                if "cfr_rfs_properties" in data:
                    path.write("        // RFs Properties\n")
                    for p in data["cfr_rfs_properties"]:
                        path.write("        {},\n".format(p))
                path.write("      ],\n")
            if "invariant_polyhedra" in data:
                path.write("      inv_polyhedra: {},\n".format(data["invariant_polyhedra"].get_constraints()))
            if "invariant_interval" in data:
                path.write("      inv_interval: {},\n".format(data["invariant_interval"].get_constraints()))
            path.write("    },\n")
        path.write("  },\n")
        trs = []
        for tr in self.get_edges():
            cons = tr[constants.transition.constraints]
            if invariant_type != "none":
                try:
                    invariants = self.nodes[tr["source"]]["invariant_" + str(invariant_type)].get_constraints()
                    cons += invariants
                except KeyError:
                    pass
            str_cs = [c.toString(lambda v:v, int, eq_symb="=", leq_symb="=<")
                      for c in cons]
            c = ", ".join(str_cs)
            trs.append("{{\n\tsource: {},\n\ttarget: {},".format(tr["source"], tr["target"]) +
                       "\n\tname: {},\n\tconstraints: [{}]\n    }}".format(tr["name"], c))
        ts = ",\n    ".join(trs)
        path.write("  transitions: [\n    {}\n  ]\n".format(ts))
        path.write("}\n")

    @open_file(1, "w")
    def toKoat(self, path=None, goal_complexity=False, invariant_type="none", with_cost=False):
        if goal_complexity:
            goal = "COMPLEXITY"
        else:
            goal = "TERMINATION"
        path.write("(GOAL {})\n".format(goal))
        initnode = self.graph[constants.initnode]
        rules, str_vars = self._toKoat_rules(invariant_type, with_cost)
        if len(self.get_edges(target=initnode)) > 0:
            initnode = "pyRinit"
            it = 1
            while initnode in self.get_nodes():
                initnode = "pyRinit_" + str(it)
                it += 1
            global_vars = self.graph[constants.variables]
            N = int(len(global_vars) / 2)
            str_vars = ",".join(global_vars[:N])
            rules = "\n  {}({}) -> Com_1({}({}))\n".format(initnode, str_vars, self.graph[constants.initnode], str_vars) + rules
        else:
            rules = "\n" + rules
        path.write("(STARTTERM (FUNCTIONSYMBOLS {}))\n".format(initnode))
        path.write("(VAR {})\n".format(str_vars))
        path.write("(RULES {})\n".format(rules))

    def _toKoat_rules(self, invariant_type, with_cost=False):
        def isolate(cons, pvars):
            from lpi import Expression
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
                    v_exp = Expression(v)
                if not v_exp:
                    lvars.append("NoDet{}".format(lvars_count))
                    v_exp = Expression(lvars[lvars_count])
                    lvars_count += 1
                pvar_exps.append(v_exp)
            pvar_str = ", ".join([str(e) for e in pvar_exps])
            return result, pvar_str, lvars
        global_vars = self.graph[constants.variables]
        N = int(len(global_vars) / 2)
        str_vars = ",".join(global_vars[:N])
        rules = ""
        # lpvars = ",".join(global_vars[N:])
        localV = set()
        for src in self.get_nodes():
            for trg in self.get_nodes():
                for tr in self.get_edges(source=src, target=trg):
                    cons = tr[constants.transition.constraints]
                    local_vars = tr[constants.transition.localvariables]
                    localV = localV.union(local_vars)
                    cons, pvalues, local_vars = isolate(cons, global_vars[N:])
                    localV = localV.union(local_vars)
                    renamedvars = lambda v: str(v)
                    if invariant_type != "none":
                        try:
                            invariants = self.nodes[src]["invariant_" + str(invariant_type)].get_constraints()
                            cons += invariants
                        except KeyError:
                            pass

                    cons_str = [c.toString(renamedvars, int, eq_symb="=")
                                for c in cons]
                    if len(cons_str) > 0:
                        phi = " :|: " + " && ".join(cons_str)
                    else:
                        phi = ""
                    cost = 1
                    if with_cost:
                        cost = tr.get("cost", 1)
                    if cost == 1:
                        rules += "  {}({}) -> Com_1({}({})){}\n".format(src, str_vars, trg, pvalues, phi)
                    else:
                        rules += "  {}({}) -{{{}}}> Com_1({}({})){}\n".format(src, str_vars, int(cost), trg, pvalues, phi)
        return rules, " ".join(global_vars + list(localV))

    def edge_data_subgraph(self, edges):
        edges_ref = [(e["source"], e["target"], e["name"])
                     for e in edges]
        subg = Cfg(nx.edge_subgraph(self, edges_ref))
        for e in edges:
            for key in e:
                subg.set_edge_info(key, e[key],
                                   e["source"], e["target"], e["name"])
        subg_nodes = list(subg.nodes())
        original_entries = self.get_info(constants.entries)
        entries = [n for n in original_entries
                   if n in subg_nodes]
        for u, v, k in self.in_edges(nbunch=subg_nodes, keys=True):
            if u not in subg_nodes and v not in entries:
                entries.append(v)
            elif (u, v, k) not in edges_ref:
                if v not in entries:
                    entries.append(v)
        if len(entries) == 0:
            raise Exception("The subgraph has not got entry points.")
        subg.set_info(constants.entries, entries)
        subg.set_info(constants.initnode, entries[0])
        subg.set_info(constants.variables, list(self.get_info(constants.variables)))
        return subg

    def node_data_subgraph(self, nodes):
        org_nodes = self.get_nodes()
        del_nodes = [n for n in org_nodes if n not in nodes]
        subg = Cfg(self)
        subg.remove_nodes_from(del_nodes)

        subg_nodes = list(subg.nodes())
        original_entries = self.get_info(constants.entries)
        entries = [n for n in original_entries
                   if n in subg_nodes]

        for u, v in self.in_edges(nbunch=subg_nodes):
            if u not in subg_nodes and v not in entries:
                entries.append(v)
        if len(entries) == 0:
            raise Exception("The subgraph has not got entry points.")
        subg.set_info(constants.entries, entries)
        subg.set_info(constants.initnode, entries[0])
        subg.set_info(constants.variables, list(self.get_info(constants.variables)))
        return subg

    def get_minimum_node_cut(self, s):
        return nx.minimum_node_cut(self, s)

    def get_all_nodes_between(self, source, target):
        tr_key = "not valid"
        self.add_edge(target, source, tr_key)
        sccs = nx.strongly_connected_components(self)
        way_nodes = []
        for scc in sccs:
            nodes = list(scc)
            if source in nodes and target in nodes:
                way_nodes = nodes
                break
        self.remove_edge(target, source, tr_key)
        return way_nodes

    def cycle_cut_nodes(self):
        cc_nodes = set()

        def aux_ccn(node, path):
            visited.append(node)
            for e in self.get_edges(source=node):
                trg = e["target"]
                if trg == node:
                    cc_nodes.add(node)
                    continue
                if trg not in visited:
                    aux_ccn(trg, path + [node])
                elif trg in path:
                    cc_nodes.add(trg)

        for n in self.get_info(constants.entries):
            visited = []
            aux_ccn(n, [])
        return list(cc_nodes)

    def get_corresponding_nodes_list(self, nodes):
        import re
        g_nodes = self.get_nodes()
        final_nodes = []
        for n in g_nodes:
            node1 = re.sub("^(n\_)*", "", n)
            node = re.sub("(\_\_\_[0-9]+)*$", "", node1)
            if node in nodes:
                final_nodes.append(n)
        return final_nodes

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
