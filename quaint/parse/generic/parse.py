
from functools import reduce

from . import ast, location, pyparsing as P
from .error import QuaintSyntaxError

###############
### HELPERS ###
###############

class Suppressor(object):
    def __init__(self, thing):
        self.thing = thing

G = P.Group
L = lambda *args, **kwargs: P.Literal(*args, **kwargs).leaveWhitespace()
O = lambda *args, **kwargs: P.Optional(*args, **kwargs).leaveWhitespace()
W = lambda *args, **kwargs: P.Word(*args, **kwargs).leaveWhitespace()
A1 = lambda x: P.oneOf(list(x)).leaveWhitespace()
N1 = lambda x: P.CharsNotIn(x, max = 1).leaveWhitespace()
Suppr = lambda x: x.setParseAction(lambda tokens: Suppressor(tokens))
E = lambda: P.Empty().leaveWhitespace()
Star = lambda *args, **kwargs: P.ZeroOrMore(*args, **kwargs).leaveWhitespace()
Plus = lambda *args, **kwargs: P.OneOrMore(*args, **kwargs).leaveWhitespace()
FW = lambda: P.Forward().leaveWhitespace()

def compute_length(tokens):
    """
    """
    length = 0
    for token in tokens:
        if isinstance(token, (list, tuple, P.ParseResults)):
            length += compute_length(token)
        elif isinstance(token, Suppressor):
            length += compute_length(token.thing)
        else:
            length += len(token)
    return length

def auto_location(f):
    """
    Automatically make a Location object given the position in the
    string and the length of the tokens. That Location will be given
    to f. Use this to wrap functions for use as parse actions.
    """
    def f2(self, s, loc, tokens):
        l = location.Location(s, (loc, loc + compute_length(tokens)), tokens)
        return f(self, l, [t for t in tokens if not isinstance(t, Suppressor)])
    return f2

def make_whitespace(loc):
    return ast.RawOperator(loc, '__')

def make_juxtaposition(loc):
    return ast.RawOperator(loc, '_')

def is_whitespace(op):
    return op.op in ('_', '__')


##############
### PARSER ###
##############

