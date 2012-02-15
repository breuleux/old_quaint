
# from colonel import core, lib
# from ..parse import parser, CanonVisitor

import exc
from exc import Exception as E

from colonel import core, lib
from colonel.core import *
from colonel.lib import *
from colonel.standard import *
from colonel.tools.svg import Span

from quaint.parse import parser, encode, decode
from quaint.parse.generic.ast import Canon, CanonVisitor, CanonModifier, Meta


def oper_check(node):
    oper, value = node.arguments
    assert (value.command == 'syntax'
            and value.arguments[0].command == 'begin'
            # and len(value.arguments[0].arguments) == 2
            and oper.command == 'symbol')
    return oper, value

def oper_as_function(node, visit):
    node.arguments = list(map(visit, node.arguments))
    oper, value = oper_check(node)
    new_value = Canon(value.meta, 'table', *value.arguments[0].arguments)
    node.arguments = [oper, new_value]
    return node

def dot(node, visit):
    node.arguments = list(map(visit, node.arguments))
    oper, value = oper_check(node)
    new_value = Canon(value.meta, 'quote', value.arguments[0].arguments[1])
    return new_value

def dotdot(node, visit):
    node.arguments = list(map(visit, node.arguments))
    oper, value = oper_check(node)
    new_value = Canon(value.meta, 'syntax', value.arguments[0].arguments[1])
    return new_value

def tilde(node, visit):
    oper, value = oper_check(node)
    m1, *m2 = value.arguments[0].arguments
    op1, v1 = oper_check(m1)
    assert (op1.arguments[0] in [':', '~'])
    new_value = m1
    synt = v1.arguments[0]
    synt.arguments = synt.arguments + list(m2)

    if op1.arguments[0] == '~':
        return tilde(new_value, visit)
    else:
        new_value = visit(new_value)
        return new_value


class Colon:

    def process(self, node, visit):
        name, args = self.extract_colon_spec(node)
        return getattr(self, 'fn_' + name)(node, args, visit)
        # args = list(map(visit, args))
        # return Canon(node.meta, name, *args)

    def extract_colon_spec(self, node):
        oper, value = oper_check(node)
        args = value.arguments[0].arguments
        name = args[0].arguments[0]
        new_args = args[1:]
        if not isinstance(name, str):
            name = args[0].arguments[0].arguments[0]
            new_args.insert(0, args[0].arguments[1])
        return name, new_args

    def fn_if(self, node, args, visit):
        condition, iftrue, *rest = args
        # iftrue = args[1]
        if len(rest) == 0:
            iffalse = Canon(Meta(None, None), 'void')
        else:
            statement = rest[0]
            word, subargs = self.extract_colon_spec(statement)
            if word == 'else':
                assert len(subargs) == 1
                assert len(rest) == 1
                iffalse = subargs[0]
            elif word == 'elif':
                iffalse = self.fn_if(statement, subargs + rest[1:], visit)
            else:
                raise E['if/wrong_syntax']('Expected else or elif.')

        return Canon(node.meta, 'if',
                     visit(condition),
                     visit(iftrue),
                     visit(iffalse))

    def fn_lambda(self, node, args, visit):
        arguments, body = args
        parameters = []
        for arg in arguments.arguments:
            assert arg.command == 'symbol'
            parameters.append(arg.arguments[0])
        return Canon(node.meta, 'lambda',
                     parameters,
                     visit(body))
        
colon = Colon()



class StaticExpr(CanonModifier):

    def __init__(self, operators):
        self.operators = operators

    def visit_apply(self, node):
        oper, value = node.arguments
        if oper.command == 'symbol':
            if oper.arguments[0] in self.operators:
                rval = self.operators[oper.arguments[0]](node, self.visit)
                return rval
        node.arguments = list(map(self.visit, node.arguments))
        return node



def htmlify(x):
    s = str(x)
    for orig, repl in [(" ", "&nbsp;"),
                       ("<", "&lt;"),
                       (">", "&gt;"),
                       ('"', "&quot;")]:
        s = s.replace(orig, repl)
    return s

