
import inspect
import exc
from .tools import KW, dmergei


class MPVMException(exc.Exception):
    def __init__(self, description = "", **arguments):
        try:
            self.description = description.format(**arguments)
        except KeyError as e:
            self.description = (
                description +
                " (while trying to fill in the details,"
                " the following error was raised: KeyError(" + str(e) + ")"
                )
        self.arguments = arguments
    def __str__(self):
        return self.description
    def __repr__(self):
        return str(self)


# indicates an empty port.
VOID = KW("VOID")


# indicates that an input is available.
AVAIL = KW("AVAIL")

# indicates an absence of tag (cannot use VOID for this purpose
# because it can't be sent)
NOTAG = KW("NOTAG")

# indicates a request for output.
REQ = KW("REQ")

# indicates that the computation path must be reset.
RESET = KW("RESET")


class GateSpec:

    def __init__(self, ports, gate_class = None):
        """
        ports: a list of port names

        The nports field contains len(ports)
        """
        self.port_names = ports
        self.ports = dict(enumerate(ports))
        self.ports.update({port_name: i for i, port_name in enumerate(ports)})
        self.nports = len(ports)
        self.gate_class = gate_class

    def port_num(self, port_name):
        """
        Returns the port number corresponding to the port name
        given. If the port name is invalid, this raises a key
        error. If the port name is a number, it is returned without
        change, unless it is not a valid port number, in which case an
        IndexError is raised.
        """
        if isinstance(port_name, int):
            if port_name < 0 or port_name >= self.nports:
                raise MPVMException['index.invalid_port_number'](
                    "Port #{port_num} of gate {gate} does not exist.",
                    port_num = port_name,
                    gate = self
                    )
            return port_name
        try:
            return self.ports[port_name]
        except KeyError:
            raise MPVMException['key.invalid_port_name'](
                "Port '{port_name}' of gate {gate} does not exist.",
                port_name = port_name,
                gate = self
                )

    def port_name(self, port_num):
        """
        Returns the port name corresponding to the port number
        given. If the port number is invalid, this raises a key
        error. If the port number is a string, it is returned without
        change, unless it is not a valid port name, in which case a
        KeyError is raised.
        """
        if isinstance(port_num, str):
            if port_num not in self.ports:
                raise MPVMException['key.invalid_port_name'](
                    "Port '{port_name}' of gate {gate} does not exist.",
                    port_name = port_num,
                    gate = self
                    )
            return port_num
        try:
            return self.ports[port_num]
        except IndexError:
            raise MPVMException['index.invalid_port_number'](
                "Port #{port_num} of gate {gate} does not exist.",
                port_num = port_num,
                gate = self
                )

    def same_signature(self, other):
        """
        Returhs true iff this GateSpec and the other GateSpec have the
        same list of ports: same number, same names and same
        order. This means they are equivalent in terms of
        connectivity.
        """
        return self.ports == other.ports

    def make_instance(self, qual = None, id = None):
        """
        Returns an instantiated version of this gate. The name of the
        instantiated gate should be "<qual>.<str(gate)>#<id>", if both
        qual and id are given (the parameters can just be passed along
        to Gate which will do the right thing with them).
        """
        if self.gate_class is None:
            raise Exc("not_implemented/gatespec")(
                "No gate_class was given to instantiate this gate spec."
                " It should be treated as an abstract specification."
                )
        else:
            return self.gate_class(self, None, qual = qual, id = id)




