# Chapter 27: Distributed Data Structures

## 27.1 The Philosophy of Distributed Data

In single-machine computing, data structures operate on shared memory with uniform access times. Distributed computing shatters this model: data spans machines, networks have latency, and failures are not exceptions but expectations. Every distributed data structure must answer a fundamental question: how do we maintain the illusion of a single coherent data structure across a cluster of unreliable machines?

**The CAP Theorem** provides the theoretical foundation. In partitioned systems, you must choose between **Consistency** (all nodes see the same data) and **Availability** (every request receives a response). You cannot have both during network partitions. This trade-off shapes every distributed data structure.

**PACELC** extends CAP: if there is a partition (P), the system must choose between Availability (A) and Consistency (C). Else (E), even without partitions, the system must choose between Latency (L) and Consistency (C). A Dynamo-style system chooses L over C; a Bigtable-style system chooses C over L.

## 27.2 Distributed Hash Tables (DHT)

A DHT extends the hash table concept across a cluster. The key insight: map both data items and nodes onto the same hash space, creating a self-organizing overlay network.

### Chord Protocol

Chord assigns each node and key an m-bit identifier using consistent hashing. Each node maintains a **finger table** of size O(log N), allowing lookups in O(log N) hops.

```
Identifier calculation:
node_id = hash(node_ip)
key_id = hash(key)

Successor operation:
successor(id) = first node whose id >= id in the identifier circle
```

**Finger table construction**: The i-th entry of node n contains the successor of (n + 2^(i-1)) mod 2^m, for i = 1..m. This enables exponential jumps across the identifier space.

**Join operation**: A new node asks a known node to find its successor, then updates predecessor's finger table and notifies its successor to adjust.

**Stabilization**: Periodically, nodes verify their successor's predecessor and fix finger table entries to maintain correctness despite churn.

### Kademlia

Kademlia uses a XOR metric for distance, enabling more efficient lookups. The key properties:

**XOR Distance**: d(a,b) = a ⊕ b. This distance is symmetric and satisfies the triangle inequality, enabling simpler routing.

**Node buckets**: Each node maintains one k-bucket (a list of up to k contacts) for each prefix length. Buckets are prioritized by least-recently-seen nodes, ensuring long-lived nodes stay in routing tables.

**Lookup algorithm**: Start with the closest node from own buckets. Parallel query α closest nodes at each step (typically α = 3). Terminate when no node in the queried set is closer than current best.

**Republishing**: Keys are republished periodically with longer expiration times. Original publishers become responsible for refreshing, preventing orphaned keys.

### Apache Cassandra's Partitioner

Cassandra uses consistent hashing with virtual nodes (vnodes). Each node owns multiple token ranges, enabling:

- **Load balancing**: Fine-grained distribution across heterogeneous hardware
- **Easier cluster expansion**: New nodes claim portions of existing ranges
- **Mechanical sympathy**: Sequential ranges for sequential access patterns

**The Murmur3 partitioner** hashes keys to 64-bit tokens. The ring divides this space into contiguous ownership zones.

## 27.3 Consistent Hashing

