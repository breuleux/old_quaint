
# Dynamically scoped variables

A dynamically scoped variable is similar to a global variable, in the
sense that it is seen by all functions and all processes. Its value,
however, may be different depending on which thread of execution we
are in. More specifically, any block of code may be wrapped in such a
way that we may control the values for the dynamic variables seen by
all functions called from within that block. Here is an example, which
overloads the `let` statement to handle these variables:

    def f[]:
        print @x
        
    let (@x = "world"):
        let (@x = "hello"):
            f[] ;; prints "hello"
        f[] ;; prints world"

A dynamically scoped environment may be represented as a table where
each variable is associated to a stack. The current value of a dynamic
variable is located at top of the stack. A `let` statement "pushes"
the new value for each variable it touches, executes the statements
within, and then "pops" them out.


## Use in a distributed system

Since dynamically scoped variables are part of the global execution
environment, they are not stored in closures. When executed, a closure
will simply fetch whatever value its caller made accessible. This has
of course the consequence that transmitting a closure does not
transmit any dynamically scoped variables (though a dynamic variable
can be put in a closure explicitly by storing it in a lexical
variable).

This has the interesting implication that we can provide node-specific
information and resources through dynamic variables. For instance, the
dynamic `@print` function may communicate to standard out on whichever
terminal the process is attached to. By contrast, a lexical `print`
function would print on the terminal of the closure's *creator*.

We thus end up with a powerful way to differentiate between "a
resource on a particular machine" and "a resource on whatever machine
we happen to be running on".

While it might also appear to provide a form of security by preventing
transmission within closures of critical resources (like the
filesystem), there is no provision against malicious or inattentive
code transferring resources to lexical variables and transmitting them
that way. It *does*, however, allow a user to limit the resources
accessed by unsafe code running on their machine, simply by clearing
the dynamic variables associated to these resources.


## Sub-environments

The system should have nested dynamic scopes: for instance, the
dynamic variable `@local` may guard access to more dynamic variables
such as `@local.print`, `@local.openfile`, etc.


## Planned uses

* `@local`: resources local to this node: stdin, stdout, command line
  arguments, filesystem, sockets, etc.
  
* `@import`: reference to a code repository and to a policy encoding
  how to consult the repository.
  
* `@dispatch`: table mapping types to interfaces.


## Optimization

The standard dynamically scoped variables (`@local`, `@import` and
`@dispatch`) are important enough to justify storing them in
pre-allocated stacks for each thread. Given that accesses are likely
to happen much more often than stack operations, we can mirror the top
values of these stacks to contiguous slots in predetermined
offsets. Therefore, fetching their values should be about as cheap as
fetching a stack variable. We can even place them in registries if
warranted.

For other dynamically scoped variables, we would normally need a table
for each thread mapping variable ids to corresponding stacks. However,
we can keep a *cache* of stack addresses: for each access to a dynamic
variable, we keep a reference (in the code stream) to the current
version of the environment and the result of the lookup. Each stack
operation on any variable will change that version, but as long as the
dynamic environment remains unchanged, we can reuse the result of the
lookup. The scheme can be made more robust with the following tricks:

1. We can hash the variable id and keep a different version of the
   environment for each value of the hash. This means only variables
   with the same hash can interfere with each other.
   
2. We can track how many times a variable id is changed or
   "forked". If it is forked enough, we can decide to handle it
   specially. To see how that could work, we can imagine that we have
   20 hashing bins, the first ten hold variable ids that seldom change
   and the last ten hold variable ids that change often. The normal
   hashing function would yield a number from 1 to 10, but in certain
   circumstances variables may be given an explicit hash from 11 to
   20.
   
3. In order to diminish conflicts with other threads (which have
   different environments), we can keep a small number of cache
   entries, that we can either scan linearly (upkeep of the entries
   would be done FIFO) or index using the hash of the current thread
   id.
   
4. We can keep count of how many cache misses are incurred by each
   thread and try to "fix" the cache, either by enlarging it or by
   giving offending threads dedicated cache entries.

The same principle goes for the `@dispatch` mechanism, which is
essentially a sub-environment. For each object, we can keep a cache of
the interface used for it.

