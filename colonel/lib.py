
from .core import CommonGateSpec, FunctionGateSpec, VOID, REQ, AVAIL, MPVMException
from .tools import dmergei


##################
### Distribute ###
##################

class Distribute(CommonGateSpec):
    """
    Returns a gate with one input port and n output ports. The data
    provided as input is retransmitted from all output ports (in other
    words, this gate allows data to go from one port to many others).
    """

    def __init__(self, n):
        self.result_names = ['o{i}'.format(i = i)
                        for i in range(n)]

        deps_map = dmergei({(): {}},
                           {(name, REQ): {'input': REQ}
                            for name in self.result_names})

        super().__init__(
            name = '{n}X'.format(n = n),
            ports = ['input'] + self.result_names,
            starter = lambda: (0, None),
            deps_map = deps_map,
            triggers = [({'input': AVAIL, name: REQ}, self.do)
                        for name in self.result_names],
            description = """
            Outputs 'input' in 'rX', X ranging from 0 to {n}.
            """.format(n = n-1))

    def do(self, state, input):
        return ((0, None),
                {name: input for name in self.result_names},
                {0})


# def Distribute(n):
#     """
#     Returns a gate with one input port and n output ports. The data
#     provided as input is retransmitted from all output ports (in other
#     words, this gate allows data to go from one port to many others).
#     """
#     result_names = ['o{i}'.format(i = i)
#                     for i in range(n)]

#     def do(state, input):
#         return ((0, None),
#                 {name: input for name in result_names},
#                 {0})

#     deps_map = dmergei({(): {}},
#                        {(name, REQ): {'input': REQ}
#                         for name in result_names})

#     return CommonGateSpec(
#         name = '{n}X'.format(n = n),
#         ports = ['input', 'error'] + result_names,
#         starter = lambda: (0, None),
#         deps_map = deps_map,
#         triggers = [({'input': AVAIL, name: REQ}, do)
#                     for name in result_names],
#         description = """
#         Outputs 'input' in 'rX', X ranging from 0 to {n}.
#         """.format(n = n-1))



##################
### IfThenElse ###
##################

def if_do(state, cond = VOID, iftrue = VOID, iffalse = VOID):
    # Careful about the arguments: normally, only one of cond, iftrue
    # and iffalse is not going to be VOID, and it depends on the value
    # of the flow state, state[0], below. See also: IfThenElse.deps_map.
    fs = state[0]
    if fs == 0:
        # We are checking the condition. If the condition is true, we
        # will place ourselves in state 1, and the next time we
        # propagate we will ask for iftrue. If the condition is false,
        # we get state 2, and we will fetch iffalse.
        fs = 1 if cond else 2
        ret = VOID     # there is no output yet
        consumed = {0} # consume the condition (port #0)
    elif fs == 1:
        # The condition was true in the previous run. Return iftrue.
        fs = 0         # return to state 0 (next condition)
        ret = iftrue   # output iftrue
        consumed = {1} # consume iftrue (port #1)
    elif fs == 2:
        # The condition was false in the previous run. Return iffalse.
        fs = 0         # return to state 0 (next condition)
        ret = iffalse  # output iffalse
        consumed = {2} # consume iffalse (port #2)
    else:
        raise MPVMException['if/badstate'](
            "IfThenElse should not have internal"
            " state other than 0, 1 or 2...",
            )
    return ((fs, None),
            dict(out = ret),
            consumed)

IfThenElse = CommonGateSpec(
    name = 'if',
    ports = ['cond', 'iftrue', 'iffalse', 'out', 'error'],
    starter = lambda: (0, None),    # initialize to state 0 (the second element is unused)
    deps_map = {(): {},
                (0, 'out', REQ): {0: REQ},  # state 0 -> ask for condition
                (1, 'out', REQ): {1: REQ},  # state 1 -> ask for iftrue
                (2, 'out', REQ): {2: REQ}}, # state 2 -> ask for iffalse
    triggers = [(0, {'out': REQ, 'cond': AVAIL}, if_do),
                (1, {'out': REQ, 'iftrue': AVAIL}, if_do),
                (2, {'out': REQ, 'iffalse': AVAIL}, if_do)],
    description = """
    IfThenElse implements a lazy If. It works as follows: first, we
    are in state 0 and we request the condition. Depending on whether
    the condition is true or false, we go to state 1 or 2. State 1
    requests the computation of the true branch, state 2 requests that
    of the false branch. The other branch is left unrequested, and
    thus its associated computations are not performed. The
    appropriate result is returned when available.
    """)



