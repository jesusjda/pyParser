import json
import os
import sys

with open('file-ext.json') as data_file:
    parserlist = json.load(data_file)


class GeneralParser:

    def parse(self, filepath):
        filename, file_extension = os.path.splitext(filepath)
        if(file_extension in parserlist):
            parserpath = parserlist[file_extension]
            sys.path.append('./'+parserpath)
            from Parser import Parser
            parser = Parser()
            return parser.parse(filepath)
        print("Parser not found (ext: '"+file_extension+"' )")


if __name__ == "__main__":
    # In debug mode dot (graphviz) files for parser model
    # and parse tree will be created for visualization.
    # Checkout current folder for .dot files.
    current_dir = os.path.dirname(__file__)
    filename = "fc-parser/example.fc"
    filepath = os.path.join(current_dir, filename)
    parser = GeneralParser()
    a = parser.parse(filepath)
    print(a)