class ProcGateSpec(GateSpec):

    def __init__(self, ports):
        super().__init__(ports, Gate)

    def propagate(self, tags_incoming, instance):
        """
        out_reqs: a list of port names or numbers (it may be empty).
        instance: a Gate for this gate spec

        Returns a set of port numbers representing the ports whose
        values are (or may be) needed in order to compute all ports in
        out_reqs (they are the inputs that must be requested).

        If out_reqs = [], returns inputs that are always requested by
        this gate in its current state.

        Uses: *private* state, in_reqs, out_reqs, available
        Returns: in_reqs
        """
        raise Exc("not_implemented/gatespec")("Override ProcGateSpec::propagate")

    def trigger(self, instance):
        """
        instance: a Gate for this gate spec

        Returns True or False depending on whether the instance is
        ready to perform some computations or not.

        Uses: *private* state, in_reqs, out_reqs, available
        Returns: True or False
        """
        raise Exc("not_implemented/gatespec")("Override ProcGateSpec::trigger")

    def produce(self, instance):
        """
        instance: a Gate for this gate spec

        Performs computations and returns the results: (state,
        outputs, consumed), where state is the new state, outputs is a
        dictionary mapping port number to data produced for that port,
        and consumed is the list of inputs that were "consumed"
        (meaning that they will not be available the next time around,
        unless they were tucked into the state).

        Uses: state, incoming, in_reqs, out_reqs, available
        Returns: state, outgoing, available
        """
        raise Exc("not_implemented/gatespec")("Override ProcGateSpec::produce")

    def handle_vm_error(self, error, instance):
        """
        error: an error from the vm
        instance: a Gate for this gate spec

        This method is called if during the simulation, some error
        happened pertaining to this gate, for instance a requested
        output that cannot be computed by the gate (basically, errors
        in the propagate/trigger phases are passed along here for
        treatment, and also errors occurring if the gate behaves
        contrary to the protocols established).

        Returns a {port_num: value} dictionary indicating what to put
        on what ports (usually it will be {self.port_num('error'):
        error}, but it can also be an empty dictionary, or anything,
        really). If this method returns False, the error will be
        raised and the execution will be terminated.

        Uses: state, incoming, in_reqs, out_reqs, available
        Returns: state, outgoing, available
        """
        raise Exc("not_implemented/gatespec")("Override ProcGateSpec::handle_vm_error")


