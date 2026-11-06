# Appendix C: Glossary

## Complexity and Analysis

**ADT (Abstract Data Type)**: A data type defined by its operations, not implementation. A stack is an ADT; an array-backed stack is an implementation.

**Amortized**: Average cost over a sequence of operations, where occasional expensive operations are paid for by many cheap ones. A dynamic array append is O(1) amortized because the O(n) resize happens rarely enough to average out. Distinct from *average case*, which is about input distribution rather than operation sequences.

**Asymptotic**: Describing behavior as input size grows without bound. Says nothing about small inputs, which is why an O(n log n) algorithm can lose to an O(n²) one at n = 50.

**Big-O**: An upper bound on growth. Θ is a tight bound and Ω a lower bound; most practical writing uses O loosely to mean Θ.

**Expected**: Average over the structure's own random choices, not over inputs. A skip list is O(log n) expected regardless of input, because the randomness is internal.

**Inverse Ackermann α(n)**: A function growing so slowly it is below 5 for any n that could physically exist. The bound on union-find with path compression.

**Time / Space Complexity**: How running time or memory grows with input size.

**Word RAM**: A cost model in which memory holds w-bit words and arithmetic and bitwise operations on a word cost O(1). It is the model in which integer structures such as van Emde Boas trees beat the O(log n) comparison bound.

**Worst case**: The maximum over all inputs, including adversarial ones. The bound that matters when input is untrusted.

## Structural Terms

**Augmented Tree**: A tree whose nodes store extra summary data about their subtrees (sizes, sums, maximums) that is kept correct through inserts, deletes and rotations. Order-statistic trees and interval trees are examples.

**Balanced Tree**: A tree whose subtree heights differ by at most a constant factor, guaranteeing O(log n) height.

**Bulk Loading**: Building a B-tree or B+ tree bottom-up from sorted data instead of by repeated insertion. Much faster, and it lets you choose how full each node is.

**Cursor**: A position indicator within a data structure.

**Decrease-Key**: The priority-queue operation that lowers an existing element's priority. A binary heap needs a position map (an indexed heap) to find the element first.

**Degenerate Tree**: A tree that has degraded to essentially a linked list, the worst case for an unbalanced BST.

**Fan-out**: The number of children a node can have. High fan-out is what makes B-trees shallow.

**Fill Factor**: How full a B-tree's nodes are allowed or chosen to be. Sorted inserts leave nodes about half full; bulk loading can pack them completely.

**Heap Property**: Every parent compares greater (max-heap) or less (min-heap) than its children. Note this is a *weaker* invariant than sorted order.

**Invariant**: A property that must hold before and after every operation. Writing invariants as runnable assertions is the most effective way to catch structural bugs near their cause.

**Leaf**: A node with no children.

**Minimum Degree (t)**: The B-tree parameter that bounds node size: every node except the root holds between t − 1 and 2t − 1 keys.

**Order Statistic**: The k-th smallest element of a set. A BST augmented with subtree sizes answers select (k-th smallest) and rank (position of a key) in O(height).

**Predecessor / Successor**: The largest key smaller than x, and the smallest key larger than x. The core query of ordered sets, and the problem van Emde Boas trees solve for integer keys.

**Rope**: A balanced tree whose leaves hold chunks of text, giving O(log n) insert, delete and indexing anywhere in a large string. Used by several text editors.

**Sentinel**: A dummy node that removes special cases (an empty-list check, a null-pointer test) by guaranteeing a node always exists.

**Serialization**: Writing a structure to a flat sequence (bytes, text) from which it can be rebuilt. A binary tree needs either null markers or two traversals to be rebuilt exactly.

**Tombstone**: A marker left in place of a deleted entry so that probe sequences in an open-addressed hash table are not broken.

**van Emde Boas Tree**: A recursive structure for integer keys below u that splits each key into high and low halves, answering predecessor and successor queries in O(log log u).

