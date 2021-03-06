from genericparser import ParserInterface


class Parser_c(ParserInterface):
    """c Parser
    """

    def parse(self, filepath, debug=False):
        """Parse .c file

        :param filepath: Full path to file to be parsed.
        :type filepath: str
        :param debug: True to show debug information. Defaults to False
        :type debug: bool
        :returns: :obj:`pyParser.Cfg.Cfg` ControlFlowGraph.
        """
        # C to Koat
        koatprogram, err = self.c2koat(filepath)
        koatprogram = koatprogram.decode("utf-8")
        if err is not None and err:
            raise Exception(err)
        # Koat to cfg
        from genericparser.Parser_koat import Parser_koat
        pkoat = Parser_koat()
        return pkoat.parse_string(koatprogram, debug)

    def c2koat(self, filepath):
        from subprocess import PIPE
        from subprocess import Popen
        import tempfile
        tmpdirname = tempfile.mkdtemp()
        pipe = Popen([self.c2koatpath, self.binpath, tmpdirname, filepath],
                     stdout=PIPE, stderr=PIPE)
        return pipe.communicate()
