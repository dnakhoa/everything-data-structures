# Volume III: Specialized and Modern Structures

The structures in Volumes I and II assume a single machine, a single thread, exact answers and data that fits in memory. Real systems break every one of those assumptions, and each chapter in this volume relaxes one of them:

| Assumption dropped | Chapter | The idea |
|--------------------|---------|----------|
| Answers must be exact | [14: Probabilistic Data Structures](ch14-probabilistic-data-structures.md) | Bloom filters, cuckoo filters, HyperLogLog and Count-Min trade a controlled error rate for huge savings in memory |
| Keys are one-dimensional | [15: Spatial and Geometric Data Structures](ch15-spatial-and-geometric-data-structures.md) | KD-trees, quadtrees, R-trees and geohashes answer "what is near this point?" |
| Memory access is uniform | [16: External Memory and Cache-Oblivious Structures](ch16-external-memory-and-cache-oblivious-structures.md) | Count block transfers instead of operations, and design layouts that are fast at every level of the memory hierarchy |
| Updates destroy the old version | [17: Persistent Data Structures](ch17-persistent-data-structures.md) | Path copying, fat nodes and structural sharing keep every version alive cheaply; persistent vectors, queues and finger trees; the basis of functional languages, Git and MVCC |
| One thread at a time | [18: Concurrent Data Structures](ch18-concurrent-data-structures.md) | Locks, compare-and-swap, the ABA problem, and when lock-free is worth its complexity |
| The textbook is the state of the art | [19: Emerging and Specialized Structures](ch19-emerging-and-specialized-structures.md) | Succinct structures, learned indexes, vector search, and why some theoretical winners lose in practice |

The last three chapters step back from individual structures to how they are built and used:

| Chapter | The idea |
|---------|----------|
| [20: Data Structure Design Patterns](ch20-data-structure-design-patterns.md) | Wrappers, iterators, adapters and builders: the recurring ways structures are composed and exposed |
| [21: Algorithm Design Using Data Structures](ch21-algorithm-design-using-data-structures.md) | Divide and conquer, dynamic programming, greedy, backtracking and randomization, and the structure each paradigm leans on |
| [22: Practical Considerations](ch22-practical-considerations.md) | Choosing structures under real constraints, what your language's standard library really gives you, profiling, and debugging structural bugs |

**Before you start.** Volume I is required. Chapter 14 uses hashing from Chapter 12, Chapter 16 builds on B-trees from Chapter 10, and Chapter 17 builds on BSTs from Chapter 7. Otherwise the chapters are independent and can be read in any order; pick the assumption that matters most to your work.
