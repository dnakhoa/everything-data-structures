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
| Extract-min | O(n) | O(log n) |
| Decrease-key | O(1)* | O(1) |
| Delete | O(n) | O(log n) |

*Plus one unit per cascading cut; the potential pays for the cuts. Extract-min's actual cost is linear in the number of roots, which can be n after n inserts.

### Why "Fibonacci"?

A node of degree k roots a subtree of at least F(k+2) ≥ φ^k nodes, where F is the Fibonacci sequence and φ ≈ 1.618 is the golden ratio. That gives the name, and it means a node has at most log_φ n ≈ 1.44 log₂ n children.

## 9.8 Pairing Heaps

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

The question for each new value is "is it bigger than the *weakest* member of the current top k?", so the structure must expose the minimum of those k in O(1): a min-heap of size k. Each element costs at most one O(log k) push or replace, so the total is O(n log k) time and O(k) space. A max-heap of all n items would also work but costs O(n) memory, which a stream may not allow. This is the "Kth largest" application in Section 9.9: after the loop, `heap[0]` is the k-th largest value.

</details>

**9.7 ★★★ Binomial heap insertion is a binary counter.** (a) Because B_k has 2^k nodes and a binomial heap holds at most one tree of each order (Section 9.6), a heap with n nodes contains B_k exactly when bit k of n is 1. Which trees make up a 13-node heap? (b) Inserting creates a B_0 and then links equal-order trees until all orders are distinct. How many links does inserting into a 7-node heap cause, and what is the result? (c) Prove that n inserts into an empty binomial heap perform fewer than n links in total, so insert is O(1) amortized even though a single insert can take Θ(log n) time.

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

---

## Where this connects

- [Chapter 19: Emerging and Specialized Structures](../volume-3/ch19-emerging-and-specialized-structures.md). Why Fibonacci heaps win on paper and lose in practice
- [Chapter 21: Algorithm Design Using Data Structures](../volume-3/ch21-algorithm-design-using-data-structures.md). The greedy algorithms that are built on this structure