##################
### EitherOnce ###
##################

def EitherOnce(n):
    """
    EitherOnce(n) has n inputs and n outputs.

    As soon as some input (let's say it is input #j) is available,
    EitherOnce lets it through (to output #j in this case), and then
    ceases emitting input requests.

    For instance, i0 might be a function's output and i1 might be the
    error. If the output arrives in i0, then EitherOnce transmits it
    to r0 and never asks anything else. Ditto if the error arrives in
    i1 (transmitted to r1). So for instance if there is an error, this
    gate will cut off the computation of the output (that is, it will
    stop the parts that can still run from doing any more work).
    """

    # TODO: add a reset port to revert to state 0

    inames = ['i{i}'.format(i = i) for i in range(n)]
    onames = ['o{i}'.format(i = i) for i in range(n)]

    def do(state, **args):
        for i in range(n):
            iname = 'i{i}'.format(i = i)
            if args[iname] is not VOID:
                return ((1, None),
                        {iname.replace('i', 'o'): args[iname]},
                        range(n))
        raise MPVMException['commongate/no_input'](
            "The Either gate instance {this} is not supposed to get"
            " called if there is no available input!",
            this = rval
            )

    deps_map = {(): {},
                (1,): {}}
    for i in range(n):
        oname = 'o{i}'.format(i = i)
        iname = 'i{i}'.format(i = i)
        deps_map[(0, oname, REQ)] = {iname: REQ}

    rval = CommonGateSpec(
        name = 'Ei{n}'.format(n = n),
        ports = inames + onames,
        starter = lambda: (0, None),    # initialize to state 0 (the second element is unused)
        deps_map = deps_map,
        triggers = [({oname: REQ, iname: AVAIL}, do)
                    for oname, iname in zip(onames, inames)],
        description = EitherOnce.__doc__)

    return rval



# #################
# ### ResetPool ###
# #################

# def ResetPool(n):
#     """
#     ResetPool(n) has 2n+2 ports. One "reset_in" port, one "reset_out"
#     ports, n numbered "inner#" ports and n corresponding "outer#"
#     ports.

#     Everything going out of "innerX" is transferred to "outerX", and
#     everything going in "outerX" is transferred to "innerX".

#     If a value is made available through the "reset_in" port, it is
#     sent through the "reset_out" port, and a unique RESET token is
#     created and sent through all "inner#" ports. RESET tokens other
#     than that unique token are sent back and forth "innerX" and
#     "outerX".
#     """

#     inners = ['inner{i}'.format(i = i) for i in range(n)]
#     outers = ['outer{i}'.format(i = i) for i in range(n)]

#     def do(state, **args):
#         if state[0] == 0:
#             transfers = {}
#             for i in range(n):
#                 iname = 'inner{i}'.format(i = i)
#                 oname = 'inner{i}'.format(i = i)
#                 if iname in args:
#                     transfers[oname] = args[iname]
#                 if oname in args:
#                     transfers[iname] = args[oname]
#             if 'reset_in' in args:
#                 transfers['reset_out'] = args['reset_in']
#                 state = (1, None)
#             return (state, transfers, range(2*n + 2))
#         else:
#             return ((0, None), {}, set())

#     all_ports = inners + outers + ['reset_in', 'reset_out']

#     deps_map = {(): {},
#                 (1,): {}}
#     for i in range(n):
#         oname = 'o{i}'.format(i = i)
#         iname = 'i{i}'.format(i = i)
#         deps_map[(0, oname, REQ)] = {iname: REQ}

#     rval = CommonGateSpec(
#         name = 'RESET{n}'.format(n = n),
#         ports = all_ports,
#         functions = [({name: REQ for name in all_ports}, do)],
#         starter = lambda: (0, None),    # initialize to state 0 (the second element is unused)


#         deps_map = ([((), {}), # also goes for state 1
#                      ((1,), {})]    # state 1 -> ask for nothing
#                     + [((0, 'o{i}'.format(i = i), REQ), {'i{i}'.format(i = i): REQ})
#                        for i in range(n)]), # state 0 -> ask for corresponding input
#         trigger_policy = 'one_in',
#         triggers = None,
#         description = EitherOnce.__doc__)

