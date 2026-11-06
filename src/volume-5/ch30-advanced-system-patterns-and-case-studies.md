# Chapter 30: Advanced System Patterns and Case Studies

## 30.1 Search Infrastructure: Inverted Index

Full-text search engines use inverted indexes for efficient keyword lookups.

### Inverted Index Structure

```
Document collection:
Doc1: "data structures are fundamental"
Doc2: "data structures enable efficient algorithms"

Forward index (doc → terms):
Doc1 → ["data", "structures", "are", "fundamental"]
Doc2 → ["data", "structures", "enable", "efficient", "algorithms"]

Inverted index (term → docs):
"data"      → [Doc1, Doc2]
"structures"→ [Doc1, Doc2]
"are"       → [Doc1]
"fundamental" → [Doc1]
"enable"    → [Doc2]
"efficient" → [Doc2]
"algorithms"→ [Doc2]
```

**Posting list**: Each term points to a sorted list of document IDs.

### BM25 Scoring

Probabilistic relevance ranking:
```
Score(D, Q) = Σ IDF(qi) × (tf × (k1 + 1)) / (tf + k1 × (1 - b + b × |D|/avgdl))

Where:
- tf = term frequency in document
- |D| = document length
- avgdl = average document length
- k1 = term frequency saturation (typically 1.2-2.0)
- b = length normalization (typically 0.75)
- IDF = log((N - n + 0.5) / (n + 0.5))
```

### Fenced and Sharded Indexes

**Sharding by document**: Different shards contain different documents. Parallel query all shards, merge results.

**Sharding by term (router)**: One shard responsible for a term range. Queries routed based on first term. Problem: hot terms cause imbalance.

## 30.2 Recommendation System Data Structures

### Collaborative Filtering with Matrix Factorization

User-item matrix decomposition:
```
R ≈ U × V^T

R: m×n user-item rating matrix
U: m×k user latent factors
V: n×k item latent factors
k: latent dimension (typical 50-200)
```

**Alternating Least Squares (ALS)**:
```python
def als(R, k, iterations, reg=0.1):
    """`reg` is the L2 regularization weight, spelled `lambda` in the papers,
    which is a reserved word in Python."""
    m, n = R.shape
    U = random(m, k)
    V = random(n, k)
    I = identity(k)

    for _ in range(iterations):
        # Fix U, solve for V
        for j in range(n):
            users = R[:, j].nonzero()
            V[j] = solve(
                U[users].T @ U[users] + reg * I,
                U[users].T @ R[users, j]
            )
        # Fix V, solve for U
        for i in range(m):
            items = R[i, :].nonzero()
            U[i] = solve(
                V[items].T @ V[items] + reg * I,
                V[items].T @ R[i, items].T
            )
    return U, V
```

### Approximate Nearest Neighbors

Vector search for embedding similarity:
```python
class HNSW:
    def __init__(self, m=16, ef_construction=200):
        self.m = m
        self.ef = ef_construction
        self.mL = 1 / log(m)  # level multiplier from the HNSW paper
        self.graph = {}  # node_id -> [neighbors]
        self.layers = []  # layer -> [node_ids]

    def insert(self, vector, max_layers=6):
        # Random layer selection (geometric): P(level >= l) = m ** -l
        level = min(int(-log(random()) * self.mL), max_layers - 1)

        # (Greedy ef=1 descent through the layers above `level` omitted.)
        # On each layer from `level` down to 0, search with ef_construction
        for l in reversed(range(level + 1)):
            candidates = self._search_layer(vector, ef=self.ef, layer=l)
            # Connect to the m nearest candidates
            self._connect(vector, candidates, l)
```

**ANN benchmarks**: HNSW, ScaNN, DiskANN, FAISS. Trade-offs: query speed vs recall vs memory.

## 30.3 Time Series Databases

Time series data requires specialized structures for append-heavy workloads and time-range queries.

### Columnar Storage with Time Partitioning

```
Partitioning scheme:
/data/year=2024/month=01/day=15/hour=12/
    segment_000.parquet
    segment_001.parquet
    segment_002.parquet

Within segment (columnar):
| timestamp | cpu | memory | disk_io |
| 1705312800 | 45 | 32 | 1200 |
| 1705312801 | 47 | 31 | 1150 |
```

**Benefits**:
- Columnar: Efficient aggregation (only read needed columns)
- Time partitioning: Prune irrelevant partitions
- Segment size: Balance between query efficiency and write buffering

### Downsampling and Aggregation

