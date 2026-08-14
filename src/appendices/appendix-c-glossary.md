# Appendix C: Glossary

## Complexity and Analysis

**ADT (Abstract Data Type)**: A data type defined by its operations, not implementation. A stack is an ADT; an array-backed stack is an implementation.

**Amortized**: Average cost over a sequence of operations, where occasional expensive operations are paid for by many cheap ones. A dynamic array append is O(1) amortized because the O(n) resize happens rarely enough to average out. Distinct from *average case*, which is about input distribution rather than operation sequences.

**Asymptotic**: Describing behavior as input size grows without bound. Says nothing about small inputs, which is why an O(n log n) algorithm can lose to an O(n²) one at n = 50.

**Big-O**: An upper bound on growth. Θ is a tight bound and Ω a lower bound; most practical writing uses O loosely to mean Θ.

**Expected**: Average over the structure's own random choices, not over inputs. A skip list is O(log n) expected regardless of input, because the randomness is internal.

**Inverse Ackermann α(n)**: A function growing so slowly it is below 5 for any n that could physically exist. The bound on union-find with path compression.

**Time / Space Complexity**: How running time or memory grows with input size.

**Worst case**: The maximum over all inputs, including adversarial ones. The bound that matters when input is untrusted.

## Structural Terms

**Balanced Tree**: A tree whose subtree heights differ by at most a constant factor, guaranteeing O(log n) height.

**Cursor**: A position indicator within a data structure.

**Degenerate Tree**: A tree that has degraded to essentially a linked list — the worst case for an unbalanced BST.

**Fan-out**: The number of children a node can have. High fan-out is what makes B-trees shallow.

**Heap Property**: Every parent compares greater (max-heap) or less (min-heap) than its children. Note this is a *weaker* invariant than sorted order.

**Invariant**: A property that must hold before and after every operation. Writing invariants as runnable assertions is the most effective way to catch structural bugs near their cause.

**Leaf**: A node with no children.

**Sentinel**: A dummy node that removes special cases — an empty-list check, a null-pointer test — by guaranteeing a node always exists.

**Tombstone**: A marker left in place of a deleted entry so that probe sequences in an open-addressed hash table are not broken.

## Hashing

**Collision**: When two distinct keys hash to the same index. Unavoidable whenever the key space exceeds the table size.

**Load Factor (α)**: Ratio of stored elements to capacity. Open addressing degrades sharply above ~0.7; chaining tolerates α > 1.

**Open Addressing**: Resolving collisions by probing for another slot within the table itself, rather than chaining externally.

**Perfect Hashing**: A collision-free hash for a known, fixed key set. *Minimal* perfect hashing maps n keys onto exactly n slots.

**Universal Hashing**: Choosing a hash function at random from a family, so that no fixed input is reliably bad. The defense against collision-flooding attacks.

## Memory and Storage

**Cache Line**: The unit of transfer between memory and cache, typically 64 bytes. Reading one byte costs the same as reading its whole line.

**Cache-Oblivious**: Achieving optimal I/O performance without knowing the block size — by being well-organized at every scale simultaneously.

**External Memory Model**: A cost model counting block transfers rather than operations. Predicts real disk performance where the RAM model does not.

**Locality**: The tendency of an access pattern to touch nearby addresses. Sequential access has good locality; pointer chasing has none.

**LSM Tree (Log-Structured Merge)**: A write-optimized structure that buffers writes in memory and flushes them as sorted immutable runs, converting random writes to sequential ones.

**Page**: The unit of transfer between memory and disk, typically 4KB.

**Write Amplification**: The ratio of bytes actually written to storage versus bytes logically written by the application.

## Persistence and Concurrency

**ABA Problem**: A compare-and-swap succeeds because a pointer's value is unchanged, even though the state it refers to has changed and changed back. Defended against with tagged pointers or hazard pointers.

**CAS (Compare-and-Swap)**: An atomic hardware instruction that sets a memory location to a new value only if it currently holds an expected one. The universal primitive for lock-free programming.

**Copy-on-Write**: Sharing data until a write occurs, at which point the written portion is duplicated.

**Linearizability**: Every operation appears to take effect instantaneously at some moment between its call and return, consistent with real time. The standard correctness condition for concurrent objects, and notable for composing.

**Lock-Free**: Guaranteeing that *some* thread always makes progress. Weaker than **wait-free**, which guarantees *every* thread finishes in bounded steps.

**MVCC (Multi-Version Concurrency Control)**: Keeping multiple versions of each row so readers see a consistent snapshot without blocking writers. Partial persistence, applied to databases.

**Persistent**: Preserving previous versions after modification. *Partial* persistence allows querying old versions; *full* allows updating them; *confluent* allows merging them. Unrelated to durable storage.

**Path Copying**: Achieving persistence by duplicating only the nodes on the path from root to the modification point — O(log n) per update in a balanced tree.

**Structural Sharing**: Reusing unchanged subtrees between versions of an immutable structure. What makes persistence affordable.

## Distributed Systems

**CAP Theorem**: During a network partition, a distributed system must sacrifice either consistency or availability. See [Appendix D](appendix-d-network-and-system-design-quick-reference.md) for why "CA" is not a third option.

**Consistent Hashing**: Mapping keys and nodes onto a ring so that adding or removing a node remaps only ~1/n of keys, rather than nearly all of them.

**CRDT (Conflict-Free Replicated Data Type)**: A structure whose merge is commutative, associative, and idempotent, so replicas converge without coordination.

**DHT (Distributed Hash Table)**: A hash table partitioned across many machines, with a routing protocol for locating the responsible node.

**Eventual Consistency**: A guarantee that replicas converge given no further updates, with no bound on when.

**Merkle Tree**: A tree of hashes where each node hashes its children, allowing two large datasets to be compared — and their differences located — in logarithmic work.

**Quorum**: A subset of replicas that must acknowledge an operation. Overlapping read and write quorums (R + W > N) give strong consistency.

**Vector Clock**: A per-replica counter vector that distinguishes causally-ordered updates from genuinely concurrent ones.

## Probabilistic and Compressed

**Bloom Filter**: A bit array with k hash functions giving approximate membership: false positives are possible, false negatives are not.

**Count-Min Sketch**: A fixed-size frequency estimator over a stream, which overestimates but never underestimates.

**HyperLogLog**: A cardinality estimator using the maximum leading-zero count of hashes, giving ~2% error in about 12KB regardless of set size.

**Rank / Select**: The two primitives underlying succinct structures. `rank(i)` counts 1-bits before position i; `select(k)` finds the position of the k-th 1-bit.

**Succinct**: Using space within a lower-order term of the information-theoretic minimum, while still supporting queries *without decompressing*.

## Spatial and String

**LCP Array**: Longest Common Prefix between each pair of adjacent suffixes in a suffix array. Together they encode a suffix tree implicitly.

**MBR (Minimum Bounding Rectangle)**: The smallest axis-aligned rectangle enclosing a set of objects. The key type in an R-tree, and overlap between sibling MBRs is what degrades R-tree queries.

**Space-Filling Curve**: A mapping from multi-dimensional coordinates to one dimension that mostly preserves locality — Z-order and Hilbert being the common ones. The basis of geohashing.

**Suffix Array**: The sorted list of a string's suffix starting positions. Suffix-tree power at about 4 bytes per character rather than 20.

**Trie**: A tree keyed by character position, where lookup costs O(key length) independent of how many keys are stored.
