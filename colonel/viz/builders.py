
from colonel.tools.svg import Group, Text, Rectangle

from .. import core, lib
from .templates import standard_rect_gate, standard_trapezoid_gate, standard_circuit_gate
from .circuit import make_circuit_gate

from .draw import text_dimensions

def strip(x):
    return str(x).replace("<", "").replace(">", "")

class GateMaker:

    def __init__(self, builders):
        self.builders = builders
        self.gate_map = {}

    def make_gate(self, gate):
        builder = self.builders.get(gate.spec, None)
        if builder is None:
            builder = self.builders[type(gate.spec)]
        figure = builder(gate, self.make_gate)
        figure.reference = gate
        for i, name in enumerate(gate.spec.port_names):
            figure.ports[name].reference = (gate, i)
        self.gate_map[gate] = figure
        return figure

    def register(self):
# {
#                 core.VOID: 'black',
#                 core.NOTAG: 'black',
#                 core.AVAIL: 'yellow',
#                 core.REQ: 'cyan'}
        listener = SVGListener(self)
        listener.register()
        return listener


class SVGListener(core.GateListener):

    def __init__(self, gate_maker): #, cmap):
        self.gate_maker = gate_maker
        self.gate_map = gate_maker.gate_map
        # self.cmap = cmap

    def register(self):
        for gate, figure in self.gate_map.items():
            gate.listeners.append(self)
            for i, incoming in enumerate(gate.incoming):
                self.set_incoming(gate, i, incoming)
            for i, tag in enumerate(gate.tags_incoming):
                self.set_tag(gate, i, tag)

    def set_tag(self, gate, port, tag):
        pname = gate.port_name(port)
        pnum = gate.port_num(port)
        gfig = self.gate_map[gate]
        figure = gfig.ports[pname]
        figure.class_ = ['port',
                         'port-{tag}'.format(tag = strip(tag)),
                         'port-send-{tag}'.format(tag = strip(gfig.reference.tags_outgoing[pnum]))]

    def trigger(self, gate, triggered):
        # cmap = {core.Circuit: {'idle': '#ddd',
        #                        'active': '#aaa'},
        #         core.
        #     }
        figure = self.gate_map[gate]
        isc = isinstance(gate, core.Circuit)
        if triggered:
            figure.shape.style.fill = '#dddddd' if isc else '40ff40'
        else:
            figure.shape.style.fill = '#aaaaaa' if isc else '#8080ff'

    def set_outgoing_tag(self, gate, port, tag):
        pname = gate.port_name(port)
        pnum = gate.port_num(port)
        gfig = self.gate_map[gate]
        figure = self.gate_map[gate].ports[pname]
        figure.class_ = ['port',
                         'port-send-{tag}'.format(tag = strip(tag)),
                         'port-{tag}'.format(tag = strip(gfig.reference.tags_incoming[pnum]))]

    def set_outgoing(self, gate, port, value):
        pname = gate.port_name(port)
        figure = self.gate_map[gate].ports[pname]
        link, direction = getattr(figure, 'inner_link', (None, None))
        self.write_label(link, direction, value)

    def set_incoming(self, gate, port, value):
        pname = gate.port_name(port)
        figure = self.gate_map[gate].ports[pname]
        link, direction = getattr(figure, 'link', (None, None))
        txt = str(value)
        self.write_label(link, direction, value)


    # def send_tags(self, gate):
    #     figure = self.gate_map[gate]
    #     for port, pfigure in figure.ports.items():
    #         pnum = gate.port_num(port)
    #         pfigure.shape.mod_style('stroke', self.cmap[gate.tags_outgoing[pnum]])

    def send(self, gate):
        pass


    def write_label(self, link, direction, value):
        if not link:
            return

        line = link.lines[direction]

        if not line:
            return

        if value is core.VOID:
            if getattr(line, 'label', None):
                # link.group.removeElement(link.label)
                line.label.detach()
                line.label = None
                link.class_ = 'link'
                # link.mod_style("stroke-width", 5)
                # link.target.mod_style("stroke", "#000")

        else:
            # link.target.mod_style("stroke-width", 8)
            # link.target.mod_style("stroke", "#00f")
            link.class_ = 'active-link'

            txt = str(value)
            # style = {'text-anchor': 'middle',
            #          'font-size': '20'}
            font_size = 20
            # boxstyle = {'fill': 'yellow'}
            w, h = text_dimensions(txt, font_size)
            distance = 20 * line.length / abs(line.dy)
            x, y = line.find(distance, 0)
            group = Group()

            box = Rectangle(x = x-w/2,
                            y = y-h/2,
                            width = w,
                            height = h)
            box.class_ = 'link-label-box'
            # box.set_style(boxstyle)
            group.append(box)

            label = Text(txt,
                         x = x,
                         y = y,
                         dy = h/4,
                         style = {'text-anchor': 'middle',
                                  'font-size': font_size})
            label.class_ = 'link-label'
            group.append(label)

            line.label = group

            link.add_neighbour(group)



def make_function_gate(gate, make_gate):
    spec = gate.spec
    return standard_rect_gate.titled_box(spec.name,
                              top = spec.input_ports,
                              # top = [x+':frewgfe' for x in spec.input_ports],
                              right = ['error:!'],
                              # bottom = ['out:x'])
                              bottom = ['out:↓'])

def make_distribute_gate(gate, make_gate):
    return standard_trapezoid_gate.create_box("~", ['input'], gate.spec.result_names)

def make_bottleneck_gate(gate, make_gate):
    return standard_trapezoid_gate.create_box("v", gate.spec.inames, ['out'])

builders = {core.FunctionGateSpec: make_function_gate,
            lib.Distribute: make_distribute_gate,
            lib.Bottleneck: make_bottleneck_gate,
            core.CircuitSpec: lambda g, mg: make_circuit_gate(g, standard_circuit_gate, mg)}


