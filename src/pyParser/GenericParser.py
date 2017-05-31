import json
import os
import sys


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
        :returns: :obj:`pyParser.Cfg.Cfg` The Cfg corresponding to the file
        :raises: ParserError
        """
        filename, file_extension = os.path.splitext(filepath)
        if(file_extension in self._parserlist):
            # import parser
            P = __import__(self._parserlist[file_extension])
            return P.parse(filepath)
        print("Parser not found (ext: '"+file_extension+"' )")


if __name__ == "__main__":
    parser = GenericParser()
    current_dir = os.path.dirname(__file__)
    filename = "examples/example.fc"
    filepath = os.path.join(current_dir, filename)
    a = parser.parse(filepath)
    print(a)
