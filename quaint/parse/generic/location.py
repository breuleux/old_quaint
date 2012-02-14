
from functools import reduce
from . import pyparsing as P


__all__ = ['Location', 'merge_locations', 'merge_node_locations',
           'lineno', 'col', 'linecol']


class Location(object):
    """
    Location object - meant to represent some code excerpt. It
    contains a pointer to the source and a (start, end) tuple
    representing the extent of the excerpt in the source.

    Methods are provided to get line/columns for the excerpt, raw or
    formatted.
    """
    def __init__(self, source, span, tokens):
        self.source = source
        self.span = span
        self.start = span[0]
        self.end = span[1]
        self.tokens = tokens
        self._linecol = None

    def __len__(self):
        return self.span[1] - self.span[0]

    def linecol(self):
        if self._linecol is not None:
            return self._linecol
        self._linecol = linecol(self.source, self.start, self.end)
        return self._linecol

    def ref(self):
        """
        Returns a string representing the location of the excerpt. If
        the excerpt is only one character, it will format the location
        as "line:column". If it is on a single line, the format will
        be "line:colstart-colend". Else,
        "linestart:colstart-lineend:colend". In the special case where
        the excerpt is a token not in the source text (e.g. one that
        was inserted by the parser), "<" will be appended to the end.
        """
        ((l1, c1), lc2) = self.linecol()
        if lc2 is not None:
            l2, c2 = lc2
        if lc2 is None or l1 == l2 and c1 == c2:
            return ("%s:%s" % (l1, c1)) + ("<" if lc2 is None else "")
        elif l1 == l2:
            return "%s:%s-%s" % (l1, c1, c2)
        else:
            return "%s:%s-%s:%s" % (l1, c1, l2, c2)

    def __add__(self, loc):
        return merge_locations([self, loc])

    def __radd__(self, loc):
        return merge_locations([loc, self])

    def __gt__(self, loc):
        return loc.start < self.start

    def __lt__(self, loc):
        return loc.start > self.start

    def __ge__(self, loc):
        return loc.start <= self.start

    def __le__(self, loc):
        return loc.start >= self.start

    def __str__(self):
        return self.ref()

def lineno(start, source):
    x = P.lineno(start, source)
    return x + (source[start] == '\n')

def col(start, source):
    x = P.col(start, source)
    return x - (source[start] == '\n')

def linecol(source, start, end, promote_zerolength = False):
    end -= 1 # end position is now inclusive
    l1, c1 = lineno(start, source), col(start, source)
    if start > end:
        return ((l1, c1), (l1, c1) if promote_zerolength else None)
    l2, c2 = lineno(end, source), col(end, source)
    return ((l1, c1), (l2, c2))

def merge_locations(locations):
    """
    Handy function to merge *contiguous* locations. (note: assuming
    that you gave a, b, c in the right order, merge_locations(a, b, c)
    does the same thing as merge_locations(a, c). However, a future
    version of the function might differentiate them, so *don't do
    it*)

    TODO: it'd be nice to have a class for discontinuous locations, so
    that you could highlight two tokens on the same line that are not
    next to each other. Do it if a good use case arise.
    """
    locations = list(sorted(loc for loc in locations if loc))
    # locations = [loc for loc in locations if loc]
    if not locations:
        return Location("", (0, 0), [])
        #raise Exception("You must merge at least one location!")
    loc1, loc2 = locations[0], locations[-1]
    # locations should be in the same source
    assert all(loc1.source is l.source for l in locations[1:])
    return Location(source = loc1.source,
                    span = (loc1.span[0], loc2.span[1]),
                    tokens = reduce(list.__add__, (list(l.tokens) for l in locations if l.tokens is not None), []))

def merge_node_locations(nodes):
    return merge_locations([n.location for n in nodes])