<figure>
{{#include ../images/consistent-hashing.svg}}
<figcaption>Why removing a node remaps 1/n of the keys instead of nearly all of them.</figcaption>
</figure>

Traditional hashing maps N items to K servers with N/K average load. But adding or removing servers requires rehashing almost all items. Consistent hashing minimizes disruption.

### Basic Algorithm

1. Map both servers and keys to points on a circular hash space (0 to 2^32-1)
2. Each key is assigned to the nearest server in the clockwise direction
3. Virtual nodes (replicas) distribute load more evenly

**Problem**: Uneven distribution when nodes join/leave. Solution: introduce virtual nodes (100-200 per physical node), creating finer-grained ownership.

```
Server placement:
server_i = hash("server_" + i + "_replica_1")
server_i = hash("server_" + i + "_replica_2")
...
server_i = hash("server_" + i + "_replica_v")

Key placement:
key_assigned_to = first_server where server_token > key_token
```

### Consistent Hashing with Bounded Load

Consistent hashing with bounded loads (Mirrokni, Thorup and Zadimoghaddam, 2018; HAProxy exposes it as `hash-balance-factor`) caps how much any node can receive:

1. Pick ε > 0. With m keys (or active requests) on n nodes, each node gets a capacity of ⌈(1+ε)·m/n⌉
2. A key hashes to the ring as usual; if its clockwise node is full, it keeps walking clockwise to the first node with spare capacity
3. No node ever exceeds (1+ε) times the average load. Smaller ε gives tighter balance but displaces more keys from their natural owner

## 27.4 Distributed Snapshots and State Machine Replication

Replicating state across machines requires capturing consistent global states despite concurrent operations.

### Chandy-Lamport Algorithm

Designed for distributed snapshot collection without process coordination:

1. **Initiator** records its own state, then sends a marker on every outgoing channel
2. When a process receives a marker on channel C:
   - If it has not yet recorded its state: record local state, record C's state as empty, send a marker on every outgoing channel, and start recording messages arriving on every other incoming channel
   - Otherwise: stop recording C; C's state is the messages that arrived on C after the process recorded its own state
3. When every process has recorded its state and received a marker on every incoming channel, the snapshot is complete

**Causality guarantee**: With FIFO channels, the algorithm captures a consistent cut: if a message's receipt is in the snapshot, so is its send. Messages sent before the cut but received after it appear as recorded channel state.

### State Machine Replication

A deterministic state machine, combined with replicated logs of identical commands, guarantees consistent replicas. Key requirements:

- **Determinism**: Same initial state + same operations = same final state
- **Atomicity**: No partial command execution
- **Ordering**: Total order across all replicas

**Paxos** and **Raft** are consensus protocols that implement replicated logs. Raft's key innovation: decomposing consensus into leader election, log replication, and safety.

```
Raft Log Entry:
{
    term: number,        // When entry was created
    index: number,       // Position in log
    command: object     // State machine command
}
```

## 27.5 CRDTs in Distributed Systems

Conflict-free Replicated Data Types (CRDTs) enable eventual consistency without coordination. They guarantee convergence regardless of operation order.

### State-based Counters and Registers

Both of these are state-based: replicas exchange their whole state and combine it with a merge that is commutative, associative and idempotent (an operation-based CRDT instead broadcasts each operation and relies on the delivery layer to deliver it exactly once):

**G-Counter (Grow-only Counter)**:
```python
class GCounter:
    def __init__(self):
        self.state = {}  # node_id -> count

    def increment(self, node_id):
        self.state[node_id] = self.state.get(node_id, 0) + 1

    def merge(self, other):
        for node_id, count in other.state.items():
            self.state[node_id] = max(self.state.get(node_id, 0), count)

    def value(self):
        return sum(self.state.values())
```

**LWW-Register (Last-Write-Wins Register)**:
```python
class LWWRegister:
    def __init__(self):
        self.value = None
        self.timestamp = 0

    def set(self, value, timestamp):
        if timestamp > self.timestamp:
            self.value = value
            self.timestamp = timestamp

    def merge(self, other):
        if other.timestamp > self.timestamp:
            self.value = other.value
            self.timestamp = other.timestamp
```

Timestamps must be unique for this register to converge: if two replicas write different values with the same timestamp, each keeps its own, since neither is strictly greater. Use (time, replica_id) pairs, compared lexicographically. Where the time comes from matters too; §27.8 shows why raw wall-clock time can let an older write beat a newer one.

### State-based Sets (Convergent CRDTs)

Operations are applied locally and entire state is merged using join operations:

**OR-Set (Observed-Remove Set)**:
```python
from uuid import uuid4

class ORSet:
    def __init__(self):
        self.elements = {}  # tag -> value
        self.tombstones = set()  # removed tags

    def add(self, value):
        tag = uuid4()
        self.elements[tag] = value
        return (tag, value)

    def remove(self, tag):
        self.tombstones.add(tag)
        self.elements.pop(tag, None)

    def merge(self, other):
        # Union of elements and of tombstones, then drop removed tags
        self.tombstones |= other.tombstones
        self.elements.update(other.elements)
        self.elements = {
            k: v for k, v in self.elements.items()
            if k not in self.tombstones
        }
```

## 27.6 Distributed Consensus Mechanisms

Consensus is the problem of getting distributed nodes to agree on a value. FLP impossibility proves deterministic consensus is impossible with even one faulty process in asynchronous systems. Real systems relax requirements.

### Raft Consensus

Raft's three roles: **Leader**, **Follower**, **Candidate**. Term numbers provide logical clocks.

**Leader election**:
1. Heartbeat timeout triggers follower → candidate transition
2. Candidate votes for self, requests votes from others
3. If majority votes, become leader
4. Election timeout randomized to prevent split votes

**Log replication**:
1. Client sends command to leader
2. Leader appends to local log, replicates to followers in parallel
3. When majority acknowledge, apply to state machine
4. Commit index propagates with AppendEntries

**Safety**: If log entry has committed in a term, future leaders must contain it.

### Multi-Paxos

Optimized Paxos for replicated state machines:
- One leader per term (reduces prepare messages)
- PreparePromise with all accepted entries instead of single value
- Prepare phase (phase 1) can be skipped while the leader is stable: each new command needs only the Accept phase

## 27.7 Quorum Systems

Quorums define the minimum number of nodes required for read/write operations.

**Strict quorum**: Read and write quorums must overlap (R + W > N)

**Quorum construction**:
- **Majority quorum**: R = W = ⌊N/2⌋ + 1 (tolerates ⌊(N−1)/2⌋ failures)
- **Sloppy quorum**: Prefer local nodes, fall back to remote on failure
- **Hierarchical quorum**: Tree structure reduces coordination

**Version vectors** track object versions across replicas:
```python
class VersionVector:
    def __init__(self):
        self.versions = {}  # node_id -> counter

    def increment(self, node_id):
        self.versions[node_id] = self.versions.get(node_id, 0) + 1

    def merge(self, other):
        for node_id, version in other.versions.items():
            self.versions[node_id] = max(
                self.versions.get(node_id, 0),
                version
            )

    def happens_before(self, other):
        # True if all entries in self <= other, and at least one <
        keys = self.versions.keys() | other.versions.keys()
        return all(
            self.versions.get(k, 0) <= other.versions.get(k, 0)
            for k in keys
        ) and any(
            self.versions.get(k, 0) < other.versions.get(k, 0)
            for k in keys
        )
```

### Anti-entropy with Merkle trees

A version vector tells two replicas how their copies of *one* key relate. It does not tell a replica which of its million keys differ from another replica's. Read repair fixes keys that happen to be read, and hinted handoff replays writes that a node missed during a short outage, but a key that is never read and whose hint was lost stays divergent forever. **Anti-entropy** closes that gap. Each replica builds a Merkle tree over a key range: each leaf hashes a bucket of keys, and each internal node hashes its children's hashes. Two replicas exchange root hashes; if they match (the common case), the ranges are identical and nothing more is sent. If not, they exchange the children of every node that differs and recurse. Each round trip descends one level, so a binary tree over n leaves locates the differing leaves in about log₂ n round trips, and with k differing leaves about 2k·log₂(n/k) hashes cross the network. [§31.2](ch31-real-world-case-studies.md) shows how Dynamo uses this, and Exercise 31.4 does the arithmetic.

Cassandra's `nodetool repair` is the best-documented production case. Each replica reads its copy of the range and builds a Merkle tree (a *validation compaction*, which is why repair is I/O-heavy), the trees are compared, and the token ranges under mismatched leaves are streamed between replicas. The tree has a fixed resolution (DataStax documents a depth of 15, about 32,000 leaves), so when a leaf covers many partitions, one damaged partition causes all of its leaf's partitions to be streamed. Operators reduce this *overstreaming* by repairing in smaller subranges, which gives each tree a finer resolution.

## 27.8 Logical Clocks

Several structures in this chapter quietly depend on a notion of time: the LWW-Register compares timestamps, version vectors compare histories, Raft orders leaders by term, and the Chandy-Lamport snapshot must not record a receive without its send. Physical clocks cannot supply that order reliably. Clocks synchronized by NTP typically disagree by milliseconds, and by far more after a bad sync or a VM pause, so a wall-clock timestamp can place an effect before its cause. What these structures actually need is the order of **causality**, and that can be tracked exactly without reading any clock.

### Happens-before

Lamport (1978) defined the **happens-before** relation → on the events of a distributed system (local steps, sends and receives):

1. If a and b are on the same process and a comes first, then a → b.
2. If a is the send of a message and b is its receipt, then a → b.
3. If a → b and b → c, then a → c.

If neither a → b nor b → a, the events are **concurrent**, written a ∥ b. Concurrent does not mean simultaneous: it means no chain of messages connects them, so neither could have influenced the other. Happens-before is a partial order, and a logical clock is a way of attaching timestamps to events that respects it.

### Lamport clocks

Each process keeps one integer L. Before every local event or send it increments L; a message carries the sender's L; on receiving a message stamped t, the receiver sets L = max(L, t) + 1.

```python
class LamportClock:
    def __init__(self):
        self.time = 0

    def local(self):                 # a local event, or a send
        self.time += 1
        return self.time

    send = local

    def receive(self, msg_time):
        self.time = max(self.time, msg_time) + 1
        return self.time
```

This guarantees the **clock condition**: a → b implies L(a) < L(b). Each of the three rules makes the timestamp strictly increase along one step of a causal chain, so it increases along the whole chain.

The converse is false: **L(a) < L(b) does not imply a → b**. Lamport time squashes a partial order into a chain of integers, and in doing so it forgets which pairs were concurrent. In the example below, L(b1) = 1 < L(a2) = 2, but no message reaches A from B before a2, so b1 ∥ a2. What Lamport timestamps do give is a cheap **total order consistent with causality**: compare (L, process_id) pairs lexicographically. That is how Lamport's mutual exclusion algorithm orders requests, how the RGA in §27.9 names characters, and the right way to break ties in the LWW-Register of §27.5. Each timestamp is one integer, and each event costs O(1), worst-case.

### Vector clocks

To detect concurrency rather than just respect causality, each process keeps one counter per process: a **vector clock** (Fidge and Mattern, independently, 1988). This is the same structure as the `VersionVector` of §27.7, with the same `merge` and the same comparison. The difference is what ticks it. A version vector belongs to a replicated *object* and increments when a replica updates that object. A vector clock belongs to a *process* and increments on every event, including sends and receives, and merges on every receive. So we build it on `VersionVector` rather than writing a second version:

```python
class VectorClock(VersionVector):
    """The VersionVector of §27.7, ticked on every event of one process."""

    def __init__(self, node_id):
        super().__init__()
        self.node_id = node_id

    def stamp(self):                 # an immutable copy to attach to an event
        snapshot = VersionVector()
        snapshot.versions = dict(self.versions)
        return snapshot

    def local(self):                 # a local event, or a send
        self.increment(self.node_id)
        return self.stamp()

    send = local

    def receive(self, msg_stamp):
        self.merge(msg_stamp)        # entry-wise max with the sender's vector
        self.increment(self.node_id)
        return self.stamp()


def concurrent(x, y):
    return (x.versions != y.versions
            and not x.happens_before(y)
            and not y.happens_before(x))
```

Entry j of V(e) counts the events of process j in e's causal past (including e itself, when e is on process j). That gives the **strong clock condition**: a → b if and only if V(a) < V(b), where < means ≤ in every entry and strictly less in at least one, which is exactly `happens_before`. If a → b, everything a has seen, b has seen too, plus b itself. Conversely, if a is the k-th event of process i and V(b)[i] ≥ k, then b's causal past contains a. So two events are concurrent exactly when their vectors are incomparable.

**Worked example.** Three processes exchange three messages: A sends m1 to B, B sends m2 to C, C sends m3 to A. Vectors are written [A, B, C].

<figure>
{{#include ../images/vector-clocks.svg}}
<figcaption>Lamport time orders c1 before b3, but only the vector clocks reveal that no message path connects them.</figcaption>
</figure>

| event | what happens | Lamport L | vector V |
|---|---|---|---|
| a1 | A, local | 1 | [1,0,0] |
| a2 | A sends m1 | 2 | [2,0,0] |
| b1 | B, local | 1 | [0,1,0] |
| b2 | B receives m1 | max(1, 2) + 1 = 3 | max([0,1,0], [2,0,0]) = [2,1,0], tick: [2,2,0] |
| b3 | B sends m2 | 4 | [2,3,0] |
| c1 | C, local | 1 | [0,0,1] |
| c2 | C receives m2 | max(1, 4) + 1 = 5 | [2,3,1], tick: [2,3,2] |
| c3 | C sends m3 | 6 | [2,3,3] |
| a3 | A receives m3 | max(2, 6) + 1 = 7 | [2,3,3], tick: [3,3,3] |

```python
lamport = {p: LamportClock() for p in "ABC"}
vector = {p: VectorClock(p) for p in "ABC"}
L, V = {}, {}

def local(name, p):
    L[name], V[name] = lamport[p].local(), vector[p].local()

def send(name, p):
    local(name, p)               # a send is a local event whose stamp travels
    return L[name], V[name]

def receive(name, p, msg):
    L[name], V[name] = lamport[p].receive(msg[0]), vector[p].receive(msg[1])

local("a1", "A"); m1 = send("a2", "A")
local("b1", "B"); receive("b2", "B", m1); m2 = send("b3", "B")
local("c1", "C"); receive("c2", "C", m2); m3 = send("c3", "C")
receive("a3", "A", m3)

assert L["b1"] < L["a2"] and concurrent(V["b1"], V["a2"])
assert L["c1"] < L["b3"] and concurrent(V["c1"], V["b3"])
assert V["a1"].happens_before(V["c2"])     # a1 → a2 → b2 → b3 → c2
assert [V["a3"].versions[p] for p in "ABC"] == [3, 3, 3]
```

c1 has Lamport time 1, tied for the smallest in the run, yet it is concurrent with every event on A and B before a3: nothing C did reached anyone until m3.

**Cost.** A vector timestamp takes O(n) space for n processes, and comparing or merging two takes O(n), worst-case. This is not a weakness of the encoding: Charron-Bost (1991) proved that characterizing causality with vectors compared entry by entry needs n entries in the worst case. That is why vector clocks are attached to replicated objects with a few writers (Dynamo keeps one per key and truncates it past a size threshold by dropping the oldest entry) and not to every event in a large cluster.

### Hybrid logical clocks

A database that assigns a timestamp to every write would like three things at once:

1. **Causality**: if a → b then ts(a) < ts(b), so a write that follows a read of another write sorts after it.
2. **Constant size**: a timestamp on every MVCC version cannot grow with the cluster.
3. **Closeness to wall-clock time**: "read the database as of 10:00:00", TTLs and log correlation all need timestamps that mean something in seconds.

Physical clocks give 2 and 3 but break 1 under skew. Lamport clocks give 1 and 2 but drift arbitrarily far from real time, since a busy node drives everyone's counter up and the counter has no units. Vector clocks give 1 but not 2 or 3. **Hybrid logical clocks** (HLC; Kulkarni, Demirbas, Madappa, Avva and Leone, 2014) give all three. A timestamp is a pair (l, c): l is the largest physical time the node has heard of, from its own clock or from any message, and c is a counter that orders events sharing the same l. Pairs compare lexicographically.

```python
class HybridLogicalClock:
    def __init__(self, physical_clock):
        self.pt = physical_clock     # function returning this node's wall clock
        self.l = 0                   # largest physical time seen so far
        self.c = 0                   # orders events that share the same l

    def local(self):                 # a local event, or a send
        old = self.l
        self.l = max(old, self.pt())
        self.c = self.c + 1 if self.l == old else 0
        return (self.l, self.c)

    send = local

    def receive(self, msg):
        lm, cm = msg
        old = self.l
        self.l = max(old, lm, self.pt())
        if self.l == old == lm:
            self.c = max(self.c, cm) + 1
        elif self.l == old:
            self.c += 1
        elif self.l == lm:
            self.c = cm + 1
        else:                        # the local clock is ahead of everything
            self.c = 0
        return (self.l, self.c)
```

Three properties follow. **Causality**: each rule makes (l, c) strictly increase over the previous local value and, on a receive, over the message's value, so a → b implies hlc(a) < hlc(b). **Bounded drift**: l is always at least the local physical time, and it is a physical reading taken somewhere in the event's causal past, so it can be ahead of the local clock by at most ε, the maximum skew between any two clocks. **Small counter**: c resets to 0 whenever the local physical clock moves past l, so it only grows while a node is behind the largest time it has heard of (the paper proves a bound). Like a Lamport clock, an HLC cannot detect concurrency: hlc(a) < hlc(b) does not imply a → b.

**Worked example.** A's clock reads 10 and B's reads 7: B is 3 units behind. A writes key k and sends the write to B. B reads it and overwrites k.

| event | local wall clock | physical timestamp | HLC |
|---|---|---|---|
| A writes k = 1, sends it | 10 | 10 | (10, 0) |
| B receives the write | 7 | 7 | max(0, 10, 7) = 10 from the message: (10, 0 + 1) = (10, 1) |
| B writes k = 2 | 7 | 7 | l unchanged at 10: (10, 2) |
| B, later, local event | 11 | 11 | clock passed l: (11, 0) |

With physical timestamps, B's write (7) sorts before A's (10), so every replica running last-writer-wins keeps k = 1 and silently discards the write that causally came second. With HLC, (10, 2) > (10, 0) and B's write wins. Once B's clock passes 10, its timestamps are plain wall time again with c = 0.

```python
wall = {"A": 10, "B": 7}                  # B's clock is 3 units behind A's
hlc_a = HybridLogicalClock(lambda: wall["A"])
hlc_b = HybridLogicalClock(lambda: wall["B"])

m = hlc_a.send()                          # A writes k = 1
assert m == (10, 0)
assert hlc_b.receive(m) == (10, 1)
w = hlc_b.local()                         # B overwrites k = 2
assert w == (10, 2) and w > m             # physical time would say 7 < 10
wall["B"] = 11
assert hlc_b.local() == (11, 0)           # back to tracking the wall clock
```

CockroachDB and YugabyteDB both timestamp transactions and MVCC versions with HLCs. CockroachDB's default maximum clock offset is 500 ms; a node whose clock drifts too far from the rest of the cluster shuts itself down, because the bound on ε is what keeps HLC timestamps meaningful. Compare Spanner's TrueTime ([§31.1](ch31-real-world-case-studies.md)), which buys a small ε with GPS and atomic clocks and then waits it out on every commit. HLC accepts ordinary NTP-grade skew and pays for it elsewhere, for example by restarting a read that finds a value whose timestamp falls within its uncertainty window.

| clock | timestamp size | cost per event | a → b ⇒ ts(a) < ts(b) | detects concurrency | close to wall time |
|---|---|---|---|---|---|
| physical | O(1) | O(1) | no | no | yes |
| Lamport | O(1) | O(1) | yes | no | no |
| vector | O(n) | O(n) | yes, and the converse | yes | no |
| hybrid logical | O(1) | O(1) | yes | no | yes, within ε |

All costs are worst-case per event, for n processes.

## 27.9 Sequence CRDTs for Collaborative Editing

The CRDTs of §27.5 are counters, registers and sets, which have no order. Text does, and users edit it by position. Operations addressed by integer index do not commute. Two replicas hold "cat". A types "s" at index 3, giving "cats"; concurrently, B types "h" at index 1, giving "chat". A then applies B's insert(1, "h") and gets "chats". B applies A's insert(3, "s") and gets "chast". The index 3 meant "after the t" on A, but B's earlier insert shifted the t. Operational transformation (OT) repairs this by rewriting each incoming index against the concurrent operations it missed, which is manageable with a central server ordering everything. A **sequence CRDT** removes the problem instead: every character gets a **unique identifier that never changes**, and the document order is defined on identifiers, not indices.

That needs three things. Identifiers must be **unique** without coordination: a (counter, replica_id) pair does it. They must be **ordered between neighbours**: a character inserted between x and y must land between x and y on every replica, and concurrent inserts at the same spot need a deterministic tie-break. And **deletes must leave tombstones**: a concurrent insert may name the deleted character as its neighbour, so the identifier has to stay resolvable after the character disappears from view.

### Fractional positions and the interleaving anomaly

The direct approach gives every character a position in a dense ordered space and sorts by (position, replica_id). Logoot (Weiss, Urso and Molli, 2009) uses sequences of digits as positions, so there is always room between two of them; floats make a simpler (if finite) stand-in. Suppose A types "dog" and B types "cat" concurrently into an empty document, each character placed halfway between the previous one and the end:

```python
def fractional_typing(word, replica, lo=0.0, hi=1.0):
    out = []
    for ch in word:
        lo = (lo + hi) / 2           # halfway between the last char and the end
        out.append(((lo, replica), ch))
    return out

doc = sorted(fractional_typing("dog", "A") + fractional_typing("cat", "B"))
assert "".join(ch for _, ch in doc) == "dcoagt"
```

Both replicas converge, on garbage. Both users chose positions 0.5, 0.75 and 0.875, and the tie-break on replica ID alternates them. This is the **interleaving anomaly**: concurrently typed runs at the same place merge character by character. Kleppmann, Gomes, Mulligan and Beresford (2019) found it in Logoot and LSEQ. Convergence is a necessary property of a collaborative editor, not a sufficient one.

### RGA: the Replicated Growable Array

RGA (Roh, Jeon, Kim and Lee, 2011) anchors each insert to a character instead of a number. An element is identified by a Lamport timestamp (counter, replica_id) from §27.8; the original paper used a custom timestamp type, and later presentations use Lamport timestamps. An insert operation is (id, ref, char), where ref is the id of the character immediately to the left at the moment of insertion (`None` for the start). A delete operation marks its target as a tombstone and keeps it in the list.

To apply an insert, find ref, then **skip right past every element whose id is greater than the new id**, and insert there:

```python
class RGA:
    def __init__(self, replica_id):
        self.replica_id = replica_id
        self.clock = 0      # Lamport counter: ids are (counter, replica_id)
        self.elems = []     # [id, char, deleted], in document order

    def _visible(self):
        return [e for e in self.elems if not e[2]]

    def _find(self, elem_id):
        for i, e in enumerate(self.elems):
            if e[0] == elem_id:
                return i
        raise KeyError(elem_id)

    def text(self):
        return "".join(e[1] for e in self._visible())

    # Local edits, by visible position; each returns the op to broadcast.
    def insert(self, pos, char):
        ref = self._visible()[pos - 1][0] if pos > 0 else None
        op = ("ins", (self.clock + 1, self.replica_id), ref, char)
        self.apply(op)
        return op

    def delete(self, pos):
        op = ("del", self._visible()[pos][0])
        self.apply(op)
        return op

    # Remote and local ops both go through apply.
    def apply(self, op):
        if op[0] == "del":
            self.elems[self._find(op[1])][2] = True   # tombstone
            return
        _, elem_id, ref, char = op
        if any(e[0] == elem_id for e in self.elems):
            return                                     # duplicate delivery
        self.clock = max(self.clock, elem_id[0])
        i = 0 if ref is None else self._find(ref) + 1
        while i < len(self.elems) and self.elems[i][0] > elem_id:
            i += 1                                     # skip newer inserts
        self.elems.insert(i, [elem_id, char, False])
```

**Why the skip rule converges.** Picture the elements as a tree: each element's parent is its ref, siblings are ordered by descending id, and the document is the pre-order traversal. Because an insert's Lamport timestamp exceeds that of its ref, every element's id is larger than all of its ancestors'. Starting just after ref, the list holds ref's child subtrees in descending order. A child with a larger id than the new element is skipped along with its whole subtree, whose ids are larger still. The first element with a smaller id is either a smaller sibling or lies beyond ref's subtree (the element there is a later sibling of ref or of one of its ancestors, so its id is smaller than that node's, which is no larger than ref's, which is smaller than the new element's). The new element goes exactly there, which is its place in the pre-order traversal. The tree depends only on the *set* of operations, not on the order they arrived in, so any two replicas that have applied the same operations hold the same list. The only delivery requirement is that an insert arrives after the insert of its ref and a delete after the insert of its target, which causal delivery provides.

**Worked trace.** A types "ab", giving ids (1,A) for a and (2,A) for b, and B receives both. Concurrently, A inserts "x" after a, with id (3,A), while B inserts "y" after a, with id (3,B), and then deletes b.

- On A, which holds `a x b`: y's ref is a, at index 0, so start at 1. x's id (3,A) is less than (3,B): stop. Result `a y x b`.
- On B, which holds `a y b†` (b† is the tombstone): x's ref is a, start at 1. y's id (3,B) is greater than (3,A): skip. b's id (2,A) is less than (3,A): stop. Result `a y x b†`. After applying B's delete, A matches.

Both read "ayx". The tombstone mattered: had B's delete arrived first and physically removed b, an insert after b from a third replica would have had nothing to anchor to.

The test below gives three replicas the same starting text, lets them make 30 edits with no syncing at all (every edit is concurrent with the other replicas' edits), and then applies the full set of operations in 100 different random causal orders to fresh replicas, as well as in log order to the three originals. Every one ends with the same text.

```python
import random

def dependency(op):
    return op[2] if op[0] == "ins" else op[1]

def random_causal_order(ops, rng):
    """A delivery order in which every op's ref or target arrives first."""
    pending, present, order = list(ops), {None}, []
    while pending:
        op = rng.choice([o for o in pending if dependency(o) in present])
        pending.remove(op)
        order.append(op)
        if op[0] == "ins":
            present.add(op[1])
    return order

rng = random.Random(27)
replicas = [RGA(r) for r in "ABC"]
ops = [replicas[0].insert(i, ch) for i, ch in enumerate("cat")]
for r in replicas[1:]:
    for op in ops:
        r.apply(op)

for _ in range(30):                   # concurrent edits, no syncing
    r = rng.choice(replicas)
    if r.text() and rng.random() < 0.3:
        ops.append(r.delete(rng.randrange(len(r.text()))))
    else:
        ops.append(r.insert(rng.randint(0, len(r.text())), rng.choice("xyz")))

results = set()
for _ in range(100):
    fresh = RGA("D")
    for op in random_causal_order(ops, rng):
        fresh.apply(op)
    results.add(fresh.text())
for r in replicas:                    # own ops are skipped as duplicates
    for op in ops:
        r.apply(op)
    results.add(r.text())
assert len(results) == 1
```

**Interleaving in RGA.** Text typed left to right stays together: every character after the first is anchored to its predecessor in the same run, so a concurrent run from another user can only go before or after the whole run. In the "dog" and "cat" scenario, RGA produces "catdog" on every replica. But a run typed by repeatedly inserting at the same position (moving the cursor back after each keystroke) anchors every character to the same ref, and those siblings are ordered only by timestamp: A inserting g, o, d at position 0 while B inserts t, a, c at position 0 merges to "cdaotg". Kleppmann et al. (2019) called this the lesser interleaving anomaly; Fugue (Weidner and Kleppmann, 2023) is a later list CRDT designed specifically to minimize interleaving.

**Cost.** In this list version every operation is O(n), worst-case, where n counts tombstones too: finding ref, converting a visible position to an element, and the list insert are all linear scans. The skip loop itself only passes over concurrent inserts at the same spot. Production implementations keep elements in a balanced tree whose nodes store the number of *visible* characters below them (the same weight trick as the rope in [§13.7](../volume-2/ch13-string-data-structures.md)), plus a hash map from id to element, for O(log n) position lookups. They also compress runs: Yjs stores consecutive characters typed by one client as a single item. Space is the real cost. Tombstones are never removed by the algorithm itself, so a document's metadata grows with every character ever typed. A tombstone can only be discarded once every replica has seen the delete and no operation still in flight can refer to it, which requires knowing who all the replicas are. Yjs, for example, discards a deleted item's content but keeps a small placeholder recording its length.

**In practice.** Yjs implements an adaptation of YATA (Nicolaescu et al., 2016), which anchors each insert to both its left and its right neighbour (each item records an origin and a right origin). Automerge documents its list type as an RGA sequence. Both use (client, counter) identifiers and tombstones as above.

**Local versus replicated buffers.** The gap buffer, rope and piece table of [Chapter 13](../volume-2/ch13-string-data-structures.md) address text by integer offset, which works because a single writer's offsets only change through that writer's own edits. A replicated buffer cannot, as "chast" shows; it must address by identifier. An editor built on a sequence CRDT usually keeps both: an ordinary local buffer for rendering and cursor movement, and the CRDT for merging. Local edits are translated from offset to identifier on the way out, and remote operations from identifier to offset on the way in, which is why the position lookup above has to be fast.

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**27.1 ★★ Trace a Chord lookup.** Take m = 6 (identifiers 0 to 63) and a ring with nodes at 1, 8, 14, 21, 32, 38, 42, 48, 51 and 56. Using the finger-table rule from §27.2 (entry i of node n is successor((n + 2^(i-1)) mod 2^m)), build the finger table of node 8, then trace a lookup for key 54 that starts at node 8. At each hop the current node forwards to the finger that most closely precedes the key, unless the key falls between the node and its successor.

<details>
<summary>Hint</summary>

Node 8's fingers point at the successors of 9, 10, 12, 16, 24 and 40. To trace the second hop you will need part of node 42's finger table too.

</details>

<details>
<summary>Solution</summary>

Finger table of node 8:

| i | 8 + 2^(i-1) | successor |
|---|---|---|
| 1 | 9 | 14 |
| 2 | 10 | 14 |
| 3 | 12 | 14 |
| 4 | 16 | 21 |
| 5 | 24 | 32 |
| 6 | 40 | 42 |

Lookup for 54:

1. At node 8: its successor is 14 and 54 is not in (8, 14]. The finger closest to 54 without passing it is 42. Forward to 42.
2. At node 42: its successor is 48, and 54 is not in (42, 48]. Node 42's fingers are the successors of 43, 44, 46, 50, 58 and 10 (that is, 74 mod 64), giving 48, 48, 48, 51, 1, 14. The finger that most closely precedes 54 is 51. Forward to 51.
3. At node 51: its successor is 56, and 54 is in (51, 56]. Node 56 owns key 54.

Path: 8 → 42 → 51 → 56. Each hop at least halves the remaining clockwise distance to the key (46, then 12, then 3), which is where the O(log N) hop bound comes from.

</details>

**27.2 ★★ XOR distance and k-buckets.** Use 4-bit Kademlia identifiers. Node x = 0110 knows the contacts 0111, 0100, 0101, 0011 and 1110. Compute d(x, y) for each contact and place each one in bucket i, where bucket i holds contacts at distance in [2^i, 2^(i+1)). Then prove that for any fixed x and any distance d there is exactly one identifier y with d(x, y) = d, and say why that matters for lookups.

<details>
<summary>Hint</summary>

Bucket i is the set of nodes that share exactly the first (3 − i) bits with x. For the proof, XOR both sides of x ⊕ y = d with x.

</details>

<details>
<summary>Solution</summary>

| contact | x ⊕ y | distance | bucket | shared prefix with 0110 |
|---|---|---|---|---|
| 0111 | 0001 | 1 | 0 | 3 bits |
| 0100 | 0010 | 2 | 1 | 2 bits |
| 0101 | 0011 | 3 | 1 | 2 bits |
| 0011 | 0101 | 5 | 2 | 1 bit |
| 1110 | 1000 | 8 | 3 | 0 bits |

Half the identifier space (everything starting with 1) lands in bucket 3, a quarter in bucket 2, and so on: the node knows a few contacts in each exponentially shrinking region, which is the same shape as a Chord finger table.

Uniqueness: if x ⊕ y = d then XOR both sides with x to get y = x ⊕ d, since x ⊕ x = 0. So y is determined by x and d. This property (unidirectionality) means that lookups for the same key converge along the same path regardless of which node starts them. Caching a value at nodes along that path therefore helps later lookups, because they pass through those same nodes.

</details>

**27.3 ★ Consistent hashing versus mod-N.** A ring runs from 0 to 99 and has nodes at 10, 35, 60 and 85. A key goes to the first node whose position is greater than the key, wrapping around past 99. (a) Assign the keys 5, 12, 33, 40, 59, 61, 90, 99. (b) A node is added at 50. Which keys move? (c) Compare with `owner = key mod N` going from N = 4 to N = 5: how many of the same eight keys change owner?

<details>
<summary>Solution</summary>

(a) 5 → 10, 12 → 35, 33 → 35, 40 → 60, 59 → 60, 61 → 85, 90 → 10 (wraps), 99 → 10 (wraps).

(b) The new node at 50 takes over the arc (35, 50), which previously belonged to 60. Only key 40 lies in that arc, so one key out of eight moves, and it moves to the new node. No key moves between two old nodes.

(c) Under mod-N:

| key | mod 4 | mod 5 | moved? |
|---|---|---|---|
| 5 | 1 | 0 | yes |
| 12 | 0 | 2 | yes |
| 33 | 1 | 3 | yes |
| 40 | 0 | 0 | no |
| 59 | 3 | 4 | yes |
| 61 | 1 | 1 | no |
| 90 | 2 | 0 | yes |
| 99 | 3 | 4 | yes |

Six of eight move. In general a key keeps its owner only when k mod 4 = k mod 5, which happens for k mod 20 in {0, 1, 2, 3}: one key in five. Mod-N moves about 80% of the data when growing from 4 to 5 nodes; consistent hashing moves about 1/5 (the new node's fair share) in expectation.

</details>

**27.4 ★★ Find the bug in a happens-before check.** An earlier version of `VersionVector.happens_before` in §27.7 looped only over the keys of `other`:

```python
def happens_before(self, other):
    return all(
        self.versions.get(k, 0) <= v
        for k, v in other.versions.items()
    ) and any(
        self.versions.get(k, 0) < v
        for k, v in other.versions.items()
    )
```

Find two version vectors for which this returns the wrong answer, and explain what the consequence would be in a Dynamo-style store.

<details>
<summary>Hint</summary>

What happens to an entry that appears in `self` but not in `other`?

</details>

<details>
<summary>Solution</summary>

Take self = {A: 1, B: 1} and other = {A: 2}. The loop only checks key A: 1 ≤ 2 and 1 < 2, so it returns True. But self has seen an update from B that other has not (B: 1 versus an implicit B: 0), so neither vector dominates: the two versions are concurrent.

The consequence: the store would decide that `other` supersedes `self` and silently discard the version containing B's write. That is exactly the lost update that version vectors exist to prevent. The fix, used in the chapter's code, compares over the union of both key sets, treating a missing key as 0.

</details>

**27.5 ★ Quorum arithmetic.** For N = 5 replicas, which of these (R, W) pairs are strict quorums: (1, 5), (2, 3), (3, 3), (2, 4), (3, 2)? For each strict one, how many replica failures can reads tolerate, and how many can writes tolerate? How many failures does the majority quorum tolerate for N = 4, 5 and 6?

<details>
<summary>Solution</summary>

A strict quorum needs R + W > N, so every read set intersects every write set.

| (R, W) | R + W | strict? | read failures tolerated (N − R) | write failures tolerated (N − W) |
|---|---|---|---|---|
| (1, 5) | 6 | yes | 4 | 0 |
| (2, 3) | 5 | no | | |
| (3, 3) | 6 | yes | 2 | 2 |
| (2, 4) | 6 | yes | 3 | 1 |
| (3, 2) | 5 | no | | |

(1, 5) gives the fastest reads but any single failure blocks all writes. (2, 3) and (3, 2) can return stale data: a read of 2 replicas can miss all 3 that took the write.

The majority quorum is ⌊N/2⌋ + 1, so it tolerates N − (⌊N/2⌋ + 1) = ⌊(N−1)/2⌋ failures: 1 for N = 4, 2 for N = 5, 2 for N = 6. An even cluster size buys no extra fault tolerance over the odd size below it, which is why consensus groups are almost always 3, 5 or 7.

</details>

**27.6 ★★ Why G-Counter merges with max.** Three replicas start empty. A increments twice, B increments once, C increments once. Then these merges happen in order: A merges B; C merges A; A merges C; B merges A; B merges A again. Give every replica's state and value at the end. Then suppose `merge` added the counts instead of taking the max. Which step gives a wrong answer, and what property of the merge has been broken?

<details>
<summary>Solution</summary>

Before any merge: A = {A: 2}, B = {B: 1}, C = {C: 1}.

| step | result | value |
|---|---|---|
| A merges B | A = {A: 2, B: 1} | 3 |
| C merges A | C = {A: 2, B: 1, C: 1} | 4 |
| A merges C | A = {A: 2, B: 1, C: 1} | 4 |
| B merges A | B = {A: 2, B: 1, C: 1} | 4 |
| B merges A again | unchanged | 4 |

All three converge to 4, the true number of increments.

With addition, the first two merges happen to give the right answer, because the states being combined share no entries. The third step breaks: when A merges C, A adds C's A: 2 to its own A: 2 and C's B: 1 to its own B: 1, ending at {A: 4, B: 2, C: 1} with value 7, although only 4 increments happened. Every repeated exchange inflates the count further. The broken property is idempotence: merging the same state twice must change nothing. Gossip protocols deliver the same state many times, so a state-based CRDT's merge must be idempotent as well as commutative and associative. Each entry only ever grows and is written by one node, so the max of two copies is always the newer one.

</details>

**27.7 ★★★ A counter that can go down.** A G-Counter cannot decrement. (a) Show that keeping one signed entry per node and merging with max does not work, by giving a sequence that loses an update. (b) Implement a PN-Counter from two G-Counters and argue that it converges. Your implementation should satisfy:

```python
a, b = PNCounter(), PNCounter()
a.increment("A"); a.increment("A"); b.decrement("B")
a.merge(b); b.merge(a)
assert a.value() == b.value() == 1
```

<details>
<summary>Hint</summary>

Max-merge only works on values that never decrease. Find a way to represent decrements as something that only grows.

</details>

<details>
<summary>Solution</summary>

(a) Replica A increments: its entry is A: 1. B merges from A and now holds A: 1. A decrements: A: 0. B merges from A again: max(1, 0) = 1. The decrement is gone, and no amount of further gossip will bring it back, because max will always prefer 1. Max-merge is only correct when each entry is monotonically non-decreasing.

(b) Count increments and decrements separately, each in its own G-Counter, so both only grow:

```python
class GCounter:
    def __init__(self):
        self.state = {}

    def increment(self, node_id):
        self.state[node_id] = self.state.get(node_id, 0) + 1

    def merge(self, other):
        for node_id, count in other.state.items():
            self.state[node_id] = max(self.state.get(node_id, 0), count)

    def value(self):
        return sum(self.state.values())


class PNCounter:
    def __init__(self):
        self.p = GCounter()  # increments
        self.n = GCounter()  # decrements

    def increment(self, node_id):
        self.p.increment(node_id)

    def decrement(self, node_id):
        self.n.increment(node_id)

    def merge(self, other):
        self.p.merge(other.p)
        self.n.merge(other.n)

    def value(self):
        return self.p.value() - self.n.value()


a, b = PNCounter(), PNCounter()
a.increment("A"); a.increment("A"); b.decrement("B")
a.merge(b); b.merge(a)
assert a.value() == b.value() == 1
```

Convergence: each of P and N is a G-Counter, whose merge (entry-wise max) is commutative, associative and idempotent. Merging a pair of them component-wise keeps all three properties. So once every replica has, directly or through others, merged every other replica's state, all replicas hold the same P and the same N, and therefore the same value P − N. The value can go below zero; if your application needs a floor (stock that cannot go negative), a PN-Counter cannot enforce it, because enforcing a global bound requires coordination.

</details>

**27.8 ★★ Lamport and vector timestamps by hand.** Three processes run these events, each process in the order listed. A: a1 sends m1 to C, a2 is local, a3 receives m2. B: b1 is local, b2 sends m2 to A, b3 receives m3. C: c1 receives m1, c2 sends m3 to B. (a) Give every event's Lamport time and vector clock [A, B, C] using the rules of §27.8. (b) Decide whether a1 → b3, whether a2 → b3, and whether b1 → c2. (c) Find every pair of events x, y with L(x) < L(y) that are nevertheless concurrent.

<details>
<summary>Solution</summary>

(a)

| event | L | V |
|---|---|---|
| a1 (send m1) | 1 | [1,0,0] |
| a2 | 2 | [2,0,0] |
| b1 | 1 | [0,1,0] |
| b2 (send m2) | 2 | [0,2,0] |
| c1 (receive m1) | max(0, 1) + 1 = 2 | [1,0,1] |
| c2 (send m3) | 3 | [1,0,2] |
| b3 (receive m3) | max(2, 3) + 1 = 4 | max([0,2,0], [1,0,2]) = [1,2,2], tick: [1,3,2] |
| a3 (receive m2) | max(2, 2) + 1 = 3 | max([2,0,0], [0,2,0]) = [2,2,0], tick: [3,2,0] |

(b) a1 → b3: yes, [1,0,0] ≤ [1,3,2] in every entry, through a1 → c1 → c2 → b3. a2 → b3: no. [2,0,0] has A = 2 > 1, and [1,3,2] has larger B and C entries, so they are concurrent: m1 left A before a2, so a2 never reached C or B. b1 → c2: no, [0,1,0] and [1,0,2] are incomparable; B's events only reach A.

(c) Comparing the vectors of all pairs, the concurrent pairs with unequal Lamport times are (a1, b2), (b1, a2), (b1, c1), (b1, c2), (a2, c2), (a2, b3), (b2, c2), (c1, a3) and (a3, b3), each listed with the smaller Lamport time first. For example L(a2) = 2 < L(b3) = 4 although a2 ∥ b3, and L(c1) = 2 < L(a3) = 3 although c1 ∥ a3. Lamport order agrees with causality where causality exists and is arbitrary everywhere else.

</details>

**27.9 ★★ A hybrid clock with a fast neighbour.** A's wall clock reads 100, B's reads 41 and C's reads 47. A sends a message to B; B receives it, then sends a message (at wall time 42) to C, which receives it. (a) Give the HLC timestamp of each of the four events. (b) Later B's wall clock reaches 101 and B performs a local event. What is its timestamp? (c) The bounded-drift property says l is never more than the maximum clock skew ahead of the local clock. Check it here, and explain what goes wrong if A's clock is not 59 units fast but a full day fast because of a bad sync.

<details>
<summary>Hint</summary>

On each receive, l becomes the largest of the old l, the message's l, and the local physical time. Which of the three wins on B and on C?

</details>

<details>
<summary>Solution</summary>

(a) A's send: l = max(0, 100) = 100, a new l, so (100, 0). B's receive: l = max(0, 100, 41) = 100, equal to the message's l only, so c = 0 + 1: (100, 1). B's send at wall time 42: l stays 100, so c increments: (100, 2). C's receive at 47: l = max(0, 100, 47) = 100 from the message, c = 2 + 1: (100, 3). Every timestamp increases along the causal chain even though B's and C's clocks are far behind A's.

(b) At wall time 101, l = max(100, 101) = 101, a new value, so c resets: (101, 0).

(c) The largest skew is 100 − 41 = 59 (between A and B). B's l − pt is 100 − 41 = 59 and then 100 − 42 = 58; C's is 100 − 47 = 53. All are within 59. If A's clock were a day fast, every node that heard from A, directly or indirectly, would carry an l a day in the future, and its timestamps would stay pinned at that l with a growing counter until its own clock caught up a day later. Causality would still hold, but "as of time t" reads, TTLs and anything comparing timestamps to real time would be wrong for a day, and nothing would bring l back down. This is why production systems refuse to run with an unbounded ε: CockroachDB shuts down a node whose clock is too far from the rest of the cluster rather than let its timestamps spread.

</details>

**27.10 ★★ Why RGA keeps tombstones.** Replicas A and B both hold "abc", with ids (1,A), (2,A), (3,A). Concurrently, A deletes b and B inserts "x" right after b. (a) Give B's insert operation and the converged text when both replicas apply both operations using the `RGA` class of §27.9. (b) Suppose `apply` removed deleted elements from the list instead of marking them. What happens on A when B's insert arrives, and why can no local rule fix it? (c) When could a replica safely discard the tombstone for b?

<details>
<summary>Solution</summary>

(a) B's clock is 3 after applying A's three inserts, so the operation is `("ins", (4, "B"), (2, "A"), "x")`. On A, b is a tombstone at index 1, so the scan starts at index 2; c's id (3,A) is less than (4,B), so x goes before c. Both replicas hold `a b† x c` and read "axc".

(b) A's `_find((2, "A"))` fails: the element x is anchored to no longer exists, so A has no way to know where x belongs. Any local fallback (drop x, or put it at the end, or at the start) either loses B's insert or puts it somewhere B did not, and replicas that received the insert before the delete would place it correctly, so the replicas diverge. The anchor carries the position information; deleting it deletes the information.

(c) Only when no operation that could still arrive refers to (2,A): every replica must have seen the delete, and every insert anchored to b that was issued before that point must have been delivered everywhere. Equivalently, the delete must be causally stable, which requires knowing the full set of replicas and hearing from all of them. In a peer-to-peer editor where a replica can go offline for weeks, that may never be known, which is why tombstones accumulate and why Yjs keeps a small placeholder for deleted items even when it discards their content.

</details>

---

## Where this connects

- [Chapter 19: Emerging and Specialized Structures](../volume-3/ch19-emerging-and-specialized-structures.md). CRDTs in the broader context of emerging structures
- [Chapter 17: Persistent Data Structures](../volume-3/ch17-persistent-data-structures.md). The persistence ideas that underpin versioned replicas
- [Chapter 13: String Data Structures](../volume-2/ch13-string-data-structures.md). The single-writer text buffers that a sequence CRDT replicates
- [Chapter 31: Real-World Case Studies](ch31-real-world-case-studies.md). Dynamo's vector clocks and Merkle trees, and Spanner's TrueTime as the hardware alternative to hybrid logical clocks
