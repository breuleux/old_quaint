
from ..generic.codec import Codec

__all__ = ['delim', 'delim_start', 'delim_end',
           'digraphs',
           'annotated_identifiers', 'identifiers',

           'codec', 'encode', 'decode']

# delim = r"\\"
delim = r"``"
delim_start, delim_end = delim

# a-zA-Z0-9 and \-=~<>/|'"^`
idchars = 'a-zA-Z0-9\\\\\\-=~<>/|\'"^`'.replace(delim_start, "").replace(delim_end, "")

digraphs = [
    # Standards digraphs
    ("<>", "\u2666"), #diams
    ("<<", "\u00AB"), #laquo
    ("<=", "\u21D0"), #Left
    ("<-", "\u2190"), #left
    ("=<", "\u2264"), #le
    (">=", "\u2265"), #ge
    (">>", "\u00BB"), #raquo
    ("=>", "\u21D2"), #Right
    ("->", "\u2192"), #right
    ("~~", "\u2248"), #asymp
    ("~=", "\u2245"), #cong 
    ("/=", "\u2260"), #ne

    # Not 100% sure about these two
    ("|-", "\u22A6"),
    ("|=", "\u22A7"),

    (delim_start * 2, delim_start), #double up delim_start to encode it literally
    (delim_end   * 2, delim_end),   #double up delim_end to encode it literally

    # Digraphs that look cool but will probably not be allowed
    # ("<~", u"\u219C"), #lwave
    # ("~>", u"\u219D"), #rwave
]


# Each line of the identifiers table works as follows:
# (("A'", "Aac", "$Aacute",), u"\u00C1"),
# This means that \A'\, \Aac\ and \Aacute\ in a quaint source file
# will all encode unicode point 0x00C1 (capital A with an acute accent).
# The first option in each list is the standard - the quaint encoder
# will always use that option, and others are only available for
# convenience.
# A leading $ or & is just a reminder of what other standards use. It is
# ignored.

# An identifier starting with $ is the standard html entity associated
# to the code point. For instance, e acute is &eacute; in html, so the
# e acute entry in the table is prefixed with $.

# An identifier starting with & is what you'd use in latex to make the
# character, e.g. \wedge in math mode for the and character. Only some
# of these are available for the time being.

