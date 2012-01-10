
exception_classes = {}

class BaseExc(Exception):
    def __init__(self, description = "", **arguments):
        try:
            self.description = description.format(**arguments)
        except KeyError as e:
            self.description = (description +
                                " (while trying to fill in the details,"
                                " the following error was raised: KeyError(" + str(e) + ")")
        self.arguments = arguments
    def has_kind(self, kind):
        return self.kind == kind or self.kind.startswith(kind + "/")
    def __str__(self):
        return self.description
    def __repr__(self):
        return str(self)

def Exc(kind):
    if kind in exception_classes:
        return exception_classes[kind]
    else:
        if "/" in kind:
            split = kind.split("/")
            basekind = "/".join(split[:-1])
            base = Exc(basekind)
        else:
            base = BaseExc
        cls = type(kind, (base,), dict(kind = kind))
        exception_classes[kind] = cls
        return cls

