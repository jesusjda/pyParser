from __future__ import unicode_literals, print_function
import os
from subprocess import Popen
from subprocess import PIPE
# from ppl import Variable
# from ppl import Constraint_System
# from lpi import C_Polyhedron
# from .Cfg import Cfg
from . import ParserInterface
from .Parser_fc import Parser_fc


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
        smtpushdown2path = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), 'smtpushdown2')
        pipe = Popen([smtpushdown2path, '-convertto', 'FC', filepath],
                     stdout=PIPE, stderr=PIPE)
        fcprogram, err = pipe.communicate()
        if err is not None and err != "":
            raise Exception(err)
        self.last_fc = (filepath + ".fc", fcprogram)
        # Fc to cfg
        pfc = Parser_fc()
        return pfc.parse_string(fcprogram, debug)

    def getLastFc(self):
        return self.last_fc

    def toT2(self, filepath):
        # SMT2 to Fc
        smtpushdown2path = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), 'smtpushdown2')
        pipe = Popen([smtpushdown2path, '-convertto', 'T2', filepath],
                     stdout=PIPE, stderr=PIPE)
        return pipe.communicate()