#     return rval



# ##############
# ### Cutter ###
# ##############

# ## !!! UNTESTED !!!
# def cutter_do(state, input = VOID, switch = VOID):
#     if switch is not VOID:
#         if switch:
#             return ((1, None), {'out': input}, {0, 1})
#         else:
#             return ((0, None), {}, {0, 1})
#     if state[0]:
#         return ((1, None), {'out': input}, {0})
#     else:
#         return ((0, None), {}, {0})

# Cutter = CommonGateSpec(
#     name = 'Cut',
#     ports = ['input', 'switch', 'out'],
#     functions = [({'input': REQ, 'switch': REQ}, cutter_do)],
#     starter = lambda: (1, None),    # initialize to state 1 (the second element is unused)
#     deps_map = {(): {'switch': REQ},
#                 (0,): {'switch': REQ},
#                 (1, 'out', REQ): {'input': REQ, 'switch': REQ}},
#     trigger_policy = 'one_in',
#     triggers = None,
#     description = """
#     If switch = 1, the input is wired to out. If switch = 0,
#     the input is never requested; switch is always requested.
#     """)



##################
### Bottleneck ###
##################

class Bottleneck(CommonGateSpec):
    """
    Bottleneck(n) has n inputs and one output ('out'). All inputs are
    requested if out is requested. If any input arrives, it will be
    sent to the output port, and so on.

    The Bottleneck gate can be used to output sequentially inputs that
    arrive in parallel (IMPORTANT: the order of the sequence depends
    on the order in which inputs arrive).
    """

    def __init__(self, n):
        self.n = n

        self.inames = ['i{i}'.format(i = i) for i in range(n)]

        super().__init__(
            name = 'Bo{n}'.format(n = n),
            ports = self.inames + ['out'],
            starter = lambda: (0, None), # state is not used
            deps_map = {(): {},
                        ('out', REQ): {i: REQ for i in range(n)}},
            triggers = [({'out': REQ, name: AVAIL}, self.do)
                        for name in self.inames],
            description = Bottleneck.__doc__)

    def do(self, state, **args):
        for i in range(self.n):
            iname = 'i{i}'.format(i = i)
            if args[iname] is not VOID:
                return ((1, None),
                        {'out': args[iname]},
                        {i})
        raise MPVMException['commongate/no_input'](
            "The Bottleneck gate instance {this} is not supposed to get"
            " called if there is no available input!",
            this = rval
            )



# def Bottleneck(n):
#     """
#     Bottleneck(n) has n inputs and one output ('out'). All inputs are
#     requested if out is requested. If any input arrives, it will be
#     sent to the output port, and so on.

#     The Bottleneck gate can be used to output sequentially inputs that
#     arrive in parallel (IMPORTANT: the order of the sequence depends
#     on the order in which inputs arrive).
#     """

#     inames = ['i{i}'.format(i = i) for i in range(n)]

#     def do(state, **args):
#         for i in range(n):
#             iname = 'i{i}'.format(i = i)
#             if args[iname] is not VOID:
#                 return ((1, None),
#                         {'out': args[iname]},
#                         {i})
#         raise MPVMException('commongate/no_input')(
#             "The Bottleneck gate instance {this} is not supposed to get"
#             " called if there is no available input!",
#             this = rval
#             )

#     rval = CommonGateSpec(
#         name = 'Bo{n}'.format(n = n),
#         ports = inames + ['out'],
#         starter = lambda: (0, None), # state is not used
#         deps_map = {(): {},
#                     ('out', REQ): {i: REQ for i in range(n)}},
#         triggers = [({'out': REQ, name: AVAIL}, do)
#                     for name in inames],
#         description = Bottleneck.__doc__)

#     return rval



################
### Sequence ###
################

