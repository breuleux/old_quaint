
import math

from ..parse.generic import pyparsing as P, linecol
from ..parse.standard import codec
from functools import reduce
from html.entities import codepoint2name as html_entities


__all__ = ['Format',
           'TermFormat', 'TermPlainFormat', 'TermColorFormat',
           'HTMLFormat',
           'basic_html_style',
           'highlight']


##################
### FORMATTERS ###
##################

class Format(object):
    """
    Base class for formats.
    """

    def __init__(self, lineno, encode = False):
        """
        lineno :: Boolean: do we show line numbers?

        encode :: Boolean: (default: False) do we encode the source
            with the quaint encoding?  (-> instead of a rightwards
            arrow symbol, \\union\\ instead of the union symbol, etc.)
        """
        self.lineno = lineno
        self.encode = encode

    def sanitize(self, text):
        if self.encode:
            return codec.encode(text)
        else:
            return text


class TermFormat(Format):
    """
    Base class for printing highlighted source to a terminal.
    """

    def __call__(self):
        t = self.__class__(self.lineno, self.encode)
        t.i = -1
        t.maxi = -1
        t.current = ""
        t.lines = []
        return t

    def describe(self, text, attribute):
        return text

    def new_line(self, i):
        assert self.current == ""
        self.i = i
        if i > self.maxi: self.maxi = i

    def end_line(self):
        self.lines.append((self.i, self.current))
        self.current = ""

    def lead_length(self):
        return int(math.log(max(self.maxi, 1))/math.log(10)) + 2


class TermColorFormat(TermFormat):
    """
    Format to print text with color highlights to a terminal.

    Recognizes attributes of the form "<color><attribute>", where
    color is one of "red", "green", "yellow", "blue", "magenta",
    "cyan", "white", and attribute is one of "" (normal), "*" (bold),
    "_" (underline), "%" (blink) or "!" (reverse). For example "red*"
    means bold red, "green" means normal green, "yellow%" means
    blinking yellow, and so on.

    __init__ takes two flags:

    lineno :: Boolean: do we show line numbers?

    encode :: Boolean: (default: False) do we encode the source
        with the quaint encoding?  (-> instead of a rightwards
        arrow symbol, \\union\\ instead of the union symbol, etc.)
    """

    attributes = {'': 0, # nothing
                  '*': 1, # bold
                  '_': 4, # underline
                  '%': 5, # blink
                  '!': 7, # reverse
                  }

    colors = dict(red = "31",
                  green = "32",
                  yellow = "33",
                  blue = "34",
                  magenta = "35",
                  cyan = "36",
                  white = "37"
                  )

    def describe(self, text, color):
        if color:
            if color[-1].isalpha():
                color_code = self.colors[color]
                attr_code = self.attributes['']
            else:
                color_code = self.colors[color[:-1]]
                attr_code = self.attributes[color[-1]]
            return "\x1B[%(attr_code)s;%(color_code)sm%(text)s\x1B[0m" % locals()
        else:
            return text

    def add(self, text, color):
        text = self.sanitize(text)
        self.current += self.describe(text, color)

    def get(self):
        if self.lineno:
            lead_length = self.lead_length()
            return "\n".join(("%i:" % i).rjust(lead_length) + line
                             for i, line in self.lines)
        else:
            return "\n".join(line for i, line in self.lines)


class TermPlainFormat(TermFormat):
    """
    Format to print text with no color highlights to a
    terminal. Instead, a line will be printed below each line of
    source code, and excerpts will have a specific symbol printed
    below them.

    Recognizes one character strings as attributes. If an excerpt is
    given attribute "^", that character will be printed on the line
    right below the excerpt.

    __init__ takes two flags:

    lineno :: Boolean: do we show line numbers?

    encode :: Boolean: (default: False) do we encode the source
        with the quaint encoding?  (-> instead of a rightwards
        arrow symbol, \\union\\ instead of the union symbol, etc.)
    """

    def __call__(self):
        t = super(TermPlainFormat, self).__call__()
        t.current_below = ""
        return t

    def describe(self, text, label):
        if label:
            return "%s (%s)" % (text, label)
        else:
            return text

    def end_line(self):
        super(TermPlainFormat, self).end_line()
        if self.current_below.strip():
            self.lines.append((None, self.current_below))
        self.current_below = ""

    def add(self, text, label):
        text = self.sanitize(text)
        self.current += text
        self.current_below += (label or " ") * len(text)

    def get(self):
        if self.lineno:
            lead_length = self.lead_length()
            return "\n".join(("" if i is None else "%i:" % i).rjust(lead_length) + line
                             for i, line in self.lines)
        else:
            return "\n".join(line for i, line in self.lines)


