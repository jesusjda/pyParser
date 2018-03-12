#!/usr/bin/env python
import os
from setuptools import setup


base = os.path.dirname(os.path.abspath(__file__))

VERSION = open(os.path.join(base, 'version.txt')).read()[:-1]

pkg_dir = os.path.join(base, 'genericparser')
pkg_name = 'genericparser'

requires = ['arpeggio', 'networkx', 'pydotplus', 'pydot', 'lark-parser']

setup(
    name='genericparser',
    version=VERSION,
    description='Python Generic Parser',
    long_description=open(os.path.join(base, "README.md")).read(),
    author='Jesus Domenech',
    author_email='jdomenec@ucm.es',
    url='https://github.com/jesusjda/pyParser',
    download_url='https://github.com/jesusjda/pyParser/archive/{}.tar.gz'.format(VERSION),
    license='GPL v3',
    platforms=['any'],
    packages=[pkg_name],
    package_dir={pkg_name: pkg_dir},
    package_data={pkg_name: ['*.py', 'file-ext.json', 'smtpushdown2', '*.g']},
    install_requires=requires,
    dependency_links=[],
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python",
        "Development Status :: 3 - Alpha",
        "Operating System :: Unix",
        "Intended Audience :: Science/Research",
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ],
    keywords=['parser', 'generic parsing', 'control flow graph'],
)
