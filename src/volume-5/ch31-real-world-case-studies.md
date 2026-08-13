# Chapter 31: Real-World Case Studies

Five systems, examined for the same thing: which data structures they chose, and what those choices bought and cost. Each one made a decision the others didn't, and in every case the decision traces back to a structure from earlier in this book.

## 31.1 Google's Spanner: Globally Distributed SQL

Spanner combines B-tree storage with distributed systems innovations:

**Architecture**:
```
Universe (global deployment)
  ↓
Zone (data center)
  ↓
Spanserver (process)
  ↓
Tablet (range of rows, ~100GB)
  ↓
Colossus (distributed file system)
```

**TrueTime API**: GPS and atomic clocks provide bounded clock uncertainty (±1ms to ±7ms). This enables:
- External consistency (linearizable transactions)
- Snapshot reads without coordination
- Consistent schema changes

**Paxos consensus**: Data replicated via Paxos between zones. Two-phase commit with participant coordinators.

**The central idea is that TrueTime turns time into a data structure with an error bar.** Ordinary clocks return a timestamp; TrueTime returns an *interval* `[earliest, latest]` guaranteed to contain the true time. That single change makes global ordering possible without global coordination.

The mechanism is called **commit wait**, and it is almost aggressively simple:

```
To commit a transaction at timestamp s:
  1. Acquire locks, pick s = TT.now().latest
  2. Do the work
  3. WAIT until TT.now().earliest > s      ← deliberately sleep
  4. Release locks, commit

After the wait, s is guaranteed to be in the past everywhere on Earth.
So any transaction that starts later gets a strictly larger timestamp.
```

Spanner **waits out the clock uncertainty** rather than trying to eliminate it. With ε ≈ 7ms of uncertainty, every commit sleeps roughly 7ms before releasing locks. Google chose to buy an ordering guarantee with latency, and then spent heavily on GPS receivers and atomic clocks in every datacenter to keep the price low — because the cost of the whole system is proportional to ε.

**Structures in play**: B-trees for tablet storage (via Colossus), a Paxos state machine per tablet group, two-phase locking, and MVCC — every row version is timestamped, so a snapshot read at time t needs no locks at all and never blocks a writer. That last property is [Chapter 17](../volume-3/ch17-persistent-data-structures.md)'s partial persistence, deployed globally.

**The cost**: writes pay a cross-region Paxos round trip plus commit wait, so write latency is tens to hundreds of milliseconds. Spanner is the right answer when you need global transactions and can tolerate that, and the wrong answer for a write-heavy local workload.

## 31.2 Amazon Dynamo: Highly Available Key-Value Store

Dynamo prioritizes availability over consistency:

**Design decisions**:
- "Always writable": Sloppy quorum + hinted handoff
- Vector clocks for causality tracking
- Quorum guarantees configurable per request

**Data distribution**:
```
Consistent hashing ring (N=3, R=2, W=2):
- N: Number of replicas
- R: Minimum read replicas
- W: Minimum write replicas
- Quorum: max(R,W) > N/2
```

**Anti-entropy**: Merkle trees for background synchronization. Each replica maintains local Merkle tree of its key range; trees compared to detect divergence.

Dynamo is the deliberate opposite of Spanner, and the paper is unusually honest about why: for Amazon's shopping cart, **rejecting a write costs a sale**. So Dynamo never rejects one. If the responsible node is unreachable, another node accepts the write and holds it with a hint to forward it later — *sloppy quorum with hinted handoff*.

The consequence is that two replicas can legitimately hold different values for the same key, and the system needs a way to tell "B replaced A" from "A and B happened concurrently". That is what **vector clocks** provide:

```
Client writes cart to node A:        [(A,1)]
Client adds item, writes to A:       [(A,2)]           A,2 descends from A,1 → replaces
Partition. Client adds via B:        [(A,2), (B,1)]
Meanwhile client adds via C:         [(A,2), (C,1)]

Partition heals. Neither vector dominates the other
→ concurrent. Both versions are returned to the client.
```

Dynamo pushes reconciliation to the application, and for a shopping cart the resolution is a set union — which is why a deleted item famously sometimes reappears. That is the visible cost of choosing availability, and it is a deliberate trade, not a bug.

**Merkle trees** solve the other problem: detecting divergence without comparing everything. Each replica hashes its key range into a tree; two replicas compare root hashes, and if they match — the common case — they are identical and nothing more transfers. If they differ, they descend only into subtrees whose hashes disagree. Comparing two replicas of a million keys with one difference takes about 20 hash comparisons instead of a million. The same structure, for the same reason, is how Git compares trees and how BitTorrent verifies pieces.

