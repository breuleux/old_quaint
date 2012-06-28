
# Data

## Functional data types

Functional data types are immutable and are identified by their
structure and contents (not by an address or gid). They may be freely
copied or merged.

* **basic**: integers, floats, strings or bitstrings. They contain no
  pointers to other values.

* **tuple**: list of pointers to other data.

* **record**: hash table. Keys are all basic, values can be anything.

* **closure**: pair (specially tagged as executable) where the first
  element is an AST (represented using the aforementioned data types)
  and the second is a record mapping variable names to data or
  variables. Note: this is the closure's external interface, not its
  internal implementation.

## Identified data types

TODO: motivation

Identified data types differ from functional data types by the fact
that they are attached to an identifier that identifies them either
locally or on the whole network. Two such objects are the same if and
only if they have the same identifier. It should be impossible from
within the language to forge an identifier or to create structurally
different objects with the same id, and very difficult from outside
the language.

When an object is created on a node, it obtains a local id (which, for
the sake of efficiency and parsimony, might simply be its memory
address), and when it is distributed, it is given a global identifier
or gid.

A functional object may be "wrapped" into a structurally equivalent
identified object. Such a wrapped object will however not be
considered equal or equivalent to the original, because one has an id
and the other has none. Wrapping the same functional object twice must
produce objects with *different* ids. If a local id is equated to an
address, this means wrapping a functional object requires copying it
(though only shallowly). It is also possible to *unwrap* an identified
object to recover a functional object (again, this may require a
shallow copy).

Distribution of an object may require a gid for the object (unless the
object is transmitted in full). A functional object has no id, so when
it is distributed, it is wrapped, sent over, and unwrapped on the
remote node.

### Accessing and mutating objects

Any identified object is associated with three pairs of keys: the
**read-keys**, the **write-keys** and the **auth-keys**.

**Reading the object**: the object's value, along with a timestamp, is
encrypted with the read-encrypt-key and the encrypted result is signed
using the private auth-encrypt-key. In order to read the object, a
process or node needs the read-decrypt-key. It can check the validity
of the contents by checking the signature with the public
auth-decrypt-key. The read-keys may not exist, in which case the
object is public and readable by all (if they obtain a reference to
it). If multiple values are read for an object, the most recent
timestamp always takes precedence.

**Writing the object**: writing a new value to an object is only
possible if the object is marked as writable, and requires stamping it
with a new version, encrypting it with the read-encrypt-key, signing
it with the auth-encrypt-key, and then distributing it to whoever
holds a reference to the object. We would rather not give these keys
too freely, however: race conditions may arise from a lack of
coordination (yielding different values with the same version number),
rogue agents can easily forge the versions to absurdly high numbers,
and we would prefer the auth-key to always remain in trusted hands.

For this reason, we add *write-keys*: a mutator receives the
write-encrypt-key, with which it must encrypt the new value for the
object. That bundle must then find its way to a trusted node which can
decrypt it, possibly inspect the contents, timestamp it, re-encrypt it
with the read-key and then sign it. The trusted node is in charge of
making sure versions are consistent and sanely ordered, and of
broadcasting the updates. The write-keys may not exist, in which case
any node can push a new value.

---

Both the read-keys and the write-keys can be repudiated using the
auth-key. They are given version numbers to determine which is most
recent. Of course, repudiating the read-key does not prevent nodes
from reading the object's value if they obtained it before the
repudiation, nor does it prevent them from sharing it. However, it
prevents any node with an old write-key from pushing changes, and any
node with an old read-key from reading updates.

Functional objects have no keys associated to them. However, they can
be wrapped into an identified object which does have
keys. Furthermore, if a keyed object contains a reference to a
functional object, that object cannot be acquired unless the client
has the read-key or receives it through another object for which it
has the read-key.

### Key assignment and mobility

The keys used in the creation of a new object will be located in
specific dynamic variables (`@key.auth/read/write`) and then stored
alongside the object. During execution, the runtime will also mask the
keys using per-object monotonic dynamic variables, meaning that a
program can dynamically block read or write access to an object.

By default, there are no read/write keys: it is assumed that any node
can read and write the object, provided they have the object's id (we
suppose that ids are practically unforgeable).

