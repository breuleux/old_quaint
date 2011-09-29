
import re
import pyparsing as P
from .location import merge_locations


__all__ = ['ASTNode', 'Identifier', 'Numeral', 'Bracketed', 'StringVI',
           'RawOperator', 'Indent', 'OperatorBlock', 'RawExpr',
           'Operator', 'Prefix', 'Infix', 'Postfix', 'mkop',
           'OpApply', 'Void']


###############
### ASTNODE ###
###############

class ASTNode:
    """
    Basic source code object. Contains a location field in order to
    track the node back to the source.
    """
    def __init__(self, location):
        self.location = location
    def __len__(self):
        """
        This returns the length of the excerpt corresponding to the
        node in the source code.
        """
        return len(self.location) if self.location else 0
    def __str__(self):
        return "XXX"
    def __repr__(self):
        return str(self)
    def all_children(self):
        return []


####################
### PARSER NODES ###
####################

class Identifier(ASTNode):
    def __init__(self, location, id):
        super().__init__(location)
        self.id = id
    def __str__(self):
        return "%s" % self.id
    def __unify_walk__(self, other, U):
        return (type(other) is type(self)
                and U.walk(self.id, other.id))


_digit_table = P.nums + P.alphas[-26:]
def to_digit_list(s):
    return [_digit_table.index(c) for c in s.upper()]
def to_digits(l):
    return "".join(_digit_table[i] for i in l)

class Numeral(ASTNode):
    def __init__(self, location, radix, digits, exp):
        super().__init__(location)
        self.radix = radix
        if isinstance(digits, str):
            digits = to_digit_list(digits)
        while digits and not digits[0]: digits = digits[1:]; exp -= 1
        while digits and not digits[-1]: digits = digits[:-1]
        if not digits: digits = [0]
        self.digits = digits
        self.exp = exp
    def __str__(self):
        return "%sr.%s^%s" % (self.radix, to_digits(self.digits), self.exp)


class Bracketed(ASTNode):
    def __init__(self, location, type, expression):
        super().__init__(location)
        self.type = type
        self.expression = expression
    def __str__(self):
        return "%s(%s)" % (self.type, self.expression)
    def all_children(self):
        return [self.expression]
    def __unify_walk__(self, other, U):
        return (type(other) is type(self)
                and U.walk([self.type, self.expression],
                           [other.type, other.expression]))


class StringVI(ASTNode): # String with Variable Interpolation
    def __init__(self, location, items):
        super().__init__(location)
        self.items = list(items)
    def __str__(self):
        s = ""
        for item in self.items:
            if isinstance(item, str):
                s += item
            else:
                s += "$" + str(item)
        return '"%s"' % s
    def all_children(self):
        return []
    def __unify_walk__(self, other, U):
        return (type(other) is type(self)
                and U.walk(self.items, other.items))


class RawOperator(ASTNode):
    def __init__(self, location, op):
        super().__init__(location)
        self.op = op
    def __str__(self):
        return "!(%s)" % (self.op)
    def __unify_walk__(self, other, U):
        return (type(other) is type(self)
                and U.walk(self.op, other.op))


class Indent(ASTNode):
    def __init__(self, location, level):
        super().__init__(location)
        self.level = level
    def __str__(self):
        return "->%s" % (self.level)


class OperatorBlock(ASTNode):
    def __init__(self, location, operators):
        super().__init__(location)
        self.operators = operators
    def __str__(self):
        return "[%s]" % " ".join(op.op for op in self.operators)


class RawExpr(ASTNode):
    def __init__(self, location, items):
        super().__init__(location)
        self.items = items
    def __str__(self):
        return "{%s}" % " ".join(map(str, self.items))


############################
### POSTPROCESSING NODES ###
############################

class Operator(ASTNode):
    def __init__(self, raw_op, fixity):
        self.location = None
        if isinstance(raw_op, str):
            # self.op = codec.decode(raw_op)
            self.op = raw_op
        elif isinstance(raw_op, RawOperator):
            self.op = raw_op.op
            self.raw_op = raw_op
            self.location = raw_op.location
        else:
            self.op = raw_op
        self.fixity = fixity

    # Note: eq and hash are required for this node, because we are
    # putting some of them in dictionaries to compare precedence of
    # fresh nodes.
    def __eq__(self, other):
        return type(self) is type(other) \
            and self.op == other.op \
            and self.fixity == other.fixity
    def __hash__(self):
        return hash(self.op) ^ hash(self.fixity)

    def __unify_walk__(self, other, U):
        return (type(other) is type(self)
                and U.walk([self.op, self.fixity],
                           [other.op, other.fixity]))


