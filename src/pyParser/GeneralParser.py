import json
import os
import sys

current_dir = os.path.dirname(__file__)
filepath = os.path.join(current_dir, 'file-ext.json')

with open(filepath) as data_file:
    parserlist = json.load(data_file)


class GeneralParser:

    def parse(self, filepath):
        filename, file_extension = os.path.splitext(filepath)
        if(file_extension in parserlist):
            parserpath = parserlist[file_extension]
	    parserpath = os.path.join(current_dir, parserpath)
            sys.path.append(parserpath)
            from Parser import Parser
            parser = Parser()
            return parser.parse(filepath)
        print("Parser not found (ext: '"+file_extension+"' )")


if __name__ == "__main__":
    parser = GeneralParser()
    filename = "fc_parser/example.fc"
    filepath = os.path.join(current_dir, filename)
    a = parser.parse(filepath)
    print(a)