annotated_identifiers = [
    # HTML entities, ordered alphabetically
    (("A'", "Aac", "$Aacute",), "\u00C1"),
    (("a'", "aac", "$aacute",), "\u00E1"),
    (("A^", "Aci", "$Acirc",), "\u00C2"),
    (("a^", "aci", "$acirc",), "\u00E2"),
    (("$acute",), "\u00B4"),
    (("&AE", "$AElig",), "\u00C6"),
    (("&ae", "$aelig",), "\u00E6"),
    (("A\\", "Agr", "$Agrave",), "\u00C0"),
    (("a\\", "agr", "$agrave",), "\u00E0"),
    (("$alefsym",), "\u2135"),
    (("$Alpha",), "\u0391"),
    (("$alpha",), "\u03B1"),
    (("$amp",), "\u0026"),
    (("$and", "&wedge",), "\u2227"),
    (("$ang",), "\u2220"),
    (("$Aring",), "\u00C5"),
    (("$aring",), "\u00E5"),
    (("$asymp",), "\u2248"),
    (("A~", "Ati", "$Atilde",), "\u00C3"),
    (("a~", "ati", "$atilde",), "\u00E3"),
    (("A\"", "Aum", "$Auml",), "\u00C4"),
    (("a\"", "aum", "$auml",), "\u00E4"),
    (("$bdquo",), "\u201E"),
    (("$Beta",), "\u0392"),
    (("$beta",), "\u03B2"),
    (("$brvbar",), "\u00A6"),
    (("b", "$bull",), "\u2022"),
    (("intersection", "$cap",), "\u2229"),
    (("Cc", "$Ccedil",), "\u00C7"),
    (("cc", "$ccedil",), "\u00E7"),
    (("$cedil",), "\u00B8"),
    (("$cent",), "\u00A2"),
    (("$Chi",), "\u03A7"),
    (("$chi",), "\u03C7"),
    (("$circ",), "\u02C6"),
    (("club", "$clubs",), "\u2663"),
    (("$cong",), "\u2245"),
    (("$copy",), "\u00A9"),
    (("$crarr",), "\u21B5"),
    (("union", "$cup",), "\u222A"),
    (("$curren",), "\u00A4"),
    (("$Dagger",), "\u2021"),
    (("$dagger",), "\u2020"),
    (("Down", "$dArr",), "\u21D3"),
    (("down", "$darr",), "\u2193"),
    (("$deg", "degree"), "\u00B0"),
    (("$Delta",), "\u0394"),
    (("$delta",), "\u03B4"),
    (("diamond", "diamonds", "$diams",), "\u2666"),
    (("$divide",), "\u00F7"),
    (("E'", "Eac", "$Eacute",), "\u00C9"),
    (("e'", "eac", "$eacute",), "\u00E9"),
    (("E^", "Eci", "$Ecirc",), "\u00CA"),
    (("e^", "eci", "$ecirc",), "\u00EA"),
    (("E\\", "Egr", "$Egrave",), "\u00C8"),
    (("e\\", "egr", "$egrave",), "\u00E8"),
    (("$empty",), "\u2205"),
    (("$emsp",), "\u2003"),
    (("$ensp",), "\u2002"),
    (("$Epsilon",), "\u0395"),
    (("$epsilon",), "\u03B5"),
    (("$equiv",), "\u2261"),
    (("$Eta",), "\u0397"),
    (("$eta",), "\u03B7"),
    (("$ETH",), "\u00D0"),
    (("$eth",), "\u00F0"),
    (("E\"", "Eum", "$Euml",), "\u00CB"),
    (("e\"", "eum", "$euml",), "\u00EB"),
    (("$euro",), "\u20AC"),
    (("exists", "$exist",), "\u2203"),
    (("$fnof",), "\u0192"),
    (("$forall",), "\u2200"),
    (("$frac12",), "\u00BD"),
    (("$frac14",), "\u00BC"),
    (("$frac34",), "\u00BE"),
    (("$frasl",), "\u2044"),
    (("$Gamma",), "\u0393"),
    (("$gamma",), "\u03B3"),
    (("$ge",), "\u2265"),
    (("$gt",), "\u003E"),
    (("LeftRight", "$hArr",), "\u21D4"),
    (("leftright", "$harr",), "\u2194"),
    (("heart", "$hearts",), "\u2665"),
    (("to",), "\u2025"),
    (("$hellip",), "\u2026"), # "to" ?
    (("I'", "Iac", "$Iacute",), "\u00CD"),
    (("i'", "iac", "$iacute",), "\u00ED"),
    (("I^", "Ici", "$Icirc",), "\u00CE"),
    (("i^", "ici", "$icirc",), "\u00EE"),
    (("$iexcl",), "\u00A1"),
    (("I\\", "Igr", "$Igrave",), "\u00CC"),
    (("i\\", "igr", "$igrave",), "\u00EC"),
    (("$image",), "\u2111"),
    (("infinity", "$infin", "infty",), "\u221E"),
    (("integral", "$int",), "\u222B"),
    (("$Iota",), "\u0399"),
    (("$iota",), "\u03B9"),
    (("$iquest",), "\u00BF"),
    (("in", "$isin",), "\u2208"),
    (("I\"", "Ium", "$Iuml",), "\u00CF"),
    (("i\"", "ium", "$iuml",), "\u00EF"),
    (("$Kappa",), "\u039A"),
    (("$kappa",), "\u03BA"),
    (("$Lambda",), "\u039B"),
    (("$lambda",), "\u03BB"),
    (("$lang",), "\u2329"),
    (("$laquo",), "\u00AB"),
    (("Left", "$lArr",), "\u21D0"),
    (("left", "$larr",), "\u2190"),
    (("$lceil",), "\u2308"),
    (("$ldquo",), "\u201C"),
    (("$le",), "\u2264"),
    (("$lfloor",), "\u230A"),
    (("$lowast",), "\u2217"),
    (("$loz",), "\u25CA"),
    (("$lrm",), "\u200E"),
    (("$lsaquo",), "\u2039"),
    (("$lsquo",), "\u2018"),
    (("$lt",), "\u003C"),
    (("$macr",), "\u00AF"),
    (("$mdash",), "\u2014"),
    (("$micro",), "\u00B5"),
    (("$middot",), "\u00B7"),
    (("$minus",), "\u2212"),
    (("$Mu",), "\u039C"),
    (("$mu",), "\u03BC"),
    (("gradient", "$nabla",), "\u2207"),
    (("$nbsp",), "\u00A0"),
    (("$ndash",), "\u2013"),
    (("$ne",), "\u2260"),
    (("$ni",), "\u220B"),
    (("$not",), "\u00AC"),
    (("$notin",), "\u2209"),
    (("$nsub",), "\u2284"),
    (("N~", "Nti", "$Ntilde",), "\u00D1"),
    (("n~", "nti", "$ntilde",), "\u00F1"),
    (("$Nu",), "\u039D"),
    (("$nu",), "\u03BD"),
    (("O'", "Oac", "$Oacute",), "\u00D3"),
    (("o'", "oac", "$oacute",), "\u00F3"),
    (("O^", "Oci", "$Ocirc",), "\u00D4"),
    (("o^", "oci", "$ocirc",), "\u00F4"),
    (("&OE", "$OElig",), "\u0152"),
    (("&oe", "$oelig",), "\u0153"),
    (("O\\", "Ogr", "$Ograve",), "\u00D2"),
    (("o\\", "ogr", "$ograve",), "\u00F2"),
    (("$oline",), "\u203E"),
    (("$Omega",), "\u03A9"),
    (("$omega",), "\u03C9"),
    (("$Omicron",), "\u039F"),
    (("$omicron",), "\u03BF"),
    (("$oplus",), "\u2295"),
    (("$or", "&vee",), "\u2228"),
    (("$ordf",), "\u00AA"),
    (("$ordm",), "\u00BA"),
    (("$Oslash",), "\u00D8"),
    (("$oslash",), "\u00F8"),
    (("O~", "Oti", "$Otilde",), "\u00D5"),
    (("o~", "oti", "$otilde",), "\u00F5"),
    (("$otimes",), "\u2297"),
    (("O\"", "Oum", "$Ouml",), "\u00D6"),
    (("o\"", "oum", "$ouml",), "\u00F6"),
    (("$para",), "\u00B6"),
    (("$part",), "\u2202"),
    (("$permil",), "\u2030"),
    (("$perp",), "\u22A5"),
    (("$Phi",), "\u03A6"),
    (("$phi",), "\u03C6"),
    (("$Pi",), "\u03A0"),
    (("$pi",), "\u03C0"),
    (("$piv",), "\u03D6"),
    (("pm", "$plusmn",), "\u00B1"),
    (("$pound",), "\u00A3"),
    (("$Prime",), "\u2033"),
    (("$prime",), "\u2032"),
    (("$prod",), "\u220F"),
    (("$prop",), "\u221D"),
    (("$Psi",), "\u03A8"),
    (("$psi",), "\u03C8"),
    (("$quot",), "\u0022"),
    (("$radic",), "\u221A"),
    (("$rang",), "\u232A"),
    (("$raquo",), "\u00BB"),
    (("Right", "$rArr",), "\u21D2"),
    (("right", "$rarr",), "\u2192"),
    (("$rceil",), "\u2309"),
    (("$rdquo",), "\u201D"),
    (("$real",), "\u211C"),
    (("$reg",), "\u00AE"),
    (("$rfloor",), "\u230B"),
    (("$Rho",), "\u03A1"),
    (("$rho",), "\u03C1"),
    (("$rlm",), "\u200F"),
    (("$rsaquo",), "\u203A"),
    (("$rsquo",), "\u2019"),
    (("$sbquo",), "\u201A"),
    (("$Scaron",), "\u0160"),
    (("$scaron",), "\u0161"),
    (("$sdot",), "\u22C5"),
    (("$sect",), "\u00A7"),
    (("$shy",), "\u00AD"),
    (("$Sigma",), "\u03A3"),
    (("$sigma",), "\u03C3"),
    (("$sigmaf",), "\u03C2"),
    (("$sim",), "\u223C"),
    (("spade", "$spades",), "\u2660"),
    (("&subset", "$sub",), "\u2282"),
    (("&subseteq", "$sube",), "\u2286"),
    (("$sum",), "\u2211"),
    (("&supset", "$sup",), "\u2283"),
    (("$sup1",), "\u00B9"),
    (("$sup2",), "\u00B2"),
    (("$sup3",), "\u00B3"),
    (("&supseteq", "$supe",), "\u2287"),
    (("&ss", "$szlig",), "\u00DF"),
    (("$Tau",), "\u03A4"),
    (("$tau",), "\u03C4"),
    (("$there4",), "\u2234"),
    (("$Theta",), "\u0398"),
    (("$theta",), "\u03B8"),
    (("$thetasym",), "\u03D1"),
    (("$thinsp",), "\u2009"),
    (("$THORN",), "\u00DE"),
    (("$thorn",), "\u00FE"),
    (("$tilde",), "\u02DC"),
    (("$times",), "\u00D7"),
    (("$trade",), "\u2122"),
    (("U'", "Uac", "$Uacute",), "\u00DA"),
    (("u'", "uac", "$uacute",), "\u00FA"),
    (("Up", "$uArr",), "\u21D1"),
    (("up", "$uarr",), "\u2191"),
    (("U^", "Uci", "$Ucirc",), "\u00DB"),
    (("u^", "uci", "$ucirc",), "\u00FB"),
    (("U\\", "Ugr", "$Ugrave",), "\u00D9"),
    (("u\\", "ugr", "$ugrave",), "\u00F9"),
    (("uml",), "\u00A8"),
    (("$upsih",), "\u03D2"),
    (("$Upsilon",), "\u03A5"),
    (("$upsilon",), "\u03C5"),
    (("U\"", "Uum", "$Uuml",), "\u00DC"),
    (("u\"", "uum", "$uuml",), "\u00FC"),
    (("$weierp",), "\u2118"),
    (("$Xi",), "\u039E"),
    (("$xi",), "\u03BE"),
    (("Y'", "Yac", "$Yacute",), "\u00DD"),
    (("y'", "yac", "$yacute",), "\u00FD"),
    (("$yen",), "\u00A5"),
    (("Y\"", "Yum", "$Yuml",), "\u0178"),
    (("y\"", "yum", "$yuml",), "\u00FF"),
    (("$Zeta",), "\u0396"),
    (("$zeta",), "\u03B6"),
    (("$zwj",), "\u200D"),
    (("$zwnj",), "\u200C"),

    # Additional identifiers, in no particular order
    (("complex",), "\u2102"),
    (("reals",), "\u211D"),
    (("rationals",), "\u211A"),
    (("naturals",), "\u2115"),
    (("integers",), "\u2124"),
    (("xor",), "\u22BB"),
    (("nor",), "\u22BD"),
    (("nand",), "\u22BC"),
    (("after", "circle",), "\u2218"),
    (("cw", "clockw", "clockwise",), "\u21BB"),
    (("ccw", "cclockw", "counterclockwise",), "\u21BA"),
    (("UpDown", "vArr",), "\u21D5"),
    (("updown", "varr",), "\u2195"),
    (("asserts",), "\u22A6"),
    (("models",), "\u22A7"),

    # Special characters for use in strings
    (("br", "lf"), "\u21B2"),
    (("tab", "ht"), "\u21B9"),
    (("esc",), "\u23CF"),

    # Workarounds to encode digraphs literally
    ((">",), ">"),
    (("<",), "<"),
    (("-",), "-"),
    (("=",), "="),
    (("~",), "~"),
    (("|",), "|"),
    (("/",), "/"),
]

# This just removes the $ and & prefixes ($ and & should only ever be used as prefixes)
def process(x):
    return x.replace("$", "").replace("&", "")
identifiers = [(list(map(process, ks)), v) for ks, v in annotated_identifiers]


####################################
########## CONCRETE CODEC ##########
####################################

codec = Codec(delim, digraphs, identifiers, idchars)

encode = codec.encode
decode = codec.decode