class Parser:

    def __init__(self, character_classes, operator_roles):

        self.character_classes = character_classes
        self.operator_roles = operator_roles
        self.string_translations = character_classes.string_translations
        self.xso, self.xsc = character_classes.ext_str

        ### Forward declarations ###
        self.expression = FW()

        ### Comments ###
        self.comment_line = ';;' + P.restOfLine
        self.comment_nested = FW()
        self.comment_nested << (';('
                                + Star(self.comment_nested
                                       | ~L(');')
                                       + N1(""))
                                + ');')
        
        self.comment = self.comment_line | self.comment_nested

        ### Identifier ###
        self.identifier = W(
            "".join(character_classes.id_lead),
            "".join(character_classes.id)).setParseAction(self.handler_identifier)

        ### Numerals ###
        _num = W(P.nums, P.nums + "_")
        _alphanum = W(P.alphanums + "_")
        _exponent = A1('eE') + (O("-") + _num).setParseAction(lambda tokens: "".join(tokens))

        self.num_radix = (G(_num + A1("rR"))
                          + G(O(_alphanum))
                          + G(O("." + O(_alphanum)))).setParseAction(self.handler_num_radix)
        self.num_decimal = ((G(_num)
                             + G(O("." + O(_num)))
                             + G(O(_exponent)))
                            | (G(E())
                               + G("." + _num)
                               + G(O(_exponent)))).setParseAction(self.handler_num_decimal)
        self.num = self.num_radix | self.num_decimal

        ### Brackets ###
        self.parens = ('(' + self.expression + ')').setParseAction(self.handler_bracketed)
        self.table = ('[' + self.expression + ']').setParseAction(self.handler_bracketed)
        self.code = ('{' + self.expression + '}').setParseAction(self.handler_bracketed)
        self.bracketed = self.parens | self.table | self.code

        ### Variable interpolation ###
        _up = character_classes.unquote

        self.vi_unit = (self.identifier | self.bracketed)
        self.vi_op = W("".join(character_classes.vi_op)).setParseAction(self.handler_vi_op)
        self.vi_group = (self.vi_unit
                         + Star(O(self.vi_op)
                                + self.vi_unit)).setParseAction(self.handler_vi_expr)
        self.vi_unquote = FW()
        self.vi_unquote << (_up
                            + (self.bracketed
                               | self.vi_group
                               | self.vi_unquote)).setParseAction(self.handler_unquote)

        ### Strings ###
        _dup = _up * 2
        _esc = character_classes.escape
        _characters = G(N1(_esc) | (_esc + N1("")))
        _characterd = G(N1(_esc + '"') | (_esc + N1("")) | '""')
        _charactern = G(N1(_esc + self.xso + self.xsc) | (_esc + N1("")))

        self.character = ("'" + _characters).setParseAction(self.handler_character)
        self.string_simple = ('"'
                              + Star(G(_dup)
                                     | self.vi_unquote
                                     | _characterd)
                              + '"').setParseAction(self.handler_string)
        self.string_nested = FW()
        self.string_nested << (self.xso
                               + Star(G(_dup)
                                      | self.vi_unquote
                                      | _charactern
                                      | self.string_nested)
                               + self.xsc).setParseAction(self.handler_string)
        self.string = self.string_simple | self.string_nested


        ### Unit ###
        self.unit = (self.identifier
                     | self.num
                     | self.character
                     | self.bracketed
                     | self.string)

        ### Operators ###
        self.class_1_op = W("".join(character_classes.op[0])).setParseAction(self.handler_op)
        self.class_2_op = W("".join(character_classes.op[1])).setParseAction(self.handler_op)
        self.list_separator = A1(character_classes.list_sep).setParseAction(self.handler_op)

        ### Whitespace ###
        _white = W(' ')
        _whitespace = _white | O(_white) + W('\\', ' ') + '\n' + O(_white)

        self.whitespace = (_whitespace).setParseAction(self.handler_whitespace)
        self.indent = Plus(W('\n', ' ')).setParseAction(self.handler_indent)


        ### Operators and operator blocks ###
        self.op = self.whitespace | self.class_1_op | self.class_2_op
        # Note: the P.NotAny(unit) is necessary to prevent an expression
        # such as "-.1" to parse as "-(.(1))" rather than the intended
        # "-(0.1)" ("." is an op, but ".1" is a unit, and we have to avoid
        # taking just "." when we should take ".1" as a
        # whole). P.NotAny(num) would work, but why not be more general
        # while we're at it?
        self.op_block = Plus(P.NotAny(self.unit)
                             + self.op).setParseAction(self.handler_op_block)


        self.invalid = N1(character_classes.valid).setParseAction(self.handler_invalid)

        ### Expression ###
        self.expression << Star(Suppr(self.comment)
                                | self.unit
                                | self.list_separator
                                | self.op_block
                                | self.indent
                                | self.invalid).setParseAction(self.handler_raw_expr)



    ################
    ### HANDLERS ###
    ################

    @auto_location
    def handler_identifier(self, t, tokens):
        [name] = tokens
        return ast.Identifier(t, name)

    @auto_location
    def handler_num_decimal(self, loc, tokens):
        [digits, decimal, exponent] = tokens
        digits = digits[0] if digits else "0"
        decimal = decimal[1] if decimal else ""
        exponent = exponent[1] if exponent else 0
        return ast.Numeral(loc, 10, digits + decimal, len(digits) + exponent)

    @auto_location
    def handler_num_radix(self, loc, tokens):
        [radix, digits, decimal] = tokens
        radix = int(radix[0])
        digits = digits[0] if digits else ""
        decimal = decimal[1] if decimal else ""
        exponent = 0
        return ast.Numeral(loc, radix, digits + decimal, len(digits))

    @auto_location
    def handler_bracketed(self, loc, tokens):
        [open, expr, close] = tokens
        if   open == '(': type = 'P'
        elif open == '[': type = 'T'
        elif open == '{': type = 'C'
        return ast.Bracketed(loc, type, expr)

    @auto_location
    def handler_unquote(self, loc, tokens):
        [uparrow, expr] = tokens
        expr.location = loc
        return expr
        # return ast.Bracketed(loc, 'U', expr)

    @auto_location
    def handler_vi_op(self, loc, tokens):
        [op] = tokens
        rop = ast.RawOperator(loc, op)
        return ast.OperatorBlock(loc, [rop])

    @auto_location
    def handler_vi_expr(self, loc, tokens):
        e = ast.RawExpr(loc, tokens)
        return self.postprocess(e)

    @auto_location
    def handler_character(self, loc, tokens):
        [single_quote, chartokens] = tokens
        if len(chartokens) == 1:
            c = chartokens[0]
            character = self.string_translations.get(c, c)
        elif len(chartokens) == 2:
            character = chartokens[1]
        return ast.StringVI(loc, [character])

    @auto_location
    def handler_string(self, loc, tokens):
        _up = self.character_classes.unquote
        _dup = _up * 2
        items = [""]
        for token in tokens[1:-1]:
            if isinstance(token, P.ParseResults):
                if token[0] == _dup:
                    character = _up
                elif len(token) == 1:
                    if token[0] == '""':
                        character = '"'
                    else:
                        c = token[0]
                        character = self.string_translations.get(c, c)
                elif len(token) == 2:
                    character = token[1]
                items[-1] += character
            elif isinstance(token, ast.StringVI):
                items[-1] += self.xso
                if isinstance(token.items[0], str):
                    items[-1] += token.items[0]
                    items += token.items[1:]
                else:
                    items += token.items
                if not isinstance(token.items[-1], str):
                    items.append("")
                items[-1] += self.xsc
            else:
                items.extend([token, ""])
        return ast.StringVI(loc, [item for item in items if item])

    @auto_location
    def handler_op(self, loc, tokens):
        [op] = tokens
        return ast.RawOperator(loc, op)

    @auto_location
    def handler_whitespace(self, loc, tokens):
        return make_whitespace(loc)

    @auto_location
    def handler_indent(self, loc, tokens):
        return ast.Indent(loc, len(tokens[-1]) - 1)

    @auto_location
    def handler_op_block(self, loc, tokens):
        return ast.OperatorBlock(loc, tokens)

    @auto_location
    def handler_raw_expr(self, loc, tokens):
        e = ast.RawExpr(loc, tokens)
        return self.postprocess(e)

    def handler_invalid(self, s, loc, tokens):
        rejections = self.character_classes.reject
        char = tokens[0]
        token = ast.ASTNode(location.Location(s, (loc, loc + 1), tokens))
        if char == '\t':
            raise QuaintSyntaxError('no_tabs', token)
        elif char in rejections:
            repl = rejections[char]
            raise QuaintSyntaxError('ambiguous_character', char, repl, token)
        else:
            raise QuaintSyntaxError('bad_character', char, token)


    ######################
    ### POSTPROCESSING ###
    ######################

    def postprocess(self, sequence):

        # Here we take care of commas and indents in order to form a
        # sequence.

        separators = [None]
        tokens = [[]]
        for prev_token, token, next_token in \
                zip([None] + sequence.items[:-1],
                    sequence.items,
                    sequence.items[1:] + [None]):

            if isinstance(token, ast.Indent):
                # Line breaks are equivalent to "," except when
                # the current line ends with an operator creating
                # a continuation with the next line (e.g. ":"), or
                # that the next line begins with an operator
                # creating a continuation from the previous line
                # (e.g. "!"). This ignores whitespace. So for
                # instance "a:\nb" is like a:b and "a\n!b" is like
                # "a!b", but "a+\nb" is like "a+,b". Normally,
                # only ":" continuates the next like and only "!"
                # continuates from the previous, but this can be
                # customized.
                consider = True
                if isinstance(prev_token, ast.OperatorBlock):
                    for operator in reversed(prev_token.operators):
                        if operator.op in self.operator_roles.cont_next:
                            consider = False
                        elif not is_whitespace(operator):
                            break
                elif isinstance(next_token, ast.OperatorBlock):
                    for operator in next_token.operators:
                        if operator.op in self.operator_roles.cont_prev:
                            consider = False
                        elif not is_whitespace(operator):
                            break
                if consider:
                    separators.append(ast.Infix(ast.RawOperator(token.location, ",")))
                    tokens.append([])

            elif isinstance(token, ast.RawOperator):
                separators.append(ast.Infix(token))
                tokens.append([])

            else:
                tokens[-1].append(token)

        new_tokens = [
            (separator,
             self.cleanup_opblocks(ast.RawExpr(location.merge_node_locations(token_list),
                                               token_list)))
            for separator, token_list in zip(separators, tokens)
            if token_list]

        def combine(current, next):
            irrelevant, current_tok = current
            next_sep, next_tok = next
            return (None, ast.OpApply(next_sep, current_tok, next_tok))

        if new_tokens:
            rval = reduce(combine, new_tokens)[1]
            # we need to readjust the location, since indents at the
            # beginning and end will have been lost
            rval.location = sequence.location
            return rval
        else:
            return ast.Void(sequence.location)

    def cleanup_opblocks(self, sequence):
        tokens = []
        last_is_opb = False
        for i, token in enumerate(sequence.items):
            if isinstance(token, ast.OperatorBlock):
                if last_is_opb:
                    tokens[-1] = ast.OperatorBlock(
                        location.merge_node_locations([tokens[-1], token]),
                        tokens[-1].operators + token.operators)
                else:
                    tokens.append(token)
                last_is_opb = True
            else:
                if i > 0 and not last_is_opb:
                    loc = location.Location(token.location.source,
                                            [token.location.start]*2, [])
                    tokens.append(ast.OperatorBlock(loc, [make_juxtaposition(loc)]))
                if tokens:
                    tokens[-1] = self.operator_fixity(tokens[-1],
                                                      len(tokens) == 1,
                                                      False)
                tokens.append(token)
                last_is_opb = False
        if tokens and last_is_opb:
            tokens[-1] = self.operator_fixity(tokens[-1],
                                              len(tokens) == 1,
                                              i == len(sequence.items) - 1)
        return self.make_expression(ast.RawExpr(sequence.location, tokens))


    def operator_fixity(self, op_block, begins, ends):

        def Gr(ops):
            return ast.OperatorBlock(op_block.location, ops)

        op_tokens = op_block.operators

        if not op_tokens:
            raise Exception('please give me at least one token...')
        elif op_tokens and all(is_whitespace(op_token) for op_token in op_tokens):
            if begins or ends:
                return Gr([]) # None
            return Gr([ast.Infix(op_tokens[0])])

        # Trim leading and trailing whitespace when they are clearly meaningless
        if begins:
            while (op_tokens and is_whitespace(op_tokens[0])):
                op_tokens = op_tokens[1:]
        if ends:
            while (op_tokens and is_whitespace(op_tokens[-1])):
                op_tokens = op_tokens[:-1]

        if begins and ends:
            # the operator is probably enclosed in brackets, e.g. (+), or
            # alone in an indent block we ban multiple operators in that
            # position, e.g. (+ *), because it's not clear at all what
            # that even means
            if len(op_tokens) > 1:
                raise QuaintSyntaxError('operator_pack',
                                          [tok for tok in op_tokens
                                           if not is_whitespace(tok)])
            this = op_tokens[0]
            #return Identifier(this.location, this.op)
            return ast.Identifier(op_block.location, this.op)

        if begins:
            # the operators are at the beginning of of a bracket or indent
            # block, e.g. (+ x ...), so they are necessarily prefix. Some
            # operators can't be prefix operators, so we raise an error if
            # they are found there.
            for op in op_tokens:
                if self.operator_roles.is_always_infix(op.op):
                    raise QuaintSyntaxError('fixity', op, "infix", "prefix")
                if self.operator_roles.is_always_postfix(op.op):
                    raise QuaintSyntaxError('fixity', op, "postfix", "prefix")
            return Gr([ast.Prefix(op)
                       for op in op_tokens
                       if not is_whitespace(op)])

        if ends:
            # the operators are at the end of of a bracket or indent
            # block, e.g. (... x +), so they are necessarily postfix. Some
            # operators can't be postfix operators, so we raise an error
            # if they are found there.
            for op in op_tokens:
                if self.operator_roles.is_always_infix(op.op):
                    raise QuaintSyntaxError('fixity', op, "infix", "postfix")
                if self.operator_roles.is_always_prefix(op.op):
                    raise QuaintSyntaxError('fixity', op, "prefix", "postfix")
            return Gr([ast.Postfix(op)
                       for op in op_tokens
                       if not is_whitespace(op)])

        # the operators are between operands on the left and right, for
        # instance x + y.

        # We check what operators can only be prefix, postfix or infix.
        prefix_indices = [i for i, op_token in enumerate(op_tokens)
                          if self.operator_roles.is_always_prefix(op_token.op)]
        postfix_indices = [i for i, op_token in enumerate(op_tokens)
                           if self.operator_roles.is_always_postfix(op_token.op)]
        infix_indices = [i for i, op_token in enumerate(op_tokens)
                         if self.operator_roles.is_always_infix(op_token.op)]

        # If the first prefix operator is located before the last operator
        # that must be infix or postfix, we're boned. Similar check for
        # the last postfix operator.
        n_prefix = len(prefix_indices)
        n_postfix = len(postfix_indices)
        n_infix = len(infix_indices)
        if (postfix_indices
            and prefix_indices
            and max(postfix_indices) > min(prefix_indices)):
            raise QuaintSyntaxError('fixity_order', op_tokens,
                                      "prefix", prefix_indices,
                                      "postfix", postfix_indices)
        elif (infix_indices
              and prefix_indices
              and max(infix_indices) > min(prefix_indices)):
            raise QuaintSyntaxError('fixity_order', op_tokens,
                                      "prefix", prefix_indices,
                                      "infix", infix_indices)
        elif (infix_indices
              and postfix_indices
              and min(infix_indices) < max(postfix_indices)):
            raise QuaintSyntaxError('fixity_order', op_tokens,
                                      "infix", infix_indices,
                                      "postfix", postfix_indices)

        # Only one infix operator may exist at once in this block.
        if n_infix > 1:
            raise QuaintSyntaxError('infix_competition', op_tokens, infix_indices)

        # Everything before the infix operator is postfix, everything
        # after is prefix.
        if infix_indices:
            j = infix_indices[0]
            rval = []
            for i, op_token in enumerate(op_tokens):
                if not is_whitespace(op_token):
                    if i < j:
                        rval.append(ast.Postfix(op_token))
                    elif i > j:
                        rval.append(ast.Prefix(op_token))
                    else:
                        rval.append(ast.Infix(op_token))
            return Gr(rval)

        last_postfix = max([-1] + postfix_indices)
        first_prefix = min([len(op_tokens) + 1] + prefix_indices)
        return Gr([ast.Postfix(op_token)
                   for i, op_token in enumerate(op_tokens)
                   if i <= last_postfix and not is_whitespace(op_token)] \
                      + self._operator_fixity(op_tokens[last_postfix + 1:first_prefix],
                                              op_block) \
                      + [ast.Prefix(op_token)
                         for i, op_token in enumerate(op_tokens)
                         if i >= first_prefix and not is_whitespace(op_token)])

    def _operator_fixity(self, op_tokens, op_block):
        if not op_tokens:
            return [ast.Infix(ast.RawOperator(op_block.location, '_'))]
        whites = [i for i, op_token in enumerate(op_tokens) if is_whitespace(op_token)]
        if len(whites) == 0:
            if len(op_tokens) != 1:
                raise QuaintSyntaxError('infix_ambiguity', op_tokens)
            return [ast.Infix(op_tokens[0])]
        elif len(whites) == 1:
            w = whites[0]
            rval = []
            for i, op_token in enumerate(op_tokens):
                if i < w:
                    rval.append(ast.Postfix(op_token))
                elif i > w:
                    rval.append(ast.Prefix(op_token))
                else:
                    rval.append(ast.Infix(op_token))
            return rval
        elif len(whites) == 2:
            if whites[1] != whites[0] + 2:
                these_tokens = [token for token in op_tokens if not is_whitespace(token)]
                raise QuaintSyntaxError('infix_ambiguity', these_tokens)
            w = whites[0] + 1
            rval = []
            for i, op_token in enumerate(op_tokens):
                if i < w-1:
                    rval.append(ast.Postfix(op_token))
                elif i > w+1:
                    rval.append(ast.Prefix(op_token))
                elif i == w:
                    rval.append(ast.Infix(op_token))
            return rval
        else:
            these_tokens = [token for token in op_tokens if not is_whitespace(token)]
            raise QuaintSyntaxError('infix_ambiguity', these_tokens)


    def make_expression(self, sequence):
        orig_sequence = sequence

        _sequence = list(sequence.items)
        sequence = []
        for item in _sequence:
            if isinstance(item, ast.OperatorBlock):
                sequence.extend(item.operators)
            else:
                sequence.append(item)

        # One for each ID node (OpApply nodes will be added when they are completed)
        # (node, start_index, end_index)
        sub_expressions = [(element, i, i+1) for i, element in enumerate(sequence)
                           if not isinstance(element, ast.Operator)]

        # One for each Op (In/Pre/Postfix)
        # (op_index, [Op, left_expression, right_expression])
        partials = dict((i, [element, None, None]) for i, element in enumerate(sequence)
                        if isinstance(element, ast.Operator))

        if not partials:
            if not sub_expressions:
                #return Void(merge_node_locations([]))
                return Void(orig_sequence.location)
            elif len(sub_expressions) == 1:
                return sub_expressions[0][0]
            else:
                raise Exception('what', sub_expressions)

        while True:
            # We will fit one of the sub expressions to some Op
            expr, start, end = sub_expressions.pop()

            # We fetch the left Op and the right Op, watching for the
            # sequence boundaries. They are simply the tokens before and
            # after the start and end tokens of the expression (end is
            # exclusive).
            left = sequence[start-1] if start else None
            right = sequence[end] if end < len(sequence) else None

            # Prefix and Postfix ops can only take expressions on one side
            if isinstance(left, ast.Postfix): left = None
            if isinstance(right, ast.Prefix): right = None
            if left is None and right is None:
                raise Exception("The expression cannot be tied to either the left or right operator. This should not happen.")

            # target = (receiver op index, 1 if left operand of the
            # receiver op, 2 if right operand)
            if left is None:
                # The current expression must be the left operand of
                # the op to the right
                (target, dest) = (end, 1)
            elif right is None:
                # The current expression must be the right operand of
                # the op to the left
                (target, dest) = (start-1, 2)
            else:
                # There's an operator on both sides, so we check for priority
                # ord = -1 if the left operator has higher priority
                # ord =  0 if the left operator cannot mingle with the right operator
                # ord =  1 if the right operator has higher priority
                ord = self.operator_roles.op_order.op_order(left, right)
                if not ord:
                    # These operators cannot mingle
                    raise QuaintSyntaxError('priority', left, right)
                (target, dest) = (start-1, 2) if ord == -1 else (end, 1)

            # We put the expression where it belongs
            partials[target][dest] = (expr, start, end)

            # Now we check if the "partial" node is complete (has all its
            # operands). If it is complete, we remove it from the partial
            # dictionary and we add it to sub_expressions so that it can
            # be the operand of another operator. We compute the start and
            # end boundaries of the completed expression.
            elem, left_expr, right_expr = partials[target]

            if isinstance(elem, ast.Infix) and left_expr and right_expr:
                # Infix operators must have both left and right operands filled
                partials.pop(target)
                x = (elem, left_expr[0], right_expr[0])
                sub_expressions.append((x, left_expr[1], right_expr[2]))

            if isinstance(elem, ast.Prefix) and right_expr:
                # Prefix operators must have right operand filled only
                partials.pop(target)
                x = (elem, None, right_expr[0])
                sub_expressions.append((x, target, right_expr[2]))

            if isinstance(elem, ast.Postfix) and left_expr:
                # Postfix operators must have left operand filled only
                partials.pop(target)
                x = (elem, left_expr[0], None)
                sub_expressions.append((x, left_expr[1], target+1))

            # If the partials list is empty, we just completed the top
            # level expression, and that expression is in the variable x.
            if not partials:
                break

        def transform(x):
            if isinstance(x, tuple):
                op, left, right = x
                return ast.OpApply(op, transform(left), transform(right))
            return x

        return transform(x)
    

    #############
    ### PARSE ###
    #############

    def parse1(self, code):
        return self.expression.parseWithTabs().parseString(code)[0]

    def parse2(self, code):
        e = self.parse1(code)
        e = Convert2().visit(ast.Bracketed(e.location, "P", e))
        return e

    # def parse3(self, code):
    #     e = self.parse2(code)
    #     e = Convert3().visit(e)
    #     return e

    def parse(self, code):
        return self.parse2(code)

    # def parse(self, code):
    #     return self.expression.parseWithTabs().parseString(code)[0]



