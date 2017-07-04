import os
import sys
import glob
import getopt
import argparse
from GenericParser import GenericParser

_name = "Generic Parser"
_version = "0.0.0.1"


def setArgumentParser():
    # parsers = ["Parser_fc", "Parser_mlc"]
    desc = _name+": a Parser and dot graph generator on python."
    argParser = argparse.ArgumentParser(description=desc)

    argParser.add_argument("-d", "--dot", required=False, action='store_true',
                           help="Generate dot file with the program graph.")
    argParser.add_argument("-ver", "--version", required=False,
                           action='store_true', help="Shows the version.")
    argParser.add_argument("-p", "--path", nargs='+', required=True,
                           help="Files or dir to be analysed.")
    argParser.add_argument('-e', '--extension', default='',
                           help='File extension to filter by.')
    return argParser


def _main():
    argParser = setArgumentParser()
    args = argParser.parse_args()

    full_paths = [os.path.join(os.getcwd(), path) for path in args.path]

    files = set()
    for path in full_paths:
        if os.path.isfile(path):
            fileName, fileExt = os.path.splitext(path)
            if(args.extension == '' or
               args.extension == fileExt or
               ('.' + args.extension) == fileExt):

                files.add(path)
        else:
            full_paths += glob.glob(path + '/*')

    P = GenericParser()
    for f in files:
        fileName, fileExt = os.path.splitext(os.path.basename(f))
        dotgraph = None
        if args.dot:
            dotgraph = (os.path.join(os.getcwd(), "graphs") + "/" +
                        fileName + "_" + fileExt[1::] + ".dot")

        a = P.parse(f, dotgraph)

    exit(0)

if __name__ == "__main__":
    _main()
