
from functools import reduce, partial
from .format import TermColorFormat, TermPlainFormat, highlight

from ..parse.standard import encode as en

from ..parse.generic import \
    ast, Location, merge_locations, QuaintSyntaxError


###############################
### RichQuaintSyntaxError ###
###############################

class RichQuaintSyntaxError(Exception):
    """
    Represents an error while lexing or parsing.

    chunks: a list of strings and (i, string) pairs. If there is a
            pair (i, string) in the list, it will be converted to a
            string highlighted with the ith syntax highlighter.

    attributes_map: a dictionary of {highlighter_class: [format]}. If
                    this error is highlighted with, say, HTMLFormat,
                    the pair (i, string) will produce the given string
                    highlighted with attributes_map[HTMLFormat][i].

    culprits: a list of "culprits". Each culprit is a node associated
              to some code location. The ith culprit will be
              highlighted in the source code with the ith highlighter.
              The culprits determine the given location of the error.

    other_nodes: other nodes to highlight. The ith member of
                 other_nodes will be highlighted with the
                 (len(culprits) + i)th highlighter. These do not count
                 as the location of the error, but may be used to
                 provide supplementary information. Defaults to [].

    The highlight() method is the prettiest way to print out the
    error, e.g. "print lexerror.highlight(1)" will print source code
    where the error is highlighted and 1 line of context is given.
    """

    def __init__(self, chunks, attributes_map, culprits, other_nodes = []):
        self.chunks = chunks
        self.attributes_map = attributes_map
        self.culprits = culprits
        self.other_nodes = other_nodes
        self.location = merge_locations(c.location if hasattr(c, 'location') else c
                                        for culprit_group in culprits
                                        for c in culprit_group)

    def highlight(self, format, context = 0):
        attributes = self.attributes_map.get(type(format), None)
        def fmt(i, text):
            if not attributes:
                return text
            return format.describe(text, attributes[i])
        message = "".join(item if isinstance(item, str) else fmt(*item)
                          for item in self.chunks)
        specifications = []
        for i, nodes in enumerate(self.culprits):
            for node in nodes:
                if hasattr(node, 'location'):
                    node = node.location
                specifications.append((node, attributes[i]))
        for i, nodes in enumerate(self.other_nodes):
            for node in nodes:
                if hasattr(node, 'location'):
                    node = node.location
                specifications.append((node, attributes[i]))
        s = "Syntax error in %s at %s\n%s\n%s" % (
            "BAH",
            self.location.ref(),
            highlight(specifications = specifications, # [(node.location, attributes[i])
                      #  for i, node in enumerate(self.culprits + self.other_nodes)],
                      format = format,
                      context = context),
            message)
        return s

    def __str__(self):
        return "".join(item if isinstance(item, str) else item[1]
                       for item in self.chunks)



########################
### Error translator ###
########################

def rich_error(err):
    if isinstance(err, QuaintSyntaxError):
        glob = globals()
        fname = err.kind + "_error"
        if fname not in glob:
            return err
        fn = glob[fname]
        new_err = fn(*err.info)
        new_err.original_error = err
        return new_err
    else:
        return err



####################
### Usual errors ###
####################

def indent_error():
    return RichQuaintSyntaxError(
        ["Indent error: the highlighted indent ",
         "is further left than the previous one, ",
         "indicating the end of an indented block, ",
         "but it does not match the indent level ",
         "of any enclosing block."],
        {TermColorFormat: ["red!"],
         TermPlainFormat: ["^"]},
        [token])


def operator_pack_error(op_tokens):

    n = len(op_tokens)
    real_op_tokens = [x for x in op_tokens if x.op != '_']
    real_n = len(real_op_tokens)
    pretty_list = [[", ", (0, x.op)] for x in real_op_tokens[:-1]]
    pretty_list = reduce(list.__add__, pretty_list)[1:]

    return RichQuaintSyntaxError(
        ["At most one ", (0, "operator"),
         " should be found at a location ",
         "where there are no non-operator tokens alongside ",
         "that they could form expressions with. ",
         "Instead, %i were found: " % real_n]
        + pretty_list +
        [" and ", (0, real_op_tokens[-1].op), ". ",
         "Note: if one operator is found at the indicated ",
         "position, it will simply evaluate to the function it ",
         "represents, which you may put in a variable and/or call, ",
         "e.g. (+)[1, 2]. If you meant to apply an operator on ",
         "the other, you may write something like '.(+)' instead of '. +'"],
        {TermColorFormat: ['red*'],
         TermPlainFormat: ['^']},
        [op_tokens])


