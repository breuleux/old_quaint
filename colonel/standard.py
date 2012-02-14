
from .core import GateSpec, CircuitSpec, MPVMException, VOID, REQ, NOTAG, AVAIL
from . import core, lib


def make_agent(name, gate, input_ports, output_port, error_port):
    """
    Pseudo-code:

    if agent.in_command == "get":
        agent.out, agent.error = gate(*agent.select)
    else:
        agent.error = "Unsupported command."
    """

    name = gate.name if name is None else name
    nin = len(input_ports)

    edges = """
    in_command    -> eq.a
    ctget.out     -> eq.b
    eq.out        -> dup.input
    dup.o0        -> if_out.cond
    dup.o1        -> if_err.cond
    select        -> explode.input
    gate.{gout}   -> if_out.iftrue
    gate.{gerr}   -> if_err.iftrue
    cterr.out     -> if_err.iffalse
    if_out.out    -> eith.i0
    if_err.out    -> err_neck.i0
    explode.error -> err_neck.i1
    err_neck.out  -> eith.i1
    eith.o0       -> out
    eith.o1       -> error
    """.format(gout = output_port,
               gerr = error_port)

    edges = [[x.strip() for x in line.split("->")]
             for line in edges.split("\n")
             if line.strip()]

    for i, input_port in enumerate(input_ports):
        edges.append(('explode.o{0}'.format(i),
                      'gate.{0}'.format(input_port)))

    exc = MPVMException["standard/unknown_command"](
        "Unknown command."
        )

    return CircuitSpec(
        name,
        ['select', 'in_command',
         'out', 'out_command', 'error'],
        dict(if_err = lib.IfThenElse,
             if_out = lib.IfThenElse,
             ctget = lib.Constant("get"),
             cterr = lib.Constant(exc),
             explode = lib.Explode(nin),
             err_neck = lib.Bottleneck(2),
             eith = lib.EitherOnce(2),
             dup = lib.Distribute(2),
             eq = lib.Eq,
             gate = gate),
        edges,
        allow_dangling = True) # out_command is dangling (always VOID)


class AbstractAgent(core.Gate):

    def __init__(self, spec, state, qual = None, id = None):
        if state is not None:
            raise MPVMException['abstract_agent/bad_state'](
                "Please give None as the state argument of AbstractAgentX"
                )
        super().__init__(spec,
                         None,
                         qual = qual,
                         id = id)

    def propagate(self):
        inst = self.state
        if inst is None:
            new = ([REQ] + [NOTAG] * (self.spec.nports - 1))
        else:
            inst.propagate()
            new = [NOTAG] + inst.tags_outgoing
        return self._propagate(new)

    def trigger(self):
        inst = self.state
        if inst is None:
            return any(self.incoming[rq] is not VOID
                       for rq, tag in enumerate(self.tags_outgoing)
                       if tag == REQ)
        else:
            return inst.trigger()

    def produce_all(self):
        inst = self.state
        if inst is None:
            gate = self.get_incoming('gate')
            if gate is not VOID:
                gate_instance = gate.make_instance()
                for i, (value, tag) in enumerate(zip(self.incoming[1:], self.tags_incoming[1:])):
                    gate_instance.set_incoming(i, value)
                    gate_instance.set_tag(i, tag)
                return self._produce_all(gate_instance, {}, {0})
            return self._produce_all(None, {}, set())
        else:
            outputted, state, outgoing, consumed = inst.produce_all()
            outputted = {inst.port_name(port) for port in outputted}
            return self._produce_all(inst,
                                     {port: inst.get_outgoing(port)
                                      for port in outputted},
                                     {inst.port_name(port) for port in consumed})

    def set_incoming(self, port, value):
        pnum = self.port_num(port)
        super().set_incoming(pnum, value)
        if pnum > 0 and self.state is not None:
            return self.state.set_incoming(pnum - 1, value)

    def set_tag(self, port, tag):
        pnum = self.port_num(port)
        super().set_tag(pnum, tag)
        if pnum > 0 and self.state is not None:
            return self.state.set_tag(pnum - 1, tag)

abstract_agent = GateSpec(ports = ['gate', 'select', 'in_command',
                                   'out', 'out_command', 'error'],
                          gate_class = AbstractAgent)



def Environment(contents):

    def do(state, select, in_command):
        state = state[1]
        if in_command == 'get':
            if select in state:
                return ((0, state), {'out': state[select]}, {'select', 'in_command'})
            else:
                err = MPVMException['environment/not_found'](
                    "The key {key} was not found in the environment.",
                    key = repr(select)
                    )
                return ((0, state), {'error': err}, {'select', 'in_command'})
        elif (isinstance(in_command, tuple)
              and len(in_command) == 2
              and in_command[0] == 'set'):
            state[select] = in_command[1]
            return ((0, state), {'out': in_command[1]}, {'select', 'in_command'})
        else:
            err = MPVMException['environment/unknown_command'](
                "The command {command} is not recognized by the environment.",
                command = in_command
                )
            return ((0, state), {'error': err}, {'select', 'in_command'})

    return core.CommonGateSpec(
        name = 'env',
        ports = ['select', 'in_command',
                 'out', 'out_command', 'error'],
        starter = lambda: (0, dict(contents)),
        deps_map = {(): {},
                    ('error', REQ): {},
                    ('out', REQ): {'select': REQ, 'in_command': REQ}},
        triggers = [({'out': REQ, 'select': AVAIL, 'in_command': AVAIL}, do),
                    ({'out_command': REQ, 'select': AVAIL, 'in_command': AVAIL}, do)],
        description = """
            Environment.
            """)