When sending an object through a port, no keys will be sent
along. Keys can be sent like any normal objects, however, and added to
a *keychain*. It is assumed that a node can and will use the keys in
its keychain to unlock any objects that can be unlocked with them (for
the purpose of efficiently finding what keys to use, hashes of the
keys can be made available for each object).

When a node requests an object, it may not be a good idea to transfer
the payload without first making sure that they can read it. Indeed,
the size of the payload may provide some information. A compromise is
to send a payload with a constant size which either contains the whole
object if it is small enough, or part of the object and a random
key. In order to retrieve the rest, the node must send the random key,
as evidence that it was able to decrypt the first part of the
message. Assuming that the read-encrypt-key is made public,
intermediaries can perform this protocol without being able to read
the payload (as long as the payload is already split).

That protocol is however not used if it is the node on which the
object resides that initiates the transfer. In that case the owner
node can choose how much to send, which is possibly the whole graph
rooted at the object.

### Structure of an identified object

* **gid**: a unique identifier for the object. The public
  auth-decrypt-key should be embedded in the object's gid.

* **read/write/auth-keys**: explained above.

* **writable**: (boolean) determines whether the object is writable or
  not. Using the auth-key, a process can switch writable from true to
  false, however it is impossible to switch the flag from false to
  true. This gives a mechanism by which mutable objects can become
  immutable.
  
* **coordinator**: a reference to a node or process responsible for
  informing the local node about updates and for transmitting write
  requests from the local node to a node that can sign the update.
  
