
from .. import namedlist, LL, LAD


class Classes(LL):

    def __init__(self, names = ""):
        if isinstance(names, str):
            names = names.split(" ") if names else []
        super().__init__(names)

    def __str__(self):
        return " ".join(map(str, self[:]))

    def __repr__(self):
        return "Classes({self})".format(self = self)


class Style(LAD):

    def __init__(self, value = {}, **attributes):
        if isinstance(value, str):
            value = dict(map(str.strip, entry.split(":"))
                         for entry in value.split(";") if entry)
        super().__init__(value, **attributes)

    # Printout
    def __str__(self):
        return ";".join("{attr}:{value}".format(attr = attr,
                                                value = value)
                        for (attr, value) in self.items())

    def __repr__(self):
        return "Style({self})".format(self = self)

    def generate(self, indent = 0):
        s = ";\n".join("{indent}{attr}: {value}".format(indent = " "*indent,
                                                       attr = attr,
                                                       value = value)
                       for (attr, value) in self.items())
        if s:
            s += ";"
        return s



class translate(namedlist('translate',
                          ['dx', 'dy'],
                          False)):
    def apply(self, x, y):
        return (x + self.dx, y + self.dy)
    def inverse(self):
        return translate(-self.dx, -self.dy)

# translate = namedlist('translate',
#                       ['dx', 'dy'],
#                       False)

rotate = namedlist('rotate',
                   ['angle'],
                   False)

class scale(namedlist('scale',
                      ['sx', 'sy'],
                      False)):
    def apply(self, x, y):
        return (x * self.sx, y * self.sy)
    def inverse(self):
        return scale(1/self.sx, 1/self.sy)

# scale = namedlist('scale',
#                   ['sx', 'sy'],
#                   False)

skewx = namedlist('skewX',
                  ['angle'],
                  False)

skewy = namedlist('skewY',
                  ['angle'],
                  False)

matrix = namedlist('matrix',
                   ['a', 'b', 'c', 'd', 'e', 'f'],
                   False)

all_transforms = [translate, rotate, scale,
                  skewx, skewy, matrix]

class Transforms(LL):

    def __init__(self, transforms = []):
        if type(transforms) in all_transforms:
            transforms = [transforms]
        super().__init__(transforms)

    def log(self, event, start, stop, new):
        for element in new:
            if type(element) not in all_transforms:
                raise Exc('svg/invalid_transform')(
                    "{element} is not a valid transform",
                    element = element)
        super().log(start, stop, new)

    def apply(self, x, y):
        for transform in self:
            x, y = transform.apply(x, y)
        return (x, y)

    def inverse(self):
        return Transforms([tr.inverse() for tr in reversed(self)])

    def seq_inverse(self):
        return Transforms([tr.inverse() for tr in self])

    def translate(self, x, y):
        self.append(translate(x, y))
        return self

    def rotate(self, angle):
        self.append(rotate(angle))
        return self

    def scale(self, sx, sy = None):
        if sy is None:
            sy = sx
        self.append(scale(sx, sy))
        return self

    def scalex(self, sx):
        return self.scale(sx, 1)

    def scaley(self, sy):
        return self.scale(1, sy)

    def skewx(self, angle):
        self.append(skewx(angle))
        return self

    def skewy(self, angle):
        self.append(skewy(angle))
        return self

    def matrix(self, a, b, c, d, e, f):
        self.append(matrix(a, b, c, d, e, f))
        return self

    def __str__(self):
        return " ".join(map(str, self[:])).replace(", ", " ")

    def __repr__(self):
        return "Transforms({self})".format(self = self)



class CSS(LAD):

    def __setitem__(self, item, value):
        value = Style(value)
        super().__setitem__(item, value)

    def generate(self, indent = 0):
        items = []
        for selector, style in self.items():
            pattern = "{indent}{selector} {{\n{body}\n{indent}}}"
            items.append(pattern.format(
                    indent = " " * indent,
                    selector = selector,
                    body = style.generate(indent + 2)))
        return "\n".join(items)

    def __str__(self):
        return self.generate()


class Text:

    def __init__(self, text):
        self.__lines = text.split('\n')

    def generate(self, indent = 0):
        indent = indent * " "
        return indent + ('\n' + indent).join(self.__lines)

    def __str__(self):
        return self.generate()


class Point(tuple):

    def __new__(cls, command, *args):
        self = tuple.__new__(cls, args)
        self.command = command
        return self

    def __str__(self):
        return "{cmd}{args}".format(
            cmd = self.command,
            args = ",".join(map(str, self)))


class Points(LL):

    def __setitem__(self, item, value):
        if isinstance(item, int):
            item = slice(item, item + 1)
            value = [value]
        value = [v if isinstance(v, Point) else Point("", *v)
                 for v in value]
        super().__setitem__(item, value)

    def __str__(self):
        return " ".join(map(str, self[:]))

    def __repr__(self):
        return "Path({self})".format(self = self)

    def go(self, command, *args):
        if isinstance(command, str):
            p = Point(command, *args)
        else:
            p = Point("", command, *args)
        self.append(p)
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



# SUPPORTED STYLES
#
# font-family
# font-size
# font-style
# font-weight
# fill
# fill-opacity
# fill-rule
# marker-start
# marker-mid
# marker-end
# stop-color
# stop-opacity
# stroke
# stroke-dasharray
# stroke-dashoffset
# stroke-linecap
# stroke-linejoin
# stroke-opacity
# stroke-width
# text-anchor

