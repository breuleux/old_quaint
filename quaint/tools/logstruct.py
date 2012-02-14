

def noop(*x, **y):
    pass


class Logged:

    def __init__(self):
        self.__logger__ = noop

    def log(self, *data):
        self.__logger__(self, *data)

    def log_with(self, logger = noop):
        self.__logger__ = logger


class LL(Logged):
    # stands for logged list

    def __init__(self, elements = []):
        self.__logger__ = noop
        self.__elems__ = []
        self.__committer__ = noop
        for element in elements:
            self.append(element)

    def log_with(self, logger = noop):
        super().log_with(logger)
        for child in self[:]:
            if hasattr(child, 'log_with'):
                child.log_with(logger)

    def __getitem__(self, item):
        return self.__elems__[item]

    def __setitem__(self, item, value):
        if isinstance(item, slice):
            assert not item.step
            start = item.start or 0
            stop = item.stop or len(self)
            value = list(value)
            self.log('ll', start, stop, value)
        else:
            self.log('ll', item, item + 1, [value])
        self.__elems__[item] = value

    def __delitem__(self, item):
        if isinstance(item, slice):
            assert not item.step
            value = list(value)
            self.log('ll', item.start, item.stop, [])
        else:
            self.log('ll', item, item + 1, [])
        del self.__elems__[item]

    def append(self, element):
        elms = self.__elems__
        self.log('ll', len(elms), len(elms), [element])
        self[len(self):] = [element]

    def extend(self, elements):
        elms = self.__elems__
        self.log('ll', len(elms), len(elms), elements)
        self[len(self):] = elements

    def __iadd__(self, elements):
        self.extend(elements)
        return self

    def insert(self, n, value):
        self[n:n] = [value]

    def index(self, value):
        return self.__elems__.index(value)

    def remove(self, value):
        idx = self.index(value)
        self[idx:idx+1] = []

    def pop(self, n = -1):
        val = self[n]
        self[n:n+1] = []
        return val

    def __len__(self):
        return len(self.__elems__)


class LAD(Logged):
    # stands for logged attribute dictionary

    def __init__(self, attributes = {}, **extra):
        self.__logger__ = noop
        self.__props__ = {}
        self.__committer__ = noop
        for x, y in attributes.items():
            self[x] = y
        for x, y in extra.items():
            self[x] = y

    def log_with(self, logger = noop):
        super().log_with(logger)
        for name, child in self.items():
            if hasattr(child, 'log_with'):
                child.log_with(logger)

    # Dict behavior
    def __getitem__(self, item):
        if item.endswith("_"):
            item = item[:-1]
        item = item.replace("_", "-")
        return self.__props__[item]

    def __setitem__(self, item, value):
        if item.endswith("_"):
            item = item[:-1]
        item = item.replace("_", "-")
        self.log('lad', item, value, self.__props__.get(item, None))
        self.__props__[item] = value

    def __delitem__(self, item):
        self.log('lad', item, None, self.__props__.get(item, None))
        del self.__props__[item]

    def __getattr__(self, attr):
        if attr.startswith("__"):
            return getattr(super(), attr)
        try:
            return self[attr]
        except KeyError as e:
            raise AttributeError(e)

    def __setattr__(self, attr, value):
        if attr.startswith("__"):
            super().__setattr__(attr, value)
        else:
            self[attr] = value

    def __delattr__(self, attr):
        if attr.startswith("__"):
            super().__detattr__(attr)
        else:
            del self[attr]

    def items(self):
        return self.__props__.items()

    def __len__(self):
        return len(self.__props__)


class LADLL(LAD, LL):

    def __init__(self, attributes = {}, **extra):
        LAD.__init__(self, attributes, **extra)

    def log_with(self, logger = noop):
        super().log_with(logger)
        for child in self[:]:
            if hasattr(child, 'log_with'):
                child.log_with(logger)
        for name, child in self.items():
            if hasattr(child, 'log_with'):
                child.log_with(logger)

    def __getitem__(self, item):
        if isinstance(item, (int, slice)):
            return LL.__getitem__(self, item)
        else:
            return LAD.__getitem__(self, item)

    def __setitem__(self, item, value):
        if isinstance(item, (int, slice)):
            LL.__setitem__(self, item, value)
        else:
            LAD.__setitem__(self, item, value)

    def __delitem__(self, item):
        if isinstance(item, (int, slice)):
            LL.__delitem__(self, item)
        else:
            LAD.__delitem__(self, item)

    def __len__(self):
        return LL.__len__(self) + LAD.__len__(self)


