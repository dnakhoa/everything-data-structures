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

## 4.6 Pointer Techniques

A handful of pointer patterns solve most problems on singly linked lists. Each runs in O(n) worst-case time with O(1) extra space, and each works by rewiring `next` fields rather than copying data into an array. The code uses the Python `Node` class from the exercises at the end of this chapter, with two helpers for building and printing lists:

```python
class Node:
    def __init__(self, data, next=None):
        self.data = data
        self.next = next


def from_list(xs):
    head = None
    for x in reversed(xs):
        head = Node(x, head)
    return head


def to_list(node):
    out = []
    while node:
        out.append(node.data)
        node = node.next
    return out
```

### In-Place Reversal

Walk the list once and turn each `next` pointer around. Three pointers do it:

```python
def reverse(head):
    prev, cur = None, head
    while cur:
        nxt = cur.next      # 1. save the rest of the list
        cur.next = prev     # 2. turn this node around
        prev = cur          # 3. it now heads the reversed part
        cur = nxt           # 4. move on to the rest
    return prev
```

The invariant, true at the top of every iteration: `prev` is the head of the reversed prefix (the nodes already visited, in reverse order), `cur` is the head of the untouched suffix, and together the two lists hold every node exactly once. Each iteration moves one node from the front of the suffix to the front of the prefix. When `cur` is None the suffix is empty and `prev` is the whole list, reversed.

| Iteration | prev (reversed part) | cur (rest) |
|-----------|----------------------|------------|
| start | None | 1 → 2 → 3 → 4 |
| 1 | 1 | 2 → 3 → 4 |
| 2 | 2 → 1 | 3 → 4 |
| 3 | 3 → 2 → 1 | 4 |
| 4 | 4 → 3 → 2 → 1 | None |

The order of the four statements is the whole difficulty. Step 2 overwrites the only reference to the rest of the list, so step 1 must save it first; Exercise 4.3 shows what happens otherwise. The loop is O(n) time and O(1) space. A recursive version is shorter but uses O(n) stack, which for a long list overflows the stack (or, in Python, hits the recursion limit of 1000).

### Fast and Slow Pointers

Two pointers start at the head; `slow` moves one node per step and `fast` moves two. After k steps, slow is at index k and fast at index 2k. That alone finds the middle in one pass, without counting the length first:

```python
def middle(head):
    """Node at index n // 2 of a non-empty list of n nodes."""
    slow = fast = head
    while fast and fast.next:
        slow = slow.next            # one step
        fast = fast.next.next       # two steps
    return slow
```

The loop stops when fast has no two nodes left to move over, so slow is at index ⌊n/2⌋: node 3 of 1 → 2 → 3 → 4 → 5, and node 3 of 1 → 2 → 3 → 4 (the second of the two middles).

**Cycle detection.** If a bug or a malicious input makes some `next` point back to an earlier node, a plain traversal loops forever. Floyd's algorithm detects this with the same two pointers. If the list ends, fast reaches None. If it has a cycle, both pointers end up going round it, and fast gains one node on slow at every step. Measured along the cycle, the distance from fast forward to slow therefore drops by exactly 1 per step, so it reaches 0 (fast cannot jump over slow) within λ steps of slow entering the cycle, where λ is the cycle length.

Finding where the cycle starts takes a counting argument. Let μ be the number of steps from the head to the first node of the cycle (the tail length), and suppose the pointers meet after slow has taken k steps, so fast has taken 2k.

1. Both pointers are on the same node, and fast has walked the same path as slow plus k more steps. Those extra k steps went round the cycle and returned to the same node, so **k is a multiple of λ**.
2. Slow is in the cycle, k − μ steps past its start.
3. Walk μ more steps from the meeting point. That is k − μ + μ = k steps past the start of the cycle, and since k is a multiple of λ, **that lands exactly on the start**.
4. A pointer starting at the head also reaches the start after exactly μ steps.

So move one pointer back to the head and advance both one step at a time. They meet at the first node of the cycle, after μ steps, without either μ or λ being known:

