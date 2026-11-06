# Chapter 19: Emerging and Specialized Structures

This chapter surveys directions the field is currently moving in. Some of these are mature enough to deploy today; others are research with an unclear path to production. Each entry says which. Where a topic gets a full treatment later in the book, this chapter gives the short version and points you there.

## 19.1 Fibonacci Heaps Revisited

Recent work has produced simpler implementations while maintaining theoretical bounds.

The Fibonacci heap from [Chapter 9](../volume-1/ch09-heaps-and-priority-queues.md) is the standard example of a structure that wins on paper and loses in practice. Its O(1) amortized `decrease-key` improves Dijkstra's algorithm from O(E log V) to O(E + V log V), which is asymptotically optimal for comparison-based implementations. Yet almost nobody uses one. The constant factors are large, the node structure is heavy (parent pointers, child lists, mark bits), and the cascading-cut logic is cache-hostile. A plain binary heap usually wins on real graphs, and a d-ary heap tuned to the cache line usually wins by more.

The response has been a search for structures with the same bounds and less machinery:

- **Pairing heaps** (Fredman et al., 1986) are dramatically simpler (a single multiway tree with a `merge` operation) and fast in practice. Their exact amortized `decrease-key` complexity was an open problem for two decades; it is now known to be O(log log n), not O(1), yet they still beat Fibonacci heaps on essentially every real workload.
- **Rank-pairing heaps** (Haeupler, Sen, Tarjan, 2011) achieve the full Fibonacci bounds with substantially simpler restructuring.
- **Strict Fibonacci heaps** (Brodal, Lagogiannis, Tarjan, 2012) attain the same bounds in the *worst case* rather than amortized: theoretically significant for real-time systems, still not competitive in practice.

The durable lesson is the one from [Chapter 1](../volume-1/ch01-the-philosophy-and-mathematics-of-data-structures.md): asymptotic superiority is a claim about behavior in a limit, and the limit may sit far beyond any input you will ever see.

**Status: mature theory, rarely deployed.** Use a binary or d-ary heap unless profiling proves `decrease-key` dominates.

## 19.2 Succinct Data Structures

Store data in space close to the information-theoretic minimum:
- Operations directly on compressed representation
- Rank, select, navigation

A succinct structure uses Z + o(Z) bits, where Z is the information-theoretic minimum, while still supporting fast queries: crucially, **without decompressing**. That last property is what separates succinct structures from ordinary compression: gzip achieves better ratios but you must decompress before you can query.

The canonical example: a binary tree of n nodes takes 2n + o(n) bits succinctly, against roughly 128n bits for a pointer-based representation with two 64-bit pointers per node. That is a 64× reduction, and it turns "this index does not fit in RAM" into "this index fits in RAM", which is a far bigger performance win than any constant-factor speedup.

Everything is built on two primitives over a bit vector:

- `rank(i)`: how many 1s occur before position i
- `select(k)`: the position of the k-th 1

Both answer in O(1) using auxiliary structures occupying o(n) extra bits. Tree navigation, string search, and set membership all reduce to these two operations.

[Chapter 24](../volume-4/ch24-research-grade-data-structures.md) covers the machinery properly: LOUDS, balanced parentheses, DFUDS, wavelet matrices, and the FM-index.

**Status: deployed where memory is the binding constraint.** Genomic aligners (BWA, Bowtie) index the human genome with FM-indexes. Succinct tries back autocomplete at scale. The Rust `succinct` and C++ `sdsl-lite` libraries are production-quality.

## 19.3 External Memory Hash Tables

For massive datasets that don't fit in memory:
- Cuckoo hashing on disk
- Buffered repository trees

A hash table's defining virtue is that a lookup is one random probe. On disk, one random probe is a ~10ms seek, and the virtue becomes the defect, which is why disk-resident indexes are overwhelmingly B-trees rather than hash tables, as [Chapter 16](ch16-external-memory-and-cache-oblivious-structures.md) explains.

