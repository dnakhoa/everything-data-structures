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

Spanner **waits out the clock uncertainty** rather than trying to eliminate it. Because s is taken from the top of an interval 2ε wide and the wait ends only when the bottom of the interval passes s, a commit waits about 2ε: with ε ≈ 7ms, roughly 14ms before releasing locks (in practice partly overlapped with the Paxos round). Google chose to buy an ordering guarantee with latency, and then spent heavily on GPS receivers and atomic clocks in every datacenter to keep the price low, because the cost of the whole system is proportional to ε.

**Structures in play**: B-trees for tablet storage (via Colossus), a Paxos state machine per tablet group, two-phase locking, and MVCC. Every row version is timestamped, so a snapshot read at time t needs no locks at all and never blocks a writer. That last property is [Chapter 17](../volume-3/ch17-persistent-data-structures.md)'s partial persistence, deployed globally.

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
- Quorum overlap: R + W > N
```

**Anti-entropy**: Merkle trees for background synchronization. Each replica maintains local Merkle tree of its key range; trees compared to detect divergence.

Dynamo is the deliberate opposite of Spanner, and the paper is unusually honest about why: for Amazon's shopping cart, **rejecting a write costs a sale**. So Dynamo never rejects one. If the responsible node is unreachable, another node accepts the write and holds it with a hint to forward it later: *sloppy quorum with hinted handoff*.

The consequence is that two replicas can legitimately hold different values for the same key, and the system needs a way to tell "B replaced A" from "A and B happened concurrently". That is what **vector clocks** provide:

```
Client writes cart to node A:        [(A,1)]
Client adds item, writes to A:       [(A,2)]           A,2 descends from A,1 → replaces
Partition. Client adds via B:        [(A,2), (B,1)]
Meanwhile client adds via C:         [(A,2), (C,1)]

