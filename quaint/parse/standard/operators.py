
import os
import pickle
from functools import reduce

from ..generic.op import \
    OperatorGroup as Group, \
    FOperatorGroup as FGroup, \
    OpOrder


__all__ = ['is_assignment',
           'is_custom',
           'op_groups',
           'op_order',
           'remove_cache',
           'cont_next',
           'cont_prev']


def is_always_prefix(op):
    return all(c in '.@$' for c in op)

def is_always_postfix(op):
    return op == '&'

def is_always_infix(op):
    return (op in ',;~') or ('←' in op) or (':' in op)


def is_assignment(op):
    return op.op.endswith('←')

def is_custom(op):
    return op not in specific_operators and not is_assignment(op)


# Operators that continuate the next line when at the end of a line
cont_next = [":"]

# Operators that continuate the previous line when at the beginning of
# a line
cont_prev = ["~"]


# It's actually fairly long to calculate the orderings for the groups,
# so we cache everything in a pickle file.
# NOTE: it used to be fairly long, it seems to be fine now

cache_path = __file__[:-3] + ".pickle"
is_cache = os.path.exists(cache_path)

def remove_cache():
    os.remove(cache_path)


if is_cache:
    this_file_modtime = os.stat(__file__).st_mtime
    cache_modtime = os.stat(cache_path).st_mtime
    if this_file_modtime > cache_modtime:
        is_cache = False


if is_cache:

    with open(cache_path, "br") as f:
        op_groups, op_order, specific_operators = pickle.load(f)

else:

    op_groups = dict(
        # Prefixes
        prefixes = Group('none',
                         '.x', # symbol
                         '%x', # syntax
                         '$x', # unquote
                         '?x', # to_infer
                         '@x', # dynamic
                         ),

        # Whitespace
        juxt = Group('left', 'x_y'), # juxtaposition: f[x]
        white = Group('left', 'x__y'), # whitespace: f [x]

        # Suffixes
        suffixes = Group('none', 'x&'),

        # Arithmetics
        add = Group('left', 'x+y', 'x-y'),
        mul = Group('left', '-x', 'x*y', 'x/y', 'x//y', 'x%y'),
        pow = Group('right', 'x^y'),
        inc = Group('left',
                    'x↑y', 'x↓y',
                    '↑x', '↓x',
                    'x↑', 'x↓'),

        # List, set
        seqadd = Group('left', 'x++y', 'x--y'),
        seqmul = Group('left', 'x**y'),
        range = Group('none', 'x‥y'),
        union = Group('left', 'x∪y'),
        inter = Group('left', 'x∩y'),

        # Comparison
        ineq = Group('none',
                     'x<y', 'x>y', 'x>=y', 'x=<y'),
        eq = Group('none',
                   'x==y', 'x/=y', 'x===y', 'x/=/=y'),
        seteq = Group('none',
                      'x⊂y', 'x⊆y',
                      'x⊃y', 'x⊇y',
                      'x∈y', 'x∉y'),

        # Logic
        neg = Group('left', '¬x'),
        conj = Group('left', 'x∧y'),
        xor = Group('left', 'x⊻y'),
        alt = Group('left', 'x∨y'),

        # Assignment
        assign = FGroup('right', is_assignment, 'x←y', 'x⇒y', 'x=y'),
        colon = Group('none', 'x:y'),
        cond = Group('left', 'x|y'),
        type = Group('left', 'x::y', 'x:<y', 'x>:y'),
        agglutinate = Group('left', 'x~y'),

        # Sequencing
        comma = Group('left', 'x,y'),
        semicolon = Group('left', 'x;y'),
        )

    specific_operators = reduce(lambda a, b: a + b.members,
                                iter(list(op_groups.values())),
                                [])

    op_groups['custom'] = FGroup('none', is_custom)

    op_order = OpOrder(**op_groups)

    op_order.priority('prefixes', 'juxt', 'white', 'suffixes',
                      'pow', 'mul', 'add',
                      'ineq', 'neg', 'conj', 'xor', 'alt', 'cond',
                      # 'agglutinate',
                      'assign',
                      'comma', 'semicolon')
    op_order.priority('suffixes', 'inc', 'mul')
    op_order.priority('add', 'eq', 'neg')
    op_order.priority('suffixes', 'range', 'seqmul', 'seqadd', 'eq')
    op_order.priority('seqadd', 'seteq', 'neg')
    op_order.priority('range', 'inter', 'union', 'eq')
    op_order.priority('union', 'seteq')
    op_order.priority('suffixes', 'type', 'assign')
    op_order.priority('suffixes', 'custom', 'assign')
    op_order.priority('agglutinate', 'assign')

    # NOTE: from this point on, keep 'infer = False'. Setting the colon
    # (:) operator as right-associative with all other operators leads to
    # an inconsistent ordering if inference is done as normal (basically,
    # everything will become right-associative with everything, and the
    # OpOrder class will recurse until the stack is expended since it
    # assumes an absence of cycles). Therefore, from the moment these
    # cycles are introduced, all inference should be off.
    for group in op_groups.keys():
        # (:) is right-associative with all operators regardless of the
        # mutual priorities of these operators, meaning that
        # a <op1> b : c <op2> d is always parsed as
        # (a <op1> (b : (c <op2> d))) for all op1, op2, with the
        # following exceptions:
        # - whitespace has strictly higher priority (and also operators
        # with higher priority than whitespace)
        # - agglutinate (!) has strictly lower priority (and also
        # operators with lower priority than agglutinate)
        if group not in ['prefixes', 'juxt', 'white', 'colon']:
            op_order.right_order(group, 'colon', infer = False)
            # op_order.left_order(group, 'agglutinate', infer = False)
        if group not in ['comma', 'semicolon', 'agglutinate', 'colon']:
            op_order.right_order('colon', group, infer = False)
            # op_order.left_order('agglutinate', group, infer = False)
    op_order.left_order('prefixes', 'colon', infer = False)
    op_order.left_order('juxt', 'colon', infer = False)
    op_order.left_order('white', 'colon', infer = False)
    op_order.left_order('colon', 'comma', infer = False)
    op_order.left_order('colon', 'semicolon', infer = False)
    op_order.left_order('colon', 'agglutinate', infer = False)

    with open(cache_path, "bw") as f:
        pickle.dump((op_groups, op_order, specific_operators), f)