def convert_html(x):
    if isinstance(x, Canon):
        return x.str_html(convert_html)
    else:
        return "<span>" + htmlify(x) + "</span>"

def presc(x):
    print("\x1B[?0y{x}".format(x = str(x).replace('\n', '')))

class PrettyPrinter:

    def __init__(self, css):
        self.css = css

    def printout(self, node):
        s = self.pr(node)
        presc('+h')
        for key, style in self.css.items():
            presc("/h style {key} {{ {style} }}".format(
                    key = key,
                    style = style))
        presc(':h <div style="padding: 10px">{x}</div>'.format(x = s))

    def pr(self, node):
        if not isinstance(node, Canon):
            return htmlify(node)
        command = node.command
        args = node.arguments
        try:
            printer = getattr(self, 'pr_' + command, None)
            if printer:
                return printer(node, *args)
        except TypeError:
            pass
        return self.pr_default(node, *args)

    def pr_default(self, node, *args):
        command = node.command
        rval = Span(command)
        rval.extend(map(self.pr, args))
        return rval

    def pr_symbol(self, node, name):
        return Span(htmlify(name),
                    class_ = "symbol")

    def pr_value(self, node, value):
        return Span(htmlify(repr(value)),
                    class_ = "value")

    def pr_apply(self, node, fn, arg):
        return Span(self.pr(fn),
                    Span(class_ = 'apply-sep'),
                    self.pr(arg),
                    class_ = 'apply')

    def pr_begin(self, node, *args):
        span = Span(class_ = 'begin-inner')
        span.extend([Span(self.pr(arg), class_ = 'begin-cell')
                     for arg in args])
        return Span(span, class_ = 'begin')

    def pr_syntax(self, node, arg):
        return Span(self.pr(arg),
                    class_ = 'syntax')

    def pr_table(self, node, *args):
        if not args:
            return Span('&nbsp', class_ = 'table')
        span = Span(class_ = 'table-inner')
        span.extend([Span(self.pr(arg), class_ = 'table-cell')
                     for arg in args])
        return Span(span, class_ = 'table')

    def pr_void(self, node):
        return Span('∅', class_ = 'void')


    def pr_quote(self, node, arg):
        if arg.command == 'symbol':
            return Span(htmlify(arg.arguments[0]),
                        class_ = "quoted-symbol")
        else:
            return Span(self.pr(arg),
                        class_ = 'quote')

    def pr_if(self, node, cond, iftrue, iffalse):
        return Span(Span(self.pr(cond), class_ = 'if-cond'),
                    Span(self.pr(iftrue), class_ = 'if-true'),
                    Span(class_ = 'if-sep'),
                    Span(self.pr(iffalse), class_ = 'if-false'),
                    class_ = 'if')

    def pr_lambda(self, node, parameters, body):
        rval = Span(Span("λ", class_ = 'lambda-chr'),
                    class_ = 'lambda')
        rval.extend(Span(name, class_ = 'lambda-param')
                    for name in parameters)
        rval.append(Span(".", class_ = 'lambda-sep'))
        rval.append(Span(self.pr(body), class_ = 'lambda-body'))
        return rval
                    
                    
def union_all(seq):
    rval = set()
    for s in seq:
        rval.update(s)
    return rval

class FreeVariables(CanonVisitor):

    def __init__(self):
        self.mapping = {}

    def assign(self, node, s):
        self.mapping[node] = s
        return s

    def visit(self, node):
        if node in self.mapping:
            return self.mapping[node]
        rval = super().visit(node)
        self.mapping[node] = rval
        return rval

    def visit_symbol(self, node):
        return {node.arguments[0]}

    def visit_value(self, node):
        return set()

    def visit_apply(self, node):
        return union_all(map(self.visit, node.arguments))

    def visit_begin(self, node):
        return union_all(map(self.visit, node.arguments))

    def visit_table(self, node):
        return union_all(map(self.visit, node.arguments))

    def visit_if(self, node):
        return union_all(map(self.visit, node.arguments))



