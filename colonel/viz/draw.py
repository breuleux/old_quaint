
from ..tools import namedlist, attrdict
from ..tools.svg import Line, Circle, Path, Text


class LineDesc:
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        self.x1, self.y1 = p1
        self.x2, self.y2 = p2
        self.dx = self.x2 - self.x1
        self.dy = self.y2 - self.y1
        self.d = (self.dx, self.dy)
        self.length = (self.dx**2 + self.dy**2)**0.5
        self.sdx = self.dx / self.length
        self.sdy = self.dy / self.length
        self.sd = (self.sdx, self.sdy)

    def find(self, distance, perp):
        """
        Return a coordinate on the line, some distance along it, and
        at a certain perpendicular distance (perp = 0 -> coordiate on
        the line). The perpendicular distance is along the direction
        90 degrees clockwise from the line (so if you define a polygon
        clockwise, you go inside the polygon).
        """
        p = self.x1 + distance*self.sdx
        q = self.y1 + distance*self.sdy
        ddy, ddx = self.sdx, -self.sdy
        return p + ddx*perp, q + ddy*perp


def draw_polygon(path, rounding):
    """
    Returns a polygon from the path given as a list of (x, y)
    coordinates. Each corner will be rounded if rounding > 0 (the
    greater the rounder), and the given style will be applied.
    """

    lines = [LineDesc(p1, p2)
             for p1, p2 in zip(path,
                               (list(path[1:]) + [path[0]]))]

    poly = Path()
    poly.lines = lines
    poly.rounding = rounding

    if rounding:
        # Draw a line until a bit before the corner, draw a quadratic
        # curve towards a similar offset on the next side, etc. This
        # rounds the edges of the polygon.
        active = False
        for line1, line2 in zip(lines, lines[1:] + [lines[0]]):
            if not active:
                x, y = line1.find(rounding, 0)
                poly.M(x, y)
                active = True

            x1, y1 = line1.find(line1.length - rounding, 0)
            poly.L(x1, y1)

            xP, yP = line2.p1
            x2, y2 = line2.find(rounding, 0)

            poly.Q((xP, yP), (x2, y2))

    else:
        # No rounding. Simple.
        poly.M(*lines[0].p1)
        for line in lines[1:]:
            poly.L(line.x1, line.y1)

    poly.Z()

    poly.offset = [0, 0]
    poly.dimensions = [max(x for x, y in path) - min(x for x, y in path),
                       max(y for x, y in path) - min(y for x, y in path)]

    return poly



def draw_ports_polygon(polygon,
                       ports,
                       radius,
                       paddings):
    """
    Draw ports around a polygon (unlabeled).

    polygon: polygon made with draw_polygon.

    ports: a list of lists of port names. Each list corresponds to a
        side of the gate, so if for instance the path is drawing a
        rectangle from the top left clockwise, ports should be four
        lists: respectively a list of ports to display along the top
        side, along the right side, along the bottom side and along
        the left side. If a list is empty, no port will be displayed
        on that side. Names should all be distincts.

    radius: each port will be a circle of this radius.

    style: style to apply to each port.

    paddings: a list of "paddings", one for each side. Each padding is
        a triple of 1) the absolute pixel distance between the port's
        center and the polygon's side (perpendicular); 2) the length
        to leave between the start of the line and the first port; 3)
        the length to leave between the last port and the end of the
        line. 0 for all values will center ports *on* the edge, and
        the first and last ports near the corners. Adjust padding to
        avoid port overlap and for aesthetics.

    return: a dictionary of {name: port_graphic}. Note that all
        graphics must be added to the svg afterwards in order to be
        displayed!
    """

    port_figures = {}

    def addport(cx, cy, name, side):
        # Creates a port shape at the specified center.
        elem = Circle(cx = cx,
                      cy = cy,
                      r = radius)
        elem.side = side
        elem.offset = [0, 0]
        port_figures[name] = elem

    for portz, line, pad in zip(ports, polygon.lines, paddings):
        nportz = len(portz)
        padperp, pada, padb = pad
        effl = line.length - pada - padb
        dx, dy = line.d

        # Determine text offset and alignment wrt the port's center
        if abs(dx) > abs(dy):
            side = "top" if (dx > 0) else "bottom"
        else:
            side = "right" if (dy > 0) else "left"

        # Determine each port's position
        for i, port in enumerate(portz):
            if nportz == 1:
                cx, cy = line.find(pada + effl/2, padperp)
            else:
                cx, cy = line.find(pada + i*effl/(nportz-1), padperp)
            addport(cx, cy, port, side)

    return port_figures


