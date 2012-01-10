
from .err import Exc


class attrdict(dict):
    def __getattr__(self, attr):
        if attr.startswith("__"):
            return getattr(super(), attr)
        return self[attr]


def dmerge(d1, d2):
    rval = dict(d1)
    rval.update(d2)
    return rval

def dmergei(d1, d2):
    d1.update(d2)
    return d1


class KW:
    def __init__(self, name, id = None):
        self.name = name
        self.id = id
        self.count = 0
    def __call__(self):
        if self.id is not None:
            raise Exc('kw/cannot_clone')(
                "Cannot clone keyword {kw} because its id is not None",
                kw = self)
        self.count += 1
        return KW(self.name, self.count)
    def __eq__(self, other):
        return (type(self) == type(other)
                and self.name == other.name)
    def __hash__(self):
        return hash(self.name)
    def __str__(self):
        if self.id:
            return "<%s/%s>" % (self.name, self.id)
        else:
            return "<%s>" % self.name
    def __repr__(self):
        return self.__str__()
