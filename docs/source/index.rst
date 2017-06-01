.. _intro:

=========================
pyParser's documentation!
=========================

Example
^^^^^^^

This module provides :ref:`several parser <mod-parsers>` for different
file extension. Each parser returns a :ref:`Control Flow Graph
<mod-cfg>` whose edges are sets of Constraints.

Example::

    parser = GenericParser()
    cfg = parser.parser('/path/to/file.ext')

You don't have to care about the file extension. :ref:`GenericParser
<mod-generic>` will detected which is the correct Parser.



.. toctree::
   :hidden:
   :maxdepth: 2
	      
   modules
