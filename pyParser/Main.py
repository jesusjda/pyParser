import os
import sys
import glob
import getopt
import argparse


_name = "Generic Parser"
_version = "0.0.0.1"


def setArgumentParser():
    parsers = ["Parser_fc"]
    desc = _name+": a Parser and dot graph generator on python."
    argParser = argparse.ArgumentParser(description=desc)

    argParser.add_argument("-d", "--dot", required=False,
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
            if args.extension == '' or args.extension == fileExt:
                files.add(path)
        else:
            full_paths += glob.glob(path + '/*')

    for f in files:
        print f
    exit(0)
    a = (Parser_fc()).parse(filepath, False)
    print(a)
    a._echo()

if __name__ == "__main__":
    _main()