```python
def find_cycle_start(head):
    """First node of the cycle, or None if the list ends."""
    slow = fast = head
    while fast and fast.next:
        slow, fast = slow.next, fast.next.next
        if slow is fast:                    # phase 1: they met inside the cycle
            slow = head
            while slow is not fast:         # phase 2: both step once
                slow, fast = slow.next, fast.next
            return slow
    return None
```

<figure>
{{#include ../images/floyd-cycle.svg}}
<figcaption>The meeting point is k − μ steps into the cycle, so μ more steps complete a whole number of laps and land on the start, which is also μ steps from the head.</figcaption>
</figure>

Worked example: nodes 1 to 8, with node 8 linking back to node 4, so μ = 3 and λ = 5.

| Step | 1 | 2 | 3 | 4 | 5 |
|------|---|---|---|---|---|
| slow | 2 | 3 | 4 | 5 | 6 |
| fast | 3 | 5 | 7 | 4 | 6 |

They meet at node 6 after k = 5 steps, a multiple of λ, and node 6 is k − μ = 2 steps past node 4. Phase 2 moves the pair (1, 6) to (2, 7), (3, 8), (4, 4): both reach node 4 after μ = 3 steps. In general k is the smallest positive multiple of λ that is at least μ, so phase 1 takes at most μ + λ steps and phase 2 takes μ: O(n) worst case, O(1) space. Remembering visited nodes in a hash set also works, but costs O(n) extra space. The cycle length comes for free as well: from the meeting point, count steps until slow returns to it.

The algorithm never uses the fact that the nodes are a list. It works on any sequence x, f(x), f(f(x)), ... where only the current value is stored, which is how it finds the period of a pseudo-random number generator and how Pollard's rho method factors integers.

### Merging Two Sorted Lists

Merging is where the sentinel of Section 4.5 pays off. The result list grows at its tail, and without a sentinel the first node is a special case: there is no tail yet to link after, so the code must pick the head separately and then repeat the same comparison inside the loop. A dummy head gives `tail` a node to start from, and the real result is `dummy.next`:

```python
def merge(a, b):
    """Merge two sorted lists by relinking their nodes; stable."""
    dummy = tail = Node(None)       # sentinel: tail always has a node to link after
    while a and b:
        if a.data <= b.data:        # <= takes from a on ties, so the merge is stable
            tail.next, a = a, a.next
        else:
            tail.next, b = b, b.next
        tail = tail.next
    tail.next = a if a else b       # splice the leftover run in O(1)
    return dummy.next
```

Invariant: `dummy.next` through `tail` holds the nodes taken so far in sorted order, and every node left in a or b is at least `tail.data`. Merging 1 → 4 → 6 with 2 → 3 → 7 takes 1, 2, 3, 4, 6; then a is empty and the single assignment `tail.next = b` attaches 7, however long the rest of b is. The merge allocates no nodes apart from the dummy: O(m + n) time in the worst case, O(1) extra space. The same merge on arrays needs an O(m + n) output buffer, because array elements cannot be relinked.

### Merge Sort on Linked Lists

Merge sort is the natural sort for linked lists. Split the list in half with fast and slow pointers, sort each half recursively, and merge:

```python
def split_point(head):
    """Last node of the first half: index (n - 1) // 2 of n >= 2 nodes."""
    slow, fast = head, head.next
    while fast and fast.next:
        slow, fast = slow.next, fast.next.next
    return slow


def merge_sort(head):
    if head is None or head.next is None:
        return head
    mid = split_point(head)
    right = mid.next
    mid.next = None                 # cut into two lists
    return merge(merge_sort(head), merge_sort(right))


assert to_list(merge_sort(from_list([5, 2, 4, 1, 3]))) == [1, 2, 3, 4, 5]
```

`split_point` starts `fast` one node ahead, so it stops at the end of the first half rather than at the start of the second, which `middle` would return; Exercise 4.8 shows why that difference matters. On 5 → 2 → 4 → 1 → 3 it cuts after 4, giving [5, 2, 4] and [1, 3]; those sort to 2 → 4 → 5 and 1 → 3, and the final merge gives 1 → 2 → 3 → 4 → 5.

The structure fits lists better than arrays on each count:

- **The merge needs no buffer.** Array merge sort copies into O(n) auxiliary space; the list version relinks nodes in place.
- **Only sequential access is used.** Splitting and merging both walk forward. Heapsort's index arithmetic needs random access, and quicksort's usual protection against its O(n²) worst case (a random or median-of-three pivot) needs cheap access to arbitrary positions.
- **It is stable** (the `<=` in `merge`) and its O(n log n) bound is worst case, not average.

Each level of recursion spends O(n) on splitting and O(n) on merging, over ⌈log₂ n⌉ levels: O(n log n) worst-case time. The top-down version above uses O(log n) stack. A bottom-up version, which merges runs of length 1, 2, 4, ... in a loop, needs only O(1) extra space; that is what the Linux kernel's `list_sort` and libstdc++'s `std::list::sort` do.

## 4.7 XOR Linked Lists

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

## 4.8 Unrolled Linked Lists

Each node contains multiple elements in a small array:

```
┌────────┬───────┐    ┌────────┬───────┐
│ 3 │ A │ B │ C │ ──┼─→│ 2 │ D │ E │ ──┼─→ NULL
│ elements│       │    │ elements│       │
└────────┴───────┘    └────────┴───────┘
```

**Advantages:**
- Better cache locality (multiple elements per node)
- Less pointer overhead
- Faster iteration
- Still O(1) insertion at arbitrary positions (with smaller shift)

**Used in**: CD-ROM filesystems (directory entries), Kyoto Cabinet database, Redis's quicklist (the encoding of the Redis list type since 3.2: a doubly linked list of packed arrays)

## 4.9 Performance Characteristics

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

## 4.10 When to Use Linked Lists

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

## 4.11 Real-World Applications

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

## 4.12 Historical Context

The linked list was invented by Allen Newell, Cliff Shaw, and Herbert A. Simon at RAND Corporation in 1956, as part of the development of the Information Processing Language (IPL), the first AI programming language.

John McCarthy made linked lists the fundamental data structure of LISP (1958) and introduced the names "car" and "cdr" (contents of the address part of register, contents of the decrement part of register) for the two fields of a list cell.

The doubly linked list emerged later as programmers recognized the need for bidirectional traversal.

The tortoise-and-hare cycle detector of Section 4.6 is credited to Robert W. Floyd by Knuth (*The Art of Computer Programming*, Vol. 2, 1969), although Floyd never published it himself; Richard Brent published a faster variant in 1980. Merge sort is older than linked lists: Knuth attributes it to John von Neumann in 1945.

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**4.1 ★ Trace the core operations.** Using the singly linked list functions from Section 4.2, what does the list look like after each line? For each `delete_node` call, say which branch of the function does the work.

```c
Node *head = NULL;
insert_head(&head, 3);
insert_head(&head, 7);
insert_head(&head, 1);
insert_after(head->next, 5);
delete_node(&head, 1);
delete_node(&head, 3);
delete_node(&head, 9);
```

<details>
<summary>Solution</summary>

| Line | List afterwards |
|------|-----------------|
| `insert_head(&head, 3)` | 3 → NULL |
| `insert_head(&head, 7)` | 7 → 3 → NULL |
| `insert_head(&head, 1)` | 1 → 7 → 3 → NULL |
| `insert_after(head->next, 5)` | 1 → 7 → 5 → 3 → NULL |
| `delete_node(&head, 1)` | 7 → 5 → 3 → NULL |
| `delete_node(&head, 3)` | 7 → 5 → NULL |
| `delete_node(&head, 9)` | 7 → 5 → NULL |

- `insert_after(head->next, 5)`: `head->next` is the node holding 7, so 5 goes between 7 and 3.
- `delete_node(&head, 1)`: the key is in the head node, so the first `if` handles it by moving `*head_ref` to the second node. This is why the function takes `Node **`: it has to be able to change the caller's `head`.
- `delete_node(&head, 3)`: the `while` loop walks with `prev` one step behind `temp` (7, then 5) until `temp` reaches 3, then `prev->next = temp->next` unlinks it. `prev` is the 5 node, whose `next` becomes NULL.
- `delete_node(&head, 9)`: the loop runs off the end, `temp` is NULL, and the `if (temp == NULL) return;` line leaves the list unchanged.

</details>

**4.2 ★ The tail pointer doesn't help deletion.** The table in Section 4.9 lists "Insert at Tail" as O(1) for a singly linked list with a tail pointer, but "Delete at Tail" as O(n). Explain why the tail pointer helps one and not the other, and what a doubly linked list changes.

<details>
<summary>Solution</summary>

Inserting at the tail only touches the old tail node: set `tail->next = new_node`, then `tail = new_node`. The tail pointer gives direct access to that node, so it is O(1).

Deleting the tail requires changing the node *before* it: its `next` must become NULL, and `tail` must move to it. A singly linked node has no pointer to its predecessor, so the only way to find it is to walk from the head: O(n). Keeping a pointer to the second-to-last node doesn't fix this either, because after one deletion you need the third-to-last, and so on.

A doubly linked list stores `prev` in every node, so the new tail is `tail->prev`, found in O(1). That one extra pointer per node is the price of O(1) deletion at the tail, and of O(1) deletion of any node you hold a pointer to (Section 4.3). This is why queues (insert at one end, remove at the other) work fine on a singly linked list with a tail pointer, but deques need a doubly linked list or an array.

</details>

**4.3 ★★ Find the bug.** This function is meant to reverse a singly linked list in place and return the new head. On the list 1 → 2 → 3 → 4 it returns a list containing only 1. Why? Fix it.

```python
class Node:
    def __init__(self, data, next=None):
        self.data = data
        self.next = next


def reverse(head):
    prev = None
    cur = head
    while cur:
        cur.next = prev
        prev = cur
        cur = cur.next
    return prev
```

<details>
<summary>Hint</summary>

Trace the first iteration and write down what `cur.next` holds at the moment `cur = cur.next` runs.

</details>

<details>
<summary>Solution</summary>

First iteration: `cur` is node 1. `cur.next = prev` sets node 1's `next` to None, which destroys the only reference to node 2. Then `prev = cur` (node 1), and `cur = cur.next` reads the pointer that was just overwritten: `cur` becomes None. The loop ends and the function returns node 1, whose `next` is None. Nodes 2, 3 and 4 are lost (in C, leaked).

The fix is to save the rest of the list before rewiring the pointer:

```python
class Node:
    def __init__(self, data, next=None):
        self.data = data
        self.next = next


def reverse(head):
    prev = None
    cur = head
    while cur:
        nxt = cur.next      # save the rest of the list first
        cur.next = prev     # reverse this node's pointer
        prev = cur
        cur = nxt
    return prev


def to_list(node):
    out = []
    while node:
        out.append(node.data)
        node = node.next
    return out


head = Node(1, Node(2, Node(3, Node(4))))
assert to_list(reverse(head)) == [4, 3, 2, 1]
assert reverse(None) is None
assert to_list(reverse(Node(1))) == [1]
```

The invariant: at the top of each iteration, `prev` is the head of the already-reversed prefix and `cur` is the head of the untouched suffix. Overwriting `cur.next` before saving it breaks the link to the suffix. The function is O(n) time and O(1) extra space.

</details>

**4.4 ★★ XOR list by hand.** Four nodes A, B, C, D form an XOR linked list (Section 4.7), in that order, at addresses A = 0x10, B = 0x20, C = 0x30, D = 0x40. NULL is 0.

(a) Compute `npx` for every node.

(b) Traverse the list starting from D with `prev = NULL`, using the traversal loop from Section 4.7. Show each step.

(c) What do you need, at minimum, to start a traversal in the middle of the list, say at C?

<details>
<summary>Solution</summary>

**(a)** `npx` = address of previous XOR address of next.

| Node | prev | next | npx |
|------|------|------|-----|
| A | 0x00 | 0x20 | 0x20 |
| B | 0x10 | 0x30 | 0x20 |
| C | 0x20 | 0x40 | 0x60 |
| D | 0x30 | 0x00 | 0x30 |

(A and B happen to have the same `npx`. That's fine; `npx` only means something together with a neighbour's address.)

**(b)** Each step computes `next = prev ^ current->npx`.

| current | prev | next = prev ^ npx | visit |
|---------|------|-------------------|-------|
| D (0x40) | 0x00 | 0x00 ^ 0x30 = 0x30 (C) | D |
| C (0x30) | 0x40 | 0x40 ^ 0x60 = 0x20 (B) | C |
| B (0x20) | 0x30 | 0x30 ^ 0x20 = 0x10 (A) | B |
| A (0x10) | 0x20 | 0x20 ^ 0x20 = 0x00 (NULL) | A |

Output: D C B A. The same loop walks backwards when started from the tail, so an XOR list *can* be traversed in both directions; what it needs is the address of one end and the starting neighbour (NULL at either end).

**(c)** The address of C alone is useless: `npx` = 0x60 could be any pair of neighbours whose addresses XOR to 0x60. You need the addresses of two adjacent nodes, such as C and B (then `next = 0x20 ^ 0x60 = 0x40`, D) or C and D (then `next = 0x40 ^ 0x60 = 0x20`, B). For the same reason you can't delete a node given only a pointer to it, which takes away one of the doubly linked list's main advantages from Section 4.3.

</details>

**4.5 ★★ One sentinel, no special cases.** The doubly linked `delete_node` in Section 4.3 needs two `if` tests, and `insert_before` needs one, all for the head and tail cases. Implement a doubly linked list in Python with a single sentinel node that is both the "before head" and "after tail" node (the list is circular through the sentinel). Write `push_front`, `push_back`, `insert_before(node, data)` and `delete(node)` without any `if` statements.

<details>
<summary>Hint</summary>

An empty list is a sentinel whose `prev` and `next` both point to itself. Then every real node always has a real `prev` and `next` object, even when that object is the sentinel.

</details>

<details>
<summary>Solution</summary>

```python
class DNode:
    def __init__(self, data=None):
        self.data = data
        self.prev = self
        self.next = self


class DList:
    def __init__(self):
        self.sentinel = DNode()   # sentinel.next is the head, sentinel.prev the tail

    def insert_before(self, node, data):
        new = DNode(data)
        new.prev, new.next = node.prev, node
        node.prev.next = new
        node.prev = new
        return new

    def push_front(self, data):
        return self.insert_before(self.sentinel.next, data)

    def push_back(self, data):
        return self.insert_before(self.sentinel, data)

    def delete(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def __iter__(self):
        cur = self.sentinel.next
        while cur is not self.sentinel:
            yield cur.data
            cur = cur.next


lst = DList()
b = lst.push_back("b")
lst.push_front("a")
d = lst.push_back("d")
lst.insert_before(d, "c")
assert list(lst) == ["a", "b", "c", "d"]
lst.delete(b)
lst.delete(d)                      # deleting the tail: no special case
assert list(lst) == ["a", "c"]
lst.delete(lst.sentinel.next)      # deleting the head: no special case
lst.delete(lst.sentinel.next)      # list is now empty
assert list(lst) == [] and lst.sentinel.next is lst.sentinel
```

The branches disappear because the conditions they tested ("is `prev` NULL?", "is `next` NULL?") can no longer be true: the head's `prev` and the tail's `next` are the sentinel. The cost is one extra node per list, and iteration must stop at the sentinel instead of at NULL. Fewer branches means fewer places for the head/tail bugs that dominate linked list code; this is the "Both" pattern from Section 4.5 with the two sentinels merged into one, and it is how the Linux kernel's `list_head` works.

</details>

**4.6 ★★★ Unrolled list insertion.** Implement `insert(i, x)` for an unrolled linked list (Section 4.8) whose nodes hold at most B = 4 elements. When the target node is full, split it into two nodes of B/2 elements each, then insert. Then analyse: with n elements and node capacity B, what does one insert cost, and what B minimises it?

<details>
<summary>Hint</summary>

Walk node by node, subtracting each node's count from i, until i falls inside (or at the end of) the current node. After a split, decide which half the insertion position belongs to.

</details>

<details>
<summary>Solution</summary>

```python
import random

B = 4  # node capacity


class UNode:
    def __init__(self, items=None):
        self.items = items if items is not None else []   # at most B elements
        self.next = None


class UnrolledList:
    def __init__(self):
        self.head = UNode()
        self.n = 0

    def insert(self, i, x):
        """Insert x so that it ends up at position i (0 <= i <= n)."""
        if not 0 <= i <= self.n:
            raise IndexError(i)
        node = self.head
        while i > len(node.items) and node.next is not None:   # skip whole nodes
            i -= len(node.items)
            node = node.next
        if len(node.items) == B:                                # full: split in half
            half = B // 2
            right = UNode(node.items[half:])
            node.items = node.items[:half]
            right.next = node.next
            node.next = right
            if i > half:
                node, i = right, i - half
        node.items.insert(i, x)                                 # shifts at most B - 1
        self.n += 1

    def __iter__(self):
        node = self.head
        while node is not None:
            yield from node.items
            node = node.next


random.seed(7)
for trial in range(200):
    u, ref = UnrolledList(), []
    for k in range(random.randint(0, 60)):
        i = random.randint(0, len(ref))
        u.insert(i, k)
        ref.insert(i, k)
        assert list(u) == ref
```

**Cost.** A split always produces two nodes with B/2 elements, and nodes only grow between splits, so every node except possibly the first holds at least B/2 elements. There are therefore at most about 2n/B nodes. One insert costs:

- O(n/B) to walk to the right node (one step per node, not per element),
- O(B) to shift elements within the node (plus O(B) for a split, which copies half a node).

Total O(n/B + B). This is minimised when n/B = B, i.e. B ≈ √n, giving O(√n) per insert, against O(n) for both a plain array (shifting) and a plain linked list (walking). In practice B is chosen from the hardware instead, so that a node fills one or a few cache lines: the walk then touches n/B cache lines instead of n, which is where the "better cache locality" in Section 4.8 comes from. Pointer overhead also drops from one pointer per element to one pointer per B/2 or more elements.

</details>

**4.7 ★ Floyd by hand.** A list has nodes 1 to 10 in order, and node 10's `next` points back to node 3. Run `find_cycle_start` from Section 4.6.

(a) What are μ and λ? After how many steps of phase 1 do slow and fast meet, and at which node?

(b) Trace phase 2.

(c) How would you compute λ from the meeting point?

<details>
<summary>Solution</summary>

**(a)** Two steps lead from node 1 to node 3, so μ = 2. The cycle is 3 → 4 → ... → 10 → 3, so λ = 8.

| Step | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|------|---|---|---|---|---|---|---|---|
| slow | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
| fast | 3 | 5 | 7 | 9 | 3 | 5 | 7 | 9 |

They meet at **node 9 after k = 8 steps**. As Section 4.6 predicts, k is the smallest positive multiple of λ that is at least μ, here 8 itself. Node 9 is k − μ = 6 steps past node 3.

**(b)** Slow restarts at node 1, fast stays at node 9, and both take single steps: (1, 9) → (2, 10) → (3, 3). They meet at **node 3** after μ = 2 steps: from node 9, two steps (to 10, then back to 3) complete the lap that the 6 steps from node 3 began.

**(c)** Keep one pointer at the meeting point and step the other around until it comes back, counting: 9 → 10 → 3 → 4 → 5 → 6 → 7 → 8 → 9 is 8 steps, so λ = 8. Together with μ from phase 2, this also gives the number of distinct nodes, μ + λ = 10.

</details>

**4.8 ★★ Find the bug.** This merge sort uses `middle` from Section 4.6 instead of `split_point`. On any list of two or more nodes it raises `RecursionError` in Python (in C, it overflows the stack). Why? Fix it while still splitting at `middle`'s node.

```python
def merge_sort(head):
    if head is None or head.next is None:
        return head
    mid = middle(head)
    right = mid.next
    mid.next = None
    return merge(merge_sort(head), merge_sort(right))
```

<details>
<summary>Hint</summary>

Run it on a two-node list. Which node does `middle` return, and how long is each half?

</details>

<details>
<summary>Solution</summary>

`middle` returns the node at index ⌊n/2⌋, and the code cuts *after* it, so the left half has ⌊n/2⌋ + 1 nodes. For n = 2 that is 2: `middle` returns the second node, `right` is None, and `merge_sort(head)` is called again on the same two-node list, forever. Larger lists shrink until some call gets two nodes (n = 3 splits into 2 and 1), so every list of two or more nodes hits the loop. A split is only safe if both halves are non-empty, so each recursive call is on a strictly shorter list.

The fix is to cut *before* the middle node, which needs the node behind `slow`:

```python
class Node:
    def __init__(self, data, next=None):
        self.data = data
        self.next = next


def merge(a, b):
    dummy = tail = Node(None)
    while a and b:
        if a.data <= b.data:
            tail.next, a = a, a.next
        else:
            tail.next, b = b, b.next
        tail = tail.next
    tail.next = a if a else b
    return dummy.next


def merge_sort(head):
    if head is None or head.next is None:
        return head
    prev, slow, fast = None, head, head
    while fast and fast.next:
        prev, slow, fast = slow, slow.next, fast.next.next
    prev.next = None                # cut just before the middle node
    return merge(merge_sort(head), merge_sort(slow))


def from_list(xs):
    head = None
    for x in reversed(xs):
        head = Node(x, head)
    return head


def to_list(node):
    out = []
    while node:
        out.append(node.data)
        node = node.next
    return out


import random
for _ in range(500):
    xs = [random.randint(0, 9) for _ in range(random.randint(0, 30))]
    assert to_list(merge_sort(from_list(xs))) == sorted(xs)
```

With n ≥ 2 the loop runs at least once, so `prev` is a real node, and the halves have ⌊n/2⌋ and ⌈n/2⌉ nodes, both at least 1. `split_point` in Section 4.6 reaches the same cut more directly by starting `fast` one node ahead, so that `slow` stops on the last node of the first half.

</details>

**4.9 ★★ Palindrome in O(1) space.** Write `is_palindrome(head)` for a singly linked list using O(1) extra space (no copying into a Python list), and leave the list exactly as it was when the function returns.

<details>
<summary>Hint</summary>

Find the end of the first half, reverse the second half in place, compare the two halves node by node, then reverse the second half again.

</details>

<details>
<summary>Solution</summary>

```python
class Node:
    def __init__(self, data, next=None):
        self.data = data
        self.next = next


def reverse(head):
    prev, cur = None, head
    while cur:
        nxt = cur.next
        cur.next = prev
        prev = cur
        cur = nxt
    return prev


def is_palindrome(head):
    """True if the list reads the same both ways; O(n) time, O(1) extra space."""
    if head is None or head.next is None:
        return True
    slow, fast = head, head.next            # slow stops at the end of the first half
    while fast and fast.next:
        slow, fast = slow.next, fast.next.next
    second = reverse(slow.next)             # reverse the second half in place
    p, q, result = head, second, True
    while q:                                # second half is never the longer one
        if p.data != q.data:
            result = False
            break
        p, q = p.next, q.next
    slow.next = reverse(second)             # restore the original list
    return result


def from_list(xs):
    head = None
    for x in reversed(xs):
        head = Node(x, head)
    return head


def to_list(node):
    out = []
    while node:
        out.append(node.data)
        node = node.next
    return out


for xs in ([1, 2, 3, 2, 1], [1, 2, 2, 1], [1, 2, 3, 1], [1, 2], [7], []):
    head = from_list(xs)
    assert is_palindrome(head) == (xs == xs[::-1])
    assert to_list(head) == xs                  # list left unchanged
```

On 1 → 2 → 3 → 2 → 1, `slow` stops at node 3 (index (n − 1) // 2 = 2, as in `split_point`), the second half 2 → 1 is reversed to 1 → 2, and the comparison checks 1 = 1 and 2 = 2; the middle element of an odd-length list is never compared, which is correct. The first half has ⌈n/2⌉ nodes and the second ⌊n/2⌋, so stopping when the second half runs out compares every mirrored pair.

Each of the three passes (find the split, reverse, compare) plus the restoring reverse is O(n), so the total is O(n) time and O(1) extra space. The restore step matters: a function called `is_palindrome` that silently scrambles its argument is a bug waiting for the caller. It is also why this technique is unsafe if another thread reads the list at the same time.

</details>

---

## Where this connects

- [Chapter 3: Arrays—The Foundation of Contiguous Storage](ch03-arrays-the-foundation-of-contiguous-storage.md). The contiguous alternative, and when it wins
- [Chapter 18: Concurrent Data Structures](../volume-3/ch18-concurrent-data-structures.md). Why lock-free versions of these structures are hard