**Structures in play**: consistent hashing with virtual nodes ([Chapter 27](ch27-distributed-data-structures.md)), vector clocks, Merkle trees, and per-node LSM or B-tree storage. Dynamo's design became DynamoDB, Cassandra, Riak, and Voldemort.

## 31.3 Apache Kafka: Distributed Log as First-Class Citizen

Kafka treats the log as the primary data structure:

**Storage architecture**:
```
Topic: "orders"
  ↓
Partitions (16):
  Partition 0: [0 → 1MB] [1MB → 2MB] ...
  Partition 1: [0 → 1.2MB] [1.2MB → 2.1MB] ...
  ...

Each partition stored as:
  - .log file (actual data)
  - .index file (offset → position)
  - .timeindex file (timestamp → offset)
```

**Zero-copy I/O**: Kafka uses kernel sendfile() to avoid copying data to user space. DMA transfers data from disk directly to network.

**Page cache**: Linux page cache used for hot data. Sequential writes cause read-ahead, sequential reads cause readahead.

Kafka's insight is that **an append-only log is a better primitive than a queue**. A traditional message queue deletes a message once consumed, which forces it to track per-message delivery state and makes replay impossible. Kafka never deletes on consumption; it keeps an ordered, immutable log and lets each consumer track its own **offset** — a single integer.

That one decision produces most of Kafka's properties:

- Multiple independent consumers read the same partition at different positions, without coordination.
- Replay is seeking backwards.
- Broker state per consumer is one integer, so brokers scale to enormous consumer counts.
- Writes are pure appends — sequential disk I/O, which as [Chapter 16](../volume-3/ch16-external-memory-and-cache-oblivious-structures.md) explains is often faster than random writes to *memory*, and vastly faster than random disk writes.

The `.index` file is a **sparse** index: an entry every few kilobytes, not per message. A lookup binary-searches it to find the nearest earlier offset, then scans forward. Sparse keeps the index small enough to stay in page cache, and the scan is sequential — the same "cheap sequential work beats expensive random work" reasoning throughout.

**Zero-copy** is worth understanding as an accounting exercise. A conventional send copies data four times: disk → kernel page cache → user buffer → socket buffer → NIC. `sendfile()` goes disk → page cache → NIC, eliminating two copies and two context switches. This is only possible because Kafka does not transform the bytes — it stores exactly what the producer sent, so the kernel can move them without user space ever seeing them. An immutable log makes the optimisation available.

**The cost**: ordering is guaranteed only within a partition, not across a topic. Anything needing global ordering must use a single partition and give up parallelism. That constraint shapes every Kafka data model.

## 31.4 Databricks Delta Lake: ACID on Data Lakes

Combines streaming (append-only log) with batch processing:

**Transaction log**: JSON entries recording changes:
```json
{"add": "part-00000.snappy.parquet", "partitionValues": {"date": "2024-01-01"}, "size": 1234567}
{"remove": "part-00099.parquet"}
```

**Optimistic concurrency**: Delta Lake uses file-level locking. Transaction validation checks:

1. Read current protocol version
2. Verify read set files still exist
3. Write new files and transaction commit
4. If conflict, retry with exponential backoff

Delta Lake solves a problem created by cloud object storage: S3 gives cheap, durable, effectively infinite storage but **no transactions and no atomic multi-file operations**. A job writing 500 Parquet files that fails halfway leaves the table in a state no reader can interpret.

The fix is to stop treating the file listing as the source of truth. **The transaction log is the table**; the Parquet files are just content addressed by it. A reader replays the log to compute the current file set, and a file not named in the log does not exist as far as the table is concerned — so a failed job leaves orphaned files that are simply invisible, rather than corruption.

This makes the table state a **persistent data structure** in exactly the sense of [Chapter 17](../volume-3/ch17-persistent-data-structures.md): each log entry produces a new version, old versions remain valid, and unchanged files are shared between them. "Time travel" — querying the table as of last Tuesday — is not a feature bolted on but a direct consequence of the representation.

Replaying the entire log would get slow, so Delta periodically writes a **checkpoint** (a Parquet file holding the full state at version N), and readers start from the newest checkpoint and replay only the entries after it. This is the same log-plus-snapshot pattern used by Raft, Redis AOF with RDB, and every event-sourced system in [Chapter 30](ch30-advanced-system-patterns-and-case-studies.md).