def Sequence(n):
    """
    Sequence(n) has n inputs (i0, i1, ..., iN) and one output
    ('out'). Sequence(n) will first request i0 (and only i0). Then,
    when i0 is obtained, it will request i1, and so on, until iN,
    which is transmitted as the output of the gate.

    This effectively guarantees that the subgraph corresponding to
    each input is computed after the one for the previous
    input. Sequence can be used in conjunction with Duplicator to
    implement applicative order (duplicate the result of each
    expression, feed r0 to Sequence in order of their evaluation and
    r1 to where it is used, and so on, and feed the final expression
    to i(n-1)).
    """

    inames = ['i{i}'.format(i = i) for i in range(n)]

    def do(state, **args):
        currentn = state[0]
        # This is the current input, the one we just requested
        current = 'i{i}'.format(i = currentn)
        # We update the state to the next (which will cause the next
        # input to be requested, as per deps_map). If this was the
        # last input, we return it via the out port. We consume
        # (discard) the input we requested.
        return (((currentn + 1) % n, None),
                {'out': args[current] if currentn == n-1 else VOID},
                {current})

    deps_map = {(): {}}
    for i in range(n):
        # Each state corresponds to an input to request:
        deps_map[(i, 'out', REQ)] = {i: REQ}

    return CommonGateSpec(
        name = 'Seq{n}'.format(n = n),
        ports = inames + ['out'],
        starter = lambda: (0, None), # second part of state is not used
        deps_map = deps_map,
        triggers = [(i, {'out': REQ, i: AVAIL}, do)
                    for i in range(n)],
        description = Sequence.__doc__)



################
### Constant ###
################

def Constant(x):
    """
    Constant(x) has no input ports. It always returns x.
    """

    do = lambda state: (state, dict(out = x), set())

    return CommonGateSpec(
        name = '`{x}`'.format(x = x),
        ports = ['out'],
        starter = lambda: (0, None), # state is not used
        deps_map = {(): {},
                    ('out', REQ): {}},
        triggers = [({'out': REQ}, do)],
        description = Constant.__doc__)



############
### NOOP ###
############

NOOP = CommonGateSpec(
    name = 'noop',
    ports = ['out'],
    starter = lambda: (0, None),
    deps_map = {(): {},
                ('out', REQ): {}},
    triggers = [],
    description = "NOOP does nothing at all. It never even triggers."
    )



###############
### Explode ###
###############

def Explode(n):

    result_names = ['o{i}'.format(i = i)
                    for i in range(n)]

    def do(state, input):
        if len(input) != n:
            err = MPVMException['explode/wrong_input_length'](
                "Input {input} has the wrong length. Expected a list"
                " of length {n}, not {n2}.",
                input = input,
                n = n,
                n2 = len(input)
                )
            return ((0, None), {'error': err}, {0})
        return ((0, None),
                {name: input[i]
                 for i, name in enumerate(result_names)},
                {0})

    triggers = {name: REQ for name in result_names}
    triggers['error'] = REQ

    deps_map = {(): {}}
    for name in result_names + ['error']:
        deps_map[(name, REQ)] = {'input': REQ}

    rval = CommonGateSpec(
        name = 'Explode{n}'.format(n = n),
        ports = ['input', 'error'] + result_names,
        starter = lambda: (0, None),
        deps_map = deps_map,
        triggers = [({name: REQ, 'input': AVAIL}, do)
                     for name in result_names],
        description = """
        Outputs 'input[X]' in 'rX', X ranging from 0 to {n}.
        """.format(n = n-1))

    return rval



#######################
### Arithmetic etc. ###
#######################

Add = FunctionGateSpec("Add", lambda a, b: a + b)
Sub = FunctionGateSpec("Sub", lambda a, b: a - b)
Mul = FunctionGateSpec("Mul", lambda a, b: a * b)
Div = FunctionGateSpec("Div", lambda a, b: a / b)

def prfn(a):
    print(a)
    return a
Pr = FunctionGateSpec("Pr", prfn)

Eq = FunctionGateSpec("Eq", lambda a, b: a == b)
Lt = FunctionGateSpec("Lt", lambda a, b: a < b)
Gt = FunctionGateSpec("Gt", lambda a, b: a > b)
Lte = FunctionGateSpec("Lte", lambda a, b: a <= b)
Gte = FunctionGateSpec("Gte", lambda a, b: a >= b)

def Join(n):
    return FunctionGateSpec("Join{n}".format(n = n),
                            lambda **args: [v for k, v in sorted(args.items()) if k.startswith('i')],
                            input_ports = ['i{i}'.format(i = i)
                                           for i in range(n)])
