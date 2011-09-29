
from ..generic import parse
from . import characters, operators

__all__ = ['parser', 'expression']

parser = parse.Parser(characters, operators)
expression = parser.expression
