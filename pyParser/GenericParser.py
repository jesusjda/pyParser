import json
import os
import sys
sys.path.append("../../pyLPi/pyLPi/")


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

    def parse(self, filepath, dot=None):
        """Parse a file with their corresponding parser

        :param filepath: Full path to the file to be parsed
        :type filepath: str
        :returns: :obj:`pyParser.Cfg.Cfg` The Cfg corresponding to the file
        :raises: ParserError
        """
        filename, file_extension = os.path.splitext(filepath)
        if(file_extension in self._parserlist):
            # import parser
            name = self._parserlist[file_extension]
            P = getattr(__import__(name), name)
            parser = P()
            cfg = parser.parse(filepath)
            if not(dot is None):
                cfg.toDot(dot)
            return cfg
        raise Exception("Parser not found (ext: '"+file_extension+"' )")


class ParserInterface:
    """Interface for parsers
    """

    def parse(filepath, debug):
        """Parse .fc file

        :param filepath: Full path to file to be parsed.
        :type filepath: str
        :param debug: True to show debug information. Defaults to False
        :type debug: bool
        :returns: :obj:`pyParser.Cfg.Cfg` ControlFlowGraph.
        """
        pass


if __name__ == "__main__":
    parser = GenericParser()
    current_dir = os.path.dirname(__file__)
    filename = "examples/example.fc"
    filepath = os.path.join(current_dir, filename)
    a = parser.parse(filepath)
    print(a)