def fixity_error(op, intended_fixity, found_fixity):
    article = "A%s " % ("n" if intended_fixity == "infix" else "")
    return RichQuaintSyntaxError(
        [article, (1, intended_fixity + "-only "), (0, "operator"),
         " was found at a location where it",
         " can only be ", (1, found_fixity), "."],
        {TermColorFormat: ['red*', 'white*'],
         TermPlainFormat: ['^', None]},
        [[op]])



def fixity_order_error(op_tokens, first, first_indices, second, second_indices):
    return RichQuaintSyntaxError(
        ["There are ", (0, first + "-only"), " ", (1, "operators"),
         " right before ", (0, second + "-only"), " ", (2, "operators"), "."],
        {TermColorFormat: ['white*', 'red*', 'green*'],
         TermPlainFormat: [None, '^', '$']},
        [[],
         [op_tokens[i] for i in first_indices],
         [op_tokens[i] for i in second_indices]])


def infix_competition_error(op_tokens, infix_indices):
    n_infix = len(infix_indices)
    return RichQuaintSyntaxError(
        ["A total of ", (0, "%i infix-only" % n_infix), " ",
         (1, "operators"), " were found at the same location "
         "(competing for the same operands). There should ",
         "be at most one."],
        {TermColorFormat: ['white*', 'red*'],
         TermPlainFormat: [None, '^']},
        [[],
         [op_tokens[i] for i in infix_indices]])


def infix_ambiguity_error(op_tokens):
    n_tok = len(op_tokens)
    colors = [['red*', 'green*', 'blue*', 'yellow*', 'magenta*'][i%5]
              for i, tok in enumerate(op_tokens)]
    labels = [['^', '$', '#', 'x', '!'][i%5]
              for i, tok in enumerate(op_tokens)]
    return RichQuaintSyntaxError(
        ["The fixity is ambiguous between the highlighted operators. ",
         "Try playing with the whitespace around them in order to clarify "
         "your intent, or use parentheses."],
        {TermColorFormat: colors,
         TermPlainFormat: labels},
        [[tok] for tok in op_tokens])


def priority_error(left, right):
    return RichQuaintSyntaxError(
        ["There is no defined priority between the operators ",
         (0, left.op), " and ", (1, right.op), ". ",
         "Insert parentheses where you see fit in order ",
         "to disambiguate the expression."],
        {TermColorFormat: ['red*', 'green*'],
         TermPlainFormat: ['^', '$']},
        [[left], [right]])


def no_tabs_error(token):
    return RichQuaintSyntaxError(
        ["Tabs are not allowed in source code. ",
         "Please replace the tabulation by an ",
         "appropriate number of spaces."],
        {TermColorFormat: ['red!'],
         TermPlainFormat: ['^']},
        [[token]])


def ambiguous_character_error(char, repl, token):
    return RichQuaintSyntaxError(
        ["Invalid source code character ", (0, char), " (", (0, en(char)), "). Character ",
         (1, char), " (", (1, en(char)), ") is too similar ",
         "to character ", (1, repl), " (", (1, en(repl)), "). ",
         "Please use the latter instead of the former. ",
         "You may use both inside strings, and they will be different characters."],
        {TermColorFormat: ['red*', 'white*'],
         TermPlainFormat: ['^', None]},
        [[token]])


def bad_character_error(char, token):
    return RichQuaintSyntaxError(
        ["Invalid source code character ", 
         (0, char), " (", (0, en(char)), "). ",
         "You may use it inside strings."],
        {TermColorFormat: ['red*'],
         TermPlainFormat: ['^']},
        [[token]])

