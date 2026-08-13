# Chapter 19: Emerging and Specialized Structures

This chapter surveys directions the field is currently moving in. Some of these are mature enough to deploy today; others are research with an unclear path to production. Each entry says which. Where a topic gets a full treatment later in the book, this chapter gives the short version and points you there.

## 19.1 Fibonacci Heaps Revisited

Recent work has produced simpler implementations while maintaining theoretical bounds.

The Fibonacci heap from [Chapter 9](../volume-1/ch09-heaps-and-priority-queues.md) is the standard example of a structure that wins on paper and loses in practice. Its O(1) amortized `decrease-key` improves Dijkstra's algorithm from O(E log V) to O(E + V log V), which is asymptotically optimal for comparison-based implementations. Yet almost nobody uses one. The constant factors are large, the node structure is heavy (parent pointers, child lists, mark bits), and the cascading-cut logic is cache-hostile. A plain binary heap usually wins on real graphs, and a d-ary heap tuned to the cache line usually wins by more.

The response has been a search for structures with the same bounds and less machinery:

- **Pairing heaps** (Fredman et al., 1986) are dramatically simpler — a single multiway tree with a `merge` operation — and fast in practice. Their exact amortized `decrease-key` complexity was an open problem for two decades; it is now known to be O(log log n), not O(1), yet they still beat Fibonacci heaps on essentially every real workload.
- **Rank-pairing heaps** (Haeupler, Sen, Tarjan, 2011) achieve the full Fibonacci bounds with substantially simpler restructuring.
- **Strict Fibonacci heaps** (Brodal, Lagogiannis, Tarjan, 2012) attain the same bounds in the *worst case* rather than amortized — theoretically significant for real-time systems, still not competitive in practice.

The durable lesson is the one from [Chapter 1](../volume-1/ch01-the-philosophy-and-mathematics-of-data-structures.md): asymptotic superiority is a claim about behavior in a limit, and the limit may sit far beyond any input you will ever see.

**Status: mature theory, rarely deployed.** Use a binary or d-ary heap unless profiling proves `decrease-key` dominates.

## 19.2 Succinct Data Structures

Store data in space close to the information-theoretic minimum:
- Operations directly on compressed representation
- Rank, select, navigation

A succinct structure uses Z + o(Z) bits, where Z is the information-theoretic minimum, while still supporting fast queries — crucially, **without decompressing**. That last property is what separates succinct structures from ordinary compression: gzip achieves better ratios but you must decompress before you can query.

The canonical example: a binary tree of n nodes takes 2n + o(n) bits succinctly, against roughly 128n bits for a pointer-based representation with two 64-bit pointers per node. That is a 64× reduction, and it turns "this index does not fit in RAM" into "this index fits in RAM" — which is a far bigger performance win than any constant-factor speedup.

Everything is built on two primitives over a bit vector:

- `rank(i)` — how many 1s occur before position i
- `select(k)` — the position of the k-th 1

Both answer in O(1) using auxiliary structures occupying o(n) extra bits. Tree navigation, string search, and set membership all reduce to these two operations.

[Chapter 24](../volume-4/ch24-research-grade-data-structures.md) covers the machinery properly — LOUDS, balanced parentheses, DFUDS, wavelet matrices, and the FM-index.

**Status: deployed where memory is the binding constraint.** Genomic aligners (BWA, Bowtie) index the human genome with FM-indexes. Succinct tries back autocomplete at scale. The Rust `succinct` and C++ `sdsl-lite` libraries are production-quality.

## 19.3 External Memory Hash Tables

For massive datasets that don't fit in memory:
- Cuckoo hashing on disk
- Buffered repository trees

A hash table's defining virtue is that a lookup is one random probe. On disk, one random probe is a 100μs seek, and the virtue becomes the defect — which is why disk-resident indexes are overwhelmingly B-trees rather than hash tables, as [Chapter 16](ch16-external-memory-and-cache-oblivious-structures.md) explains.

The techniques that make hashing viable in external memory all amount to trading probes for batching:

- **Linear hashing** and **extendible hashing** grow one bucket at a time rather than rehashing everything, so a resize never stalls. Both date to 1979–80 and both are still in use — extendible hashing indexes Berkeley DB and, more recently, PostgreSQL hash indexes.
- **Cuckoo hashing on disk** bounds lookups to a constant number of probes (two, in the basic scheme), which matters far more when a probe is 100μs than when it is 100ns. The cost is expensive insertions when eviction chains grow long.
- **Buffered repository trees** and **B^ε-trees** buffer updates in internal nodes and flush them down in batches, converting many random writes into few sequential ones. This is the same insight as the LSM tree, arrived at from the theory side. TokuDB and its successor, Percona's fractal tree indexes, shipped it commercially.

**Status: mature.** The interesting modern development is that NVMe changes the calculus — a random read on NVMe is ~10μs rather than ~10ms, which narrows the gap between hash and tree indexes considerably and is quietly reopening design questions that were settled in the disk era.

## 19.4 Learned Indexes

Machine learning for index structures:
- Replace B-trees with neural networks
- Can be faster for certain access patterns
- Active research area

The idea, from Kraska et al.'s 2018 paper "The Case for Learned Index Structures," is a genuine reframing: **an index is a function from key to position, and a model can approximate a function.** If your keys are integers 1 to 100,000,000 stored in order, the "index" is `position = key − 1` — no tree needed. Real data is not that clean, but real data is rarely random either, and a model that captures the shape of the key distribution can beat a structure that assumes nothing about it.

A learned index predicts a position, then does a bounded local search to correct the prediction. The **Recursive Model Index** stages simple models — usually linear regressions, not neural networks, because inference must cost nanoseconds — with each stage narrowing the range.

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

A CRDT is a structure whose merge operation is **commutative, associative, and idempotent**. Those three algebraic properties are the entire trick: if merging is order-independent and repeat-safe, replicas that receive the same updates in any order, possibly more than once, provably converge to the same state — with no coordination, no consensus, and no leader.

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

Collaborative text editing is the demanding case, since concurrent inserts at the same position must produce a consistent order without a coordinator. Yjs and Automerge are the mature implementations, and both are fast enough for real editors — Yjs handles documents with millions of operations.

[Chapter 27](../volume-5/ch27-distributed-data-structures.md) develops the theory and the distributed-systems context.

**Status: production-ready and spreading fast.** Figma, Linear, Apple Notes, and Redis's conflict-free replicated types all ship CRDTs. This is the most immediately practical topic in this chapter.

## 19.6 Structures for Vector Search

One significant omission from the original survey, added because it went from research to ubiquitous in roughly three years.

Embedding models turn text, images, and audio into high-dimensional vectors — typically 384 to 1,536 dimensions — and searching them means approximate nearest neighbor over millions of points. [Chapter 15](ch15-spatial-and-geometric-data-structures.md) explained why KD-trees collapse at these dimensionalities. The structures that work instead:

- **HNSW** (Hierarchical Navigable Small World, Malkov and Yashunin, 2016) builds a layered proximity graph and greedily descends it — a skip list where the "links" are nearest neighbors. It is the default in most vector databases: excellent recall, fast queries, high memory use, awkward deletion.
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
