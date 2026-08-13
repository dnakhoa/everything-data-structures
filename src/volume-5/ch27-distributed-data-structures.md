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

**Node buckets**: Each node maintains k buckets for each prefix length. Buckets are prioritized by least-recently-seen nodes, ensuring long-lived nodes stay in routing tables.

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

Amazon Dynamo improves on basic consistent hashing with load bounds:

1. Each node gets a "capacity" number representing load responsibility
2. When a node receives too many keys, it splits its range with a neighbor
3. System guarantees load within a factor of (2k/k+1) of ideal

## 27.4 Distributed Snapshots and State Machine Replication

Replicating state across machines requires capturing consistent global states despite concurrent operations.

### Chandy-Lamport Algorithm

Designed for distributed snapshot collection without process coordination:

1. **Initiator** sends marker on all outgoing channels
2. When a process receives marker on channel C:
   - Record local state (marker is first from C)
   - Forward marker on all other outgoing channels
   - Start recording messages on channel C
3. When all channels have received markers, snapshot is complete

**Causality guarantee**: The algorithm captures a consistent cut where each process's recorded state occurred at the same logical time across the system.

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

### Operation-based CRDTs

Each operation carries metadata enabling correct merge:

**G-Counter (Grow-only Counter)**:
```python
class GCounter:
    def __init__(self):
        self.state = {}  # node_id -> count

    def increment(self, node_id):
        self.state[node_id] += 1

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

### State-based CRDTs (Convergent CRDTs)

Operations are applied locally and entire state is merged using join operations:

**OR-Set (Observed-Remove Set)**:
```python
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

    def merge(self, other):
        # Union of elements, removing tombstones
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
- Accept phase can be skipped if no competing proposals

## 27.7 Quorum Systems

Quorums define the minimum number of nodes required for read/write operations.

**Strict quorum**: Read and write quorums must overlap (R + W > N)

**Quorum construction**:
- **Majority quorum**: R = W = ⌊N/2⌋ + 1 (tolerates N/2 failures)
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
        return all(
            self.versions.get(k, 0) <= v
            for k, v in other.versions.items()
        ) and any(
            self.versions.get(k, 0) < v
            for k, v in other.versions.items()
        )
```

---

## Where this connects

- [Chapter 19: Emerging and Specialized Structures](../volume-3/ch19-emerging-and-specialized-structures.md) — CRDTs in the broader context of emerging structures
- [Chapter 17: Persistent Data Structures](../volume-3/ch17-persistent-data-structures.md) — the persistence ideas that underpin versioned replicas
