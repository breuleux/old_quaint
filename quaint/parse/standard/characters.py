
from .codec import decode as de
from functools import reduce

__all__ = ['id_lead', 'id', 'op', 'list_sep',
           'unquote', 'escape', 'string_translations',
           'others', 'valid', 'reject']


# Characters that can be the first character of an identifier.

id_lead = de(r"""
a b c d e f g h i j k l m n o p q r s t u v w x y z
A B C D E F G H I J K L M N O P Q R S T U V W X Y Z
_

`aac` `eac` `iac` `oac` `uac` `yac`
`Aac` `Eac` `Iac` `Oac` `Uac` `Yac`
`agr` `egr` `igr` `ogr` `ugr`
`Agr` `Egr` `Igr` `Ogr` `Ugr`
`aci` `eci` `ici` `oci` `uci`
`Aci` `Eci` `Ici` `Oci` `Uci`
`aum` `eum` `ium` `oum` `uum` `yum`
`Aum` `Eum` `Ium` `Oum` `Uum` `Yum`
`ati` `nti` `oti`
`Ati` `Nti` `Oti`
`aring` `Aring`

`alpha` `beta` `gamma` `delta` `epsilon` `zeta` `eta` `theta`
`lambda` `mu` `xi` `pi` `sigma` `tau` `phi` `chi` `psi` `omega`
`Gamma` `Delta` `Theta`
`Lambda` `Xi` `Pi` `Sigma` `Phi` `Psi` `Omega`

`dagger` `eth` `aelig` `oelig` `ccedil` `scaron` `thorn` `oslash`
`Dagger` `ETH` `AElig` `OElig` `Ccedil` `Scaron` `THORN` `Oslash`

`degree` `infinity` `empty`
""").split()


# Characters that can be the second+ characters of an identifier

id = id_lead + "0 1 2 3 4 5 6 7 8 9".split()

############################

# Characters for class 1 (scope builders) (prefix)
c1op = ". @ $ #".split()

# Characters for class 2 (standard) (any fixity)
c2op = de(r"""
+ - * / ~ ^ < > = : ? ! %
`union` `intersection`
`subset` `subseteq` `supset` `supseteq`
`in` `notin`
`after` `cw` `ccw`
`hearts` `spades` `clubs`
`to`
<> =< >= -> ~~ ~= /=

: & |
`and` `or` `not` `nand` `nor` `xor`
`gradient` `integral`
<- ->
<= =>
""").split()

op = [c1op, c2op]

# Characters for list builders (infix)
list_sep = ", ;".split()

# Characters for extended strings
ext_str = [de("<<"), de(">>")]

# Character for variable interpolation
unquote = "$"
vi_op = ["."]

# Escape character inside code
escape = de("`esc`")

# Characters serving other uses
others = de(r"( ) [ ] { } ' \"").split()

# Translations within strings
string_translations = dict((
        de('`br` \n').split(' '),
        de('`tab` \t').split(' ')
        ))

# All valid source code characters
valid = list(set(id_lead
                 + id
                 + reduce(list.__add__, op)
                 + list_sep
                 + ext_str
                 + [unquote, escape]
                 + others))


### REJECTIONS ###

# Rejected for cause of being too similar to other letters:
# left, the rejected character, right, the character it is too similar to
# this list is used to help the user if they use rejected characters
reject = de(r"""
`iota` i
`kappa` k
`nu` v
`omicron` o
`rho` p
`upsilon` u
`Alpha` A
`Beta` B
`Epsilon` E
`Zeta` Z
`Eta` H
`Iota` I
`Kappa` K
`Mu` M
`Nu` N
`Omicron` O
`Rho` P
`Tau` T
`Upsilon` Y
`Chi` X
""").split("\n")
reject = dict(x.split() for x in reject if x)

