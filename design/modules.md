
# Module system

This document describes a mechanism for code and module sharing in the
Quaint language.

A Quaint program, upon startup, will be given a reference to a
"repository" through which it can access functionality. A
functionality may be a closure, a type definition or class, some data
structure, or a module which gives access to further functionality.

In essence, the functionality should be organized as an arborescence,
although the repository itself may allow more advanced queries (such
functionality, however, is outside the scope of this document).


## Objectives

The repository should combine many features found in revision control
systems with a fine grained authentication and signing system.

### Contents of the repository

For any given "functionality" offered in the repository (which is akin
to a file in a RCS), we would like the following features to hold:

* **live**: the repository does not contain source code *per se*, but
  serialized closures and data. A module is integrated to the system
  by running a program which constructs live objects and closures,
  serializes them and sends them to the repository. For instance,
  whereas the source code of a recursive function would encode the
  recursive call as a string, the live closure in the system would
  contain an actual pointer to itself.

* **updatable**: if a new version of some functionality is available,
  it should be possible to update the repository with it. This update
  may in turn notify any process which has a handle to the
  functionality so that they can switch to the new code.

* **safe**: only the creator of a functionality should be able to
  update it.

  * **signed**: all functionalities should be signed, so that they may
    be trusted regardless of the identity of the server providing them
    (allowing for mirroring whole or parts of repositories).

* **versioned**: the system should keep all functionality ever
  submitted to it. It should be possible for a process to use both new
  and old functionality together, should they choose to do so.

  * **taggable**: each version of a functionality should have tags,
    e.g. `stable`, `bugfix` or `v2`, allowing the user to pinpoint
    which version they want to import (or want to avoid importing).
  
  * Updating the version of some functionality also involves updating
    the version of its parents in the arborescence. Indeed, modifying
    the function `math.svd` means the pointer to the `sgd` function in
    the `math` module must change, so both `math` and `math.svd` now
    have a new version.

* **branchable**: any contributor should be able to create new
  branches for any functionality, representing their own version of
  the code, bug fixes, enhancements, etc. The user of the system
  should have control over what branches to follow in priority when
  exploring it. For instance, a developer may specify to follow their
  branch instead of the master branch whenever possible.
  
  * As for versioning, branching a functionality means branching its
    parent.

* **license-aware**: many licenses are typically used to control the
  use of source code: BSD, GPLv2/3, MIT, etc. The system should
  enforce them to the best of its capability. For instance, a
  functionality called `NoFun` may be defined such that only code with
  a certain license may use it. The system would then only allow that
  license for functionality which contains a reference to `NoFun` in
  its closure. (Note: not all repositories may choose to implement
  this feature, nor is the feature a priority, especially since it
  would likely require writing custom licenses).

### Use of the repository

If a program wants to import a functionality, it may get it at some
location in the arborescence. While one could imagine a way to query a
database for, say, "sorting functions", we will assume that the
program knows exactly what it wants. Still, each functionality
possibly has many versions and many branches, so there are many ways
to explore the tree. Furthermore, as time passes and the program runs
on, new versions may be committed; the program may be interested in
upgrading when that happens, but on the other hand, it may not be too
keen on it either, if stability is paramount.

Here's what a program may want to do when importing functionality:

* **pick a branch**: normally, when accessing a module, one wants to
  follow the master branch. Not always, however. Thus it should be
  possible to specify an *ordered preference list* for use when
  exploring the arborescence. For instance, my list may be `breuleux
  google master`, meaning that if there is a branch by myself I want
  to use it, otherwise I want to use whatever Google did, otherwise
  the master branch will work.

* **static version**: a program may ask for the very latest version of
  the code. It may also ask for the very latest *stable* version: for
  this purpose it filters the tags associated to the
  versions. Finally, it may ask for a time-anchored version, for
  instance the version that was the latest on July 14th.

* **synchronized version**: in the previous situation, the program
  will not be notified of updates to the functionality. Even if it
  asks for the latest version of `math.svd`, once it gets it, it stays
  the same even if a new version is uploaded later on. In contrast,
  one might want to *always* have the latest version: as soon as there
  is an update, the program would be notified and would fetch it so
  that the next use of the functionality uses the latest
  version. There would still be the possibility to filter by tag, so
  that one always has the latest *stable* version.

  * **triggered synchronized version**: there is a slight problem with
    the synchronized version, namely that you might not want to move
    to a new version intempestively in the middle of a
    computation. Instead, as the result of an import, the user may
    obtain a "trigger" function that performs updates at the moment of
    their choosing. The updated functionality may be downloaded
    eagerly in prevision of the update, or lazily.

