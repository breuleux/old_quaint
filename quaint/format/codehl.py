
from .format import highlight, TermColorFormat, HTMLFormat
from ..parse.generic import ast


__all__ = ['ASTHighlighter']


def is_whitespace(x):
    return (isinstance(x, ast.OpApply)
            and x.operator in (ast.Infix("_"), ast.Infix("__")))

def not_whitespace(x):
    return not is_whitespace(x)

def infix(name):
    op = ast.Infix(name)
    def chki(x):
        return (isinstance(x, ast.OpApply)
                and x.operator == op)
    return chki

def prefix(name):
    op = ast.Prefix(name)
    def chkpr(x):
        return (isinstance(x, ast.OpApply)
                and x.operator == op)
    return chkpr

def postfix(name):
    op = ast.Postfix(name)
    def chkpo(x):
        return (isinstance(x, ast.OpApply)
                and x.operator == op)
    return chkpo

def mac(name):
    def chkmac(x):
        return (isinstance(x, ast.OpApply)
                and x.operator == ast.Infix(":")
                and is_whitespace(x.children[0])
                and isinstance(x.children[0].children[0], ast.Identifier)
                and x.children[0].children[0].id == name)
    return chkmac


# Each entry in the highlighters list contains a list of matchers
# (essentially corresponding to the "path" from the top level to the
# node being highlighted, so "b" in the expression "a + b" will see
# something like [OpApply(+, a, b), 1, Identifier("b")], so if for
# example you want to match the right operand of +, you can use the
# matcher sequence [infix("+"), 1, ast.Identifier]). The second
# element is a boolean indicating whether the highlight is final
# (True), or if sub-expressions should be highlighted (False). The
# last element is the format to highlight with.

term_color_highlighters = (

    ############
    # : syntax #
    ############

    ([infix(":"), 0, infix("_"), 0, ast.ASTNode],
     True, "yellow*"),
    ([infix(":"), 0, infix("__"), 0, ast.ASTNode],
     True, "yellow*"),
    ([infix(":"), 0, not_whitespace],
     True, "yellow*"),

    # Definitions
    ([mac("pure"), 0, infix("__"), 1, infix("_"), 0, ast.Identifier],
     True, "green*"),

    ###########
    # Strings #
    ###########

    ([ast.StringVI, int, ast.ASTNode],
     True, "magenta*"),
    ([ast.StringVI],
     False, "red*"),

    ###############
    # Parentheses #
    ###############

    ([ast._Seq],
     False, "white*"),

    #############
    # Operators #
    #############

    ([prefix(".")],
     True, "yellow"),
    ([infix("~"), "op"],
     True, "yellow*"),
    ([infix(":"), "op"],
     True, "yellow*"),
    ([infix("←"), 0, ast.Identifier],
     True, "green*"),
    ([infix("_"), "op"],
     True, None),
    ([infix("__"), "op"],
     True, None),
    ([ast.OpApply, "op"],
     True, "blue*"),

    ###############
    # Identifiers #
    ###############

    ([ast.Identifier],
     True, "white*"),
    ([ast.Numeral],
     True, "cyan*"),
    )


html_highlighters = (

    ############
    # : syntax #
    ############

    ([infix(":"), 0, infix("_"), 0, ast.ASTNode],
     True, "macro"),
    ([infix(":"), 0, infix("__"), 0, ast.ASTNode],
     True, "macro"),
    ([infix(":"), 0, not_whitespace],
     True, "macro"),

    # Definitions
    ([mac("def"), 0, infix("__"), 1, infix("_"), 0, ast.Identifier],
     True, "definition"),

    ###########
    # Strings #
    ###########

    ([ast.StringVI, int, ast.ASTNode],
     True, "string_vi"),
    ([ast.StringVI],
     False, "string"),

    ###############
    # Parentheses #
    ###############

    ([ast._Seq],
     False, "sequence"),

    #############
    # Operators #
    #############

    ([prefix(".")],
     True, "symbol"),
    # ([infix("!"), "op"],
    #  True, "agglutinator"),
    # ([infix(":"), "op"],
    #  True, "macro_operator"),
    # ([infix("←"), 0, ast.Identifier],
    #  True, "set_variable"),
    ([infix("_"), "op"],
     True, None),
    ([infix("__"), "op"],
     True, None),
    ([ast.OpApply, "op"],
     True, "operator"),

    ###############
    # Identifiers #
    ###############

    ([ast.Identifier],
     True, "identifier"),
    ([ast.Numeral],
     True, "numeral"),
    )


default_highlighters = {
    TermColorFormat: term_color_highlighters,
    HTMLFormat: html_highlighters
    }


class ASTHighlighter(ast.ASTVisitor):

    def __init__(self, format, highlighters = None):
        self.format = format
        if highlighters is None:
            highlighters = default_highlighters[type(format)]
        self.highlighters = highlighters

    def highlight(self, expr):
        self.stack = []
        self.visit(expr, [])
        return highlight(self.stack, self.format, 3)

    def match_state(self, state):
        nstate = len(state)
        for target_state, final, format in self.highlighters:
            if len(target_state) > nstate:
                continue
            short_state = state[-len(target_state):]
            # print(target_state, short_state, len(target_state), len(short_state), len(state))
            for target, this in zip(target_state, short_state):
                if isinstance(target, type):
                    if isinstance(this, target):
                        continue
                elif hasattr(target, '__call__') and target(this):
                    continue
                elif this == target:
                    continue
                break
            else:
                return (final, format)
        return None

    def match_and_apply(self, location, state):
        match = self.match_state(state)
        if match is None:
            return False
        final, format = match
        # print((str(location), format, state))
        if format is not None:
            self.stack.append((location, format))
        return final

    def visit_Identifier(self, node, state):
        self.match_and_apply(node.location, state + [node])

    def visit_Numeral(self, node, state):
        self.match_and_apply(node.location, state + [node])

    def visit_StringVI(self, node, state):
        state = state + [node]
        if not self.match_and_apply(node.location, state):
            for i, item in enumerate(node.items):
                self.visit(item, state + [i])

    def visit_Operator(self, node, state):
        self.match_and_apply(node.location, state)
    
    def visit_OpApply(self, node, state):
        state = state + [node]
        if not self.match_and_apply(node.location, state):
            self.visit(node.operator, state + ["op"])
            for i, item in enumerate(node.children):
                self.visit(item, state + [i])

    def visit__Seq(self, node, state):
        state = state + [node]
        if not self.match_and_apply(node.location, state):
            for i, item in enumerate(node.items):
                self.visit(item, state + [i])

    def visit_ASTNode(self, node):
        raise Exception("This node type is not highlighted: %s" % type(node))





