# Chapter 9: Heaps and Priority Queues

## 9.1 The Heap Property

A heap is a complete binary tree satisfying the heap property:

- **Max-heap**: Parent ≥ Children (root is maximum)
- **Min-heap**: Parent ≤ Children (root is minimum)

```
Max-Heap:
            90
           /  \
         80    70
        /  \   /  \
      50   40 60   30
      / \
    10   20

Min-Heap:
             10
           /    \
         20      30
        /  \    /  \
      50   40  60   70
```

## 9.2 Heap Array Representation

Heaps are typically stored in arrays due to their completeness:

```
Array representation of max-heap:
Index:    0   1   2   3   4   5   6   7   8
Array: [90 | 80 | 70 | 50 | 40 | 60 | 30 | 10 | 20]
         ↑
       Root

Parent(i)     = (i - 1) / 2
LeftChild(i)  = 2 * i + 1
RightChild(i) = 2 * i + 2
```

The complete tree property guarantees no "holes" in the array.

<figure>
{{#include ../images/heap-array-mapping.svg}}
<figcaption>Index i's children sit at 2i + 1 and 2i + 2, so level L occupies indices 2^L − 1 through 2^(L+1) − 2 and no pointers are needed.</figcaption>
</figure>

## 9.3 Heap Operations

### Maintaining the Heap Property: Heapify

Heapify restores the heap property at a node by "sifting down" larger children:

```c
void heapify(int arr[], int n, int i) {
    int largest = i;
    int left = 2 * i + 1;
    int right = 2 * i + 2;

    if (left < n && arr[left] > arr[largest])
        largest = left;
    if (right < n && arr[right] > arr[largest])
        largest = right;

    if (largest != i) {
        swap(&arr[i], &arr[largest]);
        heapify(arr, n, largest);
    }
}
```

```
Heapify at index 1 (value 30):
Before:                After:
       90                    90
      /  \                  /  \
    [30]  70      →        50    70
    /  \                /  \
  50   40              30   40
```

### Building a Heap

Two approaches:
1. **Insert each element**: O(n log n)
2. **Heapify from bottom up**: O(n)

```c
void build_heap(int arr[], int n) {
    // Index of last non-leaf node = n/2 - 1
    for (int i = n/2 - 1; i >= 0; i--)
        heapify(arr, n, i);
}
```

Why O(n)? Most nodes are near leaves, requiring few swaps.

### Extract Maximum/Minimum

```c
int extract_max(int arr[], int *n) {
    if (*n <= 0) return -1;
    if (*n == 1) return arr[--(*n)];

    int max = arr[0];
    arr[0] = arr[--(*n)];
    heapify(arr, *n, 0);
    return max;
}
```

### Insert

```c
void insert(int arr[], int *n, int key) {
    int i = (*n)++;
    arr[i] = key;

    // Sift up
    while (i > 0 && arr[(i - 1) / 2] < arr[i]) {
        swap(&arr[i], &arr[(i - 1) / 2]);
        i = (i - 1) / 2;
    }
}
```

## 9.4 Heap Sort

Heap sort uses a heap to sort in O(n log n):

```c
void heap_sort(int arr[], int n) {
    // Build max heap
    build_heap(arr, n);

    // Extract elements
    for (int i = n - 1; i > 0; i--) {
        swap(&arr[0], &arr[i]);  // Move max to end
        heapify(arr, i, 0);      // Heapify reduced heap
    }
}
```

**Worked trace** on `[4, 10, 3, 5, 1]` (n = 5). The build phase calls `heapify` at i = 1, then i = 0; each extraction step swaps the root to the end and heapifies the shrunken prefix. The sorted tail is shown after the bar.

| step | action | array |
|---|---|---|
| build, i = 1 | 10 ≥ 5, 1: no swap | [4, 10, 3, 5, 1] |
| build, i = 0 | 4 sinks: swap with 10, then with 5 | [10, 5, 3, 4, 1] |
| i = 4 | swap 10 to the end, heapify size 4: 1 sinks past 5, 4 | [5, 4, 3, 1 \| 10] |
| i = 3 | swap 5 to the end, heapify size 3: 1 sinks past 4 | [4, 1, 3 \| 5, 10] |
| i = 2 | swap 4 to the end, heapify size 2: 3 ≥ 1, no swap | [3, 1 \| 4, 5, 10] |
| i = 1 | swap 3 to the end | [1 \| 3, 4, 5, 10] |

Each extraction costs one root-to-leaf `heapify`, at most ⌊log₂ n⌋ swaps, which is where the O(n log n) bound comes from.

Properties:
- In-place: O(1) extra space
- Not stable (equal elements may change relative order)
- O(n log n) worst case
- Good for embedded systems (no recursion, predictable)

## 9.5 Priority Queue Implementation

Heaps implement priority queues efficiently. This one is a min-priority queue (smallest priority first), the convention of Python's `heapq` and of Dijkstra's algorithm; flip the two `<` comparisons for a max-priority queue.

```python
class PriorityQueue:
    """Min-priority queue: pop returns the item with the smallest priority."""

    def __init__(self):
        self.heap = []

    def push(self, item, priority):
        self.heap.append((priority, item))
        self._sift_up(len(self.heap) - 1)

    def pop(self):
        if not self.heap:
            return None
        top = self.heap[0][1]
        last = self.heap.pop()
        if self.heap:
            self.heap[0] = last
            self._sift_down(0)
        return top

    def peek(self):
        return self.heap[0][1] if self.heap else None

    def _sift_up(self, i):
        h = self.heap
        while i > 0 and h[i][0] < h[(i - 1) // 2][0]:
            h[i], h[(i - 1) // 2] = h[(i - 1) // 2], h[i]
            i = (i - 1) // 2

    def _sift_down(self, i):
        h, n = self.heap, len(self.heap)
        while True:
            smallest = i
            for c in (2 * i + 1, 2 * i + 2):
                if c < n and h[c][0] < h[smallest][0]:
                    smallest = c
            if smallest == i:
                return
            h[i], h[smallest] = h[smallest], h[i]
            i = smallest
```

push and pop are O(log n) worst case, peek is O(1). The sifts compare only `h[i][0]`, the priority, so items with equal priorities never get compared with each other; Section 9.8 shows why that matters when you use `heapq` directly.

## 9.6 Indexed Priority Queues and Decrease-Key

Dijkstra's and Prim's algorithms need a fourth operation: **decrease-key**(item, p), which lowers the priority of an item already in the queue (a shorter path to vertex v has just been found). Lowering a key can only break the heap property between that node and its parent, so the repair is a sift-up, O(log n). The hard part is finding the node. Heap order only relates ancestors to descendants; it says nothing about *where* a given item sits, so locating vertex v means scanning the array, O(n). With one decrease-key per edge, that turns Dijkstra into O(E · V).

### The position map

Keep a second structure, `pos`, mapping each item to its current index in the heap array, and maintain the invariant `heap[pos[x]] == x` for every item x in the heap. Elements only move by swaps, and a swap moves exactly two elements, so every swap also updates two map entries: constant extra work, and no operation changes its asymptotic cost. decrease-key becomes "look up `pos[x]`, change the priority, sift up".

When the items are integers 0 to n − 1 (vertex ids), `pos` is a plain array; Sedgewick and Wayne's `IndexMinPQ` keeps the heap of ids and its inverse as exactly this pair of arrays. The version below uses dictionaries so that any hashable item works, and builds on the sifts of Section 9.5 with every swap routed through `_swap`:

```python
class IndexedMinHeap:
    """Min-heap of distinct items with priorities, plus a position map."""

    def __init__(self):
        self.heap = []   # items, in heap order
        self.prio = {}   # item -> current priority
        self.pos = {}    # item -> index of the item in self.heap

    def __len__(self):
        return len(self.heap)

    def contains(self, item):
        return item in self.pos

    def insert(self, item, priority):
        if item in self.pos:
            raise KeyError(f"{item!r} is already in the heap")
        self.heap.append(item)
        self.prio[item] = priority
        self.pos[item] = len(self.heap) - 1
        self._sift_up(len(self.heap) - 1)

    def pop(self):
        """Remove and return (item, priority) with the smallest priority."""
        self._swap(0, len(self.heap) - 1)
        item = self.heap.pop()
        del self.pos[item]
        if self.heap:
            self._sift_down(0)
        return item, self.prio.pop(item)

    def decrease_key(self, item, priority):
        if priority > self.prio[item]:
            raise ValueError("decrease_key cannot increase a priority")
        self.prio[item] = priority
        self._sift_up(self.pos[item])

    def _less(self, i, j):
        return self.prio[self.heap[i]] < self.prio[self.heap[j]]

    def _swap(self, i, j):
        h = self.heap
        h[i], h[j] = h[j], h[i]
        self.pos[h[i]] = i     # every move updates the map
        self.pos[h[j]] = j

    def _sift_up(self, i):
        while i > 0 and self._less(i, (i - 1) // 2):
            self._swap(i, (i - 1) // 2)
            i = (i - 1) // 2

    def _sift_down(self, i):
        n = len(self.heap)
        while True:
            smallest = i
            for c in (2 * i + 1, 2 * i + 2):
                if c < n and self._less(c, smallest):
                    smallest = c
            if smallest == i:
                return
            self._swap(i, smallest)
            i = smallest
```

insert, pop and decrease_key do O(log n) comparisons and swaps in the worst case, and contains is O(1). With dictionaries each map access is O(1) on average (Chapter 12); with integer ids and arrays it is O(1) worst case. An increase-key is the mirror image (sift down instead of up), and deleting an arbitrary item is "swap it with the last element, pop, then sift the moved element up or down".

**Worked trace.** Insert A:5, B:3, C:8, D:6, E:4. The heap and map are then:

```
heap: [B:3, E:4, C:8, D:6, A:5]     pos: A→4  B→0  C→2  D→3  E→1
```

`decrease_key('D', 1)` reads pos[D] = 3 in O(1) instead of searching. D's parent is index 1 (E:4): swap, so pos[D] = 1, pos[E] = 3. Its parent is now index 0 (B:3): swap, so pos[D] = 0, pos[B] = 1. Two swaps, four map updates:

```
heap: [D:1, B:3, C:8, E:4, A:5]     pos: A→4  B→1  C→2  D→0  E→3
```

Dijkstra on top of it keeps each vertex in the heap at most once, so the heap never holds more than V entries:

```python
def dijkstra_indexed(graph, source):
    """graph[u] is a list of (v, weight) pairs with weight >= 0.
    Returns distances to the vertices reachable from source."""
    dist = {source: 0}
    pq = IndexedMinHeap()
    pq.insert(source, 0)
    while pq:
        u, d = pq.pop()                  # d is final: there are no stale entries
        for v, w in graph[u]:
            if v not in dist:            # first time v is reached
                dist[v] = d + w
                pq.insert(v, d + w)
            elif pq.contains(v) and d + w < dist[v]:
                dist[v] = d + w
                pq.decrease_key(v, d + w)
    return dist
```

V pops and at most E decrease-keys give O((V + E) log V) worst case.

### The alternative: lazy deletion

Instead of changing an entry, push a new (priority, item) entry and leave the old one where it is. An item can now have several entries; only the one with the smallest priority is current. When an entry is popped, check whether it is still current and skip it if not. [Chapter 11](../volume-2/ch11-graphs-modeling-relationships.md) does exactly this in both Dijkstra's algorithm (`if d > dist[u]: continue`) and Prim's algorithm (`if v in visited: continue`), because Python's `heapq` has no decrease-key.

Each relaxation pushes at most one entry, so the heap holds up to E entries instead of V. Every push and pop is then O(log E), and since E ≤ V², log E ≤ 2 log V: the total is still O(E log V), the same bound as the indexed version. The price is memory, O(E) instead of O(V), and the work of popping stale entries. The same trick deletes arbitrary items: mark the entry as removed and skip it when it surfaces (the `heapq` documentation gives this recipe).

Which to use:

- **Lazy deletion** is the default when the heap comes from a library: Python's `heapq`, C++'s `std::priority_queue` and Java's `PriorityQueue` have no decrease-key (Java's `remove(Object)` is a linear scan). It is also simpler and often faster in practice, because entries are plain tuples in one array and no map is updated on every swap. Sparse graphs, where E is a small multiple of V, lose little memory to stale entries.
- **An indexed heap** is better when memory must stay proportional to the live items (dense graphs with many improvements can fill a lazy heap with up to E entries); when you need to read or change an item's current priority, as a scheduler re-prioritising a task or a simulation cancelling an event does; when you need increase-key or delete without accumulating garbage; or when a d-ary heap (Section 9.7) is meant to make decrease-key cheap.

Node-based heaps (binomial, Fibonacci, pairing: Sections 9.9 to 9.11) solve the same "find the element" problem differently: insert returns a pointer to the node, a *handle*, which the caller keeps and passes back to decrease-key.

## 9.7 d-ary Heaps

Nothing forces two children per node. In a **d-ary heap** each node has up to d children, stored in the same level-by-level array:

```
Parent(i)    = (i - 1) / d
Child(i, j)  = d * i + j        for j = 1, ..., d
```

With d = 2 these are the formulas of Section 9.2. The height is about log_d n = log₂ n / log₂ d, so the tree is shallower. The two sifts generalise directly (min-heap shown):

```python
def dary_sift_up(a, i, d):
    while i > 0 and a[i] < a[(i - 1) // d]:
        p = (i - 1) // d
        a[i], a[p] = a[p], a[i]
        i = p

def dary_sift_down(a, i, d):
    n = len(a)
    while True:
        first = d * i + 1                      # children are first .. first + d - 1
        if first >= n:
            return
        c = min(range(first, min(first + d, n)), key=a.__getitem__)
        if a[c] >= a[i]:
            return
        a[i], a[c] = a[c], a[i]
        i = c
```

Build-heap runs `dary_sift_down` from the last internal node, (n − 2) // d, down to 0, still O(n).

**The trade-off.** A sift-up does one comparison per level, so insert and decrease-key cost O(log_d n) worst case: larger d is strictly better for them. A sift-down must find the smallest of d children at every level (d − 1 comparisons) and compare it with the sinking element, so extract-min costs O(d log_d n): beyond some point, larger d makes it worse. For n = 10⁶:

| d | levels (log_d n) | sift-up comparisons | sift-down comparisons (d log_d n) |
|---|---|---|---|
| 2 | 19.9 | 19.9 | 39.9 |
| 4 | 10.0 | 10.0 | 39.9 |
| 8 | 6.6 | 6.6 | 53.2 |
| 16 | 5.0 | 5.0 | 79.7 |

**Why d = 4 often beats d = 2 in practice.** The table shows the 4-ary heap doing the *same* number of comparisons in a sift-down as the binary heap (4 per level, half the levels), half the comparisons in a sift-up, and half the element moves in both. The bigger win is memory. The d children of a node are adjacent in the array, so one cache line fetch brings in all of them: four 16-byte (priority, id) entries fill exactly one 64-byte line if the array is aligned so that each sibling group starts on a line boundary. In a large binary heap every level below the top few is a separate cache miss; the 4-ary heap has half the levels and so roughly half the misses ([Chapter 16](../volume-3/ch16-external-memory-and-cache-oblivious-structures.md) covers why misses dominate). LaMarca and Ladner measured this effect in 1996. Production libraries agree: .NET's `PriorityQueue<TElement, TPriority>` is a 4-ary min-heap, and Go's runtime keeps its timers in a 4-ary heap.

**Choosing d for Dijkstra.** Dijkstra does V extract-mins and up to E decrease-keys, for a total of O(V · d log_d V + E log_d V). Choosing d ≈ E/V (at least 2) balances the two terms and gives O(E log_(E/V) V). On a dense graph with E = V^(1+ε) that is O(E/ε), linear in E for any fixed ε, with nothing fancier than an array. On a sparse graph E/V is a small constant and d = 2 to 4 is the right choice anyway. Treat E/V as a starting point for tuning: the cost model above charges a decrease-key to every edge, and real runs relax far fewer.

## 9.8 Heap Patterns

Three problems come up again and again, and each is a few lines with a heap.

### Top k of a stream

To keep the k *largest* of n values arriving one at a time, keep a **min**-heap holding the k largest seen so far. For each new x, the only question is whether x beats the weakest of the current k, and the min-heap keeps that weakest value at the root: if x > heap[0], replace the root with x (`heapq.heapreplace`, one pop and push in a single sift). Each value costs at most one O(log k) operation, so the total is O(n log k) worst case with O(k) memory, against O(n log n) time and O(n) memory for sorting everything. A max-heap would put the *best* value at the root, which is the one you never evict. For the k smallest, mirror it with a max-heap of size k. Exercise 9.6 asks you to write it; `heapq.nlargest(k, iterable)` and `heapq.nsmallest` are the library versions.

### k-way merge

To merge k sorted lists with N elements in total, keep a heap of the current head of each list. Pop the smallest, output it, and push the next element of the list it came from:

```python
import heapq

def k_way_merge(lists):
    heap = [(lst[0], i, 0) for i, lst in enumerate(lists) if lst]
    heapq.heapify(heap)
    out = []
    while heap:
        value, i, j = heapq.heappop(heap)     # j-th element of list i
        out.append(value)
        if j + 1 < len(lists[i]):
            heapq.heappush(heap, (lists[i][j + 1], i, j + 1))
    return out
```

`k_way_merge([[1, 4, 9], [2, 3, 10], [5, 6]])` returns `[1, 2, 3, 4, 5, 6, 9, 10]`. The heap never holds more than k entries, so each of the N steps is O(log k) and the merge is O(N log k) worst case, against O(N k) for scanning all k heads at every step. On equal values the tuple comparison falls through to the list index i, which is unique, so it never compares anything further. `heapq.merge(*iterables)` does the same thing lazily, as a generator, which is what you want when the inputs are files too big for memory.

This is the merge phase of external merge sort, which merges hundreds of sorted runs in one pass ([Chapter 16](../volume-3/ch16-external-memory-and-cache-oblivious-structures.md)), of LSM-tree compaction, which merges sorted runs into one, and of a search engine combining sorted posting lists.

### Running median

To report the median after every value of a stream, split the values seen so far into two heaps: `low`, a max-heap holding the smaller half, and `high`, a min-heap holding the larger half. Keep two invariants:

1. **Order:** every value in `low` is ≤ every value in `high`, that is, max(low) ≤ min(high).
2. **Balance:** len(low) = len(high) or len(low) = len(high) + 1.

Then the median is max(low) when the count is odd and the average of max(low) and min(high) when it is even, both readable at the roots in O(1).

```python
import heapq

class RunningMedian:
    def __init__(self):
        self.low = []    # max-heap of the smaller half (values negated)
        self.high = []   # min-heap of the larger half

    def add(self, x):
        if not self.low or x <= -self.low[0]:
            heapq.heappush(self.low, -x)
        else:
            heapq.heappush(self.high, x)
        # restore balance: len(low) - len(high) must be 0 or 1
        if len(self.low) > len(self.high) + 1:
            heapq.heappush(self.high, -heapq.heappop(self.low))
        elif len(self.high) > len(self.low):
            heapq.heappush(self.low, -heapq.heappop(self.high))

    def median(self):
        if len(self.low) > len(self.high):
            return -self.low[0]
        return (-self.low[0] + self.high[0]) / 2
```

Choosing the side by comparing with max(low) preserves the order invariant. If the sizes are then off by one too many, moving the top of the bigger heap across preserves it too, because that top is the largest of `low` (or the smallest of `high`), so it lands on the correct side of every value in the other heap. Each `add` is at most two pushes and one pop: O(log n) worst case.

**Worked trace** on the stream 5, 15, 1, 3, 8, 7, 9, 10:

| add | goes to | rebalance | low | high | median |
|---|---|---|---|---|---|
| 5 | low (empty) | | {5} | {} | 5 |
| 15 | high (15 > 5) | | {5} | {15} | 10 |
| 1 | low (1 ≤ 5) | | {1, 5} | {15} | 5 |
| 3 | low (3 ≤ 5) | move 5 to high | {1, 3} | {5, 15} | 4 |
| 8 | high (8 > 3) | move 5 to low | {1, 3, 5} | {8, 15} | 5 |
| 7 | high (7 > 5) | | {1, 3, 5} | {7, 8, 15} | 6 |
| 9 | high (9 > 5) | move 7 to low | {1, 3, 5, 7} | {8, 9, 15} | 7 |
| 10 | high (10 > 7) | | {1, 3, 5, 7} | {8, 9, 10, 15} | 7.5 |

The two heaps store every value, so memory is O(n). A *sliding-window* median must also delete the value that leaves the window from whichever heap holds it, which needs lazy deletion or an indexed heap (Section 9.6). For approximate quantiles of an unbounded stream in fixed memory, use a sketch such as t-digest ([Chapter 14](../volume-3/ch14-probabilistic-data-structures.md)).

### Python `heapq` idioms

`heapq` is a set of functions over a plain list, not a class, and it is a **min**-heap: `h[0]` is the smallest element. `heapify` is the O(n) bottom-up build of Section 9.3; `heappush` and `heappop` are O(log n); `heapreplace(h, x)` pops then pushes and `heappushpop(h, x)` pushes then pops, each with a single sift.

- **Max-heap:** push `-x` and read `-h[0]`. This works for numbers; for (priority, item) tuples, negate only the priority. Python 3.14 added `heappush_max`, `heappop_max`, `heapify_max` and related functions; on earlier versions, negate.
- **`heapq.nlargest(k, iterable, key=None)`** and **`nsmallest`** are the top-k pattern above, O(n log k). For k = 1, `max` and `min` are faster; for k close to n, `sorted(iterable)[:k]` is.
- **`heapq.merge(*iterables, key=None)`** is the lazy k-way merge.
- **Tie-breakers.** Tuples compare element by element, so two entries with equal priorities fall through to comparing their payloads. That fails outright for payloads without an order, and is wasted work for the rest. Put a unique, increasing counter between the priority and the payload:

```python
import heapq
import itertools

tasks, counter = [], itertools.count()

def push(task, priority):
    heapq.heappush(tasks, (priority, next(counter), task))

push({"name": "backup"}, 2)
push({"name": "email"}, 1)
push({"name": "report"}, 1)          # ties with "email" on priority
print(heapq.heappop(tasks)[2])       # {'name': 'email'}: the counter broke the tie
```

Without the counter the third push raises `TypeError: '<' not supported between instances of 'dict' and 'dict'`. The counter also makes equal priorities come out first-in, first-out, which a heap otherwise does not guarantee (heaps are not stable).

## 9.9 Binomial Heaps

Binomial heaps support efficient meld (merge) operations.

### Binomial Trees

A binomial tree B_k has:
- 2^k nodes
- Height k
- Made by linking two B_(k-1) trees

```
B_0:  ○                 (1 node)

B_1:  ○                 (2 nodes)
      │
      ○

B_2:  ○                 (4 nodes)
     /│
    ○ ○
    │
    ○

B_3:  ○                 (8 nodes)
     /│\
    ○ ○ ○
   /│ │
  ○ ○ ○
  │
  ○
```

### Binomial Heap Structure

A binomial heap is a collection of binomial trees satisfying:
- Each binomial tree is a min-heap (or max-heap)
- At most one binomial tree of each order k
- Trees are stored in a root list by increasing order

```
Binomial Heap (7 nodes):
- B_2 tree (4 nodes)
- B_1 tree (2 nodes)
- B_0 tree (1 node)

Root list, by increasing order:
B_0    B_1    B_2
 ○  →  ○  →   ○  → NULL
       │     /│
       ○    ○ ○
            │
            ○
```

Operations:
- Insert: O(1) amortized, O(log n) worst case (create new B_0, merge)
- Extract-min: O(log n) (remove min, merge remaining trees)
- Meld: O(log n)
- Decrease-key: O(log n)

## 9.10 Fibonacci Heaps

Fibonacci heaps achieve O(1) amortized insert and decrease-key, making them ideal for algorithms like Dijkstra's.

### Structure

- Roots of trees form a circular doubly-linked list
- One pointer to minimum element
- Trees are heap-ordered but not necessarily binomial
- Lazy consolidation: don't immediately consolidate after deletions

```
Fibonacci Heap:

   ○20 ←── minimum
  /│\
 ○ ○ ○
 ││││
 ○ ○ ○ ○
    ...

Actual structure varies, no fixed binomial structure
```

### Amortized Analysis

Potential function: Φ = number of trees + 2 × marked nodes

| Operation | Actual | Amortized |
|-----------|--------|-----------|
| Insert | O(1) | O(1) |
| Union | O(1) | O(1) |
| Find-min | O(1) | O(1) |
| Extract-min | O(n) | O(log n) |
| Decrease-key | O(1)* | O(1) |
| Delete | O(n) | O(log n) |

*Plus one unit per cascading cut; the potential pays for the cuts. Extract-min's actual cost is linear in the number of roots, which can be n after n inserts.

### Why "Fibonacci"?

A node of degree k roots a subtree of at least F(k+2) ≥ φ^k nodes, where F is the Fibonacci sequence and φ ≈ 1.618 is the golden ratio. That gives the name, and it means a node has at most log_φ n ≈ 1.44 log₂ n children.

## 9.11 Pairing Heaps

Pairing heaps are simpler than Fibonacci heaps with similar (often better) practical performance.

### Structure

- Multiway trees with heap ordering
- Roots linked in a list
- No balance information stored

### Operations

```python
class PairingNode:
    def __init__(self, value):
        self.value = value
        self.child = None    # leftmost child
        self.sibling = None  # next sibling to the right

def link(a, b):
    # Link two heaps; the smaller root becomes the parent
    if a is None: return b
    if b is None: return a
    if b.value < a.value:
        a, b = b, a
    b.sibling = a.child
    a.child = b
    return a

def extract_min(root):
    # Remove root, link children in pairs left to right,
    # then link the pairs together right to left
    pairs = []
    node = root.child
    while node:
        first, second = node, node.sibling
        node = second.sibling if second else None
        first.sibling = None
        if second:
            second.sibling = None
        pairs.append(link(first, second))

    result = None
    for p in reversed(pairs):
        result = link(p, result)
    return result
```

### Empirical Performance

Despite weaker theoretical guarantees (decrease-key is not known to be O(1) amortized), pairing heaps:
- Perform as well as or better than Fibonacci heaps in practice
- Are much simpler to implement
- Are cache-friendly

## 9.12 Applications of Heaps

**Sorting**: Heap sort
**Priority queues**: Task scheduling, event simulation
**Graph algorithms**: Dijkstra's (with decrease-key), Prim's
**Data compression**: Huffman coding
**Operating systems**: Timer queues, CPU scheduling
**Statistics**: Kth largest/smallest elements
**Stream processing**: Sliding window median

## 9.13 Historical Context

The heap was introduced by J.W.J. Williams in 1964 as part of heap sort. The binary heap structure was further analyzed by Floyd in 1964, who proved that heapify works in O(n) time.

Fibonacci heaps were introduced by Fredman and Tarjan in 1987, revolutionizing graph algorithms by enabling faster shortest paths.

Binomial heaps were introduced by Vuillemin in 1978, providing efficient meld operations.

Donald B. Johnson introduced d-ary heaps in 1975 for minimum spanning trees, and in 1977 used them for shortest paths in sparse graphs with d chosen from the ratio E/V. LaMarca and Ladner's 1996 study of how caches affect heaps is the standard reference for why a cache-aligned 4-ary heap beats a binary one.

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**9.1 ★ Is it a heap?** Using the index formulas of Section 9.2, decide which of these arrays are max-heaps. For any that is not, name the first index whose value is larger than its parent's.

```
(a) [50, 30, 40, 10, 20, 35, 5]
(b) [50, 40, 30, 35, 45, 10, 20]
(c) [9, 9, 8, 7, 9]
```

<details>
<summary>Solution</summary>

Check every i ≥ 1 against Parent(i) = (i − 1) / 2.

(a) **Yes.** 50 ≥ 30, 40; 30 ≥ 10, 20; 40 ≥ 35, 5.

(b) **No.** Index 4 holds 45, and its parent is index (4 − 1)/2 = 1, which holds 40. (Index 3, holding 35, is fine: 35 ≤ 40.)

(c) **Yes.** 9 ≥ 9, 8 at the root; index 1 (9) ≥ its children 7 and 9. The heap property is ≥, so equal keys are allowed anywhere.

</details>

**9.2 ★ Insert, then extract.** Start from the max-heap array in Section 9.2, `[90, 80, 70, 50, 40, 60, 30, 10, 20]`. Run `insert` with key 85, then `extract_max`. Show the array after each, and list every swap.

<details>
<summary>Solution</summary>

**Insert 85.** It goes at index 9. Its parent is index 4 (40): swap. Now at index 4, parent index 1 (80): swap. Now at index 1, parent index 0 (90): 90 ≥ 85, stop. Two swaps.

```
[90, 85, 70, 50, 80, 60, 30, 10, 20, 40]
```

**extract_max.** Returns 90. The last element, 40, moves to index 0 and n becomes 9. `heapify(arr, 9, 0)`: children are 85 (index 1) and 70 (index 2), so swap with 85. At index 1: children 50 (index 3) and 80 (index 4), so swap with 80. At index 4: children would be at 9 and 10, both ≥ n, so stop.

```
[85, 80, 70, 50, 40, 60, 30, 10, 20]
```

Both operations walk one root-to-leaf path, so each is O(log n): here at most 3 levels.

</details>

**9.3 ★★ Two ways to build a heap.** Build a max-heap from `[1, 2, 3, 4, 5, 6, 7]` in two ways: (a) with `build_heap`, showing the array after each `heapify` call; (b) by calling `insert` for 1, 2, ..., 7 in turn on an empty heap. Count the swaps in each. Are the two heaps the same?

<details>
<summary>Hint</summary>

For (a), n = 7, so the loop runs i = 2, 1, 0. Remember that `heapify` keeps sifting down after a swap.

</details>

<details>
<summary>Solution</summary>

(a) `build_heap`:

| step | array | swaps |
|---|---|---|
| start | [1, 2, 3, 4, 5, 6, 7] | |
| heapify(i = 2): 3 vs 6, 7 | [1, 2, 7, 4, 5, 6, 3] | 1 |
| heapify(i = 1): 2 vs 4, 5 | [1, 5, 7, 4, 2, 6, 3] | 1 |
| heapify(i = 0): 1 vs 5, 7, then 1 vs 6, 3 | [7, 5, 6, 4, 2, 1, 3] | 2 |

**4 swaps**, result `[7, 5, 6, 4, 2, 1, 3]`.

(b) Repeated insert. Each new key is the largest so far, so it sifts all the way to the root:

| insert | array after | swaps |
|---|---|---|
| 1 | [1] | 0 |
| 2 | [2, 1] | 1 |
| 3 | [3, 1, 2] | 1 |
| 4 | [4, 3, 2, 1] | 2 |
| 5 | [5, 4, 2, 1, 3] | 2 |
| 6 | [6, 4, 5, 1, 3, 2] | 2 |
| 7 | [7, 4, 6, 1, 3, 2, 5] | 2 |

**10 swaps**, result `[7, 4, 6, 1, 3, 2, 5]`.

Both are valid max-heaps but they are **different arrays**: a set of keys has many valid heap layouts. Sorted ascending input is the worst case for repeated insertion (every key climbs to the root, about n log n swaps in total), which is the gap between the O(n log n) and O(n) approaches in Section 9.3.

</details>

**9.4 ★★ Why `build_heap` is O(n).** Section 9.3 says "most nodes are near leaves". Make that precise. (a) For a perfect heap with n = 2^k − 1 nodes, `heapify` on a node at height h does at most h swaps. Show that the total number of swaps is at most n − log₂(n + 1), and check the value for n = 15. (b) Contrast this with building by repeated `insert`, where a node at depth d may do d swaps.

<details>
<summary>Hint</summary>

There are 2^(k−1−h) nodes at height h. Sum h × 2^(k−1−h) over h = 0, ..., k − 1.

</details>

<details>
<summary>Solution</summary>

(a) In a perfect tree with k levels there are 2^(k−1) leaves (height 0), 2^(k−2) nodes at height 1, and so on, up to 1 node (the root) at height k − 1. Each does at most h swaps, so the total is at most

S = Σ_{h=0}^{k−1} h × 2^(k−1−h) = 2^k − k − 1.

(One way to see this: the sum satisfies S(k) = 2 S(k − 1) + (k − 1), since the root contributes k − 1 and its two subtrees each contribute S(k − 1); 2^k − k − 1 satisfies the same recurrence with S(1) = 0.) Since n = 2^k − 1 and k = log₂(n + 1),

S = n − log₂(n + 1) < n.

For n = 15 (k = 4): 8 leaves × 0 + 4 × 1 + 2 × 2 + 1 × 3 = **11** = 15 − 4. Running `build_heap` on `[0, 1, ..., 14]` (ascending, so every key wants to sink as far as possible) does exactly 11 swaps.

(b) With repeated insert, the cost of a node is its *depth*, not its height. Half the nodes are at depth k − 1, so the total can reach about (n/2) × log₂ n, which is Θ(n log n). `build_heap` wins because the many nodes near the bottom are the cheap ones; repeated insert makes them the expensive ones.

</details>

**9.5 ★★ Find the bug.** This Python port of `heap_sort` returns unsorted output:

```python
def sift_down(a, n, i):
    while True:
        largest = i
        l, r = 2 * i + 1, 2 * i + 2
        if l < n and a[l] > a[largest]:
            largest = l
        if r < n and a[r] > a[largest]:
            largest = r
        if largest == i:
            return
        a[i], a[largest] = a[largest], a[i]
        i = largest

def heap_sort(a):
    n = len(a)
    for i in range(n // 2 - 1, -1, -1):
        sift_down(a, n, i)
    for end in range(n - 1, 0, -1):
        a[0], a[end] = a[end], a[0]
        sift_down(a, n, 0)
```

Trace it on `[3, 1, 2]`, find the bug, and fix it.

<details>
<summary>Solution</summary>

`[3, 1, 2]` is already a max-heap, so the build loop changes nothing.

- end = 2: swap a[0], a[2] → `[2, 1, 3]`. 3 is now in its final place. But `sift_down(a, 3, 0)` still treats index 2 as part of the heap: 2 < 3, so it swaps them back → `[3, 1, 2]`.
- end = 1: swap a[0], a[1] → `[1, 3, 2]`. `sift_down(a, 3, 0)`: largest child is 3 → `[3, 1, 2]`.

Result: `[3, 1, 2]`, unchanged and unsorted.

The bug is the size passed to `sift_down` in the second loop. After moving the maximum to `a[end]`, the heap is only `a[0:end]`; the sorted tail must be out of reach. The C version in Section 9.4 gets this right with `heapify(arr, i, 0)`. Fix:

```python
def heap_sort(a):
    n = len(a)
    for i in range(n // 2 - 1, -1, -1):
        sift_down(a, n, i)
    for end in range(n - 1, 0, -1):
        a[0], a[end] = a[end], a[0]
        sift_down(a, end, 0)      # the heap is a[0:end]
```

With the fix, `[3, 1, 2]` becomes `[1, 2, 3]`.

</details>

**9.6 ★★ Top k of a stream.** You receive n numbers one at a time and must report the k largest at the end, using O(k) memory and O(n log k) time. Implement `top_k(stream, k)` with Python's `heapq` (a min-heap). Why a min-heap, when you want the *largest* values?

<details>
<summary>Hint</summary>

Keep the best k seen so far. When a new value arrives, which of the current k is the one it would replace?

</details>

<details>
<summary>Solution</summary>

```python
import heapq

def top_k(stream, k):
    heap = []                      # min-heap holding the k largest seen so far
    for x in stream:
        if len(heap) < k:
            heapq.heappush(heap, x)
        elif x > heap[0]:          # beats the smallest of the current top k
            heapq.heapreplace(heap, x)
    return sorted(heap, reverse=True)
```

`top_k([5, 1, 9, 3, 7, 2, 8], 3)` returns `[9, 8, 7]`.

The question for each new value is "is it bigger than the *weakest* member of the current top k?", so the structure must expose the minimum of those k in O(1): a min-heap of size k. Each element costs at most one O(log k) push or replace, so the total is O(n log k) time and O(k) space. A max-heap of all n items would also work but costs O(n) memory, which a stream may not allow. This is the "Kth largest" application in Section 9.12: after the loop, `heap[0]` is the k-th largest value.

</details>

**9.7 ★★★ Binomial heap insertion is a binary counter.** (a) Because B_k has 2^k nodes and a binomial heap holds at most one tree of each order (Section 9.9), a heap with n nodes contains B_k exactly when bit k of n is 1. Which trees make up a 13-node heap? (b) Inserting creates a B_0 and then links equal-order trees until all orders are distinct. How many links does inserting into a 7-node heap cause, and what is the result? (c) Prove that n inserts into an empty binomial heap perform fewer than n links in total, so insert is O(1) amortized even though a single insert can take Θ(log n) time.

<details>
<summary>Hint</summary>

Linking two B_j trees into one B_(j+1) is a carry in binary addition. Use the number of trees as a potential, or count how often each bit can flip from 1 to 0.

</details>

<details>
<summary>Solution</summary>

(a) 13 = 1101 in binary, so the heap holds **B_3, B_2 and B_0** (8 + 4 + 1 nodes).

(b) 7 = 111: the heap holds B_0, B_1, B_2. The new B_0 links with the existing B_0 to make a B_1, which links with the existing B_1 to make a B_2, which links with the existing B_2 to make a B_3. **3 links**, and the result is a single B_3 with 8 nodes, just as 111 + 1 = 1000 has three carries.

(c) Each link combines two trees into one, so it reduces the number of trees by 1, and each insert adds 1 tree. Let T be the number of trees, which starts at 0 and is never negative. After n inserts, (trees created) − (links) = T_final ≥ 1, so links ≤ n − 1 < n.

So n inserts cost O(n) in total: **O(1) amortized** per insert. A single insert into a heap with n = 2^k − 1 nodes still does k links, which is the O(log n) worst case. Counting the links per insert for n = 0 to 15 gives 0, 1, 0, 2, 0, 1, 0, 3, 0, 1, 0, 2, 0, 1, 0, 4 (the number of trailing 1 bits of the current size), summing to 15 for 16 inserts.

</details>

**9.8 ★★ Keep the map honest.** Continue the worked trace of Section 9.6 from `heap: [D:1, B:3, C:8, E:4, A:5]`. (a) Run `pop()`, then `decrease_key('C', 2)`, and show `heap` and `pos` after each. (b) Suppose `_sift_down` swapped with a plain `h[i], h[smallest] = h[smallest], h[i]` instead of calling `_swap`. Redo the `pop()`, then call `decrease_key('A', 0)` followed by `pop()`. What comes out, and why?

<details>
<summary>Solution</summary>

(a) `pop()` first swaps index 0 with the last index, so A:5 is at the root (pos[A] = 0), then removes D. `_sift_down(0)`: A:5 against B:3 and C:8, swap with B; A is now at index 1, whose only child is index 3 (E:4), swap again. It returns `('D', 1)`:

```
heap: [B:3, E:4, C:8, A:5]     pos: A→3  B→0  C→2  E→1
```

`decrease_key('C', 2)` reads pos[C] = 2; its parent is index 0 (B:3), so one swap:

```
heap: [C:2, E:4, B:3, A:5]     pos: A→3  B→2  C→0  E→1
```

(b) The heap array after the buggy `pop()` is the same, `[B, E, C, A]`, but the two swaps inside the sift-down never touched the map, which still says A→0, B→1, C→2, E→3 (A→0 was written by the `_swap` at the start of `pop`). `decrease_key('A', 0)` reads pos[A] = 0, sets A's priority to 0 and sifts up from index 0, which does nothing. A:0 is left at index 3 below E:4 and B:3, so the heap property is broken, and the next `pop()` returns `('B', 3)` while A has priority 0. The failure surfaces far from the cause, which is why every move in an indexed heap must go through one function that updates the map.

</details>

**9.9 ★★ Choosing d for Dijkstra.** Use the cost model of Section 9.7: V · d · log_d V comparisons for the extract-mins plus E · log_d V for the decrease-keys. (a) For V = 10⁴ and E = 10⁶, evaluate it for d = 2, 4, 16 and d = E/V = 100. (b) Show that the exact minimiser satisfies d(ln d − 1) = E/V, and find it for these numbers. (c) The model counts comparisons only. Name one effect that pushes the best d in practice lower, and one that pushes it higher.

<details>
<summary>Hint</summary>

Write log_d V = ln V / ln d and minimise (V d + E) / ln d.

</details>

<details>
<summary>Solution</summary>

(a) log₂ 10⁴ ≈ 13.29, so:

| d | V · d · log_d V | E · log_d V | total |
|---|---|---|---|
| 2 | 0.27 M | 13.29 M | 13.55 M |
| 4 | 0.27 M | 6.64 M | 6.91 M |
| 16 | 0.53 M | 3.32 M | 3.85 M |
| 100 | 2.00 M | 2.00 M | 4.00 M |

At d = E/V the two terms are equal, which is what "balancing" means. The binary heap is more than 3 times worse than d = 16 or d = 100, because on a graph this dense the decrease-keys dominate and a binary heap makes them pay for 13 levels.

(b) The cost is ln V × g(d) with g(d) = (V d + E) / ln d. Then g′(d) = [V ln d − (V d + E)/d] / (ln d)², which is zero when V d ln d = V d + E, that is d(ln d − 1) = E/V. For E/V = 100 this gives d ≈ 38, with total ≈ 3.49 M. The cost curve is flat near its minimum: anything from about 16 to 100 is within 15%. So d ≈ E/V is the right order of magnitude, not the exact optimum.

(c) **Lower:** most relaxations do not improve a distance, so real runs do far fewer than E decrease-keys, which shifts weight to extract-min, where large d costs more. **Higher:** the d children of a node are contiguous, so scanning them costs about one cache miss whatever d is, up to a cache line's worth; counting misses rather than comparisons favours d up to 4 or 8.

</details>

**9.10 ★★ Find the bug: running median.** A colleague "simplifies" `RunningMedian.add` from Section 9.8 to keep the sizes balanced without any comparisons:

```python
def add(self, x):
    if len(self.low) <= len(self.high):
        heapq.heappush(self.low, -x)
    else:
        heapq.heappush(self.high, x)
```

Find a stream of three values on which `median()` is wrong, say which invariant breaks, and fix `add` while keeping it O(log n).

<details>
<summary>Solution</summary>

The balance invariant always holds, but nothing maintains the order invariant. On 1, 2, 3: 1 goes to `low`, 2 to `high`, 3 to `low`. Now low = {1, 3} and high = {2}, so `median()` returns max(low) = 3, but the median of {1, 2, 3} is 2. The order invariant max(low) ≤ min(high) is broken (3 > 2).

One fix is the original `add`. Another that needs no case analysis is to push every value through both heaps, so whatever crosses over is guaranteed to be the extreme of its side:

```python
def add(self, x):
    heapq.heappush(self.low, -x)
    heapq.heappush(self.high, -heapq.heappop(self.low))   # largest of low moves up
    if len(self.high) > len(self.low):
        heapq.heappush(self.low, -heapq.heappop(self.high))
```

After the first two lines, the value moved to `high` is the largest in `low`, so the order invariant holds. The last two lines move the smallest of `high` back when `high` has become too big, which also preserves order. That is at most three pushes and two pops, O(log n) worst case.

</details>

---

## Where this connects

- [Chapter 11: Graphs, Modeling Relationships](../volume-2/ch11-graphs-modeling-relationships.md). Dijkstra and Prim with lazy deletion, the main consumers of decrease-key
- [Chapter 19: Emerging and Specialized Structures](../volume-3/ch19-emerging-and-specialized-structures.md). Why Fibonacci heaps win on paper and lose in practice
- [Chapter 21: Algorithm Design Using Data Structures](../volume-3/ch21-algorithm-design-using-data-structures.md). The greedy algorithms that are built on this structure
