'''
Created on Jan 29, 2018

@author: friker
'''
from genericparser import GenericParser


if __name__ == '__main__':
    filepath = "/home/friker/Systems/pyParser/genericparser/examples/example.pe.fc"
    p = GenericParser()
    p.parse(filepath)