## Hashing

**Collision**: When two distinct keys hash to the same index. Unavoidable whenever the key space exceeds the table size.

**Control Byte**: In a Swiss table, one byte of metadata per slot recording empty, deleted, or full plus 7 bits of the key's hash. A lookup compares a whole group of control bytes at once before touching any keys.

**Hash Flooding**: A denial-of-service attack that sends many keys known to collide, turning a hash table's O(1) operations into O(n). Defended against with seeded, keyed hash functions such as SipHash.

**Load Factor (α)**: Ratio of stored elements to capacity. Open addressing degrades sharply above ~0.7; chaining tolerates α > 1.

**Open Addressing**: Resolving collisions by probing for another slot within the table itself, rather than chaining externally.

**Perfect Hashing**: A collision-free hash for a known, fixed key set. *Minimal* perfect hashing maps n keys onto exactly n slots.

**Probe Sequence Length (PSL)**: How far an entry in an open-addressed table sits from its home slot. Robin Hood hashing keeps PSLs even by letting an inserted key take the slot of any entry closer to home.

**Robin Hood Hashing**: Linear probing where an inserted key displaces any entry with a shorter probe sequence length. Average cost is unchanged, but the variance and the cost of misses drop sharply.

**SipHash**: A fast keyed hash function designed to resist hash flooding. The default string hash in Python, Ruby and Rust.

**Swiss Table**: An open-addressing hash table that stores a control byte per slot and probes 16-slot groups with SIMD instructions. Abseil's flat_hash_map, Rust's HashMap and Go's maps since 1.24 use the design.

**Universal Hashing**: Choosing a hash function at random from a family, so that no fixed input is reliably bad. The defense against collision-flooding attacks.

## Memory and Storage

**Bit-Packing**: Storing a block of small integers in exactly as many bits each as the largest needs. With delta encoding, the basis of posting-list compression in search engines.

**Cache Line**: The unit of transfer between memory and cache, typically 64 bytes. Reading one byte costs the same as reading its whole line.

**Cache-Oblivious**: Achieving optimal I/O performance without knowing the block size. By being well-organized at every scale simultaneously.

**External Memory Model**: A cost model counting block transfers rather than operations. Predicts real disk performance where the RAM model does not.

**Gap Buffer**: A text buffer that keeps one contiguous gap at the cursor, so typing is O(1) but moving the cursor far away costs a large copy. Used by Emacs.

**Locality**: The tendency of an access pattern to touch nearby addresses. Sequential access has good locality; pointer chasing has none.

**LSM Tree (Log-Structured Merge)**: A write-optimized structure that buffers writes in memory and flushes them as sorted immutable runs, converting random writes to sequential ones.

**Page**: The unit of transfer between memory and disk, typically 4KB.

**Piece Table**: A text representation made of an append-only original buffer, an append-only add buffer, and a list of pieces pointing into them. Edits never move text, and undo is cheap.

**Segment (search index)**: An immutable chunk of an inverted index. New documents create new segments, deletions are marked in a bitset, and background merges combine segments, much like LSM-tree compaction.

**Varint (Variable-Byte Encoding)**: Encoding an integer in 7-bit groups, one per byte, with the high bit marking that more bytes follow. Small numbers take one byte.

**Write Amplification**: The ratio of bytes actually written to storage versus bytes logically written by the application.

## Persistence and Concurrency

**ABA Problem**: A compare-and-swap succeeds because a pointer's value is unchanged, even though the state it refers to has changed and changed back. Defended against with tagged pointers or hazard pointers.

**CAS (Compare-and-Swap)**: An atomic hardware instruction that sets a memory location to a new value only if it currently holds an expected one. The universal primitive for lock-free programming.

**Copy-on-Write**: Sharing data until a write occurs, at which point the written portion is duplicated.

**Linearizability**: Every operation appears to take effect instantaneously at some moment between its call and return, consistent with real time. The standard correctness condition for concurrent objects, and notable for composing.

