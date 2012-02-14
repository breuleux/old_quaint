
# from .core import xgate, VOID, CircuitSpec, MPVMException
# from . import core, lib, standard
from colonel.core import xgate, xgate_iter, VOID, CircuitSpec, MPVMException
from colonel import core, lib, standard
import random
import os


def withsalt(salt):
    def decorate(fn):
        def new():
            seed = int(os.getenv("SEED", 0)) + salt
            random.seed(seed)
            for i in range(int(os.getenv("RAND_REPEAT", 0))):
                fn()
            return fn()
        new.__name__ = fn.__name__
        return new
    return decorate


@withsalt(59532)
def test_function_gates():

    for gate, function in {
        lib.Add: (lambda a, b: a + b),
        lib.Sub: (lambda a, b: a - b),
        lib.Mul: (lambda a, b: a * b),
        lib.Div: (lambda a, b: a / b),
        }.items():

        a = random.uniform(-100, 100)
        b = random.uniform(-100, 100)
        results = xgate(gate, dict(a = a, b = b),
                        ['out', 'error'])

        r = function(a, b)

        print(results)
        assert results['out'] == r
        assert results['error'] is VOID


def test_join():
    for n in range(2, 10):
        gate = lib.Join(n)
        print(gate.ports)
        args = {'i{i}'.format(i = i): i for i in range(n)}
        print(args)
        results = xgate(gate, args, ['out', 'error'])
        print(results)
        assert results['out'] == list(range(n))
        assert results['error'] is VOID


def test_div_by_zero():
    results = xgate(lib.Div, dict(a = 10,
                                  b = 0),
                    ['out', 'error'])

    assert results['out'] == VOID
    assert type(results['error']) == ZeroDivisionError


def test_constant():
    results = xgate(lib.Constant(123), {}, ['out'])
    assert results['out'] == 123


def test_constant_circuit():
    F = CircuitSpec("F",
                ['out'],
                dict(a = lib.Constant(1),
                     b = lib.Constant(2),
                     c = lib.Constant(3),
                     op1 = lib.Add,
                     op2 = lib.Add),
                [('a.out', 'op1.a'),
                 ('b.out', 'op1.b'), # error here: a is connected to both op1.a and op1.b
                 ('op1.out', 'op2.a'),
                 ('c.out', 'op2.b'),
                 ('op2.out', 'out')])

    results = xgate(F, {}, ['out'])
    assert results['out'] == 6.0


def test_bad_circuit():

    ports = ['a', 'b', 'c', 'out']
    ops = dict(op1 = lib.Add,
               op2 = lib.Add,
               op3 = lib.Add)

    # One
    try:
        F = CircuitSpec("F", ports, ops,
                    [('a', 'op1.a'),
                     ('a', 'op1.b'), # error here: a is connected to both op1.a and op1.b
                     ('op1.out', 'op2.a'),
                     ('c', 'op2.b'),
                     ('op2.out', 'out')])
        F.make_instance()
        raise Exception("Failure")

    except MPVMException['circuit/multiple_connections']:
        pass

    # Two
    try:
        F = CircuitSpec("F", ports, ops,
                    [('a', 'op1.a'),
                     ('b', 'op1.a'), # error here: op1.a is connected to both a and b
                     ('op1.out', 'op2.a'),
                     ('c', 'op2.b'),
                     ('op2.out', 'out')])
        F.make_instance()
        raise Exception("Failure")

    except MPVMException['circuit/multiple_connections']:
        pass

    # Three
    try:
        F = CircuitSpec("F", ports, ops,
                    [('a', 'op1.a'),
                     ('b', 'op1.b'),
                     ('op1.out', 'op2.a'),
                     ('c', 'op2.a'), # error here: op2.a is connected to both op1.out and c
                     ('op2.out', 'out')])
        F.make_instance()
        raise Exception("Failure")

    except MPVMException['circuit/multiple_connections']:
        pass

    # Four
    try:
        F = CircuitSpec("F", ['a', 'b', 'c', 'd', 'out'], ops,
                    [('a', 'op1.a'),
                     ('b', 'op1.b'),
                     ('c', 'op2.a'),
                     ('d', 'op2.b'),
                     ('op1.out', 'op3.a'),
                     ('op2.out', 'op3.a'), # error here: op1.out and op2.out are both connected to op3.a
                     ('op3.out', 'out')])
        F.make_instance()
        raise Exception("Failure")

    except MPVMException['circuit/multiple_connections']:
        pass

    # Five
    try:
        F = CircuitSpec("F", ports, ops,
                    [('a', 'op1.a'),
                     # error here: the circuit's b port is not connected to anything
                     ('op1.out', 'op2.a'),
                     ('c', 'op2.b'),
                     ('op2.out', 'out')])
        F.make_instance()
        raise Exception("Failure")

    except MPVMException['circuit/missing_connection']:
        pass


