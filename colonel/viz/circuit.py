
import networkx as nx

from ..tools import attrdict
from ..core import VOID
from .draw import LineDesc
from ..tools.svg import Group, Line


def place_gates(gates):
    """

    1) Partial orders: determine a partial order between gates
       regarding horizontal and vertical positioning.

    2) For all links that span more than n_v vertical and/or n_h
       horizontal levels, cut them off and put a label.

    3) Find merge-able links that come from the same gate
       (e.g. several out ports of Distribute), and have the same
       label. Replace the gate by a smaller one with a single "merged"
       port drawn larger with a thicker link.

    """

    orderings = attrdict(horizontal = nx.DiGraph(),
                         vertical = nx.DiGraph())

    broken_up_links = []

    def attempt_edge(graph, a, b):
        a_gate, a_port = a
        b_gate, b_port = b
        graph.add_edge(a_gate, b_gate)
        try:
            nx.topological_sort(graph)
        except nx.NetworkXUnfeasible:
            graph.remove_edge(a_gate, b_gate)
            broken_up_links.append((a, b))

    for gate, desc in gates.items():

        ordered_sides = [
            (list(sorted(((port[attr],
                           port,
                           gate.connections[port.reference[1]])
                          for port in desc.ports.values()
                          if port.side == side_name),
                         key = lambda x: x[0])), side_name)
            for side_name, attr in [['top', 'cx'],
                                    ['bottom', 'cx'],
                                    ['left', 'cy'],
                                    ['right', 'cy']]]

        ordered_sides = [
            ([(y.reference, z) for x, y, z in group if z], side)
            for group, side in ordered_sides
        ]

        for group, side in ordered_sides:

            for this, other in group:
                if side == 'top':
                    attempt_edge(orderings.vertical, other, this)
                elif side == 'bottom':
                    attempt_edge(orderings.vertical, this, other)
                elif side == 'left':
                    attempt_edge(orderings.horizontal, other, this)
                elif side == 'right':
                    attempt_edge(orderings.horizontal, this, other)

            for (_, one), (_, two) in zip(group[:-1], group[1:]):
                if side in ('top', 'bottom'):
                    attempt_edge(orderings.horizontal, one, two)
                elif side in ('left', 'right'):
                    attempt_edge(orderings.vertical, one, two)

    layers = []
    vert = orderings.vertical
    horz = orderings.horizontal
    while len(vert):
        zeros = [n for n in vert if vert.out_degree(n) == 0]
        for n in zeros:
            vert.remove_node(n)
            horz.add_node(n)
        layers.append([gates[gate]
                       for gate in nx.topological_sort(horz.subgraph(zeros))])

    y = 0
    minx = 0
    wpad = 50
    hpad = 100
    positions = {}
    for layer in layers:
        width = sum(desc.dimensions[0] + wpad for desc in layer) - wpad
        height = max(desc.dimensions[1] for desc in layer)
        y -= height
        x = -width/2
        if x < minx: minx = x
        for desc in layer:
            positions[desc] = [x, y]
            x += desc.dimensions[0] + wpad
        y -= hpad

    miny = y + hpad

    rval = {d: (xx - minx, yy - miny)
            for d, (xx, yy) in positions.items()}
    return (rval, [-2 * minx, -y - hpad], broken_up_links)



