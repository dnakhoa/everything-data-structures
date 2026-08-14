# Everything Data Structures

**A complete course on data structures: from asymptotic analysis to the storage engines behind Spanner and Kafka.**

Five volumes · 31 chapters · 4 appendices · ~55,000 words · Python, C, C++, Java, and Go

By **Ngoc Anh Khoa Doan**, with the editorial help of Claude.

---

## Start here

You do not have to read this front to back. Pick the track that matches what you're doing:

| If you are… | Start with | Then |
|-------------|-----------|------|
| **New to data structures** | [Chapter 1: Philosophy and Mathematics](volume-1/ch01-the-philosophy-and-mathematics-of-data-structures.md) | Work through Volume I in order |
| **Preparing for interviews** | [Appendix B: When to Use What](appendices/appendix-b-when-to-use-what.md) | Volume I, then [Graphs](volume-2/ch11-graphs-modeling-relationships.md) and [Hash Tables](volume-2/ch12-hash-tables.md) |
| **Doing competitive programming** | [Chapter 23: CP Data Structures](volume-4/ch23-advanced-competitive-programming-data-structures.md) | [Chapter 24: Research-Grade](volume-4/ch24-research-grade-data-structures.md) |
| **Building systems** | [Chapter 29: System Design as Composition](volume-5/ch29-system-design-as-data-structure-composition.md) | [Chapter 31: Case Studies](volume-5/ch31-real-world-case-studies.md) |
| **Looking something up** | [Appendix A: Complexity Cheat Sheet](appendices/appendix-a-complexity-cheat-sheet.md) | [Chapter 25: Selection Guide](volume-4/ch25-complete-selection-guide-and-complexity-reference.md) |

The full syllabus with chapter-by-chapter reading lists is in the [repository README](https://github.com/dnakhoa/everything-data-structures#learning-paths).

---

## What makes this different

**It doesn't stop at red-black trees.** Most treatments end where the undergraduate syllabus ends. This one continues through competitive-programming machinery (link-cut trees, wavelet trees, Mo's algorithm)into research-grade structures like FM-indexes and succinct trees, and then out the other side into distributed systems.

**Volume V argues something specific.** That network topologies and system designs *are* data structures, composed at scale. A routing table is a trie. Consistent hashing is a hash ring. A message queue is a persistent FIFO with durability guarantees. Once you see systems this way, system design stops being a separate discipline you memorize and starts being a subject you can reason about from first principles.

**Every chapter answers the same questions.** What is the idea? What invariant holds? What do the operations cost, and why? What does the code look like? Where is this actually used? Who invented it, and what problem forced them to?

**Tradeoffs are stated plainly.** Fibonacci heaps have the best asymptotic bounds on the page and lose to binary heaps in practice, and this book says so, and explains why. Asymptotic superiority is a claim about a limit, and the limit may sit far beyond any input you will ever see.

---

## The five volumes

**[Volume I: Foundations and Fundamentals](volume-1/index.md)**
Complexity analysis, memory and pointers, arrays, linked lists, stacks, queues, trees, binary search trees, self-balancing trees, heaps, and B-trees. Everything a working programmer must know.

**[Volume II: Advanced Structures and Algorithms](volume-2/index.md)**
Graphs and their algorithms, hash tables in depth, and string structures: tries, suffix trees, suffix arrays.

**[Volume III: Specialized and Modern Structures](volume-3/index.md)**
Probabilistic structures, spatial indexes, external-memory and cache-oblivious design, persistence, concurrency, emerging structures, design patterns, and the practical business of choosing and debugging.

**[Volume IV: Competitive Programming and Research-Grade Structures](volume-4/index.md)**
The contest arsenal and the research frontier: segment trees with lazy propagation, heavy-light decomposition, link-cut trees, suffix automata, wavelet trees, succinct representations, FM-indexes, and fractional cascading.

**[Volume V: Network and System Design Data Structures](volume-5/index.md)**
Distributed hash tables, consistent hashing, CRDTs, consensus, routing tables, storage engines, rate limiters, inverted indexes, and case studies of Spanner, Dynamo, Kafka, Delta Lake, and Cloudflare's edge.

---

## Using this book

Every page has a **search** (press `s`), a **print/PDF view** (the printer icon), and an **edit link** to its source on GitHub. Corrections are welcome: see the [contributing guide](https://github.com/dnakhoa/everything-data-structures/blob/main/CONTRIBUTING.md).

The prose is [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) and the code is MIT. Use it in your class, your study group, or your blog.

Start with the [Preface](introduction.md), or jump straight to [Chapter 1](volume-1/ch01-the-philosophy-and-mathematics-of-data-structures.md).
