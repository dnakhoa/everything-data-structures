# Everything Data Structures

[![Deploy](https://github.com/dnakhoa/everything-data-structures/actions/workflows/deploy.yml/badge.svg)](https://github.com/dnakhoa/everything-data-structures/actions/workflows/deploy.yml)
[![Prose: CC BY 4.0](https://img.shields.io/badge/prose-CC%20BY%204.0-blue.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Code: MIT](https://img.shields.io/badge/code-MIT-green.svg)](LICENSE)
[![Chapters](https://img.shields.io/badge/chapters-31-orange.svg)](https://dnakhoa.github.io/everything-data-structures/)

A complete, free course on data structures — from asymptotic analysis and pointer arithmetic all the way to CRDTs, learned indexes, and the storage engines behind Spanner and Kafka.

**📖 Read it online: [dnakhoa.github.io/everything-data-structures](https://dnakhoa.github.io/everything-data-structures/)**

Five volumes · 31 chapters · 4 appendices · ~40,000 words · Python, C, C++, Java and Go examples.

Written by [Ngoc Anh Khoa Doan](https://github.com/dnakhoa).

---

## Why this exists

Most data structure resources stop at red-black trees. This one keeps going — through competitive-programming machinery (link-cut trees, wavelet trees, Mo's algorithm), through research-grade structures (FM-indexes, succinct trees, fractional cascading), and out the other side into system design, where the central claim of Volume V is that **a routing table is a trie, consistent hashing is a hash ring, and a message queue is a persistent FIFO**. Systems are data structures composed at scale.

Every chapter covers the same ground: the idea, the invariants, the operations with complexity analysis, working code, real-world usage, and the historical context of who invented it and why.

---

## Learning paths

You do not have to read this front to back. Pick the track that matches what you're doing.

### 🌱 Track 1 — First course (beginner)

Never studied data structures formally, or want a clean rebuild of the fundamentals.

| # | Chapter | Why it's here |
|---|---------|---------------|
| 1 | [The Philosophy and Mathematics of Data Structures](src/volume-1/ch01-the-philosophy-and-mathematics-of-data-structures.md) | Big-O, amortized analysis, the no-free-lunch tradeoff |
| 2 | [Primitive Types and Memory Organization](src/volume-1/ch02-primitive-types-and-memory-organization.md) | What a pointer actually is |
| 3 | [Arrays](src/volume-1/ch03-arrays-the-foundation-of-contiguous-storage.md) | Contiguous storage, dynamic resizing |
| 4 | [Linked Lists](src/volume-1/ch04-linked-lists-the-art-of-distributed-storage.md) | The other way to store a sequence |
| 5 | [Stacks and Queues](src/volume-1/ch05-stacks-and-queues-ordered-access-patterns.md) | LIFO, FIFO, and what they're for |
| 6 | [Tree Fundamentals and Binary Trees](src/volume-1/ch06-tree-fundamentals-and-binary-trees.md) | Traversals, representations |
| 7 | [Binary Search Trees](src/volume-1/ch07-binary-search-trees.md) | Ordered data, and how it degrades |
| 9 | [Heaps and Priority Queues](src/volume-1/ch09-heaps-and-priority-queues.md) | The workhorse of scheduling |
| 12 | [Hash Tables](src/volume-2/ch12-hash-tables.md) | O(1) average, and the fine print |

Finish with [Appendix A: Complexity Cheat Sheet](src/appendices/appendix-a-complexity-cheat-sheet.md).

### 💼 Track 2 — Interview preparation

The structures that actually come up, plus the judgment to pick between them.

Track 1, then:

- [Chapter 8: Self-Balancing Trees](src/volume-1/ch08-self-balancing-trees.md) — AVL, red-black, splay, treaps
- [Chapter 11: Graphs](src/volume-2/ch11-graphs-modeling-relationships.md) — BFS/DFS, topological sort, MST, shortest paths, union-find
- [Chapter 13: String Data Structures](src/volume-2/ch13-string-data-structures.md) — tries, suffix arrays
- [Chapter 14: Probabilistic Data Structures](src/volume-3/ch14-probabilistic-data-structures.md) — Bloom filters come up constantly
- [Chapter 25: Complete Selection Guide](src/volume-4/ch25-complete-selection-guide-and-complexity-reference.md) — the decision matrix
- [Appendix B: When to Use What](src/appendices/appendix-b-when-to-use-what.md)

### ⚔️ Track 3 — Competitive programming

Assumes you know the fundamentals and want the contest arsenal.

- [Chapter 23: Advanced Competitive Programming Data Structures](src/volume-4/ch23-advanced-competitive-programming-data-structures.md) — the big one: segment trees with lazy propagation, Fenwick trees, heavy-light decomposition, link-cut trees, Mo's algorithm, suffix automaton, eertree, wavelet trees, Li Chao trees, sparse tables, Cartesian trees, sqrt decomposition, DSU with rollback
- [Chapter 10: Multiway Search Trees and B-Trees](src/volume-1/ch10-multiway-search-trees-and-b-trees.md)
- [Chapter 21: Algorithm Design Using Data Structures](src/volume-3/ch21-algorithm-design-using-data-structures.md)
- [Chapter 24: Research-Grade Data Structures](src/volume-4/ch24-research-grade-data-structures.md) — when you want to go past the standard set

### 🏗️ Track 4 — Systems and distributed engineering

For backend, infra, and system-design work.

- [Chapter 10: B-Trees](src/volume-1/ch10-multiway-search-trees-and-b-trees.md) — why every database index is one
- [Chapter 16: External Memory and Cache-Oblivious Structures](src/volume-3/ch16-external-memory-and-cache-oblivious-structures.md)
- [Chapter 17: Persistent Data Structures](src/volume-3/ch17-persistent-data-structures.md)
- [Chapter 18: Concurrent Data Structures](src/volume-3/ch18-concurrent-data-structures.md)
- [Chapter 27: Distributed Data Structures](src/volume-5/ch27-distributed-data-structures.md) — DHTs, consistent hashing, CRDTs, consensus, quorums
- [Chapter 28: Network Topology and Routing](src/volume-5/ch28-network-topology-and-routing-data-structures.md)
- [Chapter 29: System Design as Data Structure Composition](src/volume-5/ch29-system-design-as-data-structure-composition.md)
- [Chapter 30: Advanced System Patterns](src/volume-5/ch30-advanced-system-patterns-and-case-studies.md)
- [Chapter 31: Real-World Case Studies](src/volume-5/ch31-real-world-case-studies.md) — Spanner, Dynamo, Kafka, Delta Lake, Cloudflare
- [Appendix D: Network and System Design Quick Reference](src/appendices/appendix-d-network-and-system-design-quick-reference.md)

---

## Full contents

### [Volume I — Foundations and Fundamentals](src/volume-1/index.md)

*Part 1: Mathematical Foundations*
1. [The Philosophy and Mathematics of Data Structures](src/volume-1/ch01-the-philosophy-and-mathematics-of-data-structures.md)
2. [Primitive Types and Memory Organization](src/volume-1/ch02-primitive-types-and-memory-organization.md)

*Part 2: Fundamental Linear Structures*

3. [Arrays — The Foundation of Contiguous Storage](src/volume-1/ch03-arrays-the-foundation-of-contiguous-storage.md)
4. [Linked Lists — The Art of Distributed Storage](src/volume-1/ch04-linked-lists-the-art-of-distributed-storage.md)
5. [Stacks and Queues — Ordered Access Patterns](src/volume-1/ch05-stacks-and-queues-ordered-access-patterns.md)

*Part 3: Hierarchical Structures — Trees*

6. [Tree Fundamentals and Binary Trees](src/volume-1/ch06-tree-fundamentals-and-binary-trees.md)
7. [Binary Search Trees](src/volume-1/ch07-binary-search-trees.md)
8. [Self-Balancing Trees](src/volume-1/ch08-self-balancing-trees.md)
9. [Heaps and Priority Queues](src/volume-1/ch09-heaps-and-priority-queues.md)
10. [Multiway Search Trees and B-Trees](src/volume-1/ch10-multiway-search-trees-and-b-trees.md)

### [Volume II — Advanced Structures and Algorithms](src/volume-2/index.md)

11. [Graphs — Modeling Relationships](src/volume-2/ch11-graphs-modeling-relationships.md)
12. [Hash Tables](src/volume-2/ch12-hash-tables.md)
13. [String Data Structures](src/volume-2/ch13-string-data-structures.md)

### [Volume III — Specialized and Modern Structures](src/volume-3/index.md)

14. [Probabilistic Data Structures](src/volume-3/ch14-probabilistic-data-structures.md)
15. [Spatial and Geometric Data Structures](src/volume-3/ch15-spatial-and-geometric-data-structures.md)
16. [External Memory and Cache-Oblivious Structures](src/volume-3/ch16-external-memory-and-cache-oblivious-structures.md)
17. [Persistent Data Structures](src/volume-3/ch17-persistent-data-structures.md)
18. [Concurrent Data Structures](src/volume-3/ch18-concurrent-data-structures.md)
19. [Emerging and Specialized Structures](src/volume-3/ch19-emerging-and-specialized-structures.md)
20. [Data Structure Design Patterns](src/volume-3/ch20-data-structure-design-patterns.md)
21. [Algorithm Design Using Data Structures](src/volume-3/ch21-algorithm-design-using-data-structures.md)
22. [Practical Considerations](src/volume-3/ch22-practical-considerations.md)

### [Volume IV — Competitive Programming and Research-Grade Structures](src/volume-4/index.md)

23. [Advanced Competitive Programming Data Structures](src/volume-4/ch23-advanced-competitive-programming-data-structures.md)
24. [Research-Grade Data Structures](src/volume-4/ch24-research-grade-data-structures.md)
25. [Complete Selection Guide and Complexity Reference](src/volume-4/ch25-complete-selection-guide-and-complexity-reference.md)

### [Volume V — Network and System Design Data Structures](src/volume-5/index.md)

27. [Distributed Data Structures](src/volume-5/ch27-distributed-data-structures.md)
28. [Network Topology and Routing Data Structures](src/volume-5/ch28-network-topology-and-routing-data-structures.md)
29. [System Design as Data Structure Composition](src/volume-5/ch29-system-design-as-data-structure-composition.md)
30. [Advanced System Patterns and Case Studies](src/volume-5/ch30-advanced-system-patterns-and-case-studies.md)
31. [Real-World Case Studies](src/volume-5/ch31-real-world-case-studies.md)
32. [Synthesis and Future Directions](src/volume-5/ch32-synthesis-and-future-directions.md)

### Appendices

- [A — Complexity Cheat Sheet](src/appendices/appendix-a-complexity-cheat-sheet.md)
- [B — When to Use What](src/appendices/appendix-b-when-to-use-what.md)
- [C — Glossary](src/appendices/appendix-c-glossary.md)
- [D — Network and System Design Quick Reference](src/appendices/appendix-d-network-and-system-design-quick-reference.md)
- [Bibliography](src/appendices/bibliography.md)

---

## Building locally

The site is [mdBook](https://rust-lang.github.io/mdBook/). To preview with live reload:

```bash
cargo install mdbook && mdbook serve --open
```

Every chapter is also plain Markdown — you can read the whole course on GitHub without building anything.

## Contributing

Corrections, clarifications, and better examples are welcome. Open an issue or a pull request; each page on the site has an "edit this page" link that takes you straight to the right file.

## License

Prose is licensed [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); code samples are [MIT](LICENSE). Use it in your class, your study group, or your blog — just credit the source.
