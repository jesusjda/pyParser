"""This is the Generic Parser module.

This module can parse several languages and convert them
to a common Control Flow Graph Class.
"""
import json
import os
import sys

from . import Cfg

__all__ = ['GenericParser', 'Cfg']


class GenericParser:
    """Common interface for several parsers
    """
    _current_dir = "."
    _parserList = {}

    def __init__(self, configfile=None):
        """Builds Generic Parser

        :param configfile: Full path to configuration file
        :type configfile: str

        """
        self._current_dir = os.path.dirname(__file__)
        if configfile is None:
            configfile = os.path.join(self._current_dir, 'file-ext.json')
        with open(configfile) as data:
            self._parserlist = json.load(data)

    def parse(self, filepath):
        """Parse a file with their corresponding parser

        :param filepath: Full path to the file to be parsed
        :type filepath: str
        :returns: :obj:`genericparser.Cfg.Cfg` The Cfg corresponding
        to the file
        :raises: ParserError
        """
        _, file_extension = os.path.splitext(filepath)
        if(file_extension in self._parserlist):
            # import parser
            name = self._parserlist[file_extension]
            m = getattr(__import__("genericparser."+name), name)
            P = getattr(m, name)
            parser = P()
            cfg = parser.parse(filepath)

            return cfg
        raise Exception("Parser not found (ext: '"+file_extension+"' )")


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
