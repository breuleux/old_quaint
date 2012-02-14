
from .. import dmerge, LL, LAD, LADLL
from . import prop


class Tag(LADLL):

    __tag__ = None

    __attributes__ = {'class': (prop.Classes, ""),
                      'id': (str, ""),
                      'style': (prop.Style, {})}

    def __init__(self, *elements, **attributes):
        defaults = {name: generator(init)
                    for name, (generator, init) in self.__attributes__.items()}
        LAD.__init__(self, defaults, **attributes)
        LL.__init__(self, elements)

    def parent(self):
        return self.__parent__

    def replace(self, element):
        self.add_neighbour(element)
        self.detach()

    def detach(self):
        self.__parent__.remove(self)
        return self

    def add_neighbour(self, child):
        self.__parent__.append(child)
        return child

    def convert_child(self, child):
        if isinstance(child, str):
            child = prop.Text(child)
        child.__parent__ = self
        return child

    def __setitem__(self, item, value):
        # TODO: remove __parent__ from removed items!
        if isinstance(item, int):
            value = self.convert_child(value)
        elif isinstance(item, slice):
            value = list(map(self.convert_child, value))
        else:
            if item.endswith("_"):
                item = item[:-1]
            if item in self.__attributes__:
                converter = self.__attributes__[item][0]
                value = converter(value)
        super().__setitem__(item, value)

    def log_with(self, logger):
        super().log_with(logger)
        for child in self[:]:
            if hasattr(child, 'log_with'):
                child.log_with(logger)

    def generate(self, indent = 0):

        children = "\n".join(child.generate(indent + 2)
                             for child in self.__elems__)

        attrs = ""
        for attr in self.__attributes__:
            if attr == 'children':
                continue
            value = self[attr]
            if value:
                attrs += ' {attr}="{value}"'.format(attr = attr, value = value)

        if children:
            pattern = "{indent}<{tag}{attributes}>\n{children}\n{indent}</{tag}>"
        else:
            pattern = "{indent}<{tag}{attributes}/>"

        return pattern.format(
            indent = " " * indent,
            tag = self.__tag__,
            attributes = attrs,
            children = children
            )

    def __str__(self):
        return self.generate()


class StyleTag(Tag):
    __tag__ = "style"


class SVG(Tag):
    __tag__ = 'svg'
    __attributes__ = dmerge(Tag.__attributes__,
                            {'height': (int, 0),
                             'width': (int, 0),
                             'viewBox': (LL, [])})

class SVGTag(Tag):
    __tag__ = None
    __attributes__ = dmerge(Tag.__attributes__,
                            {'transform': (prop.Transforms, [])})

    def translate(self, x, y):
        self.transform.append(prop.translate(x, y))
        return self

    def rotate(self, angle):
        self.transform.rotate(angle)
        return self

    def scale(self, sx, sy = None):
        self.transform.scale(sx, sy)
        return self

    def scalex(self, sx):
        self.transform.scalex(sx)
        return self

    def scaley(self, sy):
        self.transform.scaley(sy)
        return self

    def skewx(self, angle):
        self.transform.skewx(angle)
        return self

    def skewy(self, angle):
        self.transform.skewy(angle)
        return self

    def matrix(self, a, b, c, d, e, f):
        self.transform.matrix(a, b, c, d, e, f)
        return self


# GROUP

class Group(SVGTag):
    __tag__ = 'g'


# SHAPES

class Circle(SVGTag):
    __tag__ = 'circle'
    __attributes__ = dmerge(SVGTag.__attributes__,
                            {'cx': (int, 0),
                             'cy': (int, 0),
                             'r': (int, 0)})
    def calc_center(self):
        return self.transform.apply(self.cx, self.cy)

class Ellipse(SVGTag):
    __tag__ = 'ellipse'
    __attributes__ = dmerge(SVGTag.__attributes__,
                            {'cx': (int, 0),
                             'cy': (int, 0),
                             'rx': (int, 0),
                             'ry': (int, 0)})

class Rectangle(SVGTag):
    __tag__ = 'rect'
    __attributes__ = dmerge(SVGTag.__attributes__,
                            {'x': (int, 0),
                             'y': (int, 0),
                             'width': (int, 0),
                             'height': (int, 0),
                             'rx': (int, 0),
                             'ry': (int, 0)})

class Line(SVGTag):
    __tag__ = 'line'
    __attributes__ = dmerge(SVGTag.__attributes__,
                            {'x1': (int, 0),
                             'y1': (int, 0),
                             'x2': (int, 0),
                             'y2': (int, 0)})

class Polyline(SVGTag):
    __tag__ = 'polyline'
    __attributes__ = dmerge(SVGTag.__attributes__,
                            {'points': (prop.Points, [])})

class Polygon(SVGTag):
    __tag__ = 'polygon'
    __attributes__ = dmerge(SVGTag.__attributes__,
                            {'points': (prop.Points, [])})

class Path(SVGTag):
    __tag__ = 'path'
    __attributes__ = dmerge(SVGTag.__attributes__,
                            {'d': (prop.Points, [])})

    def go(self, command, *args):
        if isinstance(command, str):
            p = prop.Point(command, *args)
        else:
            p = prop.Point("", command, *args)
        self.d.append(p)
        return self

    def M(self, x, y):
        return self.go("M", x, y)
    def m(self, x, y):
        return self.go("m", x, y)

    def L(self, x, y):
        return self.go("L", x, y)
    def l(self, x, y):
        return self.go("l", x, y)

    def H(self, x):
        return self.go("H", x)
    def h(self, x):
        return self.go("h", x)

    def V(self, y):
        return self.go("V", y)
    def v(self, y):
        return self.go("v", y)

    def C(self, p1, p2, target):
        return self.go("C", *p1).go(*p2).go(*target)
    def c(self, p1, p2, target):
        return self.go("c", *p1).go(*p2).go(*target)

    def S(self, p, target):
        return self.go("S", *p).go(*target)
    def s(self, p, target):
        return self.go("s", *p).go(*target)

    def Q(self, p, target):
        return self.go("Q", *p).go(*target)
    def q(self, p, target):
        return self.go("q", *p).go(*target)

    def T(self, x, y):
        return self.go("T", x, y)
    def t(self, x, y):
        return self.go("t", x, y)

    def Z(self):
        return self.go("Z")
    def z(self):
        return self.go("z")


class Text(SVGTag):
    __tag__ = 'text'
    __attributes__ = dmerge(SVGTag.__attributes__,
                            {'x': (int, 0),
                             'y': (int, 0),
                             'dx': (int, 0),
                             'dy': (int, 0)})

class TSpan(SVGTag):
    __tag__ = 'tspan'
    __attributes__ = dmerge(SVGTag.__attributes__,
                            {'x': (int, 0),
                             'y': (int, 0),
                             'dx': (int, 0),
                             'dy': (int, 0)})

class Image(SVGTag):
    __tag__ = 'image'
    __attributes__ = dmerge(SVGTag.__attributes__,
                            {'xlink:href': (str, ""),
                             'x': (int, 0),
                             'y': (int, 0),
                             'width': (int, 0),
                             'height': (int, 0)})

class Link(SVGTag):
    __tag__ = 'a'
    __attributes__ = dmerge(SVGTag.__attributes__,
                            {'xlink:href': (str, "")})

