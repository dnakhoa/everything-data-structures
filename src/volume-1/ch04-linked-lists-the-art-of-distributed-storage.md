# Chapter 4: Linked Lists—The Art of Distributed Storage

## 4.1 The Linked List Philosophy

Where arrays store elements contiguously, linked lists store elements anywhere in memory, connecting them via pointers. This distribution enables efficient insertion and deletion at arbitrary positions, at the cost of no direct indexing.

The fundamental trade-off:
- Array: Fast access, slow modification
- Linked list: Slow access (must traverse), fast modification

## 4.2 Singly Linked Lists

Each node contains data and a pointer to the next node:

```c
struct Node {
    element_type data;
    struct Node *next;
};
```

```
HEAD                                                            NULL
 │                                                               │
 ▼                                                               ▼
┌────────┬───────┐    ┌────────┬───────┐    ┌────────┬───────┐    ┌────────┬───────┐
│ Data: A│ Next: ──────→│ Data: B│ Next: ──────→│ Data: C│ Next: ──────→│ Data: D│ Next: │
│       │       │    │       │       │    │       │       │    │       │       │
└────────┴───────┘    └────────┴───────┘    └────────┴───────┘    └────────┴───────┘
```

### Core Operations

**Insertion at Head:**
```c
void insert_head(Node **head_ref, element_type data) {
    Node *new_node = malloc(sizeof(Node));
    new_node->data = data;
    new_node->next = *head_ref;
    *head_ref = new_node;
}
```
Time: O(1)

**Insertion at Position:**
```c
void insert_after(Node *prev_node, element_type data) {
    if (prev_node == NULL) return;
    Node *new_node = malloc(sizeof(Node));
    new_node->data = data;
    new_node->next = prev_node->next;
    prev_node->next = new_node;
}
```
Time: O(1) given position, O(n) to find position

**Deletion:**
```c
void delete_node(Node **head_ref, element_type key) {
    Node *temp = *head_ref;
    Node *prev = NULL;

    if (temp != NULL && temp->data == key) {
        *head_ref = temp->next;
        free(temp);
        return;
    }

    while (temp != NULL && temp->data != key) {
        prev = temp;
        temp = temp->next;
    }

    if (temp == NULL) return;
    prev->next = temp->next;
    free(temp);
}
```
Time: O(n) worst case to find, O(1) to delete

**Search:**
```c
Node* search(Node *head, element_type key) {
    Node *current = head;
    while (current != NULL) {
        if (current->data == key) return current;
        current = current->next;
    }
    return NULL;
}
```
Time: O(n)

## 4.3 Doubly Linked Lists

Each node contains data, a pointer to the next node, and a pointer to the previous node:

```c
struct DNode {
    element_type data;
    struct DNode *next;
    struct DNode *prev;
};
```

```
 NULL                                                           NULL
  │                                                             │
  │     ┌────────┬────────┬───────┐    ┌────────┬────────┬───────┐
  │     │  Prev  │  Data  │  Next │    │  Prev  │  Data  │  Next │
  └────→│  NULL  │   A    │   ────┼───→│   ────┤   B    │   ────┼───→ NULL
        └────────┴────────┴───────┘    └────────┴────────┴───────┘
```

### Advantages Over Singly Linked Lists

- Traversal in both directions
- O(1) deletion given a node pointer (no need to find previous)
- O(1) insertion before a given node
- Better for implementing deques

### Implementation

**Deletion (given node pointer):**
```cpp
void delete_node(DNode *node) {
    if (node->prev != NULL)
        node->prev->next = node->next;
    else
        head = node->next;  // Was head

    if (node->next != NULL)
        node->next->prev = node->prev;

    free(node);
}
```

**Insertion Before:**
```cpp
void insert_before(DNode **head, DNode *next_node, element_type data) {
    DNode *new_node = malloc(sizeof(DNode));
    new_node->data = data;
    new_node->next = next_node;
    new_node->prev = next_node->prev;

    if (next_node->prev != NULL)
        next_node->prev->next = new_node;
    else
        *head = new_node;  // Was head

    next_node->prev = new_node;
}
```

## 4.4 Circular Linked Lists

The last node's next pointer points back to the first node (or for doubly, the first node's prev points to the last).

```
Circular Singly:
┌────────┬───────┐    ┌────────┬───────┐    ┌────────┬───────┐
│ Data: A│ Next: ────┼─→│ Data: B│ Next: ────┼─→│ Data: C│ Next: ────┐
│       │       │    │       │       │    │       │       │    │
└────────┴───────┘    └────────┴───────┘    └────────┴───────┘    │
    ↑                                                              │
    └──────────────────────────────────────────────────────────────┘

Circular Doubly:
NULL ◄────────────────────────────────────────────────────────────────► NULL
  │     ┌────────┬────────┬───────┐    ┌────────┬────────┬───────┐    │
  │     │  Prev  │  Data  │  Next │    │  Prev  │  Data  │  Next │    │
  └────→│   ●    │   A    │   ────┼───→│   ────┤   B    │   ────┼───→│
        └────────┴────────┴───────┘    └────────┴────────┴───────┘    │
            ▲                                                              │
            └──────────────────────────────────────────────────────────────┘
```