**Lock-Free**: Guaranteeing that *some* thread always makes progress. Weaker than **wait-free**, which guarantees *every* thread finishes in bounded steps.

**MVCC (Multi-Version Concurrency Control)**: Keeping multiple versions of each row so readers see a consistent snapshot without blocking writers. Partial persistence, applied to databases.

**Path Copying**: Achieving persistence by duplicating only the nodes on the path from root to the modification point, O(log n) per update in a balanced tree.

**Persistent**: Preserving previous versions after modification. *Partial* persistence allows querying old versions; *full* allows updating them; *confluent* allows merging them. Unrelated to durable storage.

**Structural Sharing**: Reusing unchanged subtrees between versions of an immutable structure. What makes persistence affordable.

## Distributed Systems

**Admission Policy**: A cache's rule for whether a new item should enter at all, rather than which item to evict. W-TinyLFU admits a newcomer only if it is estimated to be more popular than the victim.

**CAP Theorem**: During a network partition, a distributed system must sacrifice either consistency or availability. See [Appendix D](appendix-d-network-and-system-design-quick-reference.md) for why "CA" is not a third option.

**Consistent Hashing**: Mapping keys and nodes onto a ring so that adding or removing a node remaps only ~1/n of keys, rather than nearly all of them.

**CRDT (Conflict-Free Replicated Data Type)**: A structure whose merge is commutative, associative, and idempotent, so replicas converge without coordination.

**DHT (Distributed Hash Table)**: A hash table partitioned across many machines, with a routing protocol for locating the responsible node.

**Eventual Consistency**: A guarantee that replicas converge given no further updates, with no bound on when.

**Merkle Tree**: A tree of hashes where each node hashes its children, allowing two large datasets to be compared (and their differences located) in logarithmic work.

**Power of Two Choices**: Sending each request to the less loaded of two randomly chosen servers. Cuts the maximum load from Θ(log n / log log n) to Θ(log log n) and avoids the herding that "least loaded" suffers with stale data.

**Quorum**: A subset of replicas that must acknowledge an operation. Overlapping read and write quorums (R + W > N) give strong consistency.

**Scan Resistance**: A cache policy's ability to survive a one-off sequential scan without evicting its genuinely popular items. LRU has none; LFU, ARC and W-TinyLFU do.

**Vector Clock**: A per-replica counter vector that distinguishes causally-ordered updates from genuinely concurrent ones.

## Probabilistic and Compressed

**Bloom Filter**: A bit array with k hash functions giving approximate membership: false positives are possible, false negatives are not.

**Count-Min Sketch**: A fixed-size frequency estimator over a stream, which overestimates but never underestimates.

**HyperLogLog**: A cardinality estimator using the maximum leading-zero count of hashes, giving about 0.81% standard error in 12 KB (16,384 registers) regardless of set size.

**Rank / Select**: The two primitives underlying succinct structures. `rank(i)` counts 1-bits before position i; `select(k)` finds the position of the k-th 1-bit.

**Roaring Bitmap**: A compressed bitmap that splits 32-bit values into 65,536 chunks and stores each chunk as a sorted array, a plain bitmap or a list of runs, whichever is smallest. Used by Lucene, Druid, ClickHouse and many others.

**Succinct**: Using space within a lower-order term of the information-theoretic minimum, while still supporting queries *without decompressing*.

## Spatial and String