def test_circuit1():

    # out = (a + b) + c
    F1 = CircuitSpec("F1",
                 ['a', 'b', 'c', 'out'],
                 dict(op1 = lib.Add,
                      op2 = lib.Add),
                 [('a', 'op1.a'),
                  ('b', 'op1.b'),
                  ('op1.out', 'op2.a'),
                  ('c', 'op2.b'),
                  ('op2.out', 'out')])

    # Equivalent circuit:
    F2 = CircuitSpec("F2",
                 ['a', 'b', 'c', 'out'],
                 dict(op1 = lib.Add,
                      op2 = lib.Add),
                 # Connections that were (x, y) in the circuit above
                 # are (y, x) here. This should make no difference at
                 # all to its execution.
                 [('op1.a', 'a'),
                  ('op1.b', 'b'),
                  ('op2.a', 'op1.out'),
                  ('op2.b', 'c'),
                  ('out', 'op2.out')])

    for F in F1, F2:

        results = xgate(F, dict(a = 1, b = 2, c = 3),
                        ['out'])
        assert results['out'] == 6.0

        try:
            results = xgate(F, dict(a = 1, b = 2, out = 3),
                            ['c'])
        except MPVMException["network/bad_out_req"]:
            return



def TracerGate(mark):
    def f(x):
        mark.append(x)
        return x
    return core.FunctionGateSpec('trace', f)


def test_ifthenelse():

    ma = []
    mb = []

    # out = if cond then a else b
    F1 = CircuitSpec("F1",
                 ['cond', 'a', 'b', 'out'],
                 dict(iff = lib.IfThenElse,
                      tracea = TracerGate(ma),
                      traceb = TracerGate(mb)),
                 [('cond', 'iff.cond'),
                  ('a', 'tracea.x'),
                  ('b', 'traceb.x'),
                  ('tracea.out', 'iff.iftrue'),
                  ('traceb.out', 'iff.iffalse'),
                  ('iff.out', 'out')])

    # We verify the laziness of IfThenElse: TracerGate "marks" its
    # input into the list it is given, so we can check if it was
    # called or not.

    results = xgate(F1, dict(cond = 0, a = 33, b = 44), ['out'])
    assert results['out'] == 44
    assert ma == []
    assert mb == [44] # only the else branch should be evaluated

    results = xgate(F1, dict(cond = 1, a = 55, b = 66), ['out'])
    assert results['out'] == 55
    assert ma == [55] # only the true branch should be evaluated
    assert mb == [44]


@withsalt(414324)
def test_sequence():

    m = []

    # We randomize the order (basically, input[i] -> seq.input[order[i]])
    order = list(range(5))
    random.shuffle(order)

    # out = trace(a), trace(b), trace(c), trace(d), trace(e)
    # in that order
    F1 = CircuitSpec("F1",
                 ['a', 'b', 'c', 'd', 'e', 'out'],
                 dict(seq = lib.Sequence(5),
                      tracea = TracerGate(m),
                      traceb = TracerGate(m),
                      tracec = TracerGate(m),
                      traced = TracerGate(m),
                      tracee = TracerGate(m)
                      ),
                 [('a', 'tracea.x'),
                  ('b', 'traceb.x'),
                  ('c', 'tracec.x'),
                  ('d', 'traced.x'),
                  ('e', 'tracee.x'),
                  ('tracea.out', 'seq.i{x}'.format(x = order[0])),
                  ('traceb.out', 'seq.i{x}'.format(x = order[1])),
                  ('tracec.out', 'seq.i{x}'.format(x = order[2])),
                  ('traced.out', 'seq.i{x}'.format(x = order[3])),
                  ('tracee.out', 'seq.i{x}'.format(x = order[4])),
                  ('seq.out', 'out')])

    # We verify that the tracers were executed in the right order

    results = xgate(F1, dict(a = 11, b = 22, c = 33, d = 44, e = 55), ['out'])
    expected_order = [(order.index(i) + 1) * 11 for i in range(5)]

    print('order:   ', order)
    print('results: ', results)
    print('m:       ', m)
    print('expected:', expected_order)

    assert results['out'] == expected_order[-1]
    assert m == expected_order


