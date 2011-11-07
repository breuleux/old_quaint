
from quaint.parse import codec
import codecs
import sys

if __name__ == '__main__':

    if len(sys.argv) < 2:
        print("Usage: python3 %s FILENAME" % sys.argv[0])
        sys.exit(1)
    filename = sys.argv[1]

    digraphs_s = ""
    for digraph, char in codec.digraphs:
        char_hex = hex(ord(char))[2:].zfill(4)
        digraphs_s += '    ("%s" . #x%s) ;; %s\n' % (digraph, char_hex, char)

    identifiers_s = ""
    for possibilities, char in codec.identifiers:
        for p in possibilities:
            p = p.replace('\\', '\\\\').replace('"', '\\"')
            char_hex = hex(ord(char))[2:].zfill(4)
            identifiers_s += '    ("%s"%s . #x%s) ;; %s\n' % \
                (p, " " * (20 - len(p)), char_hex, char)

    encode_s = ""
    for char, encoding in sorted(codec.encode_map.items()):
        if ord(char) < 128: continue
        char_hex = hex(ord(char))[2:].zfill(4)
        encoding = encoding.replace('\\', '\\\\').replace('"', '\\"')
        encode_s += '    (#x%s . "%s")%s;; %s\n' % (char_hex, encoding, " " * (20 - len(encoding)), char)

    delim_start = codec.delim_start
    delim_end = codec.delim_end

    s = """;; AUTO-GENERATED FILE
;; Can generate with the following command at root of quaint source tree:
;; python3 goodies/emacs/gencodec.py goodies/emacs/quaint-codec-data.el

(setq quaint-codec-delim-start "%(delim_start)s")
(setq quaint-codec-delim-end "%(delim_end)s")

;; List of digraphs used in quaint
;; (digraph . character_code) ;; the character
(setq quaint-codec-digraphs-list '(
%(digraphs_s)s))

;; List of named codes used in quaint, without the surrounding backslashes.
;; Typing \\identifier\\ encodes the character. A literal backslash is \\\\.
;; (identifier . character_code) ;; the character
(setq quaint-codec-named-codes-list '(
%(identifiers_s)s))

;; Mapping from unicode code points to an encoding.
;; (character_code . encoding) ;; the character
(setq quaint-codec-encode-list '(
%(encode_s)s))
""" % locals()

    f = codecs.open(filename, encoding = 'utf-8', mode = 'w')
    print(s, file = f)
