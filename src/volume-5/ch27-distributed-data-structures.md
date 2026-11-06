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

---

## Where this connects

- [Chapter 19: Emerging and Specialized Structures](../volume-3/ch19-emerging-and-specialized-structures.md). CRDTs in the broader context of emerging structures
- [Chapter 17: Persistent Data Structures](../volume-3/ch17-persistent-data-structures.md). The persistence ideas that underpin versioned replicas