class CircuitMaker(CanonVisitor):

    def __init__(self, inputs, constants):
        self.inputs = inputs
        self.constants = constants
        self.id = 0
        self.operators = {}
        self.connections = []
        self.referrers = {}
        for inp in inputs:
            self.create_referrer(inp, inp)

        # self.env_uses = 0
        # self.n_err = 1

    def nextid(self):
        self.id += 1
        return self.id

    def create_operator(self, prefix, operator):
        name = "{pfx}{id}".format(prefix = prefix,
                                  id = self.nextid())
        self.operators[name] = operator
        return name

    def create_constant(self, ct):
        return self.create_operator('ct', Constant(ct))

    def create_referrer(self, sym, anchor):
        distr = self.create_operator('distr', [Distribute, 0])
        self.connections.append((anchor, distr + '.input'))
        self.referrers[sym] = distr
        # return distr

    def dup_symbol(self, sym):
        if sym not in self.referrers:
            if sym in self.constants:
                name = self.create_constant(self.constants[sym])
                self.create_referrer(sym, name + ".out")
                # distr = self.create_operator([Distribute, 0])
                # self.connections.append(name + '.out',
                #                         distr + '.in')
                # self.referrers[sym] = distr
            else:
                raise E['free_variable'](
                    'There is no support for free variables at the moment.')

        distr_name = self.referrers[sym]
        distributor = self.operators[distr_name]
        n = distributor[1]
        distributor[1] += 1
        return "{d}.o{n}".format(d = distr_name, n = n)

    def visit_value(self, node):
        name = self.create_constant(node.arguments[0])
        return dict(output = name+".out")

    def visit_symbol(self, node):
        targ = self.dup_symbol(node.arguments[0])
        return dict(output = targ)

    def create_operator(self, prefix, operator):
        name = "{prefix}{id}".format(prefix = prefix,
                                     id = self.nextid())
        self.operators[name] = operator
        return name

    def visit_apply(self, node):
        fn = node.arguments[0]
        if fn.command == 'symbol':
            sym = fn.arguments[0]
            if sym not in self.constants:
                raise E['fn_not_constant']('For the time being, functions must be constant')
            gate, input_names, out_name = self.constants[sym]
        else:
            fn = self.visit(fn)
            gate, input_names, out_name = fn['gate']
        gate_name = self.create_operator(gate.name, gate)

        args = map(self.visit, node.arguments[1].arguments)

        for portmap, port_name in zip(args, input_names):
            # self.connections.append((gate_name + "." + port_name,
            #                          portmap['output']))
            self.connections.append((portmap['output'],
                                     gate_name + "." + port_name))
        return dict(output = gate_name+".out")

    def visit_if(self, node):
        cond, iftrue, iffalse = map(self.visit, node.arguments)
        name = self.create_operator('if', IfThenElse)
        self.connections += [(cond['output'], '{name}.cond'.format(name = name)),
                             (iftrue['output'], '{name}.iftrue'.format(name = name)),
                             (iffalse['output'], '{name}.iffalse'.format(name = name))]
        return dict(output = name+'.out')

    def visit_void(self, node):
        name = self.create_constant(None)
        return dict(output = name+".out")

    def visit_lambda(self, node):
        parameters, body = node.arguments
        cm = CircuitMaker(parameters, self.constants)
        circ = cm.create('circ{id}'.format(id = self.nextid()),
                         body)
        return dict(gate = (circ, parameters, 'out'))

    def create(self, name, node):

        def make_incomplete(k, op):
            if isinstance(op, list):
                constructor, n = op
                if constructor is Distribute and n == 1:
                    i = '{k}.input'.format(k = k)
                    r = '{k}.o0'.format(k = k)
                    src = rconnd[i]
                    targ = connd[r]
                    self.connections.remove((src, i))
                    self.connections.remove((r, targ))
                    self.connections.append((src, targ))
                return constructor(n)
            else:
                return op

        result = self.visit(node)
        connd = dict(self.connections)
        rconnd = {y: x for x, y in self.connections}

        ports = self.inputs + ['out']
        gates = {k: make_incomplete(k, op)
                 for k, op in self.operators.items()}
        self.connections.append(('out', result['output']))
        connections = self.connections
        return CircuitSpec(name = name,
                           ports = ports,
                           gates = gates,
                           connections = connections)