* **coordinator-lock**: if the lock is nil (that's the default case),
  the language's runtime is allowed to seek alternate coordinators.

* **value**: the value of the object.

* **forward**: either a nil value or a gid. If non-nil, any access to
  this object will access the object referred to in the forward field
  instead.


## Mini-heaps (byte vector)

A basic datatype provided is the *miniheap*: a miniheap is a bit or
byte-addressable portion of memory. In order to help with memory usage
and efficiency, objects can be created and linked together within a
miniheap and the memory zone can be indexed and manipulated without
any limitations. It is however not possible for objects in a miniheap
to refer to objects in the main heap, since this would open up a way
to forge references. As a workaround, a miniheap may be paired with a
tuple of references that it can index into.

The miniheap can be exploited using bit fiddling functions or using a
high level mapper acting as a proxy to the objects embedded in the
miniheap. It can be memory-mapped locally using a special function. It
is meant to support a form of low-level programming, to implement
memory zones with explicit manual memory management or objects like
homogenous vectors without typing overhead. A decent but not too
complex optimizer should be able to fold a miniheap and a mapper
together in order to enhance performance in a way that mostly depends
on the mapper.

A miniheap is a single unit regarding distribution, though several
miniheaps may be regarded as a single logical unit by particular
mappers.


## Ports and mailboxes

Ports and mailboxes allow inter-process communication, respectively
sending and receiving messages. A *port* is an identifiable object
which has no data in it and special writing semantics. The read-keys
serve no purpose; the write-keys determine whether the process can
write to the port or not.

**Writing** to the port involves sending the value asynchronously to
an *address* signed by the port's auth-key. There is no guarantee that
the value will be received at the other end, but there is a guarantee
that messages sent sequentially will not be received out of order. If
more than one address is signed by the auth-key, sending the message
to any of them should either fail or have the same effect.

A *mailbox* can be created by a process at any moment and is
automatically associated to an address, which is essentially a network
address. The process immediately starts to listen to that
address. Data can be retrieved from the mailbox in the order of
reception and must be encrypted with the mailbox's write-key.

Mailboxes cannot be sent through ports, but they can be *transferred*
from a node to another by shutting down the original network port,
transferring the contents of the mailbox and then opening a new one on
the other node, whose address is then signed. Nodes already connected
to the mailbox are given the new address and shut down.

It is theoretically possible for a node holding the auth-key of a port
to unilaterally create a new mailbox, which will be acknowledged as a
valid destination by the port. This can be used to transparently
revive a dead service. Existing connections, when they notice that the
other end does not respond, may then seek another valid address.

Under certain circumstances, several different active addresses may
all be signed as valid, which gives the port holder the opportunity to
pick what address to use. For instance, a service that computes the
hash of some value may be replicated on many nodes, and the signature
serves as a guarantee that the service provided is the same. The
service should be stateless in this case.

A port and a mailbox may be created together so that the port is
attached to the mailbox's address and that writing to it sends data to
the mailbox.

## Data transfer

To each data transfer I associate what I will call an *extent
function*. The purpose of the extent function is to determine how much
of the reference graph rooted at an object to transfer upon request of
that object.

When sending an object, the extent function is constructed and
executed locally. A remote client may also *request* an object. In
that situation, it must send an extent function to be executed
remotely; that function may be given directly to an `acquire`
primitive, or implicitly through a dynamic variable.

Regardless, the extent function must not be able to read more than the
requestor can, nor should it be able to read more than the data server
has the permission to (the data might be held in an encrypted form by
a server, and we don't want to give that server the ability to decrypt
it). Thus we would like the extent function to use the intersection of
the client and the server's keychains.

The client thus first chooses a subset of its keychain to provide
(normally, just the key needed to read the object that's
requested). It encrypts the extent function with every key, so that
the other party can only recover it if they also have every key. Then
the other party sets its keychain to only contain these keys, which
prevents the extent function from accessing any object that the
recipient cannot access, and also prevents it from writing to them. It
runs the extent function and sends over the selected data.

If the data spans objects that have different read-keys, they are
either encrypted separately, or all encrypted together using all the
keys. Not sure which is best.

The exact dynamic environment used for an externally provided extent
function should be user-controlled, but with sensible defaults. It
should be a *generator* producing the data to send as it explores the
graph, should be time-limited to avoid abuse, and should be
single-threaded for any single requestor. The server does not
guarantee that they will deliver the data as specified by the extent
function, with the exception of the root of the request - it is the
recipient's job to verify they have what they want and to file further
requests if anything is missing. This means, for instance, that a data
server holding encrypted data pertaining to an object can discard the
extent function and send what they have.

### Incomplete data

Data which is not sent will be represented as remote references. In
some cases, these may be objects that don't have an id. In that case,
the reference is expressed as a reference to some root id-ed object
and a path through which the object can be accessed. All mutable
objects have ids, so there is always a valid root from which to draw a
path such that the path is guaranteed not to change.

This can block garbage collection in some cases, but during garbage
collection the client can ask the server to reroot the references
(thereby creating new global ids) if it sees that it doesn't need the
original root anymore. It can also come with a performance hit, since
the reference is indirect, but the alternative is memory bloat in the
form of spurious ids.

### Examples

1. Dispatching different rows of a matrix to different nodes. We
   assume that the matrix is represented as a vector of references to
   rows. The idea is that all the nodes will have access to the full
   matrix, but only certain rows will be local to them:

        def all[object, seen = set[]]:
            ;; Yield all references accessible from the object
            if not (object in seen):
                yield object
                seen.add[object]
                for [k, v] in decompose[object]:
                    yield all[v, seen]
                    
        def fromrange[i, j][root]:
            ;; Yield all references accessible from object[i..j]
            yield root
            for [k, v] in decompose[root]:
                if i <= k < j:
                    yield all[v]

        var n = 10
        var blocksize = matrix.length / n
        for i in 0..n-1:
            send[node[i],
                 matrix,
                 fromrange[i*blocksize, (i+1)*blocksize]]

   The extent function given receives a root object as a parameter and
   yields all objects to produce. `decompose[x]` returns an indexed
   list of references contained in the object `x`. If `x` is a
   closure, this will crack it open and yield a reference to the
   closure code and to all of the closure's references.
   
   The function is evaluated in the dynamic environment of the call to
   send.


2. Same example but done from the remote node:

        var [matrix, start, end] = server_port.next[]
        acquire[matrix,
                fromrange[start, end]]
        process[matrix]

   The `fromrange[start, end]` closure is sent over to the server and
   executed there in a specific dynamic environment. Since that
   environment could technically be used for privilege escalation (a
   process with access to a port may be able to execute code locally
   in that environment by injecting an extent function), it is by
   default completely empty?


3. ...

        var [rd, wr] = make_keys[2]
        def treenode[left, right]:
            var this = mutable_record[parent = nil
                                      left = left
                                      right = right]
            (left.parent = wrap[this, rd, wr]) !! nil
            (right.parent = wrap[this, rd, wr]) !! nil
        var a = treenode[1, 2]
        var b = treenode[a, 3]
        print[b.parent] ;; error
        let (@keychain = @keychain ++ [rd, wr]):
            print[b.parent] ;; ok
        remote <- b ;; other side can't read b's parent