**Tiered storage**: Raw data → Downsampled → Long-term retention
```
Raw (second precision) → 1 hour rollup → 1 day rollup → 1 month rollup
Retention: 1 week         6 months        2 years          forever
```

**Aggregation algorithms**:
- **LTTB**: Largest Triangle Three Buckets for visual fidelity
- **Min/max sketches**: Approximate aggregates with space efficiency

## 30.4 Event Sourcing and CQRS

Event sourcing stores state as a sequence of events rather than current state.

### Event Store Structure

```python
class EventStore:
    def __init__(self):
        self.streams = {}  # aggregate_id -> [event]

    def append(self, aggregate_id, event):
        self.streams.setdefault(aggregate_id, []).append(event)

    def get_stream(self, aggregate_id, from_version=0):
        return self.streams.get(aggregate_id, [])[from_version:]

    def rebuild_state(self, aggregate_id):
        state = {}
        for event in self.get_stream(aggregate_id):
            state = apply_event(state, event)
        return state
```

**Benefits**: Complete audit trail, temporal queries, easy replay for debugging.

**Challenges**: Event schema evolution, eventual consistency, query complexity.

### CQRS (Command Query Responsibility Segregation)

Separate read and write models:
```
Command side (write):
- Handle commands (not queries)
- Aggregate events into state
- Publish to event bus

Query side (read):
- Maintain read models optimized for specific queries
- Subscribe to events for projection updates
- Materialized views for fast access
```

## 30.5 Sharding Patterns

Horizontal partitioning across multiple databases.

### Consistent Hash Ring with Virtual Nodes

```
Virtual node mapping:
Physical Node A → VNode_1, VNode_5, VNode_12, VNode_23
Physical Node B → VNode_3, VNode_8, VNode_15, VNode_19
Physical Node C → VNode_2, VNode_11, VNode_17, VNode_24

Shard calculation:
vnode = hash(key) % NUM_VNODES   (fixed for the life of the cluster)
owner = vnode_owner[vnode]
```

**Rebalancing**: A new node takes over whole vnodes from existing nodes, and only the keys in those vnodes move: about 1/(n+1) of the data when growing from n to n+1 nodes. The vnode count controls how evenly load spreads, not how much data moves.

### Skip Hash for Hot Data

```
Hot data (top 1% of access):
- Replicated 3-5x across nodes
- Stored in memory or fast SSDs

Warm data (next 19%):
- Partitioned across cluster
- Standard replication factor (3)

Cold data (bottom 80%):
- Archived to cheaper storage
- Reduced replication (2)
- Accessed rarely
```

## 30.6 Consistency Patterns in Practice

### Saga Pattern for Distributed Transactions

Choreography vs orchestration:
```
Choreography (event-driven):
OrderCreated → InventoryReserve → PaymentCapture → OrderConfirmed
            ↓              ↓              ↓
         (rollback)     (rollback)     (rollback)

Orchestration (centralized):
Saga Orchestrator:
  1. Send ReserveInventory
  2. Receive InventoryReserved
  3. Send CapturePayment
  4. Receive PaymentCaptured
  5. Send ConfirmOrder
  (On failure, send compensating transactions)
```

### Two-Phase Commit (2PC)

Distributed transaction protocol:
```
Phase 1 - Prepare:
1. Coordinator asks all participants to prepare
2. Participants vote Yes/No (locks resources)
3. If all Yes, proceed to commit; otherwise abort

Phase 2 - Commit:
1. Coordinator sends commit to all participants
2. Participants apply changes, release locks
3. Coordinator confirms completion
```

**Problems**: Blocking, coordinator failure, latency.

## 30.7 Observability Data Structures

### Distributed Tracing

Span graph for request flow:
```python
class Span:
    def __init__(self, name, trace_id, span_id, parent_id=None):
        self.name = name
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent_id = parent_id
        self.start_time = time.time()
        self.end_time = None
        self.tags = {}
        self.annotations = []

    def finish(self):
        self.end_time = time.time()

    def duration_ms(self):
        return (self.end_time - self.start_time) * 1000
```

**Trace assembly**: Child spans attached to parents via span_id/parent_id. Hierarchical tree represents causal relationship.

### Metric Aggregation

Time-series aggregation with downsampling:
```
Raw metrics (every 10s):
[23, 25, 22, 28, 24, ...]

1-minute rollup:
avg: 24.4, max: 28, min: 22, p50: 24, p95: 27, p99: 28

1-hour rollup:
avg: 24.1, max: 45 (spike during incident), p99: 38
```

