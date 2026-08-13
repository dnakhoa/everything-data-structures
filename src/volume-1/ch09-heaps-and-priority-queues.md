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
Heapify at index 1 (value 80):
Before:                After:
       90                    90
      /  \                  /  \
    [80]  70      →        50    70
    /  \                /  \
  50   40              80   40
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

Properties:
- In-place: O(1) extra space
- Not stable (equal elements may change relative order)
- O(n log n) worst case
- Good for embedded systems (no recursion, predictable)

## 9.5 Priority Queue Implementation

Heaps implement priority queues efficiently:

```python
class PriorityQueue:
    def __init__(self):
        self.heap = []

    def push(self, item, priority):
        self.heap.append((priority, item))
        self._sift_up(len(self.heap) - 1)

    def pop(self):
        if not self.heap:
            return None
        max_item = self.heap[0][1]
        last = self.heap.pop()
        if self.heap:
            self.heap[0] = last
            self._sift_down(0)
        return max_item

    def peek(self):
        return self.heap[0][1] if self.heap else None
```

## 9.6 Binomial Heaps

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
     /│\
    ○ ○ ○

B_3:  ○                 (8 nodes)
     /│\
    ○ ○ ○
   /│││\
  ○○○○○○○
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

Root list:
○4 → ○2 → ○1 → NULL
 │     │
 └─○───┘   └─○─→ NULL
```

Operations:
- Insert: O(1) (create new B_0, merge)
- Extract-min: O(log n) (remove min, merge remaining trees)
- Meld: O(log n)
- Decrease-key: O(log n)

## 9.7 Fibonacci Heaps

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
| Extract-min | O(log n) | O(log n) |
| Decrease-key | O(1)* | O(1) |
| Delete | O(log n) | O(log n) |

*The degree bound ensures actual cost is bounded

### Why "Fibonacci"?

The degree of any node is bounded by about φ × n (golden ratio), leading to the name. Each node can have at most O(log n) children.

## 9.8 Pairing Heaps

Pairing heaps are simpler than Fibonacci heaps with similar (often better) practical performance.

### Structure

- Multiway trees with heap ordering
- Roots linked in a list
- No balance information stored

### Operations

```python
def link(pq1, pq2):
    # Link two heaps, return larger root
    if pq1.value < pq2.value:
        pq2.left = pq1.left
        pq1.left = pq2
        return pq1
    else:
        pq1.left = pq2.left
        pq2.left = pq1
        return pq2

def extract_min(pq):
    # Remove root, merge children two-by-two
    children = pq.children  # linked list
    pairs = []
    while children:
        pair = children
        children = children.next
        if children:
            pair.next = children.next
            children = children.next
        pairs.append(link(pair[0], pair[1]))

    result = None
    for p in pairs:
        result = link(result, p) if result else p
    return result
```

### Empirical Performance

Despite lack of theoretical guarantees, pairing heaps:
- Perform as well as or better than Fibonacci heaps in practice
- Are much simpler to implement
- Are cache-friendly

## 9.9 Applications of Heaps

**Sorting**: Heap sort
**Priority queues**: Task scheduling, event simulation
**Graph algorithms**: Dijkstra's (with decrease-key), Prim's
**Data compression**: Huffman coding
**Operating systems**: Memory allocation, CPU scheduling
**Statistics**: Kth largest/smallest elements
**Stream processing**: Sliding window median

## 9.10 Historical Context

The heap was introduced by J.W.J. Williams in 1964 as part of heap sort. The binary heap structure was further analyzed by Floyd in 1964, who proved that heapify works in O(n) time.

Fibonacci heaps were introduced by Fredman and Tarjan in 1987, revolutionizing graph algorithms by enabling faster shortest paths.

Binomial heaps were introduced by Vuillemin in 1978, providing efficient meld operations.

---

## Where this connects

- [Chapter 19: Emerging and Specialized Structures](../volume-3/ch19-emerging-and-specialized-structures.md) — why Fibonacci heaps win on paper and lose in practice
- [Chapter 21: Algorithm Design Using Data Structures](../volume-3/ch21-algorithm-design-using-data-structures.md) — the greedy algorithms that are built on this structure
