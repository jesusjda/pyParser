import argparse
from genericparser import GenericParser
from genericparser.Parser_smt2 import Parser_smt2
import glob
import os
from termination.output import Output_Manager as OM


_name = "Generic Parser"
_version = "0.1"


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


def toSVG(source, target=None):
    if target is None :
        target = source+".svg"
    command = "dot -Tsvg " + source + " -o "+ target 
    os.system(command)


def _main():
    argParser = setArgumentParser()
    args = argParser.parse_args()

    full_paths = [os.path.join(os.getcwd(), path) for path in args.path]

    files = []
    for path in full_paths:
        if os.path.isfile(path):
            fileName, fileExt = os.path.splitext(path)
            if(args.extension == '' or
               args.extension == fileExt or
               ('.' + args.extension) == fileExt):
                files.append(path)
        else:
            full_paths += glob.glob(path + '/*')
    files.sort()
    P = GenericParser()
    errors = []
    for f in files:
        try:
            fileName, fileExt = os.path.splitext(os.path.basename(f))
            dotgraph = None
            if args.dot:
                dotgraph = ("/home/friker/tmp/cache/" +
                            fileName + "." + fileExt[1::])
            print("-> {}".format(f))
            cfg = P.parse(f)
            OM.restart(vars_name=cfg.get_var_name())
            cfg.toDot(OM, outfile=(dotgraph+".dot"))
            toSVG(dotgraph+".dot")
            smt2p = Parser_smt2()
            fccode, err = smt2p.toFC(f)
            with open(dotgraph+".fc", "w") as fcfile:
                fcfile.write(fccode.decode("utf-8"))
        except Exception:
            errors.append(f)

    print("ERRORS: ", errors)
    exit(0)


if __name__ == "__main__":
    _main()