class CommonGateSpec(ProcGateSpec):

    def __init__(self,
                 name,
                 ports,
                 starter,
                 deps_map,
                 triggers,
                 description = None):
        """
        name: name of this gate

        ports: list of strings (note: a port named 'error', if it is
            given in this list, is semi-special - see handle_vm_error)

        functions: list of ({out_request}, fn) where
            out_request: a port name or number
            fn: a function that takes state and arguments named after
                the input ports that it needs to compute its
                results. It must return a dictionary of {out_request:
                value}

        starter: nullary function returning initial state for this
            gate. The state must be a pair [flow_state, state] where
            the first element is guaranteed to be private to the gate
            instance and serves to direct the flow, and the second
            part can be anything.

        deps_map: dictionary of
            {(flow_state, out_request): in_requests} where

            flow_state: this is state[0], the private part of the
                internal state. Can be None to indicate that the flow
                state does not matter.
            out_request: a port name or number that's requested as an
                output of this gate.
            in_requests: a set of port numbers that must be requested
                as inputs to this gate in order to compute the
                requested output
            If out_request is None, the in_requests are such that the
            gate requests these inputs even if no output is requested
            from it. IMPORTANT: if ports x and y are requested as
            outputs, then the inputs requested will be deps_map[None]
            | deps_map[x] | deps_map[y].  It is therefore important to
            provide a set, even the empty set, for when out_request is
            None.

        trigger_policy: one of 'always', 'all_in' or 'one_in'.
            If 'always', this gate will always be executed, even
            if no inputs are available. If 'all_in', the gate
            will be executed as soon as all the inputs it needs
            are available. If 'one_in', it will be executed as
            soon as one of the inputs it needs is available.
        """
        super().__init__(ports)
        self.name = name

        self.deps_map = {}
        for entry, ins in deps_map.items():
            if not isinstance(entry, tuple):
                raise MPVMException["wrong_deps_map"](
                    "All entries in deps_map should be tuples."
                    )
            if len(entry) <= 1:
                self.deps_map[entry] = ins
            elif len(entry) == 2:
                port, tag = entry
                self.deps_map[(self.port_num(port), tag)] = ins
            elif len(entry) == 3:
                fs, port, tag = entry
                self.deps_map[(fs, self.port_num(port), tag)] = ins

        self.starter = starter

        self.triggers = []
        for trigger in triggers:
            if len(trigger) == 2:
                trigger = (None,) + trigger
            fs, pattern, function = trigger
            argspec = getattr(function, '__argspec__',
                              inspect.getargspec(function))
            if argspec.keywords:
                args = list(self.port_names)
            else:
                if argspec.args[0] == 'self':
                    args = argspec.args[2:]
                else:
                    args = argspec.args[1:]
                for arg in args:
                    if arg not in self.port_names:
                        raise MPVMException['circuit_bad_function_arguments'](
                            "Argument '{arg}' of function {f} is not a valid port name"
                            " for circuit {this}",
                            arg = arg,
                            f = function,
                            this = self)
            self.triggers.append((fs,
                                  {self.port_num(port): tag
                                   for port, tag in pattern.items()},
                                  function,
                                  args))

        self.__doc__ = description

    def make_instance(self, qual = None, id = None):
        """
        Makes an instance of this gate. The state (a pair of a private
        flow_state and a possibly shared state) are returned by the
        nullary function self.starter.
        """
        flow_state, state = self.starter()
        return Gate(self, (flow_state, state), qual, id)

    def tag_gte(self, tag1, tag2):
        # Note: AVAIL < NOTAG because REQ might be sent through a port
        # tagged NOTAG, whereas NOTAG would be sent if that port was
        # tagged AVAIL. Since REQ > NOTAG, this entails NOTAG > AVAIL.
        order = {VOID: -1, 
                 AVAIL: 0,
                 NOTAG: 1,
                 REQ: 2,
                 RESET: 3}
        return order[tag1] >= order[tag2]

    def propagate(self, tags_incoming, instance):
        """
        out_reqs: a list of port names or numbers (it may be empty).
        instance: a Gate for this gate spec

        This is the union of self.deps(out_req, instance) for out_req
        in [None] + out_reqs.
        """

        rval = [NOTAG] * self.nports

        for k, tag in self.deps(None, None, instance):
            rval[self.port_num(k)] = tag

        for i, tag in enumerate(tags_incoming):
            if tag not in {VOID, NOTAG, AVAIL}: #$#$
                more_tags = self.deps(i, tag, instance)
                for i2, tag2 in more_tags.items():
                    i2 = self.port_num(i2)
                    tag1 = rval[i2]
                    if self.tag_gte(tag2, tag1):
                        rval[i2] = tag2

        for i, v in enumerate(instance.outgoing):
            if v is not VOID:
                rval[i] = AVAIL

        for i, v in enumerate(instance.tags_incoming):
            if v == AVAIL and rval[i] == REQ:
                rval[i] = NOTAG

        # assert ([t == AVAIL for t in instance.tags_incoming]
        #         == [t is not VOID for t in instance.incoming])

        return rval

    def deps(self, port, tag, instance):
        """
        Returns the dependencies of out_req, which is a port name or a
        port number, as a set of port numbers to request as inputs.
        Concretely speaking, this is:
            self.deps[(instance.state[0], out_req)]
         || self.deps[(None, out_req)]
         || self.deps[(instance.state[0], None)]
        The method raises a NetworkException if it finds none of these
        entries.
        """

        fs = instance.state[0]

        if port is None:
            to_try = [(fs,), ()]

            for entry in to_try:
                try:
                    return self.deps_map[entry]
                except KeyError:
                    continue

            raise MPVMException["network/commongate/no_deps_for_nil"](
                "Please give dependencies for the entry"
                " (None, None) or ({fs}, None) in the"
                " description of the gate {this}",
                fs = fs,
                this = self)

        else:
            port = self.port_num(port)
            to_try = [(fs, port, tag),
                      (fs, port, None),
                      (port, tag),
                      (port, None),
                      (fs,)]

            for entry in to_try:
                try:
                    return self.deps_map[entry]
                except KeyError:
                    continue

            raise MPVMException["network/bad_out_req"](
                "GateSpec {this} does not support tag {tag}"
                " on port '{port}' with flow state {fs}",
                this = instance,
                tag = tag,
                port = self.port_name(port),
                fs = fs)


    def trigger(self, instance):
        """
        Returns True if this gate instance is ready for execution.
        This method looks at instance.in_reqs and instance.available to
        check what is requested and what is available, respectively.

        If self.trigger_policy is 'always', the method always returns
        True. If it is 'one_in', it returns True if there is one port
        where in_req is True and available is True (incoming is not
        VOID). If it is 'all_in', it returns True if *all* ports such
        that in_req is True have corresponding incoming data which is
        not VOID.
        """

        for fs, pattern, function, args in self.triggers:
            if fs is None or fs == instance.state[0]:
                for pnum, tag in pattern.items():
                    if instance.tags_incoming[pnum] != tag:
                        break
                else:
                    return lambda: function(instance.state,
                                            **{name: instance.get_incoming(name)
                                               for name in args})
        return False


    def produce(self, instance):
        """
        Produce output values. This checks instance.incoming and
        instance.state for data useful to the computation, and
        instance.out_reqs to determine what outputs are asked for.

        The result is, roughly speaking:
        self.functions[superset<out_reqs>](state, **incoming)

        Where superset<out_reqs> is the first superset of all out_reqs
        such that a function is found to compute that set. Unneeded
        outputs are thrown away. For this reason, is recommended to
        order functions in self.functions in ascending order of set
        sizes, to avoid waste.

        If not superset is found, then a NetworkException is raised to
        indicate that the set of requests cannot be computed. produce
        does not call more than one function, since it might make
        state transitions difficult to determine depending on order
        (an option might be added in the future to merge results from
        various functions).
        """
        return self.trigger(instance)()


    def handle_vm_error(self, error, instance):
        """
        If a port called 'error' exists, and that it is requested, any
        VM error gets funnelled into it. Else, False is returned, and
        it is to the VM's discretion what to do next.
        """
        try:
            errp = self.port_num('error')
        except KeyError:
            return False
        if instance.tags_incoming[errp] == REQ:
            return {errp: error}
        return False

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()