class HTMLFormat(Format):
    """
    Format to produce an HTML table showing highlighted source code.

    Recognizes class names as attributes. Each excerpt will be
    embedded in a <span> of the given class. The style associated to
    each of these classes should be given separately in a style sheet.

    HTMLFormat will produce a table of class quaint_source. Each row
    will have the class sourcerow<i> where i is the line number's
    parity. The td containing the line number will have class name
    lineno, the td containing the source code will have class
    sourceline. These are not customizable (for now, anyway).

    The basic_html_style global variable in this module contains a
    string with a style defined for the source code table. It can be
    used in concert with custom style for the code's highlights.

    __init__ takes two flags:

    lineno :: Boolean: do we show line numbers?

    encode :: Boolean: (default: False) do we encode the source
        with the quaint encoding?  (-> instead of a rightwards
        arrow symbol, \\union\\ instead of the union symbol, etc.)
    """

    def sanitize(self, text):
        """
        Escapes all non-ASCII characters as well as the special
        characters <>&'" using html entities. If encode = True, the
        source code will be displayed as plain ASCII using the
        quaint encoding.
        """
        text = super(HTMLFormat, self).sanitize(text)
        # honestly this is pretty terrible, this functionality has got
        # to be somewhere in a standard lib
        return "".join(
            (c if (ord(c) < 128 and c not in '&<>"')
             else "&%s;" % (html_entities.get(ord(c), None) or ("#%i" % ord(c))))
            for c in text)

    def __call__(self):
        t = self.__class__(self.lineno, self.encode)
        t.text = "<table class=quaint_source>\n"
        return t

    def new_line(self, i):
        self.text += "<tr class=sourcerow%i>" % (i % 2)
        if self.lineno:
            self.text += "<td class=lineno>%i</td>" % i
        self.text += "<td class=sourceline>"

    def end_line(self):
        self.text += "</td></tr>\n"

    def add(self, text, cls):
        text = self.sanitize(text)
        if not cls: cls = 'default'
        self.text += "<span class=%(cls)s>%(text)s</span>" % locals()

    def get(self):
        self.text += "</table>\n"
        return self.text


basic_html_style = """
table.quaint_source {
  border-collapse:collapse;
  font-family: monospace;
  white-space: pre
}

td.lineno {
  border-right: 3px solid;
  text-align: right;
  padding-right: 5px
}

tr.sourcerow1 {
  background-color: #f8f8ff
}

td.sourceline {
  padding-left: 5px
}
"""



# ################
# ### LOCATION ###
# ################

# class Location(object):
#     """
#     Location object - meant to represent some code excerpt. It
#     contains a pointer to the source and a (start, end) tuple
#     representing the extent of the excerpt in the source.

#     Methods are provided to get line/columns for the excerpt, raw or
#     formatted, and to highlight the excerpt in the source code.
#     """
#     def __init__(self, source, span, tokens):
#         self.source = source
#         self.span = span
#         self.start = span[0]
#         self.end = span[1]
#         self.tokens = tokens
#         self._linecol = None

#     def __len__(self):
#         return self.span[1] - self.span[0]

#     def linecol(self):
#         if self._linecol is not None:
#             return self._linecol
#         self._linecol = linecol(self.source, self.start, self.end) # ((l1, c1), (l2, c2))
#         return self._linecol

#     def ref(self):
#         """
#         Returns a string representing the location of the excerpt. If
#         the excerpt is only one character, it will format the location
#         as "line:column". If it is on a single line, the format will
#         be "line:colstart-colend". Else,
#         "linestart:colstart-lineend:colend". In the special case where
#         the excerpt is a token not in the source text (e.g. one that
#         was inserted by the parser), "<" will be appended to the end.
#         """
#         ((l1, c1), lc2) = self.linecol()
#         if lc2 is not None:
#             l2, c2 = lc2
#         if lc2 is None or l1 == l2 and c1 == c2:
#             return ("%s:%s" % (l1, c1)) + ("<" if lc2 is None else "")
#         elif l1 == l2:
#             return "%s:%s-%s" % (l1, c1, c2)
#         else:
#             return "%s:%s-%s:%s" % (l1, c1, l2, c2)

#     def highlight(self, attribute = "green*", format = TermColorFormat(True), context = 0):
#         return highlight([(self, attribute)], format, context)

#     def __add__(self, loc):
#         return merge_locations([self, loc])

#     def __radd__(self, loc):
#         return merge_locations([loc, self])

#     def __str__(self):
#         return self.ref()

# def lineno(start, source):
#     x = P.lineno(start, source)
#     return x + (source[start] == '\n')

# def col(start, source):
#     x = P.col(start, source)
#     return x - (source[start] == '\n')

# def linecol(source, start, end, promote_zerolength = False):
#     end -= 1 # end position is now inclusive
#     l1, c1 = lineno(start, source), col(start, source)
#     if start > end:
#         return ((l1, c1), (l1, c1) if promote_zerolength else None)
#     l2, c2 = lineno(end, source), col(end, source)
#     return ((l1, c1), (l2, c2))