In this system, dynamically scoped variables are meant as a way for
the caller of a function to control the access of that function to
resources, to provide parameters to functionality several layers down
the call stack, or simply to serve as configuration variables. For
this reason, we should not expect many changes in the dynamic
environment.

Therefore, I believe that the mechanisms proposed in this section
should be adequate in recovering near optimal performance in the
average case. I have also proposed a way to mitigate the effect of
particularly volatile dynamically scoped variables on the system as a
whole.


## More optimization

In the expression `@x + @x`, it stands to reason that `@x` is going to
evaluate twice to the same thing. No thread other than the current
thread can possibly modify `@x`. We can therefore automatically
optimize the code to only fetch the value once. This is especially
useful if there is a loop repeatedly accessing the same dynamic
variable.

We can go further: in the expression `@x + f[]`, where `f[]` fetches
`@x`, we can compile a specialized version of `f` that inlines the
value of `@x` we found here. This new version can be used in place of
all occurrences of `f` in the current block, including within loops.

The system aims, among other things, to allow dynamically overriding
the default behavior of arithmetic operations. For instance, one might
want to prevent addition from ever creating bigints, raising an
overflow exception instead. We might think that the performance of the
`sum[vector]` function, which sums all the elements of a vector, would
suffer horribly from this.

However, upon entering the `sum` function, we can reasonably suspect
that lookups for the implementation of addition is always going to
yield the same result. We can formally verify this by doing a type
analysis, since we know the lookup table does not change. So if we can
determine that the `+` operation in the loop over the vector's
elements will always receive the same types of operands and will
always do the exact same thing, we can safely optimize it and even
inline the machine instructions.

Note that the strict delineation of dynamic scopes makes this kind of
analysis easier by greatly reducing the possibility of interference
between sibling calls: as it was explained before, in the expression
`@h[f[x], g[y]]`, neither `f` nor `g` can possibly interfere with the
resolution of `@h`. In this sense, dynamic scoping can *help* forcing
optimization: if you suppose that the implementation of addition is
controlled dynamically, one could conceivable force it to *only* work
on integers. Thus, even if the optimizer fails to make a proper type
inference, it can nonetheless determine statically that `+` will
either add integers or fail. This is both a boon for type inference
(because we now know the result of the operation is an integer) and an
easy optimization: at worst, all you need is a type guard and a
machine addition.

Now, that does not tell us *when* to perform the analysis and
optimization. One answer is simple statistical analysis telling us
where hotspots are located, followed by harvest of more useful
statistics. The system knows what kind of information it needs: it
needs information on what type of data is typically found around these
hot spots and the results of the lookups for the implementations to
use. With this information in hand it can do type inference and create
a version of the function that obviates the need for the vast majority
of lookups, if not all of them, both in its body and in the bodies of
the functions it is calling.

Another idea is that you can actually "hint" to the optimizer that
some optimizations are worth doing. Consider the following code:

    def sum2[vector]:
        if (@adder == overflow_adder):
            sum[vector]
        else:
            sum[vector]

Technically, `sum2` is rigorously equivalent to `sum`: both branches
of the conditional do the same thing. However, the optimizer can
easily statically infer the value of the variable `@adder` in the
first branch of the `if` and optimize the call to `sum` that's located
there. Now, the optimizer could just as well remove the check, but it
*is* a hint that it can pick up on.

Finally, an implementer may also choose to only support a specific
case, in which case the optimization is glaring enough that they may
assume it will be performed:

    def isum[vector]:
        let (@adder = overflow_adder
             result = 0):
            for (entry in vector):
                result = result + entry
            result


## Security features

Now that I think about it, it should be possible to specify certain
dynamic variables as "volatile" or "unstorable". The idea,
essentially, is that propagating the dynamic variable would create
references that expire when the dynamic variable is unwound:

    def f[]:
        save = @x
        return lambda[]: print save
            
    let (@x !!= "hello"):
        g = f[]
        g[] ;; prints "hello"
    g[] ;; error: @x expired and so did the "save" variable
    
An error would also happen if `g` is transmitted to another process.
This would enhance security by preventing resource access from
leaking, though I do not think this is a compelling security feature.


### Monotonic variables

Imagine that whether a process succeeds or fails in reading a file
depends on the value of the dynamic variable `@canopen`. This seems
rather useless, since a process can just do `let (@canopen = true):
...` and gain permission anyway. However, we could posit the existence
of *monotonous* dynamic variables such that it is not possible to push
"true" after "false", or vice versa. In that case, setting `@canopen`
to false would decisively prevent any file from being opened within
the activation block. Such variable might have slightly different
syntax, e.g. `@+canopen`, or might be declared as monotonous in some
other way without making uses stand out.

In any case, this seems like a good way to wrap untrusted code, as
long as care is given to guard *all* accesses to the resources. There
should also be one single monotonic variable that can block access to
all resources at once.

A general use of this idea would be the ability to "shut down"
objects. Each object would have a monotonous dynamic variable
controlling its access, such that setting it to false makes any code
within the activation block unable to use the object. While whitelists
are much superior ways to control access than blacklists, it is not
always easy to make sure you are *not* giving a process more than it
needs, so it is reassuring to be able to selectively lock down objects
that you definitely don't want to go anywhere.

Another use would be a feature like `@+boundcheck`, which turns off
array bound checking when false, but cannot be switched from true to
false. Should the user turn it off for a script at startup, they would
be able to forego bound checks except for some code that's either less
stable or less trusted.


## Examples

Note `a <- b` sends message `b` to port `a`, and `remote` is assumed
to be some remote process that executes every closure sent to it.

1. Printing on different terminals

    def f[]:
        @local.print["hello world"]
    f[]          ;; prints "hello world" here
    remote <- f  ;; prints "hello world" on remote terminal


2. Printing on the same terminal by capturing `@local.print`
   lexically.

    let (print = @local.print):
        def f[]:
            print["hello world"]
        f[]          ;; prints "hello world" here
        remote <- f  ;; prints "hello world" here as well
        
        
3. Accessing remote files

    def getfile[filename, origin]:
        origin <- @local.open[filename]

    let ([send, recv] = makeport[]):
        remote <- lambda []: getfile["file.txt", send]
        for (file in recv):
            for (line in file):
                @local.print[line]


4. "Saving" the whole dynamic environment (`@`) with a closure:

    def save[fn]:
        let (local = @):
            lambda args:
                let (@ = local):
                    fn args

    def f[]:
        @local.print["hello world"]

    remote <- save[f] ;; prints "hello world" on this terminal

   Note: it is unclear how that would work in the presence of
   monotonic variables. Some version of `save` might be provided as a
   primitive.


5. Manipulating the rules of arithmetic. `@arith.support` may be set
   to a list of types that arithmetic operations support. If only one
   type is in that list, numbers are created with that type or coerced
   to it, if need be. Note that this is just a possible interface.

    def test[n, type]:
        let (@arith.support = [type]):
            let (vector = math.ones[n] / n
                 result = vector.sum[]):
                result

    @local.print[test[100, int32]]       ;; 0
    if (float64perf[@local.arch] < float32perf[@local.arch] / 2):
        @local.print[test[100, float32]] ;; 0.99999997764825821
    else:
        @local.print[test[100, float64]] ;; 1.0000000000000007

   Using int32 returns 0, obviously, because all divisions become
   integer divisions. Then I verify how float64 fares relatively to
   float32 on the local architecture, and if it's more than twice as
   slow I use float32.

   Nodes may provide different defaults depending on their affinities,
   meaning that for instance a 32-bit machine might work with `int32`
   by default and a 64-bit machine might work with `int64` by default.
   
   A distributed system could enforce consistency either by
   communicating arithmetic preferences along with closures (see 4.)
   or by making sure all nodes have the same dynamic environment
   (*sans* resources, which are obviously different from a place to
   another). This can be done easily if all nodes are commonly
   administrated; otherwise, two nodes can communicate their
   respective environments to each other and verify whether they are
   the same or not. Assuming a certain level of standardness in
   environments, it should be possible to only communicate the
   (hopefully small) difference.