class FunctionGateSpec(CommonGateSpec):

    def __wrap(self, fn):
        """
        Wraps a function into another function that returns a value
        for the out port or for the error port depending on whether
        the computation succeeded or raised an error.
        """
        def wrapped(state, **args):
            try:
                return ((0, None),
                        dict(out = fn(**args)),
                        range(self.nports - 2))
            except Exception as e:
                return ((0, None),
                        dict(error = e),
                        range(self.nports - 2))
        wrapped.__name__ = self.name + ".fn"
        spec = inspect.getargspec(fn)
        spec.args.insert(0, 'state')
        wrapped.__argspec__ = spec
        return wrapped

    def __init__(self, name, fn, no_error = False, input_ports = None):
        """
        Make a gate that implements the given function. The gate will
        have as ports: ports named after the function's arguments that
        will serve as inputs, an 'out' port for the answer, and an
        'error' port for if any error occurs.

        No argument of fn may be named 'out' or 'error'. An error is
        raised in that situation.

        If cannot_error is True, no error port will be produced.
        """
        self.name = name

        if input_ports is None:
            spec = inspect.getargspec(fn)
            if spec.varargs or spec.keywords:
                raise MPVMException['functiongate/illegal_function_signature'](
                    "The function given as an argument to FunctionGateSpec"
                    " may not have varargs or keyword arguments, unless"
                    " the names of the input ports are given explicitly"
                    " as the input_ports argument"
                    )
            input_ports = list(spec.args)
        self.input_ports = input_ports
        if {'out', 'error'} & set(self.input_ports):
            raise MPVMException['functiongate/illegal_port_names'](
                "The function given as an argument to FunctionGateSpec"
                " may not have inputs named 'out' and/or 'error'."
                )

        starter = lambda: (0, None)

        trigger = dmergei({'out': REQ},
                          {port: AVAIL for port in self.input_ports})
        wfn = self.__wrap(fn)

        if no_error:
            super().__init__(name = name,
                             ports = self.input_ports + ['out'],
                             starter = starter,
                             deps_map = {('out', REQ): {port: REQ for port in self.input_ports},
                                         (): {}},
                             triggers = {trigger: wfn}
                             )

        else:
            super().__init__(name = name,
                             ports = self.input_ports + ['out', 'error'],
                             starter = starter,
                             deps_map = {('out', REQ): {port: REQ for port in self.input_ports},
                                         ('error', REQ): {},
                                         (): {}},
                             triggers = [(trigger, wfn)]
                             )