# def merge_locations(locations):
#     """
#     Handy function to merge *contiguous* locations. They must be given
#     in the order they appear (note: assuming that you did give a, b, c
#     in the right order, merge_locations(a, b, c) does the same thing
#     as merge_locations(a, c). However, a future version of the
#     function might differentiate them, so *don't do it*)

#     TODO: it'd be nice to have a class for discontinuous locations, so
#     that you could highlight two tokens on the same line that are not
#     next to each other. Do it if a good use case arise.
#     """
#     locations = [loc for loc in locations if loc]
#     if not locations:
#         return Location("", (0, 0), [])
#         #raise Exception("You must merge at least one location!")
#     loc1, loc2 = locations[0], locations[-1]
#     # locations should be in the same source
#     assert all(loc1.source is l.source for l in locations[1:])
#     return Location(source = loc1.source,
#                     span = (loc1.span[0], loc2.span[1]),
#                     tokens = reduce(list.__add__, (list(l.tokens) for l in locations)))

# def merge_node_locations(nodes):
#     return merge_locations([n.location for n in nodes])



#################
### HIGHLIGHT ###
#################

def highlight(specifications, format, context = 0):
    """
    Returns a highlighted version of the excerpts contained in several
    locations. Each excerpt may be highlighted with different
    attributes (different colors, etc.), A certain number of context
    lines (before the first excerpt and after the last excerpt) may be
    requested.

    specifications: a list of (Location, attribute) pairs. Each
        location represents an excerpt in the source code that will be
        highlighted accordingly to the attribute given.

    format: an function with no arguments returning a stateful object
        which constructs the text. The object returned by format()
        must respond to the following messages: add_line(lineno),
        end_line(), add(text, attribute), get() (to get the result).

    context: an integer >= 0. it is the number of lines that will be
        printed before the first excerpt, and after the end of the
        last excerpt (no lines will be printed before the beginning of
        the source and/or after the end).

    The attributes given in the specifications list have semantics
    that depend on the format. Common formats are TermColorFormat,
    TermPlainFormat and HTMLFormat.

    TODO: does the context work fine on boundaries? It looks like
    it does but maybe it doesn't? Anyway, if there are problems
    it should be obvious enough.

    NOTE: the specifications should be given such that if a location
    is within another location, the inner location should occur
    *before* the outer one (else the highlight for the outer location
    will shadow the inner one). Overlapping locations where one is not
    a strict subset of another should not be given, because their
    extent will not be clearly shown in the highlight.

    NOTE2: actually it seems that the code sorts the specifications
    anyway, but does it do it correctly? It doesn't look like it.
    TODO: investigate, and update the documentation.
    """
    assert specifications
    specifications = list(sorted(specifications, key = lambda loc__a: (loc__a[0].start, -loc__a[0].end)))

    loc1 = specifications[0][0]
    assert all(loc1.source is l.source for l, _a in specifications[1:])
    source = loc1.source

    leftmost = min(location.start for location, attribute in specifications)
    rightmost = max(location.end for location, attribute in specifications)
    (l1, col1), (l2, col2) = linecol(source, leftmost, rightmost, True)

    def insert_span(spans, new):
#         rem = []
        location, attribute = new
        start, end = location.span
#         print "BAH", start, end
        for i, other in enumerate(spans):
            start2, end2, _ = other
            if start2 == end2:
#                rem.append(i)
                continue
            if start2 <= start < end2:
#                 print start2 <= end <= end2, (start, end), (start2, end2)
                other[1] = start
                spans.insert(i+1, [start, end, new])
                if start2 <= end < end2:
                    spans.insert(i+2, [end, end2, _])
                break
        else:
            spans.append([end2, start, [None, None]])
            spans.append([start, end, new])
#         for j in reversed(rem):
#             spans.pop(j)

    # it's probably a bit of a waste of time to split lines, but whatever
    lines = source.split('\n')
    leftmost -= sum(map(len, lines[l1-1-context:l1-1])) + col1 - 1 + context
    rightmost += sum(map(len, lines[l2-1:l2+context])) - col2 + context
    leftmost = max(leftmost, 0)

    spans = [[leftmost, rightmost, [None, None]]]
    for spec in specifications:
        insert_span(spans, spec)

#     for a, b, c in spans:
#         print a, b, repr(source[a:b])
#     print "DONE"

    i = max(l1 - context, 1)
    format = format()
    format.new_line(i)
    i += 1

    for start, end, (location, attribute) in spans:
        these_lines = source[start:end].split('\n')
        format.add(these_lines[0], attribute)
        for line in these_lines[1:]:
            format.end_line()
            format.new_line(i)
            format.add(line, attribute)
            i += 1
    format.end_line()
    return format.get()