**Border**: A string that is both a proper prefix and a suffix of another. The prefix function (KMP's failure function) records the longest border of each prefix of a pattern.

**Inverted Index**: A map from each term to its posting list, the sorted list of documents containing it. The core structure of full-text search.

**LCP Array**: Longest Common Prefix between each pair of adjacent suffixes in a suffix array. Together they encode a suffix tree implicitly.

**MBR (Minimum Bounding Rectangle)**: The smallest axis-aligned rectangle enclosing a set of objects. The key type in an R-tree, and overlap between sibling MBRs is what degrades R-tree queries.

**Posting List**: The sorted list of document IDs (plus frequencies or positions) for one term in an inverted index. Stored as compressed gaps between consecutive IDs.

**Rolling Hash**: A hash of a sliding window that can be updated in O(1) as the window moves one character. The basis of Rabin-Karp matching and of content-defined chunking in rsync and backup tools.

**Space-Filling Curve**: A mapping from multi-dimensional coordinates to one dimension that mostly preserves locality, Z-order and Hilbert being the common ones. The basis of geohashing.

**Suffix Array**: The sorted list of a string's suffix starting positions. Suffix-tree power at about 4 bytes per character rather than 20.

**Trie**: A tree keyed by character position, where lookup costs O(key length) independent of how many keys are stored.

**Z-Array**: For each position i of a string, the length of the longest substring starting at i that matches a prefix of the string. Computed in O(n) and used for pattern matching.

## Graphs

**Adjacency List / Matrix**: The two standard graph representations. A list stores each vertex's neighbours (O(V + E) space); a matrix stores a V × V table of edges (O(V²) space, O(1) edge test).

**Back Edge**: In a DFS, an edge to an ancestor still on the recursion stack. A directed graph has a cycle exactly when DFS finds one.

**Bipartite**: A graph whose vertices split into two sides with every edge crossing between them. Equivalent to having no odd-length cycle.

**CSR (Compressed Sparse Row)**: A static graph layout of two arrays, the concatenated neighbour lists and an offset per vertex. Compact and cache-friendly; adding an edge means rebuilding.

**Cut Property**: For any split of a graph's vertices into two groups, the lightest edge crossing the split belongs to some minimum spanning tree. The reason Kruskal's and Prim's greedy choices are safe.

**DAG (Directed Acyclic Graph)**: A directed graph with no cycles. Exactly the graphs that have a topological order.

**Negative Cycle**: A cycle whose edge weights sum to less than zero. Shortest paths through it are undefined; Bellman-Ford detects one.

**Relaxation**: Updating a vertex's tentative distance with dist[v] = min(dist[v], dist[u] + w(u, v)). Every shortest-path algorithm is a strategy for which edges to relax in which order.

**Strongly Connected Component (SCC)**: A maximal set of vertices in a directed graph that can all reach one another. Collapsing each SCC to one vertex always leaves a DAG.

**Topological Order**: An ordering of a DAG's vertices in which every edge points forward. Used for build systems, scheduling and dependency resolution.

## Techniques

**Binary Search on the Answer**: Binary searching over candidate answers rather than over an array, using a yes/no test that is monotone in the answer (for example, "can everything ship in d days with capacity c?").

**Fast and Slow Pointers**: Walking two pointers through a sequence at different speeds. Finds the middle of a linked list in one pass, and detects cycles (Floyd's algorithm).

**Half-Open Interval**: A range written [lo, hi) that includes lo and excludes hi. Using it consistently is the easiest way to write a correct binary search.

**Lazy Deletion**: Leaving stale entries in a structure and skipping them when they surface, instead of removing them immediately. The usual way to get decrease-key behaviour from Python's heapq.

**Lower Bound / Upper Bound**: In a sorted array, the first position whose value is ≥ x and the first whose value is > x. Python's bisect_left and bisect_right.

**Monotonic Stack**: A stack kept in increasing or decreasing order by popping everything that would break the order before each push. Finds the next greater or smaller element for every position in O(n) total.

**Prefix Sum**: An array whose i-th entry is the sum of the first i input values, making any range sum a single subtraction. The inverse of a difference array.

**Sliding Window**: Maintaining an answer over a contiguous window as one end advances, so each element enters and leaves once and the whole scan is O(n).

**Two Pointers**: Moving two indices through a sorted array (often from both ends) so that each step rules out a candidate, giving O(n) instead of O(n²).