class CircuitSpec(GateSpec):

    def __init__(self,
                 name,
                 ports,
                 gates,
                 connections,
                 atomic = False,
                 allow_dangling = False):
        """
        Create a gate from the description of a circuit.

        ports: a list of port names representing the interface of this
            circuit to the outside world.

        gates: a dictionary of {gate_name: gate} listing all gates
            needed to build the circuit.

        connections: a list of [(gate_nameA.portA, gate_nameB.portB),
            ...]  describing the edges between ports. Basically, port
            portA of gates[gate_nameA] would be connected to port
            portB of gates[gate_nameB] in this example. Each port of
            each gate may only have at most one adjoining edge. Note
            that the graph is undirected. Instead of a 'gate.port'
            string, one may only specify a port in the circuit
            itself's ports list.

        atomic: **NOT IMPLEMENTED** if True, the produce() method of
            the gate will loop until no sub-gate can be
            triggered. Else, the circuit will only perform one
            backward phase to propagate requests and one forward phase
            to compute next results. Basically, non-atomic gates can
            be executed in an interleaved fashion, but atomic gates
            cannot be. The default value is False.

        allow_dangling: if True, it's okay for some external ports not
            to be connected to anything. They will merely never have
            any in requests and will always output VOID.
        """

        self.name = name
        super().__init__(ports)
        self.gates = gates
        self.connections = connections
        self.atomic = atomic
        self.allow_dangling = allow_dangling

    def make_instance(self, qual = None, id = None):
        return Circuit(self, qual, id)

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.__str__()