The techniques that make hashing viable in external memory all amount to trading probes for batching:

- **Linear hashing** and **extendible hashing** grow one bucket at a time rather than rehashing everything, so a resize never stalls. Both date to 1979–80 and both are still in use: linear hashing indexes Berkeley DB and, more recently, PostgreSQL hash indexes.
- **Cuckoo hashing on disk** bounds lookups to a constant number of probes (two, in the basic scheme), which matters far more when a probe is 10ms than when it is 100ns. The cost is expensive insertions when eviction chains grow long.
- **Buffered repository trees** and **B^ε-trees** buffer updates in internal nodes and flush them down in batches, converting many random writes into few sequential ones. This is the same insight as the LSM tree, arrived at from the theory side. TokuDB and its successor, Percona's fractal tree indexes, shipped it commercially.

**Status: mature.** The interesting modern development is that NVMe changes the calculus. A random read on NVMe is ~10μs rather than ~10ms, which narrows the gap between hash and tree indexes considerably and is quietly reopening design questions that were settled in the disk era.

## 19.4 Learned Indexes

Machine learning for index structures:
- Replace B-trees with neural networks
- Can be faster for certain access patterns
- Active research area

The idea, from Kraska et al.'s 2018 paper "The Case for Learned Index Structures," is a genuine reframing: **an index is a function from key to position, and a model can approximate a function.** If your keys are integers 1 to 100,000,000 stored in order, the "index" is `position = key − 1`, no tree needed. Real data is not that clean, but real data is rarely random either, and a model that captures the shape of the key distribution can beat a structure that assumes nothing about it.

A learned index predicts a position, then does a bounded local search to correct the prediction. The **Recursive Model Index** stages simple models (usually linear regressions, not neural networks, because inference must cost nanoseconds) with each stage narrowing the range.

Reported results are strong: up to 3× faster lookups at a fraction of the memory of a B-tree. The caveats are equally real, and they are what keeps this out of most production systems:

- **Updates are the hard part.** The original design was read-only. ALEX (2020) and PGM-index (2020) support updates, but a distribution shift may require retraining.
- **Worst-case bounds vanish.** A B-tree is O(log n) on adversarial input. A learned index is fast on data resembling its training distribution and can degrade badly otherwise.
- **Sorted data is the precondition.** The technique assumes a sorted array underneath; it accelerates the search, it does not replace the storage.

**Status: active research, early production.** The PGM-index has strong theoretical guarantees and a usable implementation. Learned *bloom filters* and learned cache-eviction policies are seeing more real adoption than learned indexes proper.

## 19.5 Delta Encoding and CRDTs

Conflict-free replicated data types for distributed systems:
- Eventual consistency
- No coordination needed
- Used in collaborative applications

A CRDT is a structure whose merge operation is **commutative, associative, and idempotent**. Those three algebraic properties are the entire trick: if merging is order-independent and repeat-safe, replicas that receive the same updates in any order, possibly more than once, provably converge to the same state. With no coordination, no consensus, and no leader.

That means a CRDT keeps working while partitioned. In CAP terms it chooses AP and gets convergence anyway, by restricting itself to operations that cannot conflict.

The building blocks, in increasing order of difficulty:

| CRDT | Merge rule | Use |
|------|-----------|-----|
| G-Counter | Per-replica counts, take max, sum | Metrics |
| PN-Counter | Two G-Counters (increments, decrements) | Counters that decrease |
| G-Set | Union | Append-only sets |
| LWW-Register | Highest timestamp wins | Last-writer-wins fields |
| OR-Set | Unique tags per add; remove tags observed | Sets with removal |
| RGA / Logoot / Yjs | Ordered identifiers between elements | Collaborative text |

**Delta CRDTs** address the practical problem with the basic formulation: naive state-based CRDTs ship the entire state on every sync, which is untenable for a large document. Delta CRDTs transmit only the changed portion while preserving the convergence properties.

