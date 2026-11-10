# Volume I: Foundations and Fundamentals

Everything later in this book is built from the material in this volume. A hash table is an array plus a function. A B-tree is a search tree tuned for disk. A Kafka topic is a queue that never forgets. A lock-free skip list is a linked list with ideas from probability and concurrency. If those foundations are solid, the rest of the book is a series of variations on things you already understand.

The volume moves from the language of cost (Chapter 1) and how memory really works (Chapter 2), through the two ways to store a sequence (contiguous arrays and linked nodes), to the hierarchical structures that make ordered data fast to search.

**Before you start.** You should be comfortable reading short Python programs: functions, loops, lists, dicts and classes. Most chapters also show C, because C makes memory layout visible. You don't need any prior data structures course. A little algebra (logarithms, sums of series) helps in Chapter 1 and is explained where it's used.

## Part 1: Mathematical Foundations

| Chapter | After it you can |
|---------|------------------|
| [1: The Philosophy and Mathematics of Data Structures](ch01-the-philosophy-and-mathematics-of-data-structures.md) | Read and reason with O, Ω and Θ; tell worst-case, average and amortized cost apart; explain why a dynamic array's append is O(1) amortized |
| [2: Primitive Types and Memory Organization](ch02-primitive-types-and-memory-organization.md) | Explain what a pointer is, why integers overflow, how structs are padded, how malloc manages the heap (free lists, buddy and slab allocators), and why memory layout affects speed |

## Part 2: Fundamental Linear Structures

| Chapter | After it you can |
|---------|------------------|
| [3: Arrays: The Foundation of Contiguous Storage](ch03-arrays-the-foundation-of-contiguous-storage.md) | Implement a growable array, address multi-dimensional data, use binary search, two pointers, sliding windows and prefix sums, and explain how Roaring bitmaps compress sets |
| [4: Linked Lists: The Art of Distributed Storage](ch04-linked-lists-the-art-of-distributed-storage.md) | Manipulate pointers safely with sentinels, reverse and merge lists in place, detect cycles, and know when a list loses to an array |
| [5: Stacks and Queues: Ordered Access Patterns](ch05-stacks-and-queues-ordered-access-patterns.md) | Build both on arrays or lists, evaluate expressions with a stack, use circular buffers and deques, and solve next-greater and sliding-window problems with monotonic stacks and queues |

## Part 3: Hierarchical Structures and Trees

| Chapter | After it you can |
|---------|------------------|
| [6: Tree Fundamentals and Binary Trees](ch06-tree-fundamentals-and-binary-trees.md) | Use tree vocabulary precisely, traverse a tree four ways (recursively and with an explicit stack), and write recursive tree functions |
| [7: Binary Search Trees](ch07-binary-search-trees.md) | Search, insert and delete in a BST, answer successor, range and rank queries, and explain why insertion order can ruin it |
| [8: Self-Balancing Trees](ch08-self-balancing-trees.md) | Perform rotations, insert into and delete from AVL and red-black trees, see a red-black tree as a 2-3-4 tree, and choose between AVL, red-black, splay trees and treaps |
| [9: Heaps and Priority Queues](ch09-heaps-and-priority-queues.md) | Implement a binary heap, build one in O(n), support decrease-key, and solve top-k and running-median problems |
| [10: Multiway Search Trees and B-Trees](ch10-multiway-search-trees-and-b-trees.md) | Insert into and delete from a B-tree, explain why databases use B+ trees, and estimate how many disk reads a lookup costs |

## Suggested route

Read Chapters 1, 3, 4 and 5 in order, then 6 and 7 together, since a BST is the first place tree traversals pay off. Chapter 2 can be read alongside Chapter 3 or skimmed if you already know C. Chapter 8 is the hardest in the volume; on a first pass, aim to understand rotations and the red-black invariants, and come back for the deletion cases. Chapter 9 depends only on Chapter 6's array representation of trees. Read Chapter 10 last, because it brings together search trees and the memory hierarchy from Chapter 2.

Each chapter ends with exercises. Do at least the ★ ones before moving on: they are short and check the ideas the next chapter assumes.