class Gate:

    def __init__(self, spec, state,
                 qual = None, id = None):
        # Port names, behavior, etc.
        self.spec = spec
        # State
        self.state = state
        # Data
        self.incoming = [VOID for i in range(spec.nports)]
        self.outgoing = [VOID for i in range(spec.nports)]
        # Requests
        self.tags_incoming = [NOTAG for i in range(spec.nports)]
        self.tags_outgoing = [NOTAG for i in range(spec.nports)]
        # List of (spec, port) this gate is connected to
        self.connections = [None for i in range(spec.nports)]
        # For display
        self.qual = qual
        self.id = id
        # Monitoring
        self.listeners = []

    def _connect(self, port, other):
        port = self.port_num(port)
        ex = self.connections[port]
        if ex:
            raise MPVMException['circuit/multiple_connections'](
                "Port '{iname}' of {this} is already connected"
                " to port '{jname}' of {that}. Cannot connect"
                " to port '{kname}' of {other}.",
                iname = self.spec.port_name(port),
                this = self,
                jname = ex[0].spec.port_name(ex[1]),
                that = ex[0],
                kname = other[0].spec.port_name(other[1]),
                other = other[0]
                )
        self.connections[port] = other

    def connect(self, port, other_gate, other_port):
        other_port = other_gate.port_num(other_port)
        self._connect(port, (other_gate, other_port))
        other_gate._connect(other_port, (self, self.port_num(port)))

    def port_num(self, port_name):
        return self.spec.port_num(port_name)

    def port_name(self, port_num):
        return self.spec.port_name(port_num)

    def set_incoming(self, port, value):
        pnum = self.port_num(port)
        self.incoming[pnum] = value
        # self.tags_incoming[pnum] = AVAIL if value is not VOID else NOTAG
        self.set_tag(pnum, AVAIL if value is not VOID else NOTAG)
        for listener in self.listeners:
            listener.set_incoming(self, port, value)

    def set_outgoing(self, port, value):
        pnum = self.port_num(port)
        self.outgoing[pnum] = value
        for listener in self.listeners:
            listener.set_outgoing(self, port, value)

    def set_tag(self, port, tag):
        pnum = self.port_num(port)
        if self.tags_incoming[pnum] == tag:
            return False
        self.tags_incoming[pnum] = tag
        for listener in self.listeners:
            listener.set_tag(self, port, tag)
        return True

    def get_incoming(self, port):
        return self.incoming[self.port_num(port)]

    def get_outgoing(self, port):
        return self.outgoing[self.port_num(port)]

    def _propagate(self, tags_outgoing):
        changes = set()
        for i, (v1, v2) in enumerate(zip(self.tags_outgoing, tags_outgoing)):
            if v1 != v2:
                changes.add(i)
        self.tags_outgoing = list(tags_outgoing)
        for listener in self.listeners:
            for i, t in enumerate(self.tags_outgoing):
                listener.set_outgoing_tag(self, i, t)
        return changes

    def propagate(self):
        tags_outgoing = self.spec.propagate(self.tags_incoming, self)
        return self._propagate(tags_outgoing)

    def trigger(self):
        triggered = self.spec.trigger(self)
        for listener in self.listeners:
            listener.trigger(self, triggered)
        return triggered

    def produce(self):
        rval = self.produce_all()[0]
        return rval

    def produce_all(self):
        state, outgoing, consumed = self.spec.produce(self)
        return self._produce_all(state, outgoing, consumed)

    def _produce_all(self, state, outgoing, consumed):
        self.state = state
        rval = set()
        for output_name, value in outgoing.items():
            pnum = self.port_num(output_name)
            # self.outgoing[pnum] = value
            self.set_outgoing(pnum, value)
            if value is not VOID:
                rval.add(pnum)
        for port in consumed:
            self.consume_port(port)
        for i in rval:
            self.set_tag(i, NOTAG)
            # self.tags_incoming[i] = NOTAG
        return rval, state, outgoing, consumed

    def consume_port(self, port):
        pnum = self.port_num(port)
        self.set_incoming(pnum, VOID)
        conn = self.connections[pnum]
        if conn is not None:
            inst, oport = conn
            inst.set_outgoing(oport, VOID)
            # inst.outgoing[oport] = VOID

    def send_tags(self):
        targets = set()
        for rq, tag in enumerate(self.tags_outgoing):
            conn = self.connections[rq]
            if conn is None:
                continue
            gate, port = conn
            if gate.set_tag(port, tag):
                targets.add(gate)
        # if targets:
        for listener in self.listeners:
            listener.send_tags(self)
        return targets

    def send(self):
        targets = set()
        for i, (conn, value) in enumerate(zip(self.connections, self.outgoing)):
            if conn is None:
                continue
            gate, port = conn
            if value is not VOID:
                targets.add(gate)
                gate.set_incoming(port, value)
        # if targets:
        for listener in self.listeners:
            listener.send(self)
        return targets

    def __str__(self):
        fmt = "{gate}"
        if self.qual: fmt = "{qual}." + fmt
        if self.id: fmt += "#{id}"
        return fmt.format(gate = self.spec,
                          id = self.id,
                          qual = self.qual)

    def __repr__(self):
        return self.__str__()