class Prefix(Operator):
    def __init__(self, raw_op):
        super().__init__(raw_op, 'prefix')
    def __str__(self):
        return '%sx' % self.op


class Postfix(Operator):
    def __init__(self, raw_op):
        super().__init__(raw_op, 'postfix')
    def __str__(self):
        return 'x%s' % self.op


class Infix(Operator):
    def __init__(self, raw_op):
        super().__init__(raw_op, 'infix')
    def __str__(self):
        return 'x%sy' % self.op


def mkop(description):
    """
    Returns an Operator from a string describing it. Essentially, you
    give a string representing the application of the operator on
    variables, so that it can figure out whether it's infix, prefix or
    postfix. The examples should be straightforward:

    "x+y" -> Infix("+")
    "-x"  -> Prefix("-")
    "x++" -> Postfix("++")

    The variables must be single lowercase letters. Try to stick with
    x and y.
    """
    if not isinstance(description, str):
        return description
    elif re.match('^[a-z](.*)[a-z]$', description):
        # "x+y" => Infix("+")
        return Infix(description[1:-1])
    elif re.match('^(.*)[a-z]$', description):
        # "+x" => Prefix("+")
        return Prefix(description[0:-1])
    elif re.match('^[a-z](.*)$', description):
        # "x+" => Postfix("+")
        return Postfix(description[1:])
    else:
        raise Exception('Invalid operator description: %s' % description)


class OpApply(ASTNode):
    def __init__(self, operator, *operands, location = None):
        if location is None:
            location = merge_locations([operator.location]
                                       +[operand.location
                                         for operand in operands
                                         if operand])
        super().__init__(location)
        self.operator = operator
        self.children = list(operands)
    def __str__(self):
        s = self.operator.op.join(str(child if child is not None else '')
                                  for child in self.children)
        return '(%s)' % s

    def __unify_walk__(self, other, U):
        return (type(other) is type(self)
                and U.walk([self.operator, self.children],
                           [other.operator, other.children]))


class Void(ASTNode):
    def __str__(self):
        return 'void'



#########################
### PHASE 2 AST NODES ###
#########################

class _Seq(ASTNode):
    def __init__(self, location, items):
        super().__init__(location)
        self.items = items
    def __unify_walk__(self, other, U):
        return (type(other) is type(self)
                and U.walk(self.items, other.items))

class Sequence(_Seq):
    def __str__(self):
        return "(%s)" % ", ".join(map(str, self.items))

class Table(_Seq):
    def __str__(self):
        return "[%s]" % ", ".join(map(str, self.items))

class Code(_Seq):
    def __str__(self):
        return "{%s}" % ", ".join(map(str, self.items))



# #########################
# ### PHASE 3 AST NODES ###
# #########################

# class Apply(ASTNode):
#     def __
#     def __str__(self):
#         return ":" + super().__str__()




################
### VISITORS ###
################

class ASTVisitor:

    def visit(self, node, *rest):
        for cls in type(node).__mro__:
            kind = cls.__name__
            try:
                fn = getattr(self, "visit_" + kind)
            except AttributeError as e:
                continue
            return fn(node, *rest)
        return node


class ASTModifier(ASTVisitor):

    def visit_OpApply(self, node):
        node.operator = self.visit(node.operator)
        node.children = list(map(self.visit, node.children))
        return node

    def visit_Bracketed(self, node):
        node.expression = self.visit(node.expression)
        return node

    def visit_StringVI(self, node):
        node.items = map(self.visit, node.items)
        return node

    def visit__Seq(self, node):
        node.items = map(self.visit, node.items)
        return node



# (((def__(bottles_[n])):
#       ((((((if__((n=(-10r.1^1)))):
#                "99 bottles")
#           !((elif__((n=10r.0^0))):
#                 "no more bottles"))
#          !((elif__((n=10r.1^1))):
#                "one bottle"))
#         !(else:"$n bottles")))),

#  ((def__(message_[n])):
#       ((((if__((n=10r.0^0))):
#              "Go to the store and buy some more")
#         !(else:"Take one down and pass it around")))),

#  ((def__(main_[void])):
#       (((for__((i∈(10r.99^2‥10r.0^0)))):
#             ((b←(bottles_[i])),
#              (♦"$(b_(.capitalize)_[void]) of beer on the wall, $b of beer."),
#              (♦"$(message_[i]), $(bottles_[(i-10r.1^1)]) of beer on the wall."))))))