def bad_radix_mantissa_error(radix, token):
    legal = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"[:radix] + "._"
    loc = token.location
    src = loc.source
    pfx, mantissa = src[loc.start : loc.end].split('r')
    baseline = loc.start + len(pfx) + 1
    badchars = set()
    badlocs = []
    for i, c in enumerate(mantissa):
        if c.upper() not in legal:
            badchars.add(c)
            badlocs.append(Location(src, (baseline + i, baseline + i + 1), None))
    badchars = list(sorted(badchars))
    junct = [", "] * (len(badchars) - 2) + [" and "] * (len(badchars) > 1) + [""]
    plural = len(badchars) != 1
    return RichQuaintSyntaxError(
        ["The digit", "s"*plural, " "] + sum([[(0, c), j]
                               for c, j in zip(badchars, junct)], [])
        + [(" are" if plural else " is"), " not valid in base ",
           (1, radix), ". Acceptable digits are: ",
           (2, legal[:-2]), "."
           + (" Note that the scientific notation (e.g. 2e10) cannot be used with "
              "non-decimal literal notation (at a glance I think that might be what "
              "you attempted to do)."
              if 'e' in badchars or 'E' in badchars else "")],
        {TermColorFormat: ['red*', 'green*', 'white*'],
         TermPlainFormat: ['^', '$', '%']},
        [badlocs, [Location(src, (loc.start, loc.start + len(pfx) + 1), None)], [token]])

def bad_radix_error(radix, token):
    loc = token.location
    src = loc.source
    pfx = src[loc.start : loc.end].split('r')[0]

    if token.exp >= len(token.digits):
        alt = "R({radix})[{d}]".format(
            radix = radix,
            d = ", ".join(map(str, token.digits
                              + [0] * (token.exp - len(token.digits)))))
    else:
        alt = "R({radix})[{d1}, (.), {d2}]".format(
            radix = radix,
            d1 = ", ".join(map(str, token.digits[:token.exp])),
            d2 = ", ".join(map(str, token.digits[token.exp:])))

    return RichQuaintSyntaxError(
        ["Base ", (0, radix), " is not a legal base for literals. ",
         "Bases must range from ", (1, 2), " to ", (1, 36), " inclusively. ",
         "You may try the R function instead: ",
         (1, alt),
         "."],
        {TermColorFormat: ['red*', 'white*'],
         TermPlainFormat: ['^', '$']},
        [[Location(src, (loc.start, loc.start + len(pfx) + 1), None)]])



########################################
### Errors during conversion to AST2 ###
########################################

def macro_not_simple_error(expression, culprit):
    return RichQuaintSyntaxError(
        [(0, "Macro"), " is not simple: the ", (1, "macro operator"),
         " should be an identifier, not a complex expression."],
        {TermColorFormat: ['blue*', 'red*'],
         TermPlainFormat: ['$', '^']},
        [[expression], [culprit]])

def agglut_not_infix_error(expression, culprit):
    return RichQuaintSyntaxError(
        ["The agglutination operator ", (1, "~"),
         " requires the application of an ", (0, "infix operator"),
         " on the ", (2, "left hand side"), "."],
        {TermColorFormat: ['white*', 'blue*', 'red*'],
         TermPlainFormat: [None, '$', '^']},
        [[], [expression], [expression.children[0]]])

def agglut_not_oper_error(expression, culprit):
    return agglut_not_infix_error(expression, culprit)


def _missing_condition_error(stmt, expression, unused):
    return RichQuaintSyntaxError(
        ["The highlighted ", (0, "%s statement" % stmt), " is missing a condition."],
        {TermColorFormat: ['red*'],
         TermPlainFormat: ['^']},
        [[expression]])

def _many_conditions_error(stmt, what, expression, conditions):
    return RichQuaintSyntaxError(
        ["The ", (0, "%s statement" % stmt), " should only have one %s. " % what,
         (1, "%s" % len(conditions)), " were given."],
        {TermColorFormat: ['blue*', 'red*'],
         TermPlainFormat: ['$', '^']},
        [[expression], conditions])

if_missing_condition_error = partial(_missing_condition_error, "if", "condition")
if_many_conditions_error = partial(_many_conditions_error, "if", "condition")

elif_missing_condition_error = partial(_missing_condition_error, "elif", "condition")
elif_many_conditions_error = partial(_many_conditions_error, "elif", "condition")

def elif_expected_error(expression, culprit, parent):
    return RichQuaintSyntaxError(
        ["Expected an ", (1, "elif statement"),
         ". (Syntax: ", (0, "elif <condition>: <body>"), ")"],
        {TermColorFormat: ['white*', 'red*', 'blue*'],
         TermPlainFormat: [None, '^', '$']},
        [[], [culprit], [parent]])

