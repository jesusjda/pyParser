import matplotlib.pyplot as plt
import networkx as nx
from networkx.drawing.nx_pydot import write_dot
import random


class Edge:
    def __init__(self,name,src,trg,cons=[]):
        self.name = name
        self.src = src
        self.trg = trg
        self.Cons = cons
    def add_con(self,con):
        self.Cons.append(con)
    def get_src(self):
        return self.src
    def get_trg(self):
        return self.trg
    def get_id(self):
        return self.name
    def __repr__(self):
        strr = self.name+" {\n"
        for c in self.Cons:
            strr = strr + "\t"+c.__repr__()+"\n"
        strr = strr + "}"
        return strr
        print(self.Cons[0])
        return self.name+" {\n\t"+','.join(self.Cons)+ "\n}"

class Cfg(nx.MultiDiGraph):

    def add_edge2(self,edge):
        c = "#%06x" % random.randint(0, 0xFFFFFF)
        self.add_edge(edge.get_src(),edge.get_trg(),object=edge,label=edge,color=c,fontcolor=c)
       
    def echo(self,outfile="graph.dot"):
        nx.drawing.nx_pydot.write_dot(self,outfile)

    def __repr__(self):
        return "Soy un MultiDiGraph"

    def __str__(self):
        return "Soy un MultiDiGraph"