class GateListener:

    def set_incoming(self, gate, port, value):
        pass

    def set_outgoing(self, gate, port, value):
        pass

    def set_tag(self, gate, port, tag):
        pass

    def set_outgoing_tag(self, gate, port, tag):
        pass

    def trigger(self, gate, triggered):
        pass

    def send_tags(self, gate):
        pass

    def send(self, gate):
        pass


class Circuit(Gate):

    def __init__(self, spec, qual = None, id = None):

        super().__init__(spec, None, qual, id)
        
        # Instantiate the gates in the circuit
        self.instances = {gate_name: gate.make_instance(qual = spec.name, id = gate_name)
                          for gate_name, gate in spec.gates.items()}
        
        # Prepare the mapping between the ports of the circuit itself
        # and the ports of the sub-gates they are connected to.
        self.outlets = [VOID for i in range(spec.nports)]

        all_connected = {}

        # Connect the gates together.
        for port1, port2 in spec.connections:

            if "." not in port1:
                if "." not in port2:
                    raise MPVMException['circuit/short_circuit'](
                        "You cannot connect two of the circuit's ports"
                        " together directly. The ports in fault are"
                        " '{a}' and '{b}'",
                        a = port1,
                        b = port2
                        )
                port1, port2 = port2, port1
                # from here on, port1 = gate.port and port2 is either
                # gate.port or port

            gate_name, gate_port = port1.split(".")
            gate1, port1 = self.instances[gate_name], gate_port

            if "." in port2:
                gate_name, gate_port = port2.split(".")
                gate2, port2 = self.instances[gate_name], gate_port
                gate1.connect(port1, gate2, port2)
                entry1 = (gate1, gate1.port_num(port1))
                entry2 = (gate2, gate2.port_num(port2))
                all_connected[entry1] = entry2
                all_connected[entry2] = entry1

            else:
                entry = (gate1, gate1.port_num(port1))
                pnum = self.port_num(port2)
                prev = self.outlets[pnum]

                if prev is not VOID:
                    raise MPVMException['circuit/multiple_connections'](
                        "No more than one port of the subcircuit for {this}"
                        " can correspond to an external port of the circuit."
                        " Both {one} and {two} are defined as corresponding"
                        " to {thisport}.",
                        one = (prev[0], prev[0].port_name(prev[1])),
                        two = (gate1, gate1.port_name(port1)),
                        this = self,
                        thisport = self.port_name(pnum)
                        )

                elif entry in all_connected:
                    raise MPVMException['circuit/multiple_connections'](
                        "No more than one port of {this} can correspond to" 
                        " a port of any gate in the circuit. Here,"
                        " both {one} and {two} are defined as corresponding"
                        " to {port}.",
                        one = self.port_name(pnum),
                        two = all_connected[entry],
                        this = self,
                        port = entry
                        )

                all_connected[entry] = pnum
                all_connected[pnum] = entry
                self.outlets[pnum] = entry

        # Check that all of the circuit's ports are connected to some
        # gate.
        if not spec.allow_dangling:
            for i, outlet in enumerate(self.outlets):
                if outlet is VOID:
                    raise MPVMException['circuit/missing_connection'](
                        "Port {port} of circuit {circ} is not connected"
                        " to anything. There should be an entry of the"
                        " form ('{port}', 'gate.port') in the list of"
                        " connections",
                        port = spec.ports[i],
                        circ = self
                        )

        self.propagation_sources = set(self.instances.values())

        self.prop_sources = set(self.instances.values())
        self.triggerable = set()


    def propagate(self):
        """
        out_reqs: a list of port names or numbers (it may be empty).
        instance: a Gate for this gate spec

        AAAAAA
        """

        state = self.state

        sources = set(self.prop_sources)
        self.triggerable = set(self.prop_sources)

        while sources:
            next = sources.pop()
            changes = next.propagate()
            if changes:
                connections = next.send_tags()
                sources |= connections
                self.triggerable |= connections

        rval = [VOID] * self.spec.nports
        for i, inconn in enumerate(self.outlets):
            if inconn is VOID:
                continue
            inst, port = inconn
            rval[i] = inst.tags_outgoing[port]

        return self._propagate(rval)

    def trigger(self):
        self.triggered = set()
        #print(self.triggerable, set(self.instances.values()))
        # assert len(self.triggerable) == len(self.instances)
        for inst in self.triggerable:
            if inst.trigger():
                self.triggered.add(inst)
        rval = len(self.triggered) > 0
        for listener in self.listeners:
            listener.trigger(self, rval)
        return rval

    def produce_all(self):

        state = self.state

        new = set()
        consume = set()

        for inst in self.triggered:
            new.add(inst)
            inst.produce()

        for inst in set(new):
            targets = inst.send()
            new |= targets

        rval = {}
        for i, inconn in enumerate(self.outlets):
            if inconn is VOID:
                continue
            inst, port = inconn
            that = inst.outgoing[port]
            if that is not VOID:
                # inst.outgoing[port] = VOID
                rval[i] = that
            else:
                if (self.incoming[i] is not VOID
                    # and inst.tags_outgoing[port] == REQ
                    and inst.incoming[port] is VOID):
                    self.set_incoming(i, VOID)
                    consume.add(i)

        self.prop_sources = new
        self.triggered = set()

        return self._produce_all(self.state, rval, consume)

    def set_incoming(self, port, value):
        pnum = self.port_num(port)
        super().set_incoming(pnum, value)

        inconn = self.outlets[pnum]
        if inconn is VOID:
            return False
        inst, xport = inconn
        self.prop_sources.add(inst)

        return inst.set_incoming(xport, value)

    def set_tag(self, port, tag):
        pnum = self.port_num(port)
        super().set_tag(pnum, tag)

        inconn = self.outlets[pnum]
        if inconn is VOID:
            return False
        inst, xport = inconn

        success = inst.set_tag(xport, tag)
        if success:
            self.prop_sources.add(inst)
        return success



