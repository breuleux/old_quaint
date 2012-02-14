
from .draw import (draw_polygon, draw_ports_polygon,
                   label_ports, calc_margins, text_dimensions)

from ..tools import namedlist
from ..tools.svg import Group, Text


def name_label(x):
    if ":" in x:
        return x.split(":")
    else:
        return [x, x]

class BoxGateBuilder:

    def __init__(self,
                 port_radius,
                 paddings,
                 max_label_width,
                 text_placement,
                 box_class,
                 port_class,
                 title_class,
                 port_label_class,
                 title_font_size,
                 port_label_font_size,
                 rounding,
                 equalize_margins = False):

        self.port_radius = port_radius
        self.paddings = paddings

        self.max_label_width = max_label_width
        self.text_placement = text_placement

        self.box_class = box_class
        self.port_class = port_class
        self.title_class = title_class
        self.port_label_class = port_label_class
        self.title_font_size = title_font_size
        self.port_label_font_size = port_label_font_size

        self.rounding = rounding

        self.equalize_margins = equalize_margins

    def variant(self, **kw):
        r = dict(self.__dict__)
        r.update(kw)
        return BoxGateBuilder(**r)

    def create_box(self, inner_dimensions, **ports):

        # Extract lists of ports and corresponding labels
        ports = [ports.get("top", []),
                 ports.get("right", []),
                 list(reversed(ports.get("bottom", []))),
                 list(reversed(ports.get("left", [])))]

        labels = {}
        for plist in ports:
            for i, port in enumerate(plist):
                name, label = name_label(port)
                plist[i] = name
                labels[name] = label

        # Calculate the total size of the box given that the ports all
        # around the edges must be outside of the inner center which
        # dimensions are given as argument
        widths, margins, paddings = calc_margins(
            ports = ports,
            radius = self.port_radius,
            paddings = self.paddings,
            labels = labels,
            font_size = self.port_label_font_size,
            max_label_width = self.max_label_width,
            text_placement = self.text_placement)

        if self.equalize_margins:
            margins[0] = margins[2] = max(margins[0], margins[2])
            margins[1] = margins[3] = max(margins[1], margins[3])

        iw, ih = inner_dimensions
        w = iw + margins[1] + margins[3]
        h = ih + margins[0] + margins[2]

        neededw = max(len(ports[0]) * widths[0] + sum(paddings[0][1:]),
                      len(ports[2]) * widths[2] + sum(paddings[2][1:]))
        w = max(w, neededw)
        neededh = max(len(ports[1]) * widths[1] + sum(paddings[1][1:]),
                      len(ports[3]) * widths[3] + sum(paddings[3][1:]))
        h = max(h, neededh)

        # Construct the figure
        figure = Group()

        path = ((0, 0), (w, 0), (w, h), (0, h))

        box = draw_polygon(path, self.rounding)
        box.class_ = self.box_class
        figure.append(box)

        port_figures = draw_ports_polygon(box, ports,
                                          self.port_radius,
                                          paddings)
        for x, y in port_figures.items():
            y.class_ = self.port_class
            figure.append(y)

        label_figures = label_ports(port_figures,
                                    self.port_label_font_size,
                                    labels = labels,
                                    max_width = self.max_label_width,
                                    text_placement = self.text_placement)
        for x, y in label_figures.items():
            y.class_ = self.port_label_class
            figure.append(y)

        figure.shape = box
        figure.offset = box.offset
        figure.dimensions = box.dimensions
        figure.ports = port_figures

        figure.inner_offset = (margins[3], margins[0])

        return figure

    def titled_box(self, title, **ports):
        (w, h) = text_dimensions(title, self.title_font_size)
        box = self.create_box((w, h), **ports)
        x, y = box.inner_offset

        title_node = Text(title,
                          x = x + w/2,
                          y = y + h/2,
                          dy = h/4)
        title_node.class_ = self.title_class
        title_node.style.font_size = self.title_font_size
        title_node.style.text_anchor = 'middle'

        box.append(title_node)
        box.title = title_node

        return box