Partition heals. Neither vector dominates the other
→ concurrent. Both versions are returned to the client.
```

Dynamo pushes reconciliation to the application, and for a shopping cart the resolution is a set union, which is why a deleted item famously sometimes reappears. That is the visible cost of choosing availability, and it is a deliberate trade, not a bug.

**Merkle trees** solve the other problem: detecting divergence without comparing everything. Each replica hashes its key range into a tree; two replicas compare root hashes, and if they match (the common case) they are identical and nothing more transfers. If they differ, they descend only into subtrees whose hashes disagree. Comparing two replicas of a million keys with one difference takes about 20 hash comparisons instead of a million. The same structure, for the same reason, is how Git compares trees and how BitTorrent verifies pieces.

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

Kafka's insight is that **an append-only log is a better primitive than a queue**. A traditional message queue deletes a message once consumed, which forces it to track per-message delivery state and makes replay impossible. Kafka never deletes on consumption; it keeps an ordered, immutable log and lets each consumer track its own **offset**: a single integer.

That one decision produces most of Kafka's properties:

- Multiple independent consumers read the same partition at different positions, without coordination.
- Replay is seeking backwards.
- Broker state per consumer is one integer, so brokers scale to enormous consumer counts.
- Writes are pure appends. Sequential disk I/O, which as [Chapter 16](../volume-3/ch16-external-memory-and-cache-oblivious-structures.md) explains is often faster than random writes to *memory*, and vastly faster than random disk writes.

The `.index` file is a **sparse** index: an entry every few kilobytes, not per message. A lookup binary-searches it to find the nearest earlier offset, then scans forward. Sparse keeps the index small enough to stay in page cache, and the scan is sequential. The same "cheap sequential work beats expensive random work" reasoning throughout.

**Zero-copy** is worth understanding as an accounting exercise. A conventional send copies data four times: disk → kernel page cache → user buffer → socket buffer → NIC. `sendfile()` goes disk → page cache → NIC, eliminating two copies and two context switches. This is only possible because Kafka does not transform the bytes. It stores exactly what the producer sent, so the kernel can move them without user space ever seeing them. An immutable log makes the optimisation available.

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

The fix is to stop treating the file listing as the source of truth. **The transaction log is the table**; the Parquet files are just content addressed by it. A reader replays the log to compute the current file set, and a file not named in the log does not exist as far as the table is concerned, so a failed job leaves orphaned files that are simply invisible, rather than corruption.

This makes the table state a **persistent data structure** in exactly the sense of [Chapter 17](../volume-3/ch17-persistent-data-structures.md): each log entry produces a new version, old versions remain valid, and unchanged files are shared between them. "Time travel" (querying the table as of last Tuesday) is not a feature bolted on but a direct consequence of the representation.

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

**Anycast makes routing itself the load balancer.** Hundreds of PoPs announce the same IP prefix via BGP, and the internet's own routing tables (the tries of [Chapter 28](ch28-network-topology-and-routing-data-structures.md))deliver each packet to the topologically nearest one. There is no load balancer to scale, no DNS TTL to wait out during a failover, and a PoP that goes down simply stops announcing, after which BGP reconverges automatically. The cost is that the routing tables decide, not you: BGP optimises for AS-path length, which is not always the lowest latency.

**The cache hierarchy is the memory hierarchy again**, at planetary scale and with the same arithmetic. Each tier is larger, slower, and further away, and each absorbs the misses of the tier above:

| Tier | Size | Latency | Role |
|------|------|---------|------|
| Edge PoP | ~100GB | ~5ms | Absorbs the bulk of requests |
| Regional | ~1TB | ~30ms | Catches what edges miss |
| Origin shield | ~10TB | ~80ms | Protects the origin from stampedes |
| Origin | n/a | ~200ms+ | Source of truth |

The origin shield exists for a specific failure mode: without it, a popular object expiring simultaneously across 300 edge PoPs sends 300 requests to the origin at once, a **thundering herd**. The shield collapses them into one. The general technique is *request coalescing*: concurrent misses for the same key wait on a single in-flight fetch rather than each issuing their own.

**Cache key design is where correctness lives.** Include too much in the key (a tracking parameter, a session cookie) and the hit rate collapses because every request is unique. Include too little and users are served each other's content, which is a security incident rather than a performance problem. The `Vary` header is the standard mechanism, and getting it wrong is one of the more common ways to leak data between users.

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

**Sequential access wins repeatedly.** Kafka's append-only log, Delta Lake's log, LSM-tree flushes, Merkle tree comparison: the same principle from [Chapter 16](../volume-3/ch16-external-memory-and-cache-oblivious-structures.md), reappearing at every scale from cache lines to datacenters.

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**31.1 ★★ How long is commit wait?** Spanner's TrueTime returns an interval [earliest, latest] of width 2ε around the true time. A transaction picks s = TT.now().latest and then waits until TT.now().earliest > s. Assuming ε stays constant, show that the wait lasts about 2ε, and compute it for ε = 1 ms, 4 ms and 7 ms. Then explain what could go wrong if Spanner skipped the wait.

<details>
<summary>Hint</summary>

Start by assuming the interval is centered on the true time t, so latest = t + ε and earliest = t − ε, then check whether an off-center clock changes the answer.

</details>

<details>
<summary>Solution</summary>

Take a clock centered on the true time. At true time t₀, the transaction picks s = latest = t₀ + ε. At a later true time t, earliest = t − ε, and the wait ends when t − ε > s = t₀ + ε, that is when t > t₀ + 2ε. So the wait is 2ε: 2 ms, 8 ms and 14 ms for ε = 1, 4 and 7 ms. If the true time sits at some other fixed position inside the interval, both bounds shift by the same amount and the offset cancels: the wait is still 2ε.

After the wait, earliest > s, which means the true time is definitely past s on every machine whose TrueTime interval is correct. Any transaction that starts after this one commits will pick a timestamp from a later interval, so its timestamp exceeds s. Commit order then matches real-time order: external consistency.

Without the wait, transaction T1 could commit with s₁ = t₀ + ε and release its locks immediately. A client sees T1's result and then starts T2 on another server whose clock reads slightly behind; that server might pick s₂ < s₁. A snapshot read at a time between s₂ and s₁ would then see T2's write but not T1's, although T1 visibly finished first. The wait trades a few milliseconds of write latency for never having that anomaly, and halving ε halves the price.

</details>

**31.2 ★ Quorums and sloppy quorums.** Dynamo uses N = 3. For each (R, W) of (1, 1), (1, 3), (2, 2), (3, 1), say whether a read is guaranteed to see the latest acknowledged write when no nodes fail, and which configuration favors what. Then explain why, even with R + W > N, a sloppy quorum does not give that guarantee during a failure.

<details>
<summary>Solution</summary>

The overlap condition is R + W > N, here R + W > 3.

| (R, W) | R + W | read sees latest write? | favors |
|---|---|---|---|
| (1, 1) | 2 | no | lowest latency, highest availability |
| (1, 3) | 4 | yes | fast reads; any one node down blocks writes |
| (2, 2) | 4 | yes | balanced; tolerates one failure for both |
| (3, 1) | 4 | yes | fast, always-available writes; slow reads |

Dynamo's common configuration is (2, 2).

A sloppy quorum counts the first W healthy nodes on the preference list, which may include nodes outside the key's normal three replicas. If replica B is unreachable, a write might be acknowledged by A and D (holding a hint for B). A read that then goes to B (now reachable) and C reaches two of the key's home replicas, neither of which has the write, so it returns stale data even though R + W = 4 > 3. The overlap argument only works when both quorums are drawn from the same set of N nodes. Sloppy quorum gives up that guarantee to keep accepting writes, and hinted handoff plus anti-entropy repair the divergence later.

</details>

**31.3 ★★ Vector clocks after reconciliation.** Continue the shopping-cart example in §31.2. The client reads the key, receives both [(A,2), (B,1)] and [(A,2), (C,1)], merges the carts, and writes the result through node A. (a) What vector clock does the new version get, and why does it replace both siblings? (b) For each pair, say whether the first happened before the second, after it, or concurrently: [(A,1)] and [(A,1), (B,1)]; [(A,2), (B,1)] and [(A,1), (B,2)]; [(A,3), (B,1), (C,1)] and [(A,2), (C,1)]; [(B,1)] and [(C,1)].

<details>
<summary>Solution</summary>

(a) The client sends back a context that is the entry-wise maximum of the clocks it read, [(A,2), (B,1), (C,1)], and node A increments its own entry: [(A,3), (B,1), (C,1)]. This clock is at least as large as both siblings in every entry and strictly larger in A, so it dominates both. Every node that later sees it can discard the two siblings: the conflict is resolved.

(b) Compare entry by entry, treating a missing entry as 0.

| first | second | relation |
|---|---|---|
| [(A,1)] | [(A,1), (B,1)] | before: equal on A, and B: 0 < 1 |
| [(A,2), (B,1)] | [(A,1), (B,2)] | concurrent: A is larger in the first, B in the second |
| [(A,3), (B,1), (C,1)] | [(A,2), (C,1)] | after: every entry ≥, A strictly greater |
| [(B,1)] | [(C,1)] | concurrent: each has an entry the other lacks |

Concurrent versions are returned to the client as siblings; ordered ones are resolved by keeping the later.

</details>

**31.4 ★★ The arithmetic of Merkle comparison.** Two replicas each store 2^20 (about a million) keys under a binary Merkle tree with one leaf per key. They compare by checking the roots, then, at every node whose hashes differ, comparing both children. (a) How many hash comparisons if exactly one key differs? (b) Estimate the count if 1,000 keys, scattered at random, differ. (c) What does that suggest about when Merkle synchronization stops paying off?

<details>
<summary>Solution</summary>

(a) The tree has 20 levels below the root. One differing leaf makes exactly one node differ at each level: the root and 19 internal nodes above the leaf, 20 differing internal nodes in all. The protocol compares the root (1) and both children of each differing internal node (2 × 20), so 41 hash comparisons in total, against a million for a flat comparison. (The chapter's "about 20" counts levels. Skipping the right child when the left child matches, since a differing parent with a matching left child must have a differing right child, brings it down to between 21 and 41.)

(b) Near the top, 1,000 random leaves make nearly every node differ, but levels 0 to 9 hold only 1,023 nodes in total (about 950 of them differ). Further down there are more nodes per level than differences, so close to 1,000 nodes differ per level, one per differing key, for the remaining 10 levels. That is about 10,000 differing internal nodes (the exact expectation is 10,145), so about 20,300 comparisons. A rule of thumb is 2 × k × log₂(N/k) for k differences among N keys: 2 × 1,000 × log₂(1,048) ≈ 20,000.

(c) The cost grows nearly linearly in the number of differences, plus a log factor. When the replicas differ in a large fraction of keys, the tree walk costs more than just streaming every key's hash in order (N comparisons, sequential). Merkle trees are built for the common case: replicas that are almost the same. This is also why Dynamo-style systems run anti-entropy continuously, so the differences stay small.

</details>

**31.5 ★ Find an offset with a sparse index.** A Kafka segment's `.index` file holds these (offset, byte position) entries: (0, 0), (52, 4120), (97, 8233), (150, 12400). How does the broker find offset 120? With the default of one index entry per 4,096 bytes of log and 8 bytes per entry, how large is the index for a 1 GiB segment?

<details>
<summary>Solution</summary>

Binary-search the index for the largest offset ≤ 120: that is (97, 8233). Seek to byte 8,233 of the `.log` file and scan forward, reading record headers, past offsets 97 to 119 (23 records) until reaching offset 120. The scan reads at most about 4 KB, which is likely already in the page cache and is sequential.

Index size: 2^30 / 2^12 = 262,144 entries × 8 bytes = 2 MiB per 1 GiB segment, 1/512 of the data. A dense index with one entry per record would be far larger for small records, which is the trade the chapter describes: a little sequential scanning in exchange for an index small enough to stay in memory.

</details>

**31.6 ★★ What the hierarchy buys.** Use the tier latencies in §31.5 as end-to-end response times. Suppose the edge PoP hits 90% of requests, the regional tier hits 60% of what reaches it, and the origin shield hits 50% of what reaches it. (a) What fraction of requests reach the origin, and what is the mean latency? (b) What is the mean latency if the edge hit rate improves to 95%, with the other tiers' hit rates unchanged? (c) Without the shield (regional misses go straight to the origin), what fraction of requests reach the origin?

<details>
<summary>Solution</summary>

(a) Served at the edge: 0.90. At regional: 0.10 × 0.6 = 0.06. At the shield: 0.10 × 0.4 × 0.5 = 0.02. At the origin: 0.10 × 0.4 × 0.5 = 0.02, that is 2% of requests.

Mean latency = 0.90 × 5 + 0.06 × 30 + 0.02 × 80 + 0.02 × 200 = 4.5 + 1.8 + 1.6 + 4.0 = 11.9 ms.

(b) Edge 0.95, regional 0.05 × 0.6 = 0.03, shield 0.01, origin 0.01. Mean = 4.75 + 0.9 + 0.8 + 2.0 = 8.45 ms. Five more points of edge hit rate cut mean latency by 29% and origin load in half, because misses are what dominate the mean: 2% of requests at the origin contributed a third of the latency in (a). This is the same reasoning as average memory access time for CPU caches.

(c) 0.10 × 0.4 = 4% of requests reach the origin, double the load. And that is the average; the shield's larger job is collapsing simultaneous misses for the same object from many PoPs into one origin fetch, which the averages here do not show.

</details>

**31.7 ★★★ Optimistic commits on object storage.** In Delta Lake (§31.4), writers commit version N+1 by atomically creating the log file for N+1. Writers W1 and W2 both read version 7. W1 commits version 8 first. (a) W1 only appended new files to partition date=2024-01-01. W2 read and rewrote files in partition date=2024-01-02. Must W2 redo its work? (b) Instead, W1 was a compaction that removed file f4 and added a merged file, and W2 was an UPDATE that read f4 and wrote a modified copy. Must W2 redo its work? (c) Why must "create the file for version N+1" be a put-if-absent operation, and what happens if the storage only offers a plain overwrite?

<details>
<summary>Hint</summary>

The conflict check compares what W2 read against what W1's commit changed. For (c), consider both writers succeeding at writing the same file name.

</details>

<details>
<summary>Solution</summary>

(a) No. W2's attempt to create version 8 fails, so it reads version 8's log entry, sees that W1 only added files in a partition W2 never read, and concludes its own result is still correct against the new table state. It retries the commit as version 9 without redoing any work. This is the common case the design relies on: concurrent writers usually touch disjoint data.

(b) Yes. W2 read f4, but version 8 removed f4, and the merged file now holds those rows. If W2 committed anyway, its log entry would remove f4 (already gone) and add its modified copy, while the merged file still contains the unmodified rows: the table would hold both versions of those rows. This is a real conflict, so W2 must abort, re-read the table at version 8, and redo the UPDATE.

(c) The atomic create is the only serialization point in the whole protocol: it decides which of the concurrent writers gets each version number. With plain overwrite, both W1 and W2 would successfully write the file for version 8, the second silently replacing the first. W1 believes it committed, but its log entry is gone, and readers will never see its files: a lost write with no error. This is why Delta Lake on stores that lacked a put-if-absent primitive needed an external coordination service (a lock or a conditional write in a database) to guard log commits.

</details>

---

## Where this connects

- [Chapter 29: System Design as Data Structure Composition](ch29-system-design-as-data-structure-composition.md). The composition principle these systems demonstrate
- [Chapter 27: Distributed Data Structures](ch27-distributed-data-structures.md). The distributed primitives they are built from