Collaborative text editing is the demanding case, since concurrent inserts at the same position must produce a consistent order without a coordinator. Yjs and Automerge are the mature implementations, and both are fast enough for real editors: Yjs handles documents with millions of operations.

[Chapter 27](../volume-5/ch27-distributed-data-structures.md) develops the theory and the distributed-systems context.

**Status: production-ready and spreading fast.** Figma, Linear, Apple Notes, and Redis's conflict-free replicated types all ship CRDTs. This is the most immediately practical topic in this chapter.

## 19.6 Structures for Vector Search

One significant omission from the original survey, added because it went from research to ubiquitous in roughly three years.

Embedding models turn text, images, and audio into high-dimensional vectors (typically 384 to 1,536 dimensions) and searching them means approximate nearest neighbor over millions of points. [Chapter 15](ch15-spatial-and-geometric-data-structures.md) explained why KD-trees collapse at these dimensionalities. The structures that work instead:

- **HNSW** (Hierarchical Navigable Small World, Malkov and Yashunin, 2016) builds a layered proximity graph and greedily descends it. A skip list where the "links" are nearest neighbors. It is the default in most vector databases: excellent recall, fast queries, high memory use, awkward deletion.
- **IVF** (inverted file index) clusters vectors and searches only the nearest clusters. Lower memory, tunable recall.
- **Product quantization** compresses vectors into compact codes, letting billion-scale indexes fit in RAM at some accuracy cost. Usually combined with IVF.
- **ScaNN** (Google, 2020) uses anisotropic quantization tuned for inner-product search specifically.

**Status: production, moving very fast.** FAISS, hnswlib, pgvector, Pinecone, Weaviate, Qdrant, and Milvus all ship these. Every retrieval-augmented LLM application depends on one.

## 19.7 Reading the Frontier

A few honest heuristics for evaluating structures like these, since most novel structures do not survive contact with production:

**What tends to succeed** solves a problem created by a hardware or workload shift. LSM trees won because write amplification on flash mattered. HNSW won because embeddings created a genuinely new query type. CRDTs won because collaborative editing became a product requirement.

**What tends to fail** improves an asymptotic bound while worsening constants, requires the workload to be well-behaved, or optimizes something that was not the bottleneck. Fibonacci heaps are the enduring cautionary example.

**Questions worth asking of any new structure:** What is the constant factor, measured? How does it behave on adversarial input? Does it support updates, or only bulk builds? What happens at the cache and page level? Is there a tested implementation, or only a paper?

That last question filters out most of them.

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**19.1 ★ Rank and select by hand.** Take the bit vector below, with positions numbered from 0, `rank(i)` counting the 1s strictly before position i, and `select(k)` giving the position of the k-th 1 (counting k from 1).

```
position: 0 1 2 3 4 5 6 7 8 9
bit:      1 0 1 1 0 0 1 0 1 1
```

1. Compute `rank(4)`, `rank(7)`, and `rank(10)`.
2. Compute `select(1)`, `select(4)`, and `select(6)`.
3. Check that `rank(select(k)) = k − 1` for those three values of k, and say why it holds in general.
4. 19.2 compares 2n bits against 128n bits for a binary tree. Put numbers on that for a tree of 100 million nodes.

<details>
<summary>Solution</summary>

1. `rank(4)` counts positions 0 to 3: bits 1, 0, 1, 1, so **3**. `rank(7)` adds positions 4 to 6 (0, 0, 1): **4**. `rank(10)` counts the whole vector: **6**.
2. The 1s sit at positions 0, 2, 3, 6, 8, 9. So `select(1) = 0`, `select(4) = 6`, `select(6) = 9`.
3. `rank(0) = 0`, `rank(6) = 3`, `rank(9) = 5`, which are k − 1 for k = 1, 4, 6. In general, `select(k)` is the position of the k-th 1, and exactly k − 1 ones come strictly before it.
4. Pointers: 128 × 10⁸ bits = 1.6 × 10⁹ bytes = **1.6 GB**. Succinct: 2 × 10⁸ bits = **25 MB**, plus the o(n) rank/select directories (typically a few percent to a quarter of that). That is the 64× reduction from 19.2: the succinct tree fits in RAM on a laptop, while the pointer version needs a machine sized for it.