def else_expected_error(expression, culprit, parent):
    return RichQuaintSyntaxError(
        ["Expected an ", (1, "else or elif statement"),
         ". (Syntax: ", (0, "elif <condition>: <body>"),
         " *OR* ", (0, "else: <body>"), ")"],
        {TermColorFormat: ['white*', 'red*', 'blue*'],
         TermPlainFormat: [None, '^', '$']},
        [[], [culprit], [parent]])


def subordinate_macro_error(parent_macro, usage, expression):
    macro = expression.children[0]
    if not isinstance(macro, ast.Identifier):
        macro = macro.children[0]
    assert isinstance(macro, ast.Identifier)

    return RichQuaintSyntaxError(
        ["The macro ", (1, macro.id), " is meant to be used ",
         "along with the ",  (3, parent_macro), " statement. ",
         "Here it is used alone. If your code looks right to you, ",
         "try prefixing %s with a tilde " % macro.id,
         "(the tilde links the current statement with the previous one, "
         "regardless of line breaks, and is always needed in this case). "
         "(Syntax: ", (3, parent_macro), (0, usage[0]), " ~", (1, macro.id), (0, usage[1]), ")."],
        {TermColorFormat: ['white*', 'red*', 'blue*', 'green*'],
         TermPlainFormat: [None, '^', '$', None]},
        [[], [macro], [expression], []])

def unknown_macro_error(expression):
    macro = expression.children[0]
    if not isinstance(macro, ast.Identifier):
        macro = macro.children[0]
    assert isinstance(macro, ast.Identifier)

    return RichQuaintSyntaxError(
        ["The macro ", (0, macro.id), " is unknown to me."],
        {TermColorFormat: ['red*', 'blue*'],
         TermPlainFormat: ['^', '$']},
        [[macro], [expression]])


from_many_arguments_error = partial(_many_conditions_error, "from", "root")

def from_malformed_root_error(expression, unused, parent):
    return RichQuaintSyntaxError(
        ["The ", (1, "root"), " to import from in the ",
         (2, "from statement"), " is malformed. "
         "(Examples of correct usage: ",
         (0, "from "), (3, "x"), (0, ": ..."), " OR ",
         (0, "from "), (3, "x.y.z"), (0, ": ..."), " OR ",
         (0, "from "), (3, ".here"), (0, ": ..."), " OR ",
         (0, "from "), (3, ".here.now"), (0, ": ..."), " OR ",
         (0, "from "), (3, "(.)"), (0, ": ..."), ")"],
        {TermColorFormat: ['white*', 'red*', 'blue*', 'yellow*'],
         TermPlainFormat: [None, '^', '$', None]},
        [[], [expression], [parent], []])

def from_invalid_error(expression, unused, parent):
    return RichQuaintSyntaxError(
        ["A declaration of an ", (1, "element to import"), " in the ",
         (2, "from statement"), " is malformed. ",
         "Each element to import should take the form ",
         (0, "name"), " OR ", (0, "name ⇒ alias"), " where name and ",
         "alias are identifiers."],
        {TermColorFormat: ['white*', 'red*', 'blue*'],
         TermPlainFormat: [None, '^', '$']},
        [[], [expression], [parent]])



def bad_target_error(expression, culprit):
    return RichQuaintSyntaxError(
        ["A ", (1, "binding or assignment"), " was made to an ",
         (0, "expression"), ". Please make sure the target is ",
         "a single identifier."],
        {TermColorFormat: ['red*', 'blue*'],
         TermPlainFormat: ['^', '$']},
        [[culprit], [expression]])

def stmt_in_expr_error(expression, culprit):
    return RichQuaintSyntaxError(
        ["A ", (0, "statement"), " was found as an operand ",
         "to an ", (1, "expression"), ". Please only use statements ",
         "in non-terminal positions of a sequence (stmt, stmt, expr) ",
         "or anywhere in a table [stmt, stmt, stmt]."],
        {TermColorFormat: ['red*', 'blue*'],
         TermPlainFormat: ['^', '$']},
        [[culprit], [expression]])