**Cardinality management**: High-cardinality labels (user IDs, request IDs) must be aggregated before storage.

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**30.1 ★ Answer a Boolean query.** Add a third document, Doc3: "efficient data pipelines", to the collection in §30.1. Write the posting lists for "data", "structures", "efficient" and "pipelines" (document IDs 1, 2, 3). Then write a function that intersects two sorted posting lists, and use it to answer "data AND efficient" and "structures AND pipelines". What does the intersection cost?

<details>
<summary>Solution</summary>

Posting lists: data → [1, 2, 3], structures → [1, 2], efficient → [2, 3], pipelines → [3].

Because both lists are sorted, two pointers can walk them together, always advancing the one pointing at the smaller ID:

```python
def intersect(a, b):
    """Intersect two sorted posting lists in O(len(a) + len(b))."""
    i = j = 0
    out = []
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            out.append(a[i])
            i += 1
            j += 1
        elif a[i] < b[j]:
            i += 1
        else:
            j += 1
    return out


index = {
    "data": [1, 2, 3],
    "structures": [1, 2],
    "efficient": [2, 3],
    "pipelines": [3],
}
assert intersect(index["data"], index["efficient"]) == [2, 3]
assert intersect(index["structures"], index["pipelines"]) == []
```

"data AND efficient" returns [2, 3]; "structures AND pipelines" returns []. The cost is O(|a| + |b|) comparisons. When one list is far shorter than the other (a rare term AND a common one), searching the long list for each element of the short one, by binary search or galloping, costs O(|short| × log |long|) instead, which is why engines intersect the rarest term first and store skip pointers in long posting lists.

</details>

**30.2 ★★ Compute a BM25 score.** A collection has N = 1,000 documents with average length avgdl = 200 terms. The query term "trie" appears in n = 10 documents. Document D has |D| = 100 terms and contains "trie" tf = 3 times. With k1 = 1.2 and b = 0.75, compute the IDF, the term-frequency factor, and the score, using the natural log. Then answer: (a) what is the largest score this term can contribute however large tf gets, for a document of this length? (b) What happens to the score if D were 400 terms long? (c) What IDF does a term found in 600 of the 1,000 documents get, and why is that a problem?

<details>
<summary>Hint</summary>

Compute the length normalization 1 − b + b × |D|/avgdl first; it multiplies k1 in the denominator.

</details>

<details>
<summary>Solution</summary>

IDF = ln((1000 − 10 + 0.5) / (10 + 0.5)) = ln(990.5 / 10.5) = ln(94.33) ≈ 4.547.

Length normalization: 1 − 0.75 + 0.75 × 100/200 = 0.625, so k1 × 0.625 = 0.75.

Term-frequency factor: 3 × (1.2 + 1) / (3 + 0.75) = 6.6 / 3.75 = 1.76.

Score ≈ 4.547 × 1.76 ≈ 8.00.

(a) As tf → ∞ the factor tf × (k1 + 1) / (tf + constant) approaches k1 + 1 = 2.2, so the score saturates at 4.547 × 2.2 ≈ 10.0. Going from tf = 3 to tf = 100 only raises the factor from 1.76 to about 2.18. This saturation is the point of k1: the hundredth occurrence of a word says much less than the first.

(b) With |D| = 400 the normalization is 1 − 0.75 + 0.75 × 2 = 1.75, so the factor is 6.6 / (3 + 2.1) ≈ 1.29 and the score drops to about 5.88. Three occurrences in a long document are weaker evidence than three in a short one.

(c) ln((1000 − 600 + 0.5) / (600 + 0.5)) = ln(400.5 / 600.5) ≈ −0.405. Any term in more than half the documents gets a negative IDF, so matching it lowers a document's score. Lucene and most modern engines use ln(1 + (N − n + 0.5)/(n + 0.5)) instead, which stays positive.

</details>

**30.3 ★★ How tall is an HNSW graph?** The `insert` method in §30.2 picks level = ⌊−ln(u) × mL⌋ with u uniform on (0, 1] and mL = 1/ln(m). (a) Show that P(level ≥ l) = m^(−l). (b) For m = 16 and one million vectors, how many vectors do you expect on layer 1 and above, layer 2 and above, and so on? How many layers does the graph have? (c) Why is a level distribution that decays this fast what makes search fast?

<details>
<summary>Solution</summary>

(a) level ≥ l exactly when −ln(u) × mL ≥ l, that is −ln(u) ≥ l × ln(m), that is u ≤ e^(−l ln m) = m^(−l). Since u is uniform, that event has probability m^(−l).

(b) Expected count on layer l and above = 10⁶ × 16^(−l):