standard_rect_gate = BoxGateBuilder(

    port_radius = 10,

    paddings = [(0, 30, 30),
                (0, 50, 50),
                (0, 30, 30),
                (0, 50, 50)],

    max_label_width = 40,

    text_placement = dict(top = (0, 1, "middle", 2),
                          bottom = (0, -1, "middle", -1),
                          right = (-1.5, 0, "end", 0.5),
                          left = (1.5, 0, "start", 0.5)),

    box_class = 'rect-gate',
    port_class = 'port',
    title_class = 'title',
    port_label_class = 'port-label',
    title_font_size = 100,
    port_label_font_size = 20,

    rounding = 20,

    equalize_margins = True)


standard_circuit_gate = standard_rect_gate.variant(

    paddings = [(15, 30, 30),
                (15, 50, 50),
                (15, 30, 30),
                (15, 50, 50)],

    text_placement = dict(top = (1.25, 0, "start", 0.5),
                          bottom = (1.25, 0, "start", 0.5),
                          right = (1, 1.25, "end", 2),
                          left = (-1, 1.25, "start", 2)),

    box_class = 'circuit-gate'

    )

###########################


class TrapezoidGateBuilder:

    def __init__(self,
                 port_radius,
                 port_gap,
                 paddings,
                 min_height,
                 title_font_size,
                 box_class,
                 port_class,
                 title_class,
                 rounding):

        self.port_radius = port_radius
        self.port_gap = port_gap
        self.paddings = paddings
        self.min_height = min_height
        self.title_font_size = title_font_size
        self.box_class = box_class
        self.port_class = port_class
        self.title_class = title_class
        self.rounding = rounding

    def create_box(self, title, ins, outs):
        nin = len(ins)
        nout = len(outs)

        wt = self.port_gap * nin - self.port_gap + sum(self.paddings[0][1:])
        wb = self.port_gap * nout - self.port_gap + sum(self.paddings[1][1:])

        pad = abs(wt - wb) / 2
        if title:
            h = max(text_dimensions(title, self.title_font_size)[1], self.min_height)
        else:
            h = self.min_height

        if nin > nout:
            sh = (self.port_radius + self.paddings[0][0]) * 2
            path = ((0, 0), (wt, 0), (wt, sh), (wb+pad, h), (pad, h), (0, sh))
        else:
            sh = self.port_radius + self.paddings[1][0] * 2
            path = ((pad, 0), (wt+pad, 0), (wb, h-sh), (wb, h), (0, h), (0, h-sh))

        ports = [ins, [], [], list(reversed(outs)), [], []]

        figure = Group()

        box = draw_polygon(path, self.rounding)
        box.class_ = self.box_class
        figure.append(box)

        paddings = ([self.paddings[0]] + [(0, 0, 0)]*2
                    + [self.paddings[1]] + [(0, 0, 0)]*2)
        port_figures = draw_ports_polygon(box, ports,
                                          self.port_radius,
                                          paddings)
        for x, y in port_figures.items():
            y.class_ = self.port_class
            figure.append(y)

        # TODO: add parameters for the title's position
        meanx = sum(x for x, y in path) / len(path)
        meany = sum(y for x, y in path) / len(path)
        title_node = Text(title, x = meanx, y = meany, dy = h/4)
        title_node.class_ = self.title_class
        title_node.style.font_size = self.title_font_size
        title_node.style.text_anchor = 'middle'
        figure.append(title_node)

        figure.shape = box
        figure.offset = box.offset
        figure.dimensions = box.dimensions
        figure.ports = port_figures

        return figure



standard_trapezoid_gate = TrapezoidGateBuilder(

    port_radius = 10,

    port_gap = 30,

    paddings = [(15, 30, 30),
                (15, 30, 30)],

    min_height = 75,

    title_font_size = 100,
    box_class = 'trapezoid-gate',
    port_class = 'port',
    title_class = 'title',

    rounding = 20)
