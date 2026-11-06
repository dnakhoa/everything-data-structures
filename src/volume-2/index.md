# Volume II: Advanced Structures and Algorithms

Volume I organised data by position (arrays, lists) and by order (search trees, heaps). This volume adds three ideas that each change what is possible:

- **Relationships with no fixed shape.** A graph records only which things are connected. With the right auxiliary structure (a queue, a stack, a heap, a union-find) it answers questions about reachability, ordering, connectivity and distance.
- **Lookup without order.** A hash table gives up sorted order entirely and gets expected O(1) lookup in return. It is the most widely used structure in practice, and the fine print (hash quality, load factor, adversarial input) is where real systems succeed or fail.
- **Structure inside the keys.** When the keys are strings, their shared prefixes and suffixes can themselves be indexed. Tries, suffix arrays and Aho-Corasick turn text search from scanning into lookup.

**Before you start.** You need Volume I, especially Chapters 5 (stacks and queues), 7 (BSTs) and 9 (heaps); Chapter 11's algorithms are those structures driven over a graph. Chapter 1's notion of expected cost is used throughout Chapter 12.

| Chapter | After it you can |
|---------|------------------|
| [11: Graphs: Modeling Relationships](ch11-graphs-modeling-relationships.md) | Choose a graph representation, run BFS and DFS, detect cycles, order a DAG, find strongly connected components and MSTs, and pick the right shortest-path algorithm for the edge weights you have |
| [12: Hash Tables](ch12-hash-tables.md) | Explain chaining versus open addressing, reason about load factor and resizing, choose a hash function, explain why Robin Hood hashing and Swiss tables are what modern hash maps use, defend against hash flooding, and build an LRU cache |
| [13: String Data Structures](ch13-string-data-structures.md) | Build tries and radix trees, explain suffix trees and suffix arrays, match patterns with KMP, the Z-array and rolling hashes, search for many patterns at once with Aho-Corasick, and choose between a gap buffer, rope and piece table for a text editor |

The three chapters are independent, so read them in any order. If you are preparing for interviews, Chapters 11 and 12 are the most frequently tested material in the whole book.