| layer l | expected nodes at level ≥ l |
|---|---|
| 0 | 1,000,000 |
| 1 | 62,500 |
| 2 | 3,906 |
| 3 | 244 |
| 4 | 15 |
| 5 | about 1 |

So the graph has about five or six layers, roughly log base 16 of a million, which is 5.

(c) Each layer has about 1/m as many nodes as the one below, like the levels of a skip list with promotion probability 1/m. A greedy search on a sparse upper layer covers large distances in a few hops and lands near the target; each lower layer refines the position. With a constant number of hops per layer and log_m(N) layers, the expected search cost grows logarithmically. If the distribution decayed slowly, upper layers would be nearly as large as layer 0 and would no longer give long-range shortcuts; that is exactly the bug in a version that computed the level as `-log(random()) % max_layers`, which puts about 37% of nodes above layer 0 instead of 1/16.

</details>

**30.4 ★★ Snapshots for an event store.** Rebuilding an aggregate from the `EventStore` in §30.4 replays its entire stream. Add a `take_snapshot(aggregate_id)` method that stores (version, state), and change `rebuild_state` to start from the snapshot and replay only later events. Test it on a bank account with events deposited 100, withdrew 30, (snapshot), deposited 50. What property must `apply_event` have for the snapshot to stay valid?

<details>
<summary>Hint</summary>

Consider what happens to the stored snapshot if `apply_event` updates the dictionary it is given in place.

</details>

<details>
<summary>Solution</summary>

```python
def apply_event(state, event):
    # Pure: returns a new dict and never mutates its input
    kind, amount = event
    balance = state.get("balance", 0)
    if kind == "deposited":
        return {**state, "balance": balance + amount}
    if kind == "withdrew":
        return {**state, "balance": balance - amount}
    return state


class EventStore:
    def __init__(self):
        self.streams = {}    # aggregate_id -> [event]
        self.snapshots = {}  # aggregate_id -> (version, state)

    def append(self, aggregate_id, event):
        self.streams.setdefault(aggregate_id, []).append(event)

    def get_stream(self, aggregate_id, from_version=0):
        return self.streams.get(aggregate_id, [])[from_version:]

    def take_snapshot(self, aggregate_id):
        version = len(self.streams.get(aggregate_id, []))
        self.snapshots[aggregate_id] = (version, self.rebuild_state(aggregate_id))

    def rebuild_state(self, aggregate_id):
        version, state = self.snapshots.get(aggregate_id, (0, {}))
        for event in self.get_stream(aggregate_id, from_version=version):
            state = apply_event(state, event)
        return state


store = EventStore()
store.append("acct-1", ("deposited", 100))
store.append("acct-1", ("withdrew", 30))
store.take_snapshot("acct-1")
assert store.snapshots["acct-1"] == (2, {"balance": 70})
store.append("acct-1", ("deposited", 50))
assert store.rebuild_state("acct-1") == {"balance": 120}
assert store.rebuild_state("acct-1") == {"balance": 120}  # snapshot untouched
assert store.snapshots["acct-1"] == (2, {"balance": 70})
```

Rebuilding now costs O(events since the snapshot) instead of O(all events). The version stored with the snapshot is the number of events it covers, so `get_stream(..., from_version=version)` returns exactly the events not yet folded in.

`apply_event` must be pure: it must return a new state and never mutate its argument. `rebuild_state` starts from the very dictionary stored in `self.snapshots`; if `apply_event` did `state["balance"] += amount` in place, the first rebuild would silently add the deposit of 50 into the stored snapshot, and every later rebuild would add it again, giving 170, 220, and so on. The assertion that the snapshot is still (2, {"balance": 70}) after two rebuilds catches exactly this. (A defensive alternative is to deep-copy the snapshot state before replaying.)

This is the same log-plus-checkpoint pattern as a Raft snapshot or a Delta Lake checkpoint: the log stays the source of truth, and the snapshot is a cache of a prefix of it.

</details>

**30.5 ★ How much data moves?** A cluster maps keys to 24 fixed vnodes as in §30.5, and three physical nodes own 8 vnodes each. (a) A fourth node joins and the vnodes are rebalanced evenly. What fraction of keys move? (b) Compare with `owner = hash(key) % num_physical` going from 3 to 4 nodes. (c) Suppose the vnode were instead computed as `hash(key) % (num_physical × 8)`, so the vnode count grows with the cluster. What fraction of keys end up in a different vnode when going from 3 to 4 nodes?

<details>
<summary>Solution</summary>

(a) Each node should own 24/4 = 6 vnodes, so the new node takes 2 from each existing node: 6 vnodes, 6/24 = 25% of the keys, all moving to the new node. That is the minimum possible: the new node must end up with its fair share of 1/4.