def text_dimensions(text, font_size):
    text_width_mult = 0.62
    width = len(text) * (font_size * text_width_mult)
    return (width, font_size)

def text_width(text, style):
    return text_dimensions(text, style)[0]

def make_label(label,
               tx, ty,
               font_size,
               max_width = None,
               shift = 0):

    if max_width:
        width = text_width(label, font_size)
        font_size = int(font_size)
        if width > max_width:
            font_size *= max_width/width

    txt = Text(label,
               x = tx,
               y = ty,
               dy = shift * font_size / 2)

    txt.style.font_size = font_size
    return txt


def label_ports(ports, font_size, labels = {}, max_width = None,
                text_placement = dict(top = (0, 1, "middle", 2),
                                      bottom = (0, -1, "middle", -1),
                                      right = (-1, 0, "end", 0.5),
                                      left = (1, 0, "start", 0.5))):

    labels = {name: labels.get(name, name)
              for name in ports}

    all_labels = {}

    for name, port in ports.items():
        (dtx, dty, anchor, shift) = text_placement[port.side]
        radius = port.r
        tx = port.cx + dtx * radius
        ty = port.cy + dty * radius
        label = labels[name]
        txt = make_label(label, tx, ty, font_size,
                         max_width, shift)
        txt.style.text_anchor = anchor
        all_labels[name] = txt

    return all_labels


def merge_bbox(bb1, bb2):
    x1, y1, w1, h1 = bb1
    x2, y2, w2, h2 = bb2
    ex1, ey1 = x1+w1, y1+h1
    ex2, ey2 = x2+w2, y2+h2
    xr = min(x1, x2)
    yr = min(y1, y2)
    exr = max(ex1, ex2)
    eyr = max(ey1, ey2)
    return [xr, yr, exr-xr, eyr-yr]


def calc_margins(ports,
                 radius,
                 paddings,
                 labels,
                 font_size,
                 max_label_width,
                 text_placement):

    r = radius

    widths = []
    margins = []
    new_paddings = []

    for i, (plist, pad, side) \
            in enumerate(zip(ports,
                             paddings,
                             'top right bottom left'.split())):

        (padperp, pada, padb) = pad
        (dtx, dty, anchor, shift) = text_placement[side]
        orient = (~i)&1 # (1 = horizontal edge, 0 = vertical edge)

        if plist:
            bbox = [-r, -r, 2*r, 2*r]

            for port in plist:
                label = labels.get(port, port)
                tw = min(text_width(label, font_size),
                         max_label_width)
                text_bbox = [r*dtx + {'start': 0,
                                      'middle': -tw/2,
                                      'end': -tw}[anchor],
                             r*dty + (shift - 2)*font_size/3,
                             tw,
                             font_size]
                bbox = merge_bbox(bbox, text_bbox)

            bbox[orient] += padperp * (1 - 2*(i == 1 or i == 2))
        else:
            bbox = [0, 0, 0, 0]

        margin = 0
        if side == 'top':
            width = bbox[2]
            margin = max(bbox[1] + bbox[3], 0)
            pada -= r + bbox[0]
            padb -= r - (bbox[0] + bbox[2])

        elif side == 'bottom':
            width = bbox[2]
            margin = max(-bbox[1], 0)
            pada -= r - (bbox[0] + bbox[2])
            padb -= r + bbox[0]

        elif side == 'left':
            width = bbox[3]
            margin = max(bbox[0] + bbox[2], 0)
            pada -= r - (bbox[1] + bbox[3])
            padb -= r + bbox[1]

        elif side == 'right':
            width = bbox[3]
            margin = max(-bbox[0], 0)
            pada -= r + bbox[1]
            padb -= r - (bbox[1] + bbox[3])

        widths.append(width)
        margins.append(margin)
        if len(plist) == 1:
            new_paddings.append(pad)
        else:
            new_paddings.append((padperp, pada, padb))

    return (widths, margins, new_paddings)




# from pysvg.shape import line, circle, path as init_path
# from pysvg.text import text


# port_desc = namedlist('port_desc',
#                       ['port', 'shape', 'label',
#                        'side', 'link', 'offset'])

# link_desc = namedlist('link_desc',
#                       ['target', 'direction', 'group', 'line', 'label'])


        # port_figures[name] = port_desc(None, elem, "", side,
        #                                link_desc(None, None, None, None, None), [0, 0])