</details>

**19.2 ★★ When does the Fibonacci heap's bound pay?** Estimate Dijkstra's operation counts with a binary heap, O((V + E) log V), and a Fibonacci heap, O(E + V log V), for (a) a road network with V = 10⁶ and E = 4 × 10⁶, and (b) a dense graph with V = 10⁴ and E = 5 × 10⁷. Treat each bound as an exact operation count with log₂. By what factor would a Fibonacci heap operation have to be slower than a binary heap operation for the binary heap to win in each case? What does the estimate leave out?

<details>
<summary>Solution</summary>

log₂ 10⁶ ≈ 19.9 and log₂ 10⁴ ≈ 13.3.

| Graph | Binary heap (V + E) log V | Fibonacci heap E + V log V | Ratio |
|-------|---------------------------|----------------------------|-------|
| Road, V = 10⁶, E = 4 × 10⁶ | 5 × 10⁶ × 19.9 ≈ 1.0 × 10⁸ | 4 × 10⁶ + 2.0 × 10⁷ ≈ 2.4 × 10⁷ | ≈ 4.2 |
| Dense, V = 10⁴, E = 5 × 10⁷ | ≈ 6.6 × 10⁸ | 5 × 10⁷ + 1.3 × 10⁵ ≈ 5.0 × 10⁷ | ≈ 13 |

On the road network, the binary heap wins if a Fibonacci heap operation costs more than about **4×** as much. That is easily exceeded: the Fibonacci heap's heavy nodes, pointer-chased child lists, and cascading cuts miss cache where an array-backed binary heap does not. On the dense graph the theoretical advantage is about 13×, which is where Fibonacci heaps have a real case. But at that density the plain unsorted-array version from Chapter 21 costs V² = 10⁸ simple scans with no heap at all, which is competitive with both.

What the estimate leaves out: the binary heap bound charges a log V decrease-key to *every* edge, but in practice only a fraction of relaxations improve a distance, so the binary heap does much less work than (V + E) log V. That narrows the gap further, and it is the main reason the 19.1 advice is "use a binary or d-ary heap unless profiling proves decrease-key dominates".

</details>

**19.3 ★★ A learned index by hand.** A sorted array holds 12 keys at positions 0 to 11:

```
keys: 2 3 5 7 11 13 17 19 23 29 31 37
```

The model is the straight line through the first and last points: `pos(k) = 11 × (k − 2) / 35`, rounded to the nearest integer.

1. Compute the predicted position of every key and the maximum error ε.
2. Describe a lookup for 23 and for 24 (absent) using the prediction plus a bounded local search.
3. Now append the key 1000 at position 12 and refit the line through the endpoints. What happens to ε, and which caveat from 19.4 does this illustrate?

<details>
<summary>Hint</summary>

The local search only has to cover positions within ε of the prediction, so its cost is O(log ε), not O(log n).

</details>

<details>
<summary>Solution</summary>

1. Predictions (unrounded, then rounded) and errors:

| Key | 2 | 3 | 5 | 7 | 11 | 13 | 17 | 19 | 23 | 29 | 31 | 37 |
|-----|---|---|---|---|----|----|----|----|----|----|----|----|
| Exact | 0.00 | 0.31 | 0.94 | 1.57 | 2.83 | 3.46 | 4.71 | 5.34 | 6.60 | 8.49 | 9.11 | 11.00 |
| Rounded | 0 | 0 | 1 | 2 | 3 | 3 | 5 | 5 | 7 | 8 | 9 | 11 |
| True | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
| Error | 0 | 1 | 1 | 1 | 1 | 2 | 1 | 2 | 1 | 1 | 1 | 0 |

So **ε = 2**.