(b) A key keeps its owner only if h mod 3 = h mod 4, which holds when h mod 12 is 0, 1 or 2: 3 values in 12, so 75% of keys move, most of them between old nodes.

(c) A key stays in the same vnode only if h mod 24 = h mod 32. Over one period of lcm(24, 32) = 96 this holds only for h in 0 to 23, so again 75% of keys move. The vnode layer only helps if the number of vnodes is fixed; changing the modulus brings back mod-N's behavior.

</details>

**30.6 ★★★ Where two-phase commit blocks.** In the 2PC protocol of §30.6, participants P1, P2 and P3 all vote Yes, and the coordinator crashes before any of them receives the decision. (a) Can P1 commit on its own? Abort on its own? (b) P1 contacts P2 and P3. In which situations can they resolve the transaction without the coordinator, and when are they stuck? (c) Why must the coordinator write its decision to its own durable log before sending it? (d) How does a saga avoid this blocking, and what does it give up?

<details>
<summary>Hint</summary>

After voting Yes, a participant has promised it can commit, but it does not know whether everyone else promised too.

</details>

<details>
<summary>Solution</summary>

(a) Neither. P1 cannot commit, because some other participant might have voted No, in which case the coordinator decided abort. P1 cannot abort, because the coordinator might have decided commit and already told someone, or recorded it; aborting would then break atomicity. Having voted Yes, P1 must hold its locks and wait. That is the blocking problem.

(b) If any reachable participant received the decision, everyone adopts it. If any participant has not yet voted, it can unilaterally abort (no Yes vote means no promise), so everyone aborts. If any participant voted No, the outcome must be abort. But in this scenario all three voted Yes and none received the decision, so the outcome depends only on what the crashed coordinator decided, possibly commit. They are stuck holding locks until the coordinator recovers. Participants that are themselves unreachable make it worse: a silent one might be the one that received the decision.

(c) On recovery the coordinator must give the same answer it may already have sent to some participants. If it decided commit, told P1, then crashed and recovered with no record, it might abort when asked again by P2, leaving P1 committed and P2 aborted. Logging the decision durably before sending it is what makes the decision recoverable. (Protocols that replicate the coordinator's decision with consensus, such as Paxos Commit, remove the single point of blocking.)

(d) A saga commits each local step immediately and never holds locks across services. If a later step fails, it runs compensating actions (release the inventory, refund the payment) for the steps already done. Nothing blocks, but there is no isolation: other transactions can observe the intermediate state (stock reserved for an order that will be cancelled), and every step needs a compensation that is correct to run after arbitrary interleavings.

</details>

**30.7 ★★ Rollups that lie.** §30.7 rolls 10-second samples up into 1-minute and 1-hour summaries. Minute 1 sees 100 requests: 98 at 10 ms and 2 at 300 ms. Minute 2 sees 100 requests, all at 10 ms. Using the nearest-rank percentile (the ⌈0.99 × n⌉-th smallest value), compute each minute's p99, the true p99 of the two minutes combined, and the two "rollups" someone might compute from the per-minute p99s: their average and their maximum. Which summary statistics can be rolled up exactly from per-minute values, and what should you store to roll up percentiles?

<details>
<summary>Solution</summary>

Minute 1: the 99th smallest of 100 values. The 98 values at 10 ms come first, so the 99th is 300 ms. Minute 2: 10 ms.

Combined: 200 values, 198 at 10 ms and 2 at 300 ms. The ⌈0.99 × 200⌉ = 198th smallest is 10 ms.

Average of the per-minute p99s: (300 + 10)/2 = 155 ms. Maximum: 300 ms. Both are wrong: the true answer is 10 ms. With other data the average of p99s can just as easily be far too low.

Exact rollups: count, sum, min and max combine exactly (add, add, min, max), and the mean is sum/count, which needs both; averaging the per-minute averages is only correct when every minute has the same count. Percentiles do not combine from percentiles at all. To roll them up, store a mergeable summary per interval: a histogram with fixed bucket boundaries (merge by adding bucket counts, the Prometheus approach) or a mergeable sketch such as a t-digest or DDSketch. The percentile is then computed from the merged summary, with error set by the bucket or sketch resolution rather than by the rollup.

</details>

---

## Where this connects

- [Chapter 29: System Design as Data Structure Composition](ch29-system-design-as-data-structure-composition.md). The component structures these patterns compose
- [Chapter 19: Emerging and Specialized Structures](../volume-3/ch19-emerging-and-specialized-structures.md). The vector-search structures behind modern recommendation
