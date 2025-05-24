from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import sys
import setuptools

__version__ = '0.0.1'

class get_pybind_include(object):
    def __init__(self, user=False):
        self.user = user

    def __str__(self):
        import pybind11
        return pybind11.get_include(self.user)

ext_modules = [
    Extension(
        'connect4',
        ['bindings.cpp', 'Solver.cpp'],
        include_dirs=[
            get_pybind_include(),
            get_pybind_include(user=True),
        ],
        language='c++'
    ),
]

setup(
    name='connect4',
    version=__version__,
    author='Pascal Pons',
    author_email='contact@gamesolver.org',
    description='Python bindings for Connect4 Game Solver',
    long_description='',
    ext_modules=ext_modules,
    install_requires=['pybind11>=2.6.0'],
    setup_requires=['pybind11>=2.6.0'],
    zip_safe=False,
)