* **dynamic resolution**: even the two previous cases do not cover all
  possibilities. Indeed, imagine that you make a library `L` which
  uses another library `M`. You might want to let the user of your
  library decide which version of `M` your own library is going to
  work with. In this case, you may use a *dynamic* reference to
  `M`. This reference will respect the user's preferences in branch
  exploration order or "bleeding-edgeness", giving you the same `M`
  that they would use should they import it themselves. To add a
  modicum of control and safety, one may refine the import to avoid
  versions that are known to be incompatible.

* **eagerness**: some modules may be small, others may be huge, and
  the root repository may be gigantic. The user should have some
  control over what parts of the modules they import are downloaded -
  and when. This includes, but might not be limited to:
  
  * **completely lazy**: the contents of a field are downloaded only
    when accessed.
    
  * **completely eager**: the whole subgraph corresponding to the
    module is downloaded at once. This guarantees the module can be
    used offline. The loading may be done asynchronously, with
    accesses blocking when the data is not yet available.
    
  * **speculative lazy**: since communication is expensive, a
    middle-of-the-road approch can be considered where the system
    loads up to a certain quantity of data every time, speculating on
    what is the most likely to be used. For instance, a function may
    be downloaded along with the data and functions it refers to in
    its closure, up to a certain threshold. The repository may also
    collect statistics about likely sequences of downloads, and it is
    reasonable to think a central repository would be able to quickly
    accumulate enough information from multiple clients to make this
    strategy very accurate.
    
  * **tag-based loading**: only load functionality that bears a
    certain (set of) tag(s). To see how that might be useful, a
    developer may tag core functionality explicitly, or "image
    processing" functions, both of which may be of particular interest
    to some users. A large set of precise and useful tags might also
    be obtained through crowd-sourcing. Furthermore, a repository
    might collect statistics about usage and communicate them using
    tags. An exclusion set may also be used, to avoid loading parts
    that are known to be of low priority.
    
  * **cache gc policy**: if a functionality has not been used for a
    long time, even if it is technically accessible, it might not be
    worth it to keep it around locally. In this case one would delete
    the local version of the datum and replace it by a remote
    reference, so that it can be fetched again if need be (note:
    serializing the datum on solid storage should be preferred if
    possible, but something needs to be done if that runs out). It is
    not entirely clear what to provide here, but it is reasonable to
    think that when the user asks for eager loading, they expect the
    data to stick around.

I believe that the three policies regarding versioning (static,
synchronized and dynamic) cover use cases fairly well. A static
version is recommended if only a specific version of a functionality
works with your code: it is pointless, not to mention harmful to
delegate resolution in this case. It is also the most
optimization-friendly option. Synchronized is useful for real time
development and debugging, whereas triggered synchronized is a great
way to safely update a program at discrete moments while it is
running. Finally, dynamic allows the developer of a library to shift
the responsibility of module resolution to its user. There is of
course some overlap: with dynamic resolution, the user may choose for
imports to be static or synchronized, and the library will follow
suit.

Similarly, the various policies for downloading functionality cover
many important use cases. A user who wants to make sure their program
can run offline, or wants to avoid any network delays caused by the
non-availability of functionality may eagerly import everything they
need. Using tags, they can avoid loading what they know they don't
need. A user stingy about memory would prefer a completely lazy
strategy. I speculate that the speculative lazy strategy will fit most
practical uses.


## Mechanism of use

Quaint's module system is *live*, meaning that function and class
definitions are stored in live objects or records served by a local or
remote process. A reference to a port connected to the repository is
provided to a program upon startup in the dynamic variable `@repo`.

Given a path in the arborescence (e.g. `.math.svd`) and a *resolution
policy*, a repository returns the object at that position in the
arborescence given the preferences expressed by the resolution
policy. The policy contains: a *branch resolution order*, to choose
which branches to follow in priority; a *version qualifier* which can
be an integer (up from version 1), a negative integer (down from
latest), a date (which might be the current date), or `bleeding-edge`;
a *loading policy* indicating whether the subtree should be downloaded
in full, lazily or in-between; a *tag whitelist* and a *tag blacklist*
that filter out any versions without or with the specified tags; other
fields yet to be determined.

Example use:

    object = @repo <- [.get, path, policy]

This will fetch a static version of the object, unless the version
qualifier is `bleeding-edge`, in which case the object will be updated
when new versions are available. A dynamic reference, on the other
hand, is such that the policy of the caller must be used. This
translates to the following:

    dynobj = lambda: @repo <- [.get, path, @policy]

Here the object is associated to a parameterless lambda, called on
every access to the variable. The parameters `@policy` is a dynamic
variable set by the caller. Therefore, a user may construct a policy
which loads modules from their own branches when available, and make
sure that the libraries he or she imports do the same, as long as
these libraries allow them to by using a dynamic reference.

Syntactic shortcuts will be provided to import functionality and
define policies.


## Mechanism of contribution

A user may contribute to the repository by building a functionality
(such as a closure or type object) and sending an appropriate message.

    @repo <- [.update, auth, path, branch, functionality, tags]

The `auth` object is a cryptographic token representing the
contributor's access rights, which is also used to sign the
functionality unless the functionality is already signed (which would
be the case if a package's maintainer was simply merging an existing
branch into the trunk). The other parameters do what logic dictates.


## Issues and solutions

There are many potential issues regarding the interaction of different
functionality. Since the repository is a global live system, there are
issues about who can modify what. Since it is versioned and that
different versions of the same functionality can cohabit, there are
issues about how old and new functionality interact.

### Subtyping

A lot of programming languages allow subtyping, and this is usually
done explicitly: one can define a class C, and then a subclass D, such
that any object of class D is also an instance of C. Now, the problem
is: how does the version 2 of class C relate to the version 1 of class
C (and for that matter, how does D relate to both)? If a function
demands an object of class C as its argument, which version(s) is it
going to accept?

One option would be to consider both versions as unrelated. Version 2
can however import version 1 and inherit from it, so that it is
accepted by all functionality expecting v1 of the class. This does
seem a bit... involved (explicitly importing and using your previous
self, though I imagine this can be hidden behind a macro), and
confusing, since the class arborescence becomes considerably more
complicated as a result. Furthermore, it does not allow v1 to inherit
from v2.

Two principles seem adequate to facilitate reasoning about the system
and minimize frictions between different versions of the same things:

* **Separate interface from implementation**, so that updated
  implementations can reuse the same interface. Interfaces indeed tend
  to change much less often than implementations.

* **Eliminate declarations of intent**: an interface for an object
  that's divorced from its implementations merely consists in a list
  of fields and methods the object must have, along with the expected
  interfaces for these fields and methods. An implementation does not
  need to *declare* that it extends some interface in order to satisfy
  it. Avoiding that declaration means the implementation needs not be
  concerned about what versions of the interface it declares that it
  implements, and it does not have to import a reference to the
  interface either. The Go language uses this approach and I believe
  it is what's most appropriate for the proposed system.
  
  This being said, for some purposes it may be useful to allow the
  developer to annotate their intent - verifying that they implemented
  the interface correctly, and it may be useful to disambiguate
  overloading (see next section).

The subtyping relation would be determined by inspection of the
interfaces (so that an interface requiring methods `a` and `b` is
automatically considered a subtype of one that only requires `a`).

### Overloading

Imagine that we have two objects `a` and `b` of types `A` and `B`. It
might make sense to define the addition `a + b` on these objects. If
`a` is a rational number and `b` is a matrix, perhaps we want to add
`a` to all elements of `b`. This language feature is called
*overloading*: the ability to define many versions of the same
function depending on the types of its arguments. It is a rather
useful feature to have, since it allows virtually unlimited
extensibility, e.g. defining the `toString` function to work on
arbitrary custom datatypes.

In our system, however, there are some important stumbling blocks:

* **ambiguity**: suppose interfaces `A` and `B` exist. One may
  overload a funtion `f` to have a certain behavior on objects
  implementing the interface `A` and another on objects implementing
  the interface `B`. So what happens if an object implements *both*
  interfaces? Worse yet, if a developer does not have to declare
  intent in order to implement an interface, then they may implement
  an interface they don't even know about.
  
  One way to solve ambiguity is to shift the responsibility to the
  objects given as arguments (more on that in the *ask the arguments*
  section farther below). Another is to allow developers to annotate
  objects with the interfaces they are meant to implement, in order of
  importance, and use these annotations to disambiguate (this is
  likely insufficient for multiple arguments overloading).

* **responsibility**: in the example given in the intro, *who* defines
  the addition operation? The developer of the `Rational` type, the
  developer of the `Matrix` type, or a third party responsible for the
  `+` operator?

* **acquisition**: when, exactly, is the functionality acquired? In a
  lazy setting that may just be when it is needed, but what happens
  when a developer demands to download functionalities in their
  "entirety"? Does acquiring the `+` operator involve downloading
  every single version of it? There may be tens of thousands of these,
  most of which involving types we have no references to
  (problematically, though, we might acquire these references
  *later*). Does acquiring an object of a certain type trigger the
  download of all versions of all (accessible) functions that involve
  it?

  Given a hundred types and a hundred overloadable functions (`+`,
  `-`, `*`, `toString`, `length`, ...), that's very possibly ten
  thousand implementations. It is unlikely that we will use all of
  them, even though we cannot statically determine the exact subset we
  will use. Downloading everything does not scale, downloading as
  needed may cause problematic delays or failures, so in the interest
  of satisfying all developers it seems that we need a way to perform
  a manual selection.


Here are the various strategies we could employ with respect to
overloading:

1. **disallow overloading**: that's the cheapest solution. A lot of
   dynamic programming languages fall in that category, as does the Go
   language.

2. **ask the arguments**: this is what the Python language does. The
   expression `a + b` is equivalent to `a.__add__(b)`, but if there is
   no such method or that the method returns the special token
   `NotImplemented`, the system tries `b.__radd__(a)`. Thus we only
   need a single definition of the `+` operator which delegates the
   resolution to the first object and then the second. This can be
   generalized to more than two arguments. Finding the code in that
   system is reasonably easy.

   There are a few problems, however: first, if this is the only
   overloading mechanism, every function we might want to overload
   will necessitate an additional field in all types that may be used
   as arguments. Concrete classes may therefore inflate in size to a
   point where it's unreasonable to ever transmit them in full.

   The second problem is that a third party developer cannot modify
   classes that he or she has not written. Therefore, if they write an
   overloadable function `f` and want to support class `C` as an
   argument, they need to make a special case or use a backup
   mechanism that they control. This is seen in Python: if you define
   your own serialization mechanism, you will want to support basic
   datatypes and those of some external libraries, but you can't
   exactly add a `__myserial__` method to each (well, in Python, you
   usually can, but it's slightly tricky and unacceptable for a
   distributed system like ours where many users refer to these
   types).

3. **dynamic interfaces**: this is a refinement of 2. where method
   lookup on objects uses a table provided in a dynamically scoped
   variable. In this system, each object holds a reference to a token
   that identifies its concrete type. A method lookup on an object
   with token `t` would be equivalent to `@dispatch[t, method]`. By
   constructing a custom `@dispatch` table, a user would gain control
   over what methods what types have.

   The main advantage of this method is that it allows the user
   virtually total control over how certain operations work. Consider
   addition of integers with doubles: typically, the result would be a
   double, but in some circumstances you might prefer to always cast
   *down*. With the system presented here you would simply use a
   slightly modified dispatch table for use for a certain block of
   code, where some entries for the methods corresponding to the `+`
   operator would be modified. The change would not apply to code
   executing remotely, in other threads, or outside of the targeted
   block.

   Another potential use is overriding to `toString` method to use
   ANSI color codes or to print out html. All you would need to do
   would be to find proper implementations of that method for a
   variety of types and modify `@dispatch` around the block of code
   you want to execute. No other threads, processes or remote nodes
   would see the changes. Yet another use case would be declaring a
   `mark` method on all objects for use within a procedure or a group
   of procedures that visit a graph of objects. The marks would
   disappear as soon as the scope defining them is popped off the
   stack.


## Related work

### Spoon

Spoon is a fork of Squeak (Smalltalk) that offers distributed
computing features. They seem to have an interesting module system but
I need to read more about it (even though documentation seems a bit
scarce).

### Oz

Oz has a module system based on a structure they call a
"functor". Requirements between functors are made explicit. Functors
can be serialized along with precomputed data, which is a step in the
direction our system aims to go, and thus they can be communicated in
a distributed fashion. It does not, however, offer versioning-aware
imports, nor branching or tagging.

I believe my use of dynamically scoped variables is expressive enough
to subsume the idea of functor and is in fact capable of doing more.

### Racket

Racket has a centralized versioned repository, but the modules are not
"live" as in the proposed system. It does not seem to have been
written with distribution in mind.









