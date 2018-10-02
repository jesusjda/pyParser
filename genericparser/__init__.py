"""This is the GenericParser module.

This module can parse several languages and convert them
to a common Control Flow Graph Class.
"""
import json
import os

from . import Cfg


__all__ = ['parse', 'parse_constraint', 'Cfg']


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
        for t in program["transitions"]:
            G.add_edge(**t)
        if "entry_nodes" not in program and "init_node" in program:
            program["entry_nodes"] = [program["init_node"]]
        if "nodes" in program:
            for n in program["nodes"]:
                for k in program["nodes"][n]:
                    G.nodes[n][k] = program["nodes"][n][k]
        for key in program:
            if not(key in ["transitions", "nodes"]):
                G.set_info(key, program[key])
        return G


from . import Parser_fc
from . import Parser_mlc
from . import Parser_smt2
from . import Parser_koat

_parserlist = {
    ".fc": Parser_fc.Parser_fc,
    ".smt2": Parser_smt2.Parser_smt2,
    ".mlc": Parser_mlc.Parser_mlc,
    ".koat": Parser_koat.Parser_koat,
    }

def parse(filepath):
    """Parse a file with their corresponding parser

    :param filepath: Full path to the file to be parsed
    :type filepath: str
    :returns: :obj:`genericparser.Cfg.Cfg` The corresponding Cfg
    :raises: ParserError
    """
    _, file_extension = os.path.splitext(filepath)
    if(file_extension in _parserlist):
        name = _parserlist[file_extension]
        parser = name()
        cfg = parser.parse(filepath)

        return cfg
    raise Exception("Parser not found (ext: '" + file_extension + "' )")

def parse_constraint(cons_string):
    
    from . import Constraint_parser
    """Parse a string to a constraint
    
    :param cons_string: string to be parsed
    :type cons_string: str
    :returns: :obj: `genericparser.expessions.inequality` The corresponding constraint
    :raises: ParserError
    """
    return Constraint_parser.Parser_Constraint().parse_string(cons_string)

