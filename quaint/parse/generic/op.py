
import re
from collections import defaultdict

from .ast import mkop

__all__ = ['OperatorGroup', 'FOperatorGroup', 'OpOrder']

###################
### OP ORDERING ###
###################

class OperatorGroup:
    """
    Holds a set of operators that have consistent associativity
    between each other. Priorities are usually defined between groups
    of operators, though it is possible to only have one operator in a
    group.

    How to use
    ==========

    og = OperatorGroup("left", "x*y", "x/y", "-x") declares a group
    containing Infix("*"), Infix("/") and Prefix("-"), all
    left-associative with themselves and each other. Each item in the
    list of member operators is filtered through ast.mkop(item).

    Then you can do something like "Infix("*") in og", which will
    return True in this case. Most of the time, you just want to give
    operator groups to OpOrder.

    The associativity can be "left", "right" or "none" (the string
    "none", but None will work too). They respectively mean
    left-associative, right-associative, or not associative at all
    (i.e. stringing together several operators in the group is a
    syntax error)

    Consider that we define * and / in a group and what various
    associativities mean for parsing the expression "x*y/z":

    "left" means x*y/z -> (x*y)/z
    "right" means x*y/z -> x*(y/z)
    "none" means that x*y/z is ambiguous and a syntax error
    """
    def __init__(self, associativity, *members):
        # left => -1, none => 0, right => 1
        self.associativity = ['left', 'none', 'right'].index(associativity or "none") - 1
        self.members = list(map(mkop, members))
    def __contains__(self, op):
        return op in self.members

class FOperatorGroup(OperatorGroup):
    """
    In addition to a list of members (see OperatorGroup), a function
    can be provided to check membership. That function's signature
    must be Operator -> boolean. If for a given operator it yields
    true, then that operator belongs to the group. There can only be
    one function and it must be the second argument, after
    associativity.
    """
    def __init__(self, associativity, fn, *members):
        super().__init__(associativity, *members)
        self.fn = fn
    def __contains__(self, op):
        return super().__contains__(op) or self.fn(op)

class OpOrder(object):
    # NOTE: NO CYCLES IN ORDERINGS SHOULD BE INTRODUCED HERE.
    # OPERATORS THAT ARE LEFT/RIGHT ASSOCIATIVE WITH EACH OTHER SHOULD
    # BE IN GROUPS

    def __init__(self, **groups):
        self.groups = groups
        self.bgroups = dict((v, k) for k, v in groups.items())
        self.left = defaultdict(set)
        self.bleft = defaultdict(set)
        self.right = defaultdict(set)
        self.bright = defaultdict(set)
        self.op_lookup = {}
        for g in self.groups.values():
            for op in g.members:
                self.op_lookup[op] = g
        self.fgroups = [g for g in self.groups.values() if isinstance(g, FOperatorGroup)]
        self.lord_cache = set()
        self.rord_cache = set()

    def _priority(self, g1, g2):
        self._left_order(g1, g2)
        self._right_order(g2, g1)

    def _left_order(self, g1, g2, infer = True):
        if infer and (g1, g2) not in self.lord_cache:
            self.lord_cache.add((g1, g2))
            for g in self.left[g2]:
                self._left_order(g1, g)
            for g in self.bleft[g1]:
                self._left_order(g, g2)
        self.left[g1].add(g2)
        self.bleft[g2].add(g1)

    def _right_order(self, g1, g2, infer = True):
        if infer and (g1, g2) not in self.rord_cache:
            self.rord_cache.add((g1, g2))
            for g in self.right[g2]:
                self._right_order(g1, g)
            for g in self.bright[g1]:
                self._right_order(g, g2)
        self.right[g1].add(g2)
        self.bright[g2].add(g1)

    def priority(self, *group_names):
        groups = list(map(self.groups.__getitem__, group_names))
        for g1, g2 in zip(groups[:-1], groups[1:]):
            self._priority(g1, g2)

    def left_order(self, g1, g2, infer = True):
        g1, g2 = self.groups[g1], self.groups[g2]
        self._left_order(g1, g2, infer)

    def right_order(self, g1, g2, infer = True):
        g1, g2 = self.groups[g1], self.groups[g2]
        self._right_order(g1, g2, infer)

    def op_order(self, op1, op2):
        # NOTE: maybe have somewhat better sanity checks to avoid
        # accidentally having ops in several groups etc.
        g1 = self.op_lookup.get(op1, None) or [g for g in self.fgroups if op1 in g][0]
        g2 = self.op_lookup.get(op2, None) or [g for g in self.fgroups if op2 in g][0]
        if g1 is g2:
            return g1.associativity
        if g2 in self.left[g1]:
            return -1
        elif g2 in self.right[g1]:
            return 1
        else:
            return 0

