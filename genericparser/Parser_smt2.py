from genericparser import ParserInterface


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
        fcprogram, err = self.toFC(filepath)
        fcprogram = fcprogram.decode("utf-8")
        if err is not None and err:
            raise Exception(err)
        # Fc to cfg
        from genericparser.Parser_fc import Parser_fc
        pfc = Parser_fc()
        return pfc.parse_string(fcprogram, debug)

    def toT2(self, filepath):
        return self.smtpushdown('T2', filepath)

    def toFC(self, filepath):
        return self.smtpushdown('FC', filepath)

    def smtpushdown(self, convertto, filepath):
        from subprocess import PIPE
        from subprocess import Popen
        pipe = Popen([self.smtpushdown2path, '-convertto', convertto, filepath],
                     stdout=PIPE, stderr=PIPE)
        return pipe.communicate()