# F = CircuitSpec(
#     name = 'F',
#     ports = ['env', 'out', 'error'],
#     gates = v.operators,
#     connections = v.connections
#     )











# class V(CanonVisitor):

#     def __init__(self):
#         self.operators = {}
#         self.connections = []
#         self.id = 0
#         self.env_uses = 0
#         self.n_err = 1

#     def visit_value(self, node):
#         ct = Constant(node.all[2])
#         name = "ct{id}".format(id = self.id)
#         self.operators[name] = ct
#         self.id += 1
#         return (name+".out", None)

#     def visit_symbol(self, node):

#         gate = abstract_agent
#         gate_name = "aa{id}".format(id = self.id)
#         self.operators[gate_name] = gate
#         self.id += 1

#         ct = Constant(node.all[2])
#         ct_name = "ct_{name}{id}".format(name = node.all[2], id = self.id)
#         self.operators[ct_name] = ct
#         self.id += 1

#         gct = Constant("get")
#         gct_name = "gct{id}".format(id = self.id)
#         self.operators[gct_name] = gct
#         self.id += 1

#         edges = """
#         env_distr.o{uses} -> {g}.gate
#         {ct}.out          -> {g}.select
#         {gct}.out         -> {g}.in_command
#         {g}.error         -> neck.i{errs}
#         """.format(uses = self.env_uses,
#                    ct = ct_name,
#                    gct = gct_name,
#                    g = gate_name,
#                    errs = self.n_err)

#         edges = [[x.strip() for x in line.split("->")]
#                  for line in edges.split("\n")
#                  if line.strip()]

#         self.env_uses += 1
#         self.n_err += 1
                   
#         self.connections += edges

#         return (gate_name+".out", gate_name+".error")

#     def visit_apply(self, node):

#         applicator = self.visit(node[2])
#         argument = self.visit(node[3])

#         gate = abstract_agent
#         gate_name = "aa{id}".format(id = self.id)
#         self.operators[gate_name] = gate
#         self.id += 1

#         gct = Constant("get")
#         gct_name = "gct{id}".format(id = self.id)
#         self.operators[gct_name] = gct
#         self.id += 1

#         edges = """
#         {appout}   -> {aa}.gate
#         {argout}   -> {aa}.select
#         {gct}.out  -> {aa}.in_command
#         {aa}.error -> neck.i{errs}
#         """.format(appout = applicator[0],
#                    argout = argument[0],
#                    gct = gct_name,
#                    aa = gate_name,
#                    errs = self.n_err)
#         edges = [[x.strip() for x in line.split("->")]
#                  for line in edges.split("\n")
#                  if line.strip()]

#         self.n_err += 1

#         self.connections += edges

#         return (gate_name+".out", gate_name+".error")

#     def visit_table(self, node):
#         length = len(node.all[2:])

#         joiner = Join(length)
#         name = "J{id}".format(id = self.id)
#         self.operators[name] = joiner
#         self.id += 1

#         results = [self.visit(x) for x in node.all[2:]]

#         self.connections += [
#             (result[0], '{J}.i{i}'.format(J = name, i = i))
#             for i, result in enumerate(results)
#             ]

#         return (name+".out", name+".err")

#     # def visit_begin(self, node):
#     #     node.all[2:] = list(map(self.visit, node.all[2:]))
#     #     return node

#     # def visit_syntax(self, node):
#     #     node.all[2:] = list(map(self.visit, node.all[2:]))
#     #     return node
