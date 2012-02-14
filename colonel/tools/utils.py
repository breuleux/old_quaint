
import exc

class attrdict(dict):

    def __getattr__(self, attr):
        if attr.startswith("__"):
            return getattr(super(), attr)
        return self[attr]

    def __setattr__(self, attr, value):
        if attr.startswith("__"):
            setattr(super(), attr, value)
        else:
            self[attr] = value


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
            raise exc.Exception['kw/cannot_clone'](
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


class NamedList:

    def __init__(self, title, names, values, print_fields = True):
        self.__dict__['title'] = title
        self.__dict__['names'] = list(names)
        self.__dict__['values'] = list(values)
        self.__dict__['print_fields'] = print_fields

    def __getitem__(self, item):
        if isinstance(item, (int, slice)):
            return self.values[item]
        else:
            return self.values[self.names.index(item)]

    def __setitem__(self, item, value):
        if isinstance(item, (int, slice)):
            self.values[item] = value
        else:
            self.values[self.names.index(item)] = value

    def __getattr__(self, attr):
        values = self.__dict__['values']
        names = self.__dict__['names']
        try:
            return values[names.index(attr)]
        except ValueError:
            if (attr in self.__dict__):
                return self.__dict__[attr]
            else:
                raise AttributeError('{attr} not in {me}'.format(attr = attr,
                                                                 me = self))

    def __setattr__(self, attr, value):
        values = self.__dict__['values']
        names = self.__dict__['names']
        try:
            values[names.index(attr)] = value
        except ValueError:
            self.__dict__[attr] = value

    def __str__(self):
        if self.print_fields:
            return "{title}({args})".format(
                title = self.title,
                args = ", ".join("{n} = {v}".format(n = n, v = v)
                                 for n, v in zip(self.names, self.values)))
        else:
            return "{title}({args})".format(
                title = self.title,
                args = ", ".join(map(str, self.values)))

    def __repr__(self):
        return str(self)

    def __iter__(self):
        return iter(self.values)


def namedlist(title, fields, print_fields = True):
    class builder(NamedList):
        def __init__(self, *args, **kwargs):
            init = args + (None,) * (len(fields) - len(args))
            super().__init__(title, fields, init, print_fields)
            for k, v in kwargs.items():
                self[k] = v
    return builder


