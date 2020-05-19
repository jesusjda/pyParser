"""This is the GenericParser module.

This module can parse several languages and convert them
to a common Control Flow Graph Class.
"""
import os

from . import Cfg
from . import constants


__all__ = ['parse', 'parse_constraint', 'parse_cfg_props', 'Cfg', "constants"]


class ParserInterface:
    """Interface for parsers
    """

    def parse(self, filepath, debug=False):
        """Parse .EXTENSION file

        :param filepath: Full path to file to be parsed.
        :type filepath: str
        :param debug: True to show debug information. Defaults to False
        :type debug: bool
        :returns: :obj:`genericparser.Cfg.Cfg` ControlFlowGraph.
        """
        raise Exception("Not implemented yet!")

    def program2cfg(self, program):
        G = Cfg.Cfg()
        tr_names = []
        for t in program["transitions"]:
            if t["name"] in tr_names:
                raise ValueError("Multiple transitions with the same name: {}.".format(t["name"]))
            tr_names.append(t["name"])
            G.add_edge(**t)
        if constants.entries not in program and constants.initnode in program:
            program[constants.entries] = [program[constants.initnode]]
        if "nodes" in program:
            for n in program["nodes"]:
                for k in program["nodes"][n]:
                    G.nodes[n][k] = program["nodes"][n][k]
        for key in program:
            if not(key in ["transitions", "nodes"]):
                G.set_info(key, program[key])

        if len(G.in_edges(G.get_info(constants.initnode))) > 0:
            default_name = "_init"
            init_node = default_name
            i = 1
            while init_node in G.get_nodes():
                init_node = default_name + str(i)
                i += 1
            default_name = "t"
            init_tr = default_name + str(0)
            i = 1
            trs_name = [t["name"] for t in program["transitions"]]
            while init_tr in trs_name:
                init_tr = default_name + str(i)
                i += 1
            from lpi import Expression
            gvs = G.get_info(constants.variables)
            N = int(len(gvs) / 2)
            cons = [Expression(gvs[i]) == Expression(gvs[i + N]) for i in range(N)]
            t = {"source": init_node, "target": G.get_info(constants.initnode), "name": init_tr,
                 constants.transition.islinear: True, constants.transition.localvariables: [], constants.transition.constraints: cons}
            G.add_edge(**t)
            G.set_info(constants.initnode, init_node)
            G.set_info(constants.entries, [init_node])
        domain = program.get("domain", "Z")
        if domain not in ["Z", "Q"]:
            raise ValueError("Invalid Domain: {}".format(domain))
        G.set_info("domain", domain)
        return G


from . import Parser_fc
from . import Parser_mlc
from . import Parser_smt2
from . import Parser_koat
from . import Parser_c

_parserlist = {
    ".fc": Parser_fc.Parser_fc,
    ".smt2": Parser_smt2.Parser_smt2,
    ".mlc": Parser_mlc.Parser_mlc,
    ".koat": Parser_koat.Parser_koat,
    ".c": Parser_c.Parser_c
}


def parse(filepath):
    """Parse a file with their corresponding parser

    :param filepath: Full path to the file to be parsed
    :type filepath: str
    :returns: :obj:`genericparser.Cfg.Cfg` The corresponding Cfg
    :raises: ParserError
    """
    __, file_extension = os.path.splitext(filepath)
    if(file_extension in _parserlist):
        name = _parserlist[file_extension]
        parser = name()
        return parser.parse(filepath)
    raise Exception("Parser not found (ext: '" + file_extension + "' )")


def parse_constraint(cons_string):
    from . import Constraint_parser
    """Parse a string to a constraint
    :param cons_string: string to be parsed
    :type cons_string: str
    :returns: :obj: `lpi.Constraint` The corresponding constraint
    :raises: ParserError
    """
    return Constraint_parser.Parser_Constraint().parse_string(cons_string)


def parse_cfg_props(filepath, cfg):
    """Parse a file

    :param filepath: Full path to the file to be parsed
    :type filepath: str
    :returns: :obj: dictionary
    :raises: ParserError
    """
    nodes = cfg.get_nodes()
    from .Properties_parser import Parser_Properties
    props = {}
    cfg_props = Parser_Properties().parse(filepath)
    if "nodes" in cfg_props:
        node_props = cfg_props["nodes"]
        for n in node_props:
            if n not in nodes:
                raise ValueError("Properties defined for a node that doesn't exists")
            for k in node_props[n]:
                if k not in props:
                    props[k] = {}
                props[k][n] = node_props[n][k]
        for k in props:
            cfg.set_nodes_info(props[k], k)