class Convert2(ast.ASTVisitor):

    def do_collapse(self, op):
        return op in (ast.Infix(","), ast.Infix("_"), ast.Infix("__"))

    def visit_OpApply(self, node):
        # operator = self.visit(node.operator)
        operator = node.operator
        children = map(self.visit, node.children)
        if self.do_collapse(operator):
            a, *b = children
            if isinstance(a, ast.OpApply) and a.operator == operator:
                return ast.OpApply(operator, *(a.children + b), location = node.location)
            else:
                return ast.OpApply(operator, a, *b, location = node.location)
        return ast.OpApply(operator, *children, location = node.location)

    def visit_Bracketed(self, node):
        expr = self.visit(node.expression)
        if isinstance(expr, ast.OpApply) and expr.operator == ast.Infix(","):
            items = expr.children
        elif isinstance(expr, ast.Void):
            items = []
        else:
            items = [expr]
        if node.type == 'P':
            return ast.Sequence(node.location, items)
        if node.type == 'T':
            return ast.Table(node.location, items)
        if node.type == 'C':
            return ast.Code(node.location, items)
        raise Exception("Not handled: %s - %s" % (node, node.type))

    def visit_StringVI(self, node):
        items = map(self.visit, node.items)
        return ast.StringVI(node.location, items)

    def visit_Identifier(self, node):
        return node

    def visit_Numeral(self, node):
        return node

    # def visit_Operator(self, node):
    #     return node

    def visit_Void(self, node):
        return node

    def visit_ASTNode(self, node):
        raise Exception("This node type is not handled: %s" % type(node))