2. Lookup 23: predict 7, then binary search positions 5 to 9 (7 ± 2) and find 23 at position 8. Lookup 24: predict round(6.91) = 7, search positions 5 to 9, and conclude it is absent because 23 < 24 < 29 are adjacent. Each lookup is one multiply-add plus a binary search over 2ε + 1 = 5 slots, no matter how large the array is.

3. With 1000 appended, the line is `pos(k) = 12 × (k − 2) / 998`. Every original key now predicts less than 0.5, so all of them round to position 0, and key 37 (true position 11) is off by **11**: ε jumped from 2 to 11, and the "bounded" search now covers the whole original array. One outlier wrecked the model. That is the caveat "worst-case bounds vanish": a B-tree's cost does not depend on the key distribution, while a learned index is only as good as its fit. Practical designs such as the RMI and the PGM-index use many piecewise models, so an outlier only damages the segment it falls in.

</details>

**19.4 ★ G-Counter merge.** Three replicas keep a G-Counter as a map from replica name to count. Replica A has incremented 3 times, B 5 times, C twice, and none has synced yet. (a) Replica A merges B's state, then C's. What is A's state and value? (b) A message bug delivers B's state to A a second time. What changes? (c) Someone proposes merging by *adding* counts instead of taking the max. Show what goes wrong.

<details>
<summary>Solution</summary>

```python
def merge(a, b):
    return {r: max(a.get(r, 0), b.get(r, 0)) for r in a.keys() | b.keys()}

def value(c):
    return sum(c.values())

A, B, C = {'A': 3}, {'B': 5}, {'C': 2}
ab = merge(A, B)
abc = merge(ab, C)
assert abc == {'A': 3, 'B': 5, 'C': 2} and value(abc) == 10      # (a)
assert merge(abc, B) == abc                                      # (b) idempotent
assert merge(merge(A, B), C) == merge(A, merge(B, C)) == merge(C, merge(B, A))

def bad_merge(a, b):
    return {r: a.get(r, 0) + b.get(r, 0) for r in a.keys() | b.keys()}

assert value(bad_merge(ab, ab)) == 16                            # (c) double counted
```

(a) `{A: 3, B: 5, C: 2}`, value **10**.

(b) Nothing changes. `max(5, 5) = 5`: the merge is idempotent, so duplicate delivery is harmless.

(c) Merging a state with a copy of itself doubles it: `{A: 3, B: 5}` merged with itself gives `{A: 6, B: 10}`, value 16 instead of 8. Addition is commutative and associative but **not idempotent**, and real networks redeliver messages. The per-replica max works because each entry is written by only one replica and only grows, so the larger number is always the more recent one.

</details>

**19.5 ★★ Design: sizing a vector index.** You need nearest-neighbor search over 50 million 768-dimensional float32 embeddings on a machine with 64 GB of RAM, with recall around 95% at 10 nearest neighbors. Estimate the memory for HNSW and for IVF with product quantization (64-byte codes), and pick a design. HNSW with parameter M = 16 stores up to 2M = 32 neighbor ids (4 bytes each) per vector on its bottom layer, and the upper layers add only a small fraction more.

<details>
<summary>Solution</summary>

**Raw vectors:** 50 × 10⁶ × 768 × 4 bytes = **153.6 GB**. That alone is more than twice the RAM.

**HNSW:** it searches against the full vectors, so it needs the 153.6 GB plus the graph: about 32 × 4 = 128 bytes per vector on the bottom layer, 6.4 GB, so roughly **160 GB**. It does not fit. Halving precision to float16 gives about 83 GB, which still does not fit.

**IVF + PQ:** each vector is stored as a 64-byte code: 50 × 10⁶ × 64 = **3.2 GB**, plus ids (8 bytes each, 0.4 GB) and the cluster centroids (negligible). It fits with plenty of room.

The catch is recall. Compressing 3,072 bytes to 64 loses information, and PQ distances alone typically fall short of 95% recall. The standard fix is to **re-rank**: use IVF-PQ to fetch a few hundred candidates, then read those candidates' full vectors from SSD and compute exact distances. At NVMe latencies of about 10μs per read (19.3), a few hundred reads add a few milliseconds, or less with parallel I/O.