def test_make_agent():

    agent = standard.make_agent("div", lib.Div, ['a', 'b'], 'out', 'error')

    # Correct execution
    results = xgate(agent,
                    dict(select = [10, 2], in_command = "get"),
                    ['out', 'error'])
    print(results)
    assert results['out'] == 5.0
    assert results['error'] == VOID

    # Error in the gate
    results = xgate(agent,
                    dict(select = [10, 0], in_command = "get"),
                    ['out', 'error'])
    print(results)
    assert results['out'] == VOID
    assert isinstance(results['error'], ZeroDivisionError)

    # Wrong number of arguments
    results = xgate(agent,
                    dict(select = [10, 20, 30], in_command = "get"),
                    ['out', 'error'])
    print(results)
    assert results['out'] == VOID
    assert isinstance(results['error'], MPVMException['explode/wrong_input_length'])

    # Invalid command for an agent made with make_agent
    results = xgate(agent,
                    dict(select = [10, 20], in_command = ["set", 13]),
                    ['out', 'error'])
    print(results)
    assert results['out'] == VOID
    assert isinstance(results['error'], MPVMException['standard/unknown_command'])


def test_standard_circuit():
    # Test a simple network of agents, using Join to create lists of
    # arguments.

    adder = standard.make_agent("add", lib.Add, ['a', 'b'], 'out', 'error')

    # out = (a + b) + c
    F = CircuitSpec("F",
                ['a', 'b', 'c', 'out'],
                dict(add1 = adder,
                     add2 = adder,
                     join1 = lib.Join(2),
                     join2 = lib.Join(2),
                     ctget2 = lib.Constant("get"),
                     ctget1 = lib.Constant("get")),
                [('a', 'join1.i0'),
                 ('b', 'join1.i1'),
                 ('join1.out', 'add1.select'),
                 ('ctget1.out', 'add1.in_command'),
                 ('add1.out', 'join2.i0'),
                 ('c', 'join2.i1'),
                 ('join2.out', 'add2.select'),
                 ('ctget2.out', 'add2.in_command'),
                 ('add2.out', 'out')])

    results = xgate(F, dict(a = 10, b = 83, c = 7),
                    ['out'])
    print(results)
    assert results['out'] == 100.0


def test_abstract_agent():

    agent = standard.make_agent("div", lib.Div, ['a', 'b'], 'out', 'error')

    # Correct execution
    results = xgate(standard.abstract_agent,
                    dict(gate = agent, select = [10, 2], in_command = "get"),
                    ['out', 'error'])
    print(results)
    assert results['out'] == 5.0
    assert results['error'] == VOID

    # Error in the gate
    results = xgate(standard.abstract_agent,
                    dict(gate = agent, select = [10, 0], in_command = "get"),
                    ['out', 'error'])
    assert results['out'] == VOID
    assert isinstance(results['error'], ZeroDivisionError)

    # Wrong number of arguments
    results = xgate(standard.abstract_agent,
                    dict(gate = agent, select = [10, 20, 30], in_command = "get"),
                    ['out', 'error'])
    assert results['out'] == VOID
    assert isinstance(results['error'], MPVMException['explode/wrong_input_length'])

    # Wrong command
    results = xgate(standard.abstract_agent,
                    dict(gate = agent, select = [10, 20], in_command = ["set", 13]),
                    ['out', 'error'])
    assert results['out'] == VOID
    assert isinstance(results['error'], MPVMException['standard/unknown_command'])


def test_environment():

    env = standard.Environment({"hello": "world"})

    # Correct execution
    results = xgate(env,
                    dict(select = "hello", in_command = "get"),
                    ['out', 'error'])
    assert results['out'] == "world"
    assert results['error'] == VOID

    # Key not there
    results = xgate(env,
                    dict(select = "not_there", in_command = "get"),
                    ['out', 'error'])
    assert results['out'] == VOID
    assert isinstance(results['error'], MPVMException['environment/not_found'])

    # Setting a key
    results = xgate(env,
                    dict(select = "not_there", in_command = ("set", 14)),
                    ['out', 'error'])
    assert results['out'] == 14
    assert results['error'] == VOID

    # Bogus command
    results = xgate(env,
                    dict(select = "hello", in_command = 'bogus'),
                    ['out', 'error'])
    assert results['out'] == VOID
    assert isinstance(results['error'], MPVMException['environment/unknown_command'])