def make_naked_circuit_gate(circuit, make_gate):

    circ_fig = Group()

    subgates = {}

    for gate in circuit.instances.values():
        gate_fig = make_gate(gate)
        # gate_fig.gate = gate
        # for i, name in enumerate(gate.spec.port_names):
        #     gate_fig.ports[name].port = (gate, i)
        subgates[gate] = gate_fig

    positions, dimensions, broken_up = place_gates(subgates)

    for gate_fig, (x, y) in positions.items():
        # fig = desc.figure
        circ_fig.append(gate_fig)
        # tr = TransformBuilder()
        gate_fig.offset[:] = [x, y]
        for port_fig in gate_fig.ports.values():
            port_fig.offset[:] = [x, y]
        # tr.setTranslation(x, y)
        # fig.set_transform(tr.getTransform())
        gate_fig.translate(x, y)

    connected = set()
    for gate in circuit.instances.values():
        for pname, entry in zip(gate.spec.port_names,
                                gate.connections):
            if (entry is None or (gate, pname) in connected):
                continue
            other, port = entry
            p2name = other.port_name(port)
            connected.add((gate, pname))
            connected.add((other, p2name))
            g1 = subgates[gate]
            g2 = subgates[other]
            p1 = g1.ports[pname]
            p2 = g2.ports[p2name]
            # x1 = p1.cx + p1.offset[0]
            # y1 = p1.cy + p1.offset[1]
            # x2 = p2.cx + p2.offset[0]
            # y2 = p2.cy + p2.offset[1]
            x1, y1 = g1.transform.apply(p1.cx, p1.cy)
            x2, y2 = g2.transform.apply(p2.cx, p2.cy)
            link = Line(x1 = x1,
                        y1 = y1,
                        x2 = x2,
                        y2 = y2)
            link.class_ = "link"
            # link.set_style({'stroke-width': 5,
            #                 'stroke': 'black'})
            # p1.link = link_desc(link, 0, circ_fig, LineDesc((x1, y1), (x2, y2)), None)
            # p2.link = link_desc(link, 1, circ_fig, LineDesc((x2, y2), (x1, y1)), None)
            # circ_fig.addElement(link)
            link.lines = (LineDesc((x1, y1), (x2, y2)),
                          LineDesc((x2, y2), (x1, y1)))
            p1.link = (link, 0)
            p2.link = (link, 1)
            circ_fig.append(link)

    outlet_ports = {}
    for outlet, name in zip(circuit.outlets,
                            circuit.spec.port_names):
        if outlet is VOID:
            continue
        inconn, port = outlet
        desc = subgates[inconn]
        outlet_ports[name] = desc.ports[inconn.port_name(port)]

    circ_fig.offset = [0, 0]
    circ_fig.dimensions = dimensions
    circ_fig.ports = outlet_ports
    circ_fig.subgates = subgates

    return circ_fig

    # return gate_desc(figure = circ_fig,
    #                  shape = circ_fig,
    #                  label = text("", 0, 0),
    #                  offset = [0, 0],
    #                  dimensions = dimensions,
    #                  gate = circuit,
    #                  ports = outlet_ports,
    #                  subgates = subgates)



def make_circuit_gate(circuit, template, make_gate):

    circ_fig = make_naked_circuit_gate(circuit, make_gate)

    padw, padh = 50, 50
    cw, ch = circ_fig.dimensions
    if cw > ch:
        scale = 200/cw
    else:
        scale = 200/ch
    iw, ih = cw*scale + padw, ch*scale + padh

    sides = attrdict(top = [],
                     bottom = [],
                     left = [],
                     right = [],
                     unconn = [])
    conns = {}

    for pname, outlet in zip(circuit.spec.port_names,
                             circuit.outlets):
        if outlet is VOID:
            sides.unconn.append(pname)
            continue
        inconn, port = outlet
        gate = circ_fig.subgates[inconn]
        pfig = gate.ports[inconn.port_name(port)]
        sides[pfig.side].append(pname)
        conns[pname] = (gate, pfig)

    figure = Group()
    box = template.create_box((iw, ih), **sides)
    x, y = box.inner_offset
    x += padw/2
    y += padh/2

    circ_fig.translate(x, y).scale(scale)

    figure.append(box)
    figure.append(circ_fig)

    for pname1, p1 in box.ports.items():
        g2, p2 = conns[pname1]
        x1, y1 = circ_fig.transform.seq_inverse().apply(p1.cx, p1.cy)
        x2, y2 = g2.transform.apply(p2.cx, p2.cy)

        link = Line(x1 = x1,
                    y1 = y1,
                    x2 = x2,
                    y2 = y2)
        link.class_ = "link"

        link.lines = [LineDesc((x1, y1), (x2, y2)),
                      LineDesc((x2, y2), (x1, y1))]

        p1.inner_link = (link, 0)
        p2.link = (link, 1)

        circ_fig.append(link)

    figure.shape = box
    figure.offset = [0, 0]
    figure.dimensions = box.dimensions
    figure.ports = box.ports
    subgates = circ_fig.subgates
    return figure

    # return gate_desc(figure = figure,
    #                  shape = box.shape,
    #                  label = circ_desc.label,
    #                  offset = [0, 0],
    #                  dimensions = box.dimensions,
    #                  gate = circuit,
    #                  ports = box.ports,
    #                  subgates = circ_desc.subgates)


