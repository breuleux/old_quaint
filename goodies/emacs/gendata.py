
from quaint.parse import characters, codec, encode
import codecs
import sys

if __name__ == '__main__':

    if len(sys.argv) < 2:
        print("Usage: python %s FILENAME" % sys.argv[0])
        sys.exit(1)
    filename = sys.argv[1]

    ss = """;; AUTO-GENERATED FILE
;; Can generate with the following command at root of quaint source tree:
;; python3 goodies/emacs/gendata.py goodies/emacs/quaint-data.el

"""

    for typ in ('id_lead', 'id', 'c1op', 'c2op', 'list_sep'): # 'id_lead', 
        s = ""
        for char in getattr(characters, typ):
            opts = set(codec.all_options.get(char, [char]))
            opts.add(encode(char))
            # if any(len(encoding) == 1 for encoding in opts):
            #     continue
            s += "    "
            for encoding in sorted(opts):
                encoding = encoding.replace('\\', '\\\\').replace('"', '\\"')
                s += ' "%s"' % encoding
            s += "\n"
        ss += """

;; Characters in category %s
(setq quaint-%s-characters '(
%s))
""" % (typ, typ.replace("_", "-"), s)

    f = codecs.open(filename, encoding = 'utf-8', mode = 'w')
    print(ss, file = f)