def test_xgate_iter():
    results = xgate_iter(lib.Add,
                         dict(a = [1, 20, 300, 4000, 50000, 600000],
                              b = [6, 50, 400, 3000, 20000, 100000]),
                         ['out', 'error'])
    print(results)
    assert results['out'] == [7, 70, 700, 7000, 70000, 700000]
    assert results['error'] == [VOID] * 6


def test_bottleneck():
    results = xgate_iter(lib.Bottleneck(5),
                         dict(i0 = [10],
                              i1 = [20],
                              i2 = [30],
                              i3 = [40],
                              i4 = [50]),
                         ['out'])
    assert set(results['out']) == {10, 20, 30, 40, 50}


def test_bottleneck_circuit():

    # out = bottleneck(a + b, c + d, e)
    F1 = CircuitSpec("F1",
                 ['a', 'b', 'c', 'd', 'e', 'out'],
                 dict(add1 = lib.Add,
                      add2 = lib.Add,
                      neck = lib.Bottleneck(3)
                      ),
                 [('a', 'add1.a'),
                  ('b', 'add1.b'),
                  ('c', 'add2.a'),
                  ('d', 'add2.b'),
                  ('add1.out', 'neck.i0'),
                  ('add2.out', 'neck.i1'),
                  ('e', 'neck.i2'),
                  ('neck.out', 'out')])

    results = xgate_iter(F1,
                         dict(a = [10, 77],
                              b = [20],
                              c = [30],
                              d = [40],
                              e = [50, 90]),
                         ['out'])

    # should be [50, 30, 70, 90] or [50, 70, 30, 90], since e=50
    # arrives first and e=90 arrives last
    print(results)

    # but we don't care all that much about the order
    assert set(results['out']) == {30, 50, 70, 90}


def test_either_once():
    results = xgate_iter(lib.EitherOnce(2),
                         dict(i0 = [10, 20, 30, 40],
                              i1 = [100, 200, 300]),
                         ['o0', 'o1'])
    print(results)
    # Only one output will ever pass. Typically it'll be o0 here, but
    # it's also correct if it is o1.
    assert (results == dict(o0 = [10], o1 = [VOID]) or
            results == dict(o0 = [VOID], o1 = [100]))


def test_either_once_circuit():

    m = []

    # out = either(trace(trace(trace(a))), trace(b))
    F1 = CircuitSpec("F1",
                 ['a', 'b', 'o0', 'o1'],
                 dict(eith = lib.EitherOnce(2),
                      tracea = TracerGate(m),
                      traceb = TracerGate(m),
                      traceX1 = TracerGate(m),
                      traceX2 = TracerGate(m)
                      ),
                 [('a', 'tracea.x'),
                  ('b', 'traceb.x'),
                  ('tracea.out', 'traceX1.x'),
                  ('traceX1.out', 'traceX2.x'),
                  ('traceX2.out', 'eith.i0'),
                  ('traceb.out', 'eith.i1'),
                  ('eith.o0', 'o0'),
                  ('eith.o1', 'o1')])

    results = xgate_iter(F1,
                         dict(a = [10, 20],
                              b = [30]),
                         ['o0', 'o1'])

    print(results)
    print(m)

    # Only one output will ever pass. Since the path to i0 is longer
    # than the path to i1, i1 should get in before, eith and traceX1
    # should be evaluated at the same time, and then the evaluation of
    # traceX2 should not occur, because the request on i0 is removed.
    assert (results == dict(o0 = [VOID], o1 = [30]))
    assert sorted(m) == [10, 10, 30]


def test_long_circuit():

    m = []

    F = CircuitSpec("F",
                    ['a', 'out'],
                    dict(op1 = TracerGate(m),
                         op2 = TracerGate(m),
                         op3 = TracerGate(m),
                         op4 = TracerGate(m),
                         op5 = TracerGate(m),
                         op6 = TracerGate(m),
                         op7 = TracerGate(m),
                         op8 = TracerGate(m)),
                    [('a', 'op1.x'),
                     ('op1.out', 'op2.x'),
                     ('op2.out', 'op3.x'),
                     ('op3.out', 'op4.x'),
                     ('op4.out', 'op5.x'),
                     ('op5.out', 'op6.x'),
                     ('op6.out', 'op7.x'),
                     ('op7.out', 'op8.x'),
                     ('op8.out', 'out')])

    results = xgate(F, dict(a = 100),
                    ['out'])
    print(results)
    print(m)
    assert results['out'] == 100
    assert m == [100]*8