So: **IVF-PQ in RAM, full vectors on NVMe for re-ranking.** The alternative is a machine with 192 GB or more of RAM running HNSW, which gives faster queries and simpler tuning at a much higher hardware cost. This is the 19.6 tradeoff in concrete form: HNSW buys recall and speed with memory, quantization buys memory with accuracy.

</details>

**19.6 ★★★ Build an OR-Set.** First, show why the naive replicated set fails: each replica keeps a plain set, `remove` deletes locally, and merge is union. Then implement the OR-Set from the 19.5 table: each `add` creates a unique tag, `remove` tombstones the tags it has observed, and an element is present if it has at least one tag that is not tombstoned. Trace this scenario: replica A adds `x`; B syncs from A; B removes `x` while, concurrently, A adds `x` again; then both sync. Is `x` present?

<details>
<summary>Hint</summary>

A merge can only combine information, never subtract it, so a removal has to be recorded as something that is *added* to the state.

</details>

<details>
<summary>Solution</summary>

**Naive set.** Both replicas hold `{x}`. B removes x, giving `{}`. Merging is union: `{x} ∪ {} = {x}`. The remove is undone by the very next sync, even with no concurrent add. Union can only grow sets, so a delete represented as "absence" is indistinguishable from "never heard of it" and always loses.

**OR-Set.** Removal is recorded as a set of tombstoned tags, which only grows, so merge is union on both components and inherits union's commutativity, associativity, and idempotence.

```python
class ORSet:
    """State-based observed-remove set."""

    def __init__(self, replica):
        self.replica = replica
        self.counter = 0
        self.adds = set()          # (element, tag) pairs ever added
        self.removed = set()       # tags some remove has observed

    def add(self, x):
        self.counter += 1
        self.adds.add((x, (self.replica, self.counter)))   # globally unique tag

    def remove(self, x):
        self.removed |= {tag for (e, tag) in self.adds if e == x}

    def contains(self, x):
        return any(e == x and tag not in self.removed for (e, tag) in self.adds)

    def merge(self, other):
        self.adds |= other.adds
        self.removed |= other.removed

a, b = ORSet("A"), ORSet("B")
a.add("x")                 # tag (A, 1)
b.merge(a)                 # B observes (x, (A, 1))
b.remove("x")              # B tombstones (A, 1) only
a.add("x")                 # concurrently: tag (A, 2), which B never saw
a.merge(b)
b.merge(a)
assert a.contains("x") and b.contains("x")
assert a.adds == b.adds and a.removed == b.removed               # converged
```

Trace:

| Step | A.adds | B.adds | removed (after step) | x present? |
|------|--------|--------|----------------------|------------|
| A adds x | (x, A1) | | | A: yes |
| B syncs from A | (x, A1) | (x, A1) | | both: yes |
| B removes x | (x, A1) | (x, A1) | B: {A1} | B: no |
| A adds x again | (x, A1), (x, A2) | (x, A1) | B: {A1} | A: yes |
| Both sync | (x, A1), (x, A2) | same | both: {A1} | **both: yes** |

**x is present.** B's remove only killed the tag it had seen (A1). A's concurrent add created A2, which no remove observed. This is **add-wins** semantics: a remove deletes exactly the adds that happened before it, and never a concurrent one. That is usually what users expect ("I re-added it, why did it vanish?").

The cost is that tombstones accumulate forever in this simple version. Production implementations compact them using version vectors so that a tag can be dropped once every replica is known to have seen its removal.

</details>

---

## Where this connects

- [Chapter 24: Research-Grade Data Structures](../volume-4/ch24-research-grade-data-structures.md). The research-grade treatment of succinct structures
- [Chapter 15: Spatial and Geometric Data Structures](ch15-spatial-and-geometric-data-structures.md). The spatial structures vector search replaces
