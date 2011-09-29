
import re

__all__ = ["Codec"]

class Codec:
    """
    Codec to encode and decode strings.

    delim: string of length 2

        Delimiters for identifier encoding. For instance, if delim =
        r"\\", then ♥ is encoded as \heart\. If delim = r"``", then ♥
        is encoded as `heart`. If delim = r"{}", then ♥ is encoded as
        {heart}. Each identifier should be encoded by itself, doubled
        up, but this class does not add the option
        automatically. Include the options explicitly as digraphs.

    digraphs: list of pairs of (digraph, character)

        Digraphs are two-character codes that translate to a specific
        unicode character. In order to reduce ambiguity, there are no
        trigraphs. Digraphs should be kept to a minimum and should
        look as much like what they encode as possible.

        Do not forget to include doubled up versions of the delimiters
        that evaluate to a single occurrence (so if your delimiters
        are "{}", include ("{{", "{") and ("}}", "}")). Digraphs have
        priority in decoding.

        IMPORTANT: In order to encode a sequence of two characters
        that would otherwise be interpreted as a digraph, there should
        be a way to encode them between delims. For instance, if "<-"
        encodes a left arrow, but you want to literally write "<-"
        (less-than-minus), and delim = "``", then both "`<`-" and
        "<`-`" should encode the character < followed by the character
        -. You MUST include these options in the identifiers list, for
        all characters found by digraphs. The Codec class brazenly
        assumes that you do (and if you don't, the errors might be
        sneaky).

    identifiers: list of pairs of ([encodings], character)

        Each entry in the encodings list should be such that when
        surrounded by delims, it encodes the character. For instance,
        if there is an entry (["cup", "union"], "∪"), and that delim =
        "``", then "`cup`" and "`union`" encode "∪".

        The first option in each list is the standard encoding for the
        given character - the quaint encoder will always use that
        option, and others are only available for convenience. Note
        that if the character is ASCII, the encoder will ignore the
        provided encodings (unless there is an ambiguity with a
        digraph, see below).

        IMPORTANT: for each character used in digraphs, include an
        entry that is the character itself. For instance, if there is
        a "<-" digraph, then you should put (["<"], "<") and (["-"],
        "-") in the list. Again, the Codec class assumes that you
        include them.

    idchars: a string of characters that will be put in []s in a regexp.

        This should be figured out automatically by this class, but it
        isn't. All characters found in the encoders of the identifiers
        list should be in this list. So this should usually be at
        least "a-zA-Z0-9", and some other characters if you want to
        use them in encodings. Also include "^" if you want hex
        identifier encodings to be recognized.
    """

    def __init__(self, delim, digraphs, identifiers, idchars):
        self.delim = delim
        self.delim_start, self.delim_end = self.delim

        self.digraphs = digraphs
        self.encode_digraphs = dict((v, k) for k, v in self.digraphs)
        self.decode_digraphs = dict(self.digraphs)


        self.identifiers = identifiers
        self.idchars = idchars

        # unicode point -> default encoding
        self.encode_identifiers = dict((v, ks[0]) for ks, v in self.identifiers)
        # encoding -> unicode point
        self.decode_identifiers = {}
        for ks, v in self.identifiers:
            for k in ks:
                self.decode_identifiers[k] = v

        # This regular expression matches digraphs and \identifier\
        # It is like "(digraph1|digraph2|...)|(\idchar*\)", so
        # group 1 captures digraphs and group 2 captures \identifiers\
        decode_regexp_expr = "(" + '|'.join(map(re.escape, self.decode_digraphs)) \
            + (')|%s([%s]*)%s' % (re.escape(self.delim_start),
                                  self.idchars,
                                  re.escape(self.delim_end)))
        self.decode_regexp = re.compile(decode_regexp_expr)

        # A map of {character: [possible_encodings]}, not used by this
        # package except for the emacs mode so far.
        self.all_options = dict((v, ["%s%s%s" % (self.delim_start, k, self.delim_end)
                                     for k in ks])
                                for ks, v in self.identifiers)
        for k, v in self.digraphs:
            self.all_options.setdefault(v, []).append(k)

        # A map of {character: main_encoding} used for encoding.
        self.encode_map = dict([(k, "%s%s%s" % (self.delim_start, v, self.delim_end))
                                for k, v in self.encode_identifiers.items()],
                               **self.encode_digraphs)

    def decode(self, text):
        text = self.decode_regexp.sub(self.__get_unicode, text)
        return text

    def encode(self, text):
        res = []
        previous = None
        for character in text:
            if previous and previous + character in self.decode_digraphs:
                # If the sequence of the previous character and this character
                # is a digraph encoding, like "<-", the second character is put
                # between backslashes (e.g. "<\-\")
                res.append('%s%s%s' % (self.delim_start, character, self.delim_end))
                previous = None
            elif character == self.delim_start:
                # Backslash has to be encoded specially
                res.append(self.delim_start * 2)
                previous = None
            elif character == self.delim_end:
                # Note: delim_end doesn't need to be encoded specially,
                # since it has no special meaning when we are not encoding
                # a character. It might look better if we do, though.
                res.append(self.delim_end * 2)
                previous = None
            elif ord(character) <= 127:
                # Standard ascii is unchanged
                res.append(character)
                previous = character
            else:
                if character in self.encode_digraphs:
                    # Digraph is the priority encoding
                    dig = self.encode_digraphs[character]
                    if previous and previous + dig[0] in self.decode_digraphs:
                        # The previous character might form a digraph with
                        # the first character of this digraph, which is bad
                        # because digraphs are read left-to-right! Only
                        # solution is to put the previous character between
                        # backslashes.
                        res[-1] = "%s%s%s" % (self.delim_start, res[-1], self.delim_end)
                    res.append(dig)

                    # digraphs are read left-to-right, so the next character
                    # can't accidentally form a digraph with dig[1]
                    previous = None
                elif character in self.encode_identifiers:
                    # Then we look for an intelligible identifier
                    res.append("%s%s%s" % (self.delim_start, self.encode_identifiers[character], self.delim_end))
                    previous = None
                else:
                    # If all else fails, we use a numerical encoding (decimal)
                    # TODO: use hex instead?
                    # NOTE: decoder does not yet understand \#####\
                    res.append("%s%i%s" % (self.delim_start, ord(character), self.delim_end))
                    previous = None
        return "".join(res)


    def __get_unicode(self, m):
        # applies on a match object, it should be from self.decode_regexp_expr
        di, id = m.groups() # we get groups 1 and 2
        if di is not None:
            # group 1 matches some digraph from the list of digraphs
            # if the match is from decode_regexp_expr we know it's a valid digraph
            return self.decode_digraphs[di]
        else:
            # group 2 matches something like \blablabla\
            # we just have to look in our database of valid identifiers
            try:
                if id.isdecimal():
                    # id is a number in base 10, we get the corresponding character.
                    return chr(int(id))
                elif id[0] == "^":
                    # id is a number in base 16, we get the corresponding character.
                    return chr(int(id[1:], base = 16))
                return self.decode_identifiers[id]
            except KeyError:
                raise Exception('Unknown character: %s%s%s'
                                % (self.delim_start, id, self.delim_end))