### Applications

**Round-Robin Scheduling**: Each process gets equal CPU time
**Circular Buffers**: Efficient producer-consumer patterns
**Music Playlists**: Seamless looping
**Undo/Redo History**: Recent actions cycle through

## 4.5 The Sentinel's Guard

Sentinel nodes (dummy nodes) simplify boundary conditions by eliminating null checks:

```c
// Without sentinel - careful null handling
void insert_first(Node **head, element_type data) {
    Node *new_node = malloc(sizeof(Node));
    new_node->data = data;
    new_node->next = *head;
    *head = new_node;
}

// With sentinel - cleaner code
void insert_after(Node *prev, element_type data) {
    Node *new_node = malloc(sizeof(Node));
    new_node->data = data;
    new_node->next = prev->next;
    prev->next = new_node;
}
```

Common sentinel patterns:
- **Head sentinel**: Dummy node before first real element
- **Tail sentinel**: Dummy node after last real element
- **Both**: Simplifies all operations to "insert after/before"

## 4.6 XOR Linked Lists

XOR linked lists store only the XOR of consecutive node addresses, saving space:

```c
struct XorNode {
    element_type data;
    uintptr_t npx;  // XOR of previous and next pointers
};
```

The trick: to traverse, you need the previous node's address to XOR with npx to get the next node's address.

**Traversal:**
```c
XorNode* prev = NULL;
XorNode* current = head;
XorNode* next;

while (current != NULL) {
    printf("%d ", current->data);
    next = (XorNode*)((uintptr_t)prev ^ current->npx);
    prev = current;
    current = next;
}
```

**Advantages**: 50% space reduction for pointers
**Disadvantages**: Can't traverse backwards without storing previous pointer, debugging is harder

## 4.7 Unrolled Linked Lists

Each node contains multiple elements in a small array:

```
┌────────┬───────┐    ┌────────┬───────┐
│ 4 │ A │ B │ C │ ──┼─→│ 2 │ D │ E │ ──┼─→ NULL
│ elements│       │    │ elements│       │
└────────┴───────┘    └────────┴───────┘
```

**Advantages:**
- Better cache locality (multiple elements per node)
- Less pointer overhead
- Faster iteration
- Still O(1) insertion at arbitrary positions (with smaller shift)

**Used in**: CD-ROM filesystems (directory entries), Kyoto Cabinet database, Lua's table implementation

## 4.8 Performance Characteristics

| Operation | Singly | Doubly | Circular | Unrolled |
|-----------|--------|--------|----------|----------|
| Insert at Head | O(1) | O(1) | O(1) | O(1)* |
| Insert at Tail | O(1)* | O(1) | O(1) | O(1)* |
| Delete at Head | O(1) | O(1) | O(1) | O(1)* |
| Delete at Tail | O(n) | O(1) | O(1)* | O(1)* |
| Delete at Position | O(n) | O(n)* | O(n) | O(n)* |
| Search | O(n) | O(n) | O(n) | O(n) |
| Memory Overhead | Low | Medium | Low | Low-Medium |
| Cache Efficiency | Poor | Poor | Poor | Better |

*With tail pointer or other augmentation

## 4.9 When to Use Linked Lists

**Use Linked Lists When:**
- Frequent insertions/deletions at arbitrary positions
- Size is unknown or highly variable
- Memory is fragmented
- No random access needed
- Implementing other structures (stacks, queues)

**Avoid Linked Lists When:**
- Frequent random access (use arrays)
- Cache performance matters (use arrays or unrolled)
- Memory overhead is a concern (pointers take space)
- Simple iteration is the primary operation (vectors are faster)

## 4.10 Real-World Applications

**Operating Systems**:
- Process scheduling queues
- Memory allocation (free lists)
- File system directory entries
- Driver device queues

**Databases**:
- B-tree leaf nodes (doubly linked for range scans)
- Transaction logs
- Lock chains

**Compilers**:
- Symbol tables (hash table + linked list chaining)
- Abstract syntax trees (child lists)

**Applications**:
- Music playlists (doubly linked for bidirectional navigation)
- Browser history (back/forward buttons)
- Undo/redo functionality
- Text buffer implementation (lines as linked list)

## 4.11 Historical Context

The linked list was invented by Allen Newell, Cliff Shaw, and Herbert A. Simon at RAND Corporation in 1956, as part of the development of the Information Processing Language (IPL), the first AI programming language.

John McCarthy introduced the concept of "linked list" and "car/cdr" (contents of address/register and contents of decrement/register) in LISP (1958), where lists are the fundamental data structure.

The doubly linked list emerged later as programmers recognized the need for bidirectional traversal.

---

## Where this connects

- [Chapter 3: Arrays—The Foundation of Contiguous Storage](ch03-arrays-the-foundation-of-contiguous-storage.md) — the contiguous alternative, and when it wins
- [Chapter 18: Concurrent Data Structures](../volume-3/ch18-concurrent-data-structures.md) — why lock-free versions of these structures are hard
