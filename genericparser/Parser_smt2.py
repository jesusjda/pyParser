from __future__ import unicode_literals, print_function
from subproccess import Popen
from subproccess import PIPE
from ppl import Variable
from ppl import Constraint_System
from lpi import C_Polyhedron
from .Cfg import Cfg
from . import ParserInterface
from .Parser_t2 import Parser_t2
from termination.output import Output_Manager as OM


class Parser_smt2(ParserInterface):
    """SMT2 Parser
    """

    def parse(self, filepath, debug=False):
        """Parse .smt2 file

        :param filepath: Full path to file to be parsed.
        :type filepath: str
        :param debug: True to show debug information. Defaults to False
        :type debug: bool
        :returns: :obj:`pyParser.Cfg.Cfg` ControlFlowGraph.
        """
        # SMT2 to Fc
        pipe = Popen(['smtpushdown2', '-convertto', 'FC', filepath],
                     stdout=PIPE, stderr=PIPE)
        fcprogram, err = pipe.communicate()
        print(fcprogram)
        print(err)
        if err is not None:
            raise Exception(err)
        # Fc to cfg
        pfc = Parser_fc()
        return pfc.parse_string(fcprogram, debug)