# class Convert3(ast.ASTModifier):

#     def visit_OpApply(self, node):
#         super().visit_OpApply(node)
#         if node.operator == ast.Infix(":"):
            
#         else:
#             return node


#################
### DEAD CODE ###
#################


# This was for when indentation was significant. Not useful anymore.

    # def convert_indent(self, sequence):

    #     tokens = [[]]
    #     levels = []
    #     items = sequence.items
    #     last_indents = []
    #     while items and isinstance(items[-1], ast.Indent):
    #         last_indents.append(items.pop())

    #     ##loc = merge_node_locations(last_indents or (items and items[-1:]))
    #     ##items.append(ast.Indent(loc, -1))
    #     loc = location.merge_node_locations(last_indents)    
    #     items.append(ast.Indent(loc, -1))
    #     for token in items:
    #         if isinstance(token, ast.Indent):
    #             # if not levels:
    #             if True or not levels: # SIGNIFICANT INDENT TURNED OFF
    #                 levels.append(token.level)
    #                 tokens[-1].append(ast.RawOperator(token.location, "BREAK"))
    #             else:
    #                 level = token.level
    #                 if level > levels[-1]:
    #                     levels.append(level)
    #                     tokens.append([token])
    #                 elif level < levels[-1]:
    #                     while levels and level != levels[-1]:
    #                         levels.pop()
    #                         if not levels and level >= 0:
    #                             raise indent_error()
    #                         if len(tokens) > 1:
    #                             new_raw = tokens.pop()
    #                             loc = location.merge_node_locations(new_raw)
    #                             tokens[-1].append(ast.Bracketed(loc, 'I',
    #                                                             self.cleanup_opblocks(self.convert_commas(ast.RawExpr(loc, new_raw[1:])))))
    #                             tokens[-1].append(ast.RawOperator(token.location, "BREAK"))
    #                 else:
    #                     tokens[-1].append(ast.RawOperator(token.location, "BREAK"))
    #         else:
    #             tokens[-1].append(token)

    #     return ast.RawExpr(sequence.location, tokens[0])