**Optimistic concurrency** works here because the workload is right for it: writers are few and conflicts are rare. Each writer reads the current version, does its work, and attempts to commit version N+1 by atomically creating a file with that name. Exactly one wins; the loser checks whether the conflict was real (did anyone touch the files I read?) and retries if not. Pessimistic locking would be pure overhead at this conflict rate.

**The cost**: small, frequent writes produce many small files and log entries, degrading read performance until compaction runs. Delta Lake suits batch and micro-batch workloads, not per-record streaming.

## 31.5 Cloudflare's Edge Cache: Global Caching Infrastructure

**Anycast routing**: All edge nodes announce same IP via BGP. Traffic routed to nearest PoP (Point of Presence).

**Cache hierarchy**:
```
User → Edge PoP (L1 cache, ~100GB)
           ↓ (miss)
        Regional DC (L2 cache, ~1TB)
           ↓ (miss)
        Origin Shield (L3 cache, ~10TB)
           ↓ (miss)
        Origin server
```

**Cache key normalization**:
- Strip query parameters (configurable)
- Normalize URL encoding
- Include vary headers in key
- TTL rules per content type

Two structural ideas do most of the work here.

**Anycast makes routing itself the load balancer.** Hundreds of PoPs announce the same IP prefix via BGP, and the internet's own routing tables — the tries of [Chapter 28](ch28-network-topology-and-routing-data-structures.md) — deliver each packet to the topologically nearest one. There is no load balancer to scale, no DNS TTL to wait out during a failover, and a PoP that goes down simply stops announcing, after which BGP reconverges automatically. The cost is that the routing tables decide, not you: BGP optimises for AS-path length, which is not always the lowest latency.

**The cache hierarchy is the memory hierarchy again**, at planetary scale and with the same arithmetic. Each tier is larger, slower, and further away, and each absorbs the misses of the tier above:

| Tier | Size | Latency | Role |
|------|------|---------|------|
| Edge PoP | ~100GB | ~5ms | Absorbs the bulk of requests |
| Regional | ~1TB | ~30ms | Catches what edges miss |
| Origin shield | ~10TB | ~80ms | Protects the origin from stampedes |
| Origin | — | ~200ms+ | Source of truth |

The origin shield exists for a specific failure mode: without it, a popular object expiring simultaneously across 300 edge PoPs sends 300 requests to the origin at once — a **thundering herd**. The shield collapses them into one. The general technique is *request coalescing*: concurrent misses for the same key wait on a single in-flight fetch rather than each issuing their own.

**Cache key design is where correctness lives.** Include too much in the key — a tracking parameter, a session cookie — and the hit rate collapses because every request is unique. Include too little and users are served each other's content, which is a security incident rather than a performance problem. The `Vary` header is the standard mechanism, and getting it wrong is one of the more common ways to leak data between users.

## 31.6 What the Five Have in Common

Reading them side by side, the patterns are more instructive than any individual system:

| | Spanner | Dynamo | Kafka | Delta Lake | Cloudflare |
|---|---|---|---|---|---|
| **Chooses** | Consistency | Availability | Throughput | Correctness on cheap storage | Latency |
| **Gives up** | Write latency | Read consistency | Cross-partition order | Small-write efficiency | Cache-key complexity |
| **Core structure** | Paxos + MVCC B-trees | Consistent hash ring | Append-only log | Versioned log of files | Hierarchical cache + trie routing |
| **Key insight** | Bound clock error, then wait it out | Never reject a write | Never delete on read | The log *is* the table | Let BGP do the balancing |

Three observations worth carrying:

**Every system is a composition, not an invention.** Spanner is B-trees plus Paxos plus MVCC plus a clock. Dynamo is consistent hashing plus vector clocks plus Merkle trees. None of the components are new; the arrangement is. This is the claim [Chapter 29](ch29-system-design-as-data-structure-composition.md) makes, and these systems are the evidence.

**The interesting decision is always what to give up.** Spanner and Dynamo faced the same problem and chose opposite sides of CAP, and both were right for their workload. A system that appears to give up nothing has usually hidden the cost somewhere you haven't looked yet.

**Sequential access wins repeatedly.** Kafka's append-only log, Delta Lake's log, LSM-tree flushes, Merkle tree comparison — the same principle from [Chapter 16](../volume-3/ch16-external-memory-and-cache-oblivious-structures.md), reappearing at every scale from cache lines to datacenters.

---

## Where this connects

- [Chapter 29: System Design as Data Structure Composition](ch29-system-design-as-data-structure-composition.md) — the composition principle these systems demonstrate
- [Chapter 27: Distributed Data Structures](ch27-distributed-data-structures.md) — the distributed primitives they are built from