def xgate_step(instance, inputs, requests):
    # instance = gate.make_instance()
    for input_name, value in inputs.items():
        instance.set_incoming(input_name, value)
    for output_name in requests:
        instance.set_tag(output_name, REQ)
    results = {output_name: VOID for output_name in requests}
    instance.propagate()
    while instance.trigger():
        yield
        instance.produce()
        results = {output_name: instance.get_outgoing(output_name)
                   for output_name in requests}
        if all(v is not VOID for v in results.values()):
            yield results
            return
        instance.propagate()

    yield results
    return


    

def xgate(gate, inputs, requests):
    instance = gate.make_instance()
    for input_name, value in inputs.items():
        instance.set_incoming(input_name, value)
    for output_name in requests:
        instance.set_tag(output_name, REQ)
    results = {output_name: VOID for output_name in requests}
    instance.propagate()
    while instance.trigger():
        instance.produce()
        results = {output_name: instance.get_outgoing(output_name)
                   for output_name in requests}
        if all(v is not VOID for v in results.values()):
            return results
        instance.propagate()

    return results





def xgate_iter(gate, inputs, requests):
    instance = gate.make_instance()
    inputs = {k: iter(v) for k, v in inputs.items()}
    for output_name in requests:
        instance.set_tag(output_name, REQ)
    results = {output_name: []
               for output_name in requests}

    def prop():
        instance.propagate()
        for input_name, value in inputs.items():
            pnum = instance.port_num(input_name)
            if (instance.tags_outgoing[pnum] == REQ
                and instance.incoming[pnum] is VOID):
                try:
                    instance.set_incoming(input_name, next(value))
                except StopIteration:
                    pass

    prop()
    while instance.trigger():
        instance.produce()
        curr_results = {output_name: instance.get_outgoing(output_name)
                        for output_name in requests}
        if any(v is not VOID for v in curr_results.values()):
            for output_name, l in results.items():
                res = curr_results[output_name]
                l.append(res)
                if res is not VOID:
                    instance.set_tag(output_name, REQ)
        prop()

    return results
