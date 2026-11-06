# Chapter 3: Arrays—The Foundation of Contiguous Storage

## 3.1 The Array Concept

An array is a contiguous block of memory containing elements of identical type. This simplicity is its power: given the address of the first element and an index, we can compute the address of any element in constant time.

The address formula: address(arr[i]) = base_address + i × element_size

This direct addressing is why arrays provide O(1) indexed access. No traversal, no searching, the location is known.

## 3.2 One-Dimensional Arrays

The simplest array form stores elements in a single row:

```
Memory Layout for int array[5] = {10, 20, 30, 40, 50}:

Address:  0x1000  0x1004  0x1008  0x100C  0x1010
         ┌───────┬───────┬───────┬───────┬───────┐
Index:   │   0   │   1   │   2   │   3   │   4   │
         ├───────┼───────┼───────┼───────┼───────┤
Value:   │  10   │  20   │  30   │  40   │  50   │
         └───────┴───────┴───────┴───────┴───────┘
         ↑
       base_address = 0x1000
```

The power of this layout is cache prefetching. When you access arr[0], the CPU typically loads not just that element but a cache line (often 64 bytes). This means arr[1], arr[2], arr[3]... are likely already in cache. Sequential array access is extremely fast.

## 3.3 Multi-Dimensional Arrays

Multi-dimensional arrays store data in grid or higher-dimensional tensor form.

### Row-Major Order (C, C++, Python)

Elements stored row-by-row:

```
int matrix[3][4] = {
    {1, 2, 3, 4},
    {5, 6, 7, 8},
    {9, 10, 11, 12}
};

Address formula: address(matrix[i][j]) = base + (i × 4 + j) × element_size
```

### Column-Major Order (Fortran, MATLAB, R)

Elements stored column-by-column:

```
Address formula: address(matrix[i][j]) = base + (j × 3 + i) × element_size
```

### Arrays of Arrays (Jagged Arrays)

Instead of contiguous memory, each row/column is a separate array:

```cpp
vector<vector<int>> matrix(3);
for (int i = 0; i < 3; i++)
    matrix[i] = vector<int>(4);  // Each row independently allocated
```

This allows irregular shapes but loses cache locality and complicates memory management.

## 3.4 Dynamic Arrays

Fixed-size arrays require size at compile time. Dynamic arrays resize as needed.

### The Resize Strategy

When capacity is exhausted:
1. Allocate new, larger array (typically 2× current size)
2. Copy all elements to new array
3. Deallocate old array

```
Initial array (capacity 4):
┌────┬────┬────┬────┐
│ 1  │ 2  │ 3  │ 4  │
└────┴────┴────┴────┘

After inserting 5 (capacity exceeded):
┌────┬────┬────┬────┬────┬────┬────┬────┐
│ 1  │ 2  │ 3  │ 4  │ 5  │    │    │    │
└────┴────┴────┴────┴────┴────┴────┴────┘
      (old array, now freed)
```

### Amortized Analysis of Dynamic Arrays

With capacity doubling, starting from capacity 1:
- Insert 2: Copy 1 element
- Insert 3: Copy 2 elements
- Insert 5: Copy 4 elements
- Insert 9: Copy 8 elements
- ...
- Insert 2^k + 1: Copy 2^k elements

Total copies for n insertions:
1 + 2 + 4 + ... + 2^k where 2^k < n (the largest copy is smaller than n)
< 2 × 2^k (geometric series)
< 2n (since 2^k < n)

Amortized per insertion: O(2n/n) = O(1)

### Implementation in Various Languages

**C++ vector:**
```cpp
vector<int> v;
for (int i = 0; i < 1000; i++) {
    v.push_back(i);  // Amortized O(1)
}
```

**Python list:**
```python
lst = []
for i in range(1000):
    lst.append(i)  # Amortized O(1)
```

**Java ArrayList:**
```java
ArrayList<Integer> list = new ArrayList<>();
for (int i = 0; i < 1000; i++) {
    list.add(i);  // Amortized O(1)
}
```

**Go slices:**
```go
slice := make([]int, 0)
for i := 0; i < 1000; i++ {
    slice = append(slice, i)  // Amortized O(1)
}
```

## 3.5 Bit Arrays and Bitsets

When each element needs only one bit, bit arrays provide massive space savings.

### Operations on Bit Arrays

```c
// Set bit i to 1
bits[i / 8] |= (1 << (i % 8));

// Clear bit i to 0
bits[i / 8] &= ~(1 << (i % 8));

// Test bit i
if (bits[i / 8] & (1 << (i % 8))) { ... }
```

### Popular Bitset Implementations

| Language | Class/Type |
|----------|------------|
| C++ | `std::bitset<N>`, `dynamic_bitset` |
| Java | BitSet |
| Python | int (arbitrary precision bit operations) |
| C# | BitArray, BitVector32 |
| Scala | BitSet (uses Longs internally) |

### Applications of Bit Arrays

**Bloom Filters**: Multiple hash functions map elements to bits
**Sets**: Efficient set operations (union, intersection, difference)
**Sieve of Eratosthenes**: Finding primes
**Computer Graphics**: Pixel masks, sprites
**Networking**: IP packet filters, routing tables
**Database**: Bitmap indexes

### Compressed Bitmaps

A bitmap pays one bit for every value that *could* be in the set, whether or not it is. For n values from a universe of size U, that is U bits, against 32n bits for a sorted array of 32-bit integers, so the plain bitmap is smaller only when n > U/32: more than about 3% of the universe present. Bitmap indexes hit this constantly. A column of 10 million rows with 10,000 distinct values needs one 10-million-bit (1.25 MB) bitmap per value, 12.5 GB in all, to record what sorted arrays of row IDs store in 40 MB (10 million IDs, 4 bytes each). Yet bitmaps are worth keeping, because intersecting or uniting two of them is a loop of word-wide ANDs and ORs, 64 elements per instruction, and counting the result is a popcount per word. Compressed bitmaps try to keep that speed while paying space only where values actually are.

**Run-length encoding.** A sparse bitmap is mostly long runs of zero words (and clustered data also produces runs of one words). Word-aligned schemes replace each run with a single counter word and keep every other word as a literal copy, so logical operations still work a machine word at a time. WAH (Word-Aligned Hybrid) cuts the bitmap into 31-bit groups and stores each 32-bit word as either a *literal*, a flag bit plus 31 bitmap bits, or a *fill*, a flag bit, the fill value (0 or 1), and how many consecutive all-0 or all-1 groups it stands for. EWAH (Enhanced WAH) works on 64-bit words and uses a marker word meaning "k clean words of 0s (or of 1s), then m literal words". To AND two such bitmaps, walk both in step and skip a whole run at once, so the cost is proportional to the compressed sizes rather than to U. The weakness is random access: there is no way to find bit i without decoding from the start, so a single membership test is O(compressed size). Git stores its reachability bitmaps (which objects each commit can reach, in pack order) in EWAH.

**Roaring bitmaps** keep fast random access by partitioning instead of run-length encoding. For a 32-bit value x, the high 16 bits (`x >> 16`) pick a *chunk* of 65,536 consecutive values, and the low 16 bits (`x & 0xFFFF`) are stored in that chunk's *container*. The top level is a sorted array of the chunk numbers present, each paired with its container; empty chunks cost nothing. Each container chooses its own representation:

| Container | Contents | Size | Used when |
|-----------|----------|------|-----------|
| Array | sorted 16-bit low halves | 2 bytes per value | at most 4096 values |
| Bitmap | 65,536 bits | 8 KB, fixed | more than 4096 values |
| Run | sorted (start, length − 1) pairs | 4 bytes per run | the values form few runs and this is smallest |

The threshold of 4096 is where the two basic containers cost the same: 4096 values × 2 bytes = 8192 bytes = 8 KB, which is exactly a 65,536-bit bitmap. Below it the array is smaller, above it the bitmap is, so the rule simply picks the smaller one, and a container is converted when an insertion or deletion crosses the line. As a result no container uses more than 16 bits per value: an array container uses exactly 16, and a bitmap container spreads 65,536 bits over more than 4096 values. Run containers were added later for data with long runs, such as sorted columns; libraries switch a container to runs when that is smallest, typically when asked to optimize (`runOptimize()` in the Java library).

Operations follow the two levels:

- **Membership:** binary search the top level for the high half (at most 65,536 keys, so about 16 probes), then binary search an array container, test one bit in a bitmap container, or binary search the run starts. Both levels are bounded, so this is effectively O(1), and unlike EWAH no decoding from the start is needed.
- **Insertion** into an array container shifts up to 4095 entries, and the 4097th value converts it to a bitmap. That bounded shift is the price of the sorted array.
- **Intersection:** merge the two sorted top-level arrays; only chunks present in both can contribute. Then intersect container pairs. Two bitmaps: 1024 64-bit ANDs, with popcount giving the result's size, and the result becomes an array if it holds 4096 values or fewer. Array and bitmap: test each array value against the bitmap, O(size of the array), and the result is an array. Two arrays: merge them, or use galloping (exponential) search when one is much smaller. Real libraries have routines for run containers too, and use SIMD instructions for the bitmap and array cases.

The cost of an intersection therefore depends on the sizes of the containers involved, never on U, and the dense parts are processed a word at a time. Here is a model in Python, with a Python `int` standing in for the 65,536-bit bitmap:

```python
from bisect import bisect_left

ARRAY_MAX = 4096         # 4096 values x 2 bytes = 8 KB = one 65,536-bit bitmap


def runs_of(lows):
    """Sorted distinct 16-bit values -> list of (start, length - 1) runs."""
    runs = []
    for v in lows:
        if runs and runs[-1][0] + runs[-1][1] + 1 == v:
            runs[-1] = (runs[-1][0], runs[-1][1] + 1)
        else:
            runs.append((v, 0))
    return runs


def make_container(lows):
    """Pick the smallest representation for one chunk's sorted low halves."""
    runs = runs_of(lows)
    sizes = {"array": 2 * len(lows), "bitmap": 8192, "run": 4 * len(runs)}
    if len(lows) > ARRAY_MAX:
        del sizes["array"]               # an array container never passes 8 KB
    kind = min(sizes, key=sizes.get)     # ties go to the first: array, then bitmap
    if kind == "array":
        return kind, list(lows)
    if kind == "run":
        return kind, runs
    bits = 0
    for v in lows:
        bits |= 1 << v
    return kind, bits


def values(container):
    kind, data = container
    if kind == "array":
        return data
    if kind == "run":
        return [v for s, l in data for v in range(s, s + l + 1)]
    return [v for v in range(65536) if data >> v & 1]


def contains(container, low):
    kind, data = container
    if kind == "array":
        i = bisect_left(data, low)
        return i < len(data) and data[i] == low
    if kind == "bitmap":
        return data >> low & 1 == 1
    i = bisect_left(data, (low + 1, 0)) - 1      # last run starting at or before low
    return i >= 0 and low <= data[i][0] + data[i][1]


class Roaring:
    def __init__(self, xs=()):
        chunks = {}
        for x in sorted(set(xs)):
            chunks.setdefault(x >> 16, []).append(x & 0xFFFF)
        self.chunks = {hi: make_container(lows) for hi, lows in chunks.items()}

    def __contains__(self, x):
        c = self.chunks.get(x >> 16)
        return c is not None and contains(c, x & 0xFFFF)

    def __iter__(self):
        for hi in sorted(self.chunks):
            for low in values(self.chunks[hi]):
                yield hi << 16 | low

    def __and__(self, other):
        out = Roaring()
        for hi in self.chunks.keys() & other.chunks.keys():
            (ka, a), (kb, b) = self.chunks[hi], other.chunks[hi]
            if ka == kb == "bitmap":
                lows = values(("bitmap", a & b))     # 1024 word ANDs in C
            elif ka == "array":
                lows = [v for v in a if contains((kb, b), v)]
            elif kb == "array":
                lows = [v for v in b if contains((ka, a), v)]
            else:                                    # runs: decode one side
                lows = [v for v in values((ka, a)) if contains((kb, b), v)]
            if lows:
                out.chunks[hi] = make_container(lows)
        return out
```

A set with three very different chunks:

```python
s = Roaring([1, 2, 3, 1000, 50000]                         # chunk 0: 5 scattered values
            + list(range(65536 + 100, 65536 + 8100))       # chunk 1: 8000 in a row
            + list(range(2 * 65536, 3 * 65536, 3)))        # chunk 2: every third value
assert {hi: c[0] for hi, c in s.chunks.items()} == {0: "array", 1: "run", 2: "bitmap"}

evens = Roaring(range(0, 3 * 65536, 2))                    # three half-full bitmaps
both = s & evens
assert {hi: c[0] for hi, c in both.chunks.items()} == {0: "array", 1: "array", 2: "bitmap"}
assert set(both) == set(s) & set(range(0, 3 * 65536, 2))
assert 65636 in both and 65637 not in both
```

`s` holds 29,851 values. Chunk 0 becomes an array container of 10 bytes, chunk 1 a single run of 4 bytes (an array would be 16,000 bytes, a bitmap 8 KB), and chunk 2, with 21,846 values, a bitmap of 8 KB: about 8.2 KB in total. A sorted array of 32-bit integers would take 119,404 bytes, and a plain bitmap over all 32-bit values 512 MB. In the intersection with `evens` (all bitmaps), chunk 0 is array ∧ bitmap and keeps 3 values; chunk 1 is run ∧ bitmap and keeps 4000 values, few enough to fall back to an array container; chunk 2 is bitmap ∧ bitmap and keeps the 10,923 multiples of 6, so it stays a bitmap.

In its authors' benchmarks Roaring is usually faster than WAH and EWAH, and often smaller, and it has become the default compressed bitmap. Apache Lucene's `RoaringDocIdSet` (and so Elasticsearch and OpenSearch), the bitmap indexes of Apache Druid and Apache Pinot, ClickHouse's bitmap functions, and Spark's tracking of empty shuffle blocks all use it. Delta Lake and Apache Iceberg store deletion vectors, the positions of deleted rows in a data file, as 64-bit Roaring bitmaps, which apply the same high/low split one level up: the high 32 bits select an ordinary 32-bit Roaring bitmap.

## 3.6 Array Variants for Specific Purposes

### Circular Buffers

A circular buffer wraps around at the end, ideal for queues:

```
                rear           front
                 │               │
                 ▼               ▼
┌────┬────┬────┬────┬────┬────┬────┬────┐
│ 30 │ 40 │ 50 │ -- │ -- │ -- │ 10 │ 20 │
└────┴────┴────┴────┴────┴────┴────┴────┘
Queue order: 10, 20, 30, 40, 50. front is the oldest element;
rear is the next free slot, and the writes have wrapped past the end.
```

Elegant implementation using modulo arithmetic:
- `enqueue`: rear = (rear + 1) % capacity
- `dequeue`: front = (front + 1) % capacity

### Difference Arrays

Store the difference between consecutive elements:

```
Original:     [10, 20, 25, 30, 35]
Difference:   [10, 10, 5, 5, 5]

Range update [1,3) += 3:
Original becomes: [10, 23, 28, 30, 35]
Difference becomes: [10, 13, 5, 2, 5]   (diff[1] += 3, diff[3] -= 3)
```

Range updates become O(1); original array reconstruction is O(n).

### Sparse Arrays

For arrays with mostly default values:
```c
struct SparseEntry {
    int index;
    value_type value;
};
vector<SparseEntry> sparse;
```

Only non-default values stored, with index for position.

## 3.7 Searching Sorted Arrays and Array Techniques

O(1) indexing makes a handful of techniques possible that come up constantly in practice. Binary search needs random access outright: it jumps to the middle of a range. Two pointers, sliding windows and prefix sums need only sequential passes: they keep a few indices into the array, move each one in a single direction, and replace an O(n²) or O(nk) loop with an O(n) one.

### Binary Search Done Right

Binary search finds a value in a sorted array of n elements in O(log n) worst-case time by halving the range of candidate positions at every step. The idea fits in one sentence; the off-by-one details are where implementations go wrong.

The cleanest formulation does not ask "where is x?" but "where does x belong?": the first index whose element is ≥ x. That question always has an answer in 0..n (n means "after everything"), so there is no special "not found" case, and one answer serves for membership, insertion point and counting. C++ calls it `lower_bound`.

The search keeps a half-open interval [lo, hi) of positions not yet classified, with this invariant:

- every element of `a[:lo]` is < x, and
- every element of `a[hi:]` is ≥ x.

At the start lo = 0 and hi = n, both slices are empty, and the invariant holds trivially. Each step looks at one element inside [lo, hi) and moves a boundary to classify it, which keeps the invariant and strictly shrinks the interval. When lo = hi nothing is unclassified, and lo is the first index with an element ≥ x.

```python
def lower_bound(a, x):
    """First index i with a[i] >= x, or len(a) if there is none."""
    lo, hi = 0, len(a)              # invariant: a[:lo] < x <= a[hi:]
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] < x:
            lo = mid + 1            # a[mid] and everything left of it are < x
        else:
            hi = mid                # a[mid] and everything right of it are >= x
    return lo


def upper_bound(a, x):
    """First index i with a[i] > x, or len(a) if there is none."""
    lo, hi = 0, len(a)              # invariant: a[:lo] <= x < a[hi:]
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] <= x:
            lo = mid + 1
        else:
            hi = mid
    return lo
```

Every detail follows from the invariant:

- `hi = mid`, not `mid - 1`: a[mid] ≥ x, so it belongs to the "≥ x" region that starts at hi. Setting `hi = mid - 1` would claim a[mid − 1] ≥ x, which nobody checked.
- `lo < hi`, not `lo <= hi`: when lo = hi the interval is empty. With `<=` the loop would read `a[mid]` with lo = hi = n, one past the end.
- `(lo + hi) // 2` rounds down, so lo ≤ mid < hi. `a[mid]` is always in bounds, and both branches shrink the interval.

Trace on `a = [3, 8, 8, 8, 15, 21, 30]` with x = 8:

| lo | hi | mid | a[mid] | a[mid] < 8? | Action |
|----|----|-----|--------|-------------|--------|
| 0 | 7 | 3 | 8 | no | hi = 3 |
| 0 | 3 | 1 | 8 | no | hi = 1 |
| 0 | 1 | 0 | 3 | yes | lo = 1 |
| 1 | 1 | | | | return 1 |

`upper_bound(a, 8)` probes indices 3, 5, 4 and returns 4. So 8 occurs 4 − 1 = 3 times, at indices 1 to 3. For x = 10 both functions return 4: 10 is absent (`a[4]` is 15), and index 4 is where it would be inserted. Membership is `i < len(a) and a[i] == x` with `i = lower_bound(a, x)`.

**Cost.** If the interval has s elements, both branches leave at most ⌊s/2⌋, so the loop runs at most ⌈log₂(n + 1)⌉ times: 20 iterations for a million elements, 30 for a billion. That is the worst case, and the search uses O(1) extra space.

**The overflow in `(lo + hi) // 2`.** Python integers do not overflow, so the line is correct in Python. In C, C++, Java or Go with 32-bit `int` indices, `lo + hi` exceeds 2³¹ − 1 once the array has more than about 2³⁰ (1.07 billion) elements and the search moves into the upper half. The sum wraps to a negative number and `mid` becomes a negative index: Java throws `ArrayIndexOutOfBoundsException`, and C has undefined behavior. The fix is `mid = lo + (hi - lo) / 2`, which never exceeds hi, or in Java `(lo + hi) >>> 1`, which reads the wrapped sum as unsigned. In 2006 Joshua Bloch reported that `java.util.Arrays.binarySearch`, which he had written, had carried this bug for about nine years, and that the same line appears in Jon Bentley's *Programming Pearls*. It only showed up once arrays of a billion elements became practical.

**Use the library.** Python's `bisect` module provides both functions: `bisect_left(a, x)` is `lower_bound`, `bisect_right(a, x)` (also exported as `bisect`) is `upper_bound`, and since Python 3.10 both accept `key=`. `bisect.insort(a, x)` finds the position in O(log n) but then shifts elements to insert, so it is O(n) overall. C++ has `std::lower_bound`, `std::upper_bound` and `std::equal_range`. Java's `Arrays.binarySearch` returns *some* matching index, not necessarily the first, or −(insertion point) − 1 if x is absent.

### Binary Search on the Answer

Look at what `lower_bound` actually tests: the predicate "a[i] ≥ x" is false for a prefix of the indices and true for the rest. Any predicate with that shape (monotone: once true, true for every larger input) can be searched the same way, with no array at all.

```python
def first_true(lo, hi, pred):
    """Smallest v in [lo, hi) with pred(v) true, or hi if there is none.
    pred must be monotone: once true, true for every larger v."""
    while lo < hi:
        mid = (lo + hi) // 2
        if pred(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo
```

`lower_bound(a, x)` is `first_true(0, len(a), lambda i: a[i] >= x)`. The pattern pays off when an optimisation question ("what is the smallest c such that ...?") is hard to answer directly but easy to check for a given c.

Example: packages with weights `[3, 2, 2, 4, 1, 4]` must ship in order, each day's load a contiguous run, within d = 3 days. What is the smallest daily capacity that works? Checking one capacity is a greedy pass (load each day until the next package does not fit; filling a day as far as possible never hurts later days). Feasibility is monotone, because a larger capacity never needs more days. The answer lies between max(weights), below which some package fits on no day, and sum(weights), which ships everything in one day.

```python
def days_needed(weights, cap):
    """Days to ship weights, in order, if each day carries at most cap."""
    days, load = 1, 0
    for w in weights:
        if load + w > cap:
            days, load = days + 1, 0
        load += w
    return days


def min_capacity(weights, d):
    return first_true(max(weights), sum(weights) + 1,
                      lambda cap: days_needed(weights, cap) <= d)


assert min_capacity([3, 2, 2, 4, 1, 4], 3) == 6
```

| lo | hi | mid | days_needed | ≤ 3? | Action |
|----|----|-----|-------------|------|--------|
| 4 | 17 | 10 | 2 | yes | hi = 10 |
| 4 | 10 | 7 | 3 | yes | hi = 7 |
| 4 | 7 | 5 | 4 | no | lo = 6 |
| 6 | 7 | 6 | 3 | yes | hi = 6 |

The answer is 6 (days [3, 2], [2, 4], [1, 4]). With n packages of total weight S, the search costs O(n log S) in the worst case, against O(nS) for trying every capacity. `git bisect` is the same algorithm over commit history, with the predicate "this commit has the bug", which is monotone as long as the bug was introduced once and never fixed.

### Two Pointers

Given a sorted array, find two elements that sum to a target. Trying all pairs is O(n²). Instead, start one index at each end and move them toward each other:

```python
def pair_with_sum(a, target):
    """Indices i < j with a[i] + a[j] == target in sorted a, or None."""
    i, j = 0, len(a) - 1
    while i < j:
        s = a[i] + a[j]
        if s == target:
            return i, j
        if s < target:
            i += 1          # a[i] + (largest remaining) is too small: drop a[i]
        else:
            j -= 1          # (smallest remaining) + a[j] is too big: drop a[j]
    return None
```

The invariant is that any solution uses two indices in [i, j]. If a[i] + a[j] < target, then a[i] plus any remaining element is at most a[i] + a[j], still too small, so a[i] is in no solution and can be dropped. The other case is symmetric. Each iteration drops one index, so there are at most n − 1 iterations: O(n) worst case and O(1) extra space. Binary searching for target − a[i] for each i is O(n log n); a hash set is O(n) expected and does not need sorted input, but costs O(n) extra space.

Trace on `a = [1, 3, 4, 6, 9, 11]` with target 13:

| i | j | a[i] + a[j] | Action |
|---|---|-------------|--------|
| 0 | 5 | 1 + 11 = 12 | too small, i += 1 |
| 1 | 5 | 3 + 11 = 14 | too big, j −= 1 |
| 1 | 4 | 3 + 9 = 12 | too small, i += 1 |
| 2 | 4 | 4 + 9 = 13 | return (2, 4) |

The same move-the-index-that-cannot-help idea gives in-place duplicate removal from a sorted array (one read index, one write index), three-sum in O(n²) (fix one element, two-pointer the rest), and the merge step of merge sort, where one index walks each sorted input.

### Sliding Window

A window is a contiguous run `a[lo:hi]` that moves left to right. Instead of recomputing a property of each window from scratch, update it as one element enters on the right and one leaves on the left.

**Fixed size.** The largest sum of k consecutive elements costs O(nk) by summing every window, and O(n) by sliding:

```python
def max_window_sum(a, k):
    """Largest sum of k consecutive elements (1 <= k <= len(a))."""
    s = sum(a[:k])
    best = s
    for i in range(k, len(a)):
        s += a[i] - a[i - k]        # a[i] enters, a[i - k] leaves
        best = max(best, s)
    return best
```

For `[4, 2, 12, 3, 8, 1, 7]` and k = 3 the window sums are 18, 17, 23, 12, 16, so the answer is 23. Moving averages over a stream and rolling hashes (Rabin-Karp string search) are fixed windows.

**Variable size.** The shortest run whose sum is at least a target: grow the window on the right; whenever it is valid, record it and shrink it from the left for as long as it stays valid.

```python
def shortest_at_least(a, target):
    """Length of the shortest run a[lo:hi+1] with sum >= target, or 0 if none.
    Requires every a[i] >= 0."""
    best = len(a) + 1
    s = lo = 0
    for hi, x in enumerate(a):
        s += x                      # grow on the right
        while s >= target:          # shrink from the left while still valid
            best = min(best, hi - lo + 1)
            s -= a[lo]
            lo += 1
    return best if best <= len(a) else 0
```

Trace on `a = [2, 3, 1, 2, 4, 3]` with target 7:

| hi | a[hi] | Sum after adding | Valid windows recorded while shrinking |
|----|-------|------------------|----------------------------------------|
| 0 | 2 | 2 | none |
| 1 | 3 | 5 | none |
| 2 | 1 | 6 | none |
| 3 | 2 | 8 | [2, 3, 1, 2] (length 4) |
| 4 | 4 | 10 | [3, 1, 2, 4] (4), [1, 2, 4] (3) |
| 5 | 3 | 9 | [2, 4, 3] (3), [4, 3] (2) |

The answer is 2. The inner `while` can run many times in one iteration, but `lo` only moves forward, so over the whole run each element enters the window once and leaves at most once: O(n) total in the worst case, amortized O(1) per element. The precondition matters. With non-negative elements, growing a window never lowers its sum and shrinking never raises it. So the first valid window that starts at `lo` is the shortest one that starts there, and `lo` can be dropped as soon as it is recorded; and once shrinking makes the window invalid, every window ending at `hi` with a later start is invalid too, so only growing on the right can help. With negative elements that monotonicity fails and so does the method; Exercise 3.8 handles that case with prefix sums.

### Prefix Sums

Precompute p[i] = a[0] + ... + a[i − 1], with p[0] = 0. Then the sum of any range `a[l:r]` is p[r] − p[l]: O(n) to build, O(1) per query, against O(r − l) to add the range up each time.

```python
def prefix_sums(a):
    """p[i] = a[0] + ... + a[i-1], so p has len(a) + 1 entries and p[0] = 0."""
    p = [0] * (len(a) + 1)
    for i, x in enumerate(a):
        p[i + 1] = p[i] + x
    return p


def range_sum(p, l, r):
    """Sum of a[l:r] in O(1)."""
    return p[r] - p[l]
```

For `a = [10, 20, 25, 30, 35]`, p = `[0, 10, 30, 55, 85, 120]`, and the sum of `a[1:4]` is p[4] − p[1] = 85 − 10 = 75 = 20 + 25 + 30. In the standard library this is `itertools.accumulate(a, initial=0)`; NumPy has `cumsum`.

Prefix sums and the difference arrays of Section 3.6 are inverse operations, the discrete versions of integration and differentiation. The difference array of `[10, 20, 25, 30, 35]` is `[10, 10, 5, 5, 5]`, and its prefix sums give the original back (that is `rebuild` in Exercise 3.4). In the other direction, p[i + 1] − p[i] = a[i]. The two make opposite trades:

| | Range update | Range query | Use when |
|---|---|---|---|
| Prefix sums | O(n): every later p[i] changes | O(1) | The array is fixed and queried many times |
| Difference array | O(1) | O(n): rebuild first | Many updates, then one read |

When updates and queries interleave, neither works well; a Fenwick tree or segment tree ([Chapter 23](../volume-4/ch23-advanced-competitive-programming-data-structures.md)) does both in O(log n) worst case.

**Two dimensions.** Let P[i][j] be the sum of the rectangle of rows 0..i − 1 and columns 0..j − 1. Building a cell adds the element to the rectangles above and to the left, and subtracts their overlap, which was counted twice. A query uses the same inclusion-exclusion in reverse.

```python
def prefix_sums_2d(m):
    rows, cols = len(m), len(m[0])
    p = [[0] * (cols + 1) for _ in range(rows + 1)]
    for i in range(rows):
        for j in range(cols):
            p[i + 1][j + 1] = m[i][j] + p[i][j + 1] + p[i + 1][j] - p[i][j]
    return p


def rect_sum(p, r1, c1, r2, c2):
    """Sum of m[i][j] for r1 <= i < r2 and c1 <= j < c2, in O(1)."""
    return p[r2][c2] - p[r1][c2] - p[r2][c1] + p[r1][c1]
```

For the 3 × 4 `matrix` of Section 3.3 (values 1 to 12), the table P has rows `[0, 0, 0, 0, 0]`, `[0, 1, 3, 6, 10]`, `[0, 6, 14, 24, 36]`, `[0, 15, 33, 54, 78]`. The sum of rows 1 to 2 and columns 1 to 2 is P[3][3] − P[1][3] − P[3][1] + P[1][1] = 54 − 6 − 15 + 1 = 34 = 6 + 7 + 10 + 11. Building is O(rows × cols) and every rectangle query is O(1), whatever its size. Graphics calls this a summed-area table and uses it to blur an image with a box filter of any radius at constant cost per pixel; the Viola-Jones face detector calls it an integral image.

## 3.8 Performance Characteristics

| Operation | Static Array | Dynamic Array | Bit Array |
|-----------|-------------|---------------|-----------|
| Random Access | O(1) | O(1) | O(1) |
| Sequential Scan | O(n) | O(n) | O(n/word_size) |
| Insert at End | O(n) | O(1)* | O(1) |
| Insert at Position | O(n) | O(n) | O(n/word_size) |
| Delete at Position | O(n) | O(n) | O(n/word_size) |
| Memory | Fixed | 1× to 2× | 1/bit_size |
| Cache Efficiency | Excellent | Excellent | Good |

*Amortized; the append that triggers a resize is O(n) (Section 3.4).

### Why Arrays Win in Practice

The table gives a scan O(n), the same as for a linked list in Chapter 4, but the hardware does not treat the two alike. Memory moves between DRAM and the caches in 64-byte lines, so one line holds 16 four-byte ints, and scanning a million-int array (4 MB) misses at most 62,500 times, not a million. Better still, after a few sequential misses the hardware prefetcher starts requesting the following lines before the loop asks for them, so the scan runs at memory bandwidth instead of paying the DRAM latency (on the order of 100 ns) for each line. A linked list gets neither benefit: its nodes can be anywhere, and the address of the next node is unknown until the current node has arrived, so each miss waits for the previous one. [Chapter 16](../volume-3/ch16-external-memory-and-cache-oblivious-structures.md) puts the gap at 10× or more for the same O(n) loop.

Binary search (Section 3.7) sits in between. On a large array each early probe lands on a different cache line, and the prefetcher cannot guess the next one; only the last four or so probes, once the range has narrowed to 16 ints, fall inside a single line. This is why a linear scan often matches binary search on arrays of a few dozen elements, and why search structures for large data pack many keys into each cache line or disk block ([Chapter 10](ch10-multiway-search-trees-and-b-trees.md)).

## 3.9 Real-World Applications

**Database Systems**: Column stores use columnar arrays for analytical queries
**Scientific Computing**: Dense matrix operations (BLAS, LAPACK)
**Image Processing**: Pixel arrays with convolution operations
**Signal Processing**: Sample buffers with circular buffer patterns
**Compilers**: Symbol tables using open addressing
**Networking**: Packet buffers, ring buffers in device drivers

## 3.10 Historical Context

The array concept predates electronic computers. In mathematics, matrices and vectors have been studied for centuries. The FORTRAN language (1957) introduced multi-dimensional arrays as a first-class concept, heavily influencing scientific computing.

The dynamic array (vector) concept emerged with languages supporting heap allocation. The Ada language (1983) provided array slicing; modern languages provide richer array operations.

Binary search was first described by John Mauchly in the 1946 Moore School Lectures, but according to Knuth (*The Art of Computer Programming*, Vol. 3) the published versions worked only for some array lengths until D. H. Lehmer's in 1960. Getting it right stayed hard: Joshua Bloch's 2006 report of the `(low + high) / 2` overflow covered both the JDK and *Programming Pearls*. Two-dimensional prefix sums entered graphics as Franklin Crow's summed-area tables (1984) and computer vision as the integral images of Paul Viola and Michael Jones's face detector (2001).

Compressed bitmaps grew out of bitmap indexes. Gennady Antoshenkov's Byte-aligned Bitmap Code (1995) was used in Oracle; Kesheng Wu, Ekow Otoo and Arie Shoshani's WAH (journal version 2006) aligned the runs to machine words; Daniel Lemire, Owen Kaser and Kamel Aouiche's EWAH (2010) moved to 64-bit words. Roaring was introduced by Samy Chambi, Daniel Lemire, Owen Kaser and Robert Godin in 2016, and run containers were added in a follow-up paper by Lemire, Gregory Ssi-Yan-Kai and Kaser the same year.

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**3.1 ★ Row-major or column-major?** The 3 × 4 `matrix` from Section 3.3 (values 1 to 12) starts at address 0x1000, and each element is 4 bytes.

(a) What is the address of `matrix[2][1]` in row-major order? In column-major order?

(b) Which value is stored at address 0x1018 under each layout?

<details>
<summary>Solution</summary>

**(a)** Row-major: base + (i × 4 + j) × 4 = 0x1000 + (2 × 4 + 1) × 4 = 0x1000 + 36 = **0x1024**. Column-major: base + (j × 3 + i) × 4 = 0x1000 + (1 × 3 + 2) × 4 = 0x1000 + 20 = **0x1014**.

**(b)** 0x1018 − 0x1000 = 24 bytes = element offset 6.

- Row-major: offset 6 = i × 4 + j, so i = 1, j = 2: `matrix[1][2]` = **7**.
- Column-major: offset 6 = j × 3 + i, so j = 2, i = 0: `matrix[0][2]` = **3**.

Same bytes, different meaning: the layout is a convention between the writer and the reader of the memory, which is why passing a NumPy (row-major) array to a Fortran (column-major) routine needs either a transpose or a flag.

</details>

**3.2 ★ Bit array trace.** `bits` is a 2-byte array, initially all zero. Using the operations from Section 3.5, apply in order: set bit 3, set bit 10, set bit 15, clear bit 3. Give both bytes in hex after each step, and the result of testing bit 10 and bit 11 at the end.

<details>
<summary>Solution</summary>

Bit i lives in byte i / 8 at position i % 8.

| Step | Byte, position | bits[0] | bits[1] |
|------|----------------|---------|---------|
| start | | 0x00 | 0x00 |
| set 3 | byte 0, bit 3 (0x08) | 0x08 | 0x00 |
| set 10 | byte 1, bit 2 (0x04) | 0x08 | 0x04 |
| set 15 | byte 1, bit 7 (0x80) | 0x08 | 0x84 |
| clear 3 | byte 0, AND with ~0x08 | 0x00 | 0x84 |

Test bit 10: `0x84 & 0x04` = 0x04, nonzero, so **set**. Test bit 11: `0x84 & 0x08` = 0, so **clear**.

</details>

**3.3 ★★ Other growth factors.** Section 3.4 doubles the capacity. Many implementations grow by a factor of 1.5 instead (and CPython's list grows by about 1.125).

(a) For a growth factor r > 1, show that the total number of element copies over n appends is less than n · r / (r − 1). Evaluate the bound for r = 2 and r = 1.5.

(b) What do you give up by choosing a smaller r?

(c) Suppose instead the array grows by a fixed amount k (capacity k, 2k, 3k, ...). What is the total copy cost of n appends?

<details>
<summary>Hint</summary>

List the capacities at which copies happen, from the last one backwards. Each is at most 1/r of the next.

</details>

<details>
<summary>Solution</summary>

**(a)** A copy happens when the array is full, and copies every element currently stored, i.e. the current capacity. Let the capacities at which copies happened be c₁ < c₂ < ... < cₜ. The last one is less than n (an append found the array full with fewer than n elements). Each capacity is at least r times the previous one, so going backwards: cₜ < n, cₜ₋₁ ≤ cₜ / r < n / r, cₜ₋₂ < n / r², and so on. Therefore

total copies < n (1 + 1/r + 1/r² + ...) = n · 1 / (1 − 1/r) = n · r / (r − 1).

- r = 2: fewer than 2n copies, as in Section 3.4.
- r = 1.5: fewer than 3n copies.

A simulation starting from capacity 1 gets close to both bounds (about 2.0n and 3.0n at worst) without exceeding them. Either way, appends are amortized O(1).

**(b)** Smaller r means more frequent resizes and more total copying (the constant r / (r − 1) grows as r → 1), in exchange for less wasted space: right after a resize the array is only 1/r full, so doubling can leave up to half the allocation empty while 1.5 leaves at most a third empty. Factor 1.5 has a second, allocator-level advantage: the blocks freed by earlier resizes eventually add up to more than the next request, so an allocator that merges adjacent free blocks can reuse them. With factor 2 that never happens, because 1 + 2 + ... + 2^(k−1) = 2^k − 1 is always smaller than the next request of 2^(k+1).

**(c)** Copies happen at sizes k, 2k, 3k, ..., up to about n, so the total is k (1 + 2 + ... + n/k) ≈ k · (n/k)² / 2 = n² / (2k). That is Θ(n²) total and Θ(n / k) amortized per append. For n = 10,000 and k = 100, it is 495,000 copies, against fewer than 20,000 with doubling. Additive growth only looks cheaper; any constant k loses to any constant factor r > 1.

</details>

**3.4 ★★ Difference array updates.** Implement `range_add(diff, l, r, v)`, which adds v to every element of the original array in the half-open range [l, r) by editing the difference array, and `rebuild(diff)`, which recovers the original array. Then apply these three updates in order to the example in Section 3.6 (original `[10, 20, 25, 30, 35]`): [1, 3) += 3, then [0, 5) += 1, then [2, 5) −= 2. Show the difference array after each update.

<details>
<summary>Hint</summary>

Adding v to a range raises the step into position l by v and lowers the step out of position r − 1 by v. If r is the length of the array, there is no step out.

</details>

<details>
<summary>Solution</summary>

```python
def range_add(diff, l, r, v):
    """Add v to original[l:r] in O(1)."""
    diff[l] += v
    if r < len(diff):
        diff[r] -= v


def rebuild(diff):
    """Prefix sums of diff give back the original array: O(n)."""
    out, running = [], 0
    for d in diff:
        running += d
        out.append(running)
    return out


diff = [10, 10, 5, 5, 5]                 # difference array of [10, 20, 25, 30, 35]
range_add(diff, 1, 3, 3)
assert diff == [10, 13, 5, 2, 5]
range_add(diff, 0, 5, 1)
assert diff == [11, 13, 5, 2, 5]
range_add(diff, 2, 5, -2)
assert diff == [11, 13, 3, 2, 5]
assert rebuild(diff) == [11, 24, 27, 29, 34]
```

| After | Difference array | Original (rebuilt) |
|-------|------------------|--------------------|
| start | [10, 10, 5, 5, 5] | [10, 20, 25, 30, 35] |
| [1, 3) += 3 | [10, 13, 5, 2, 5] | [10, 23, 28, 30, 35] |
| [0, 5) += 1 | [11, 13, 5, 2, 5] | [11, 24, 29, 31, 36] |
| [2, 5) −= 2 | [11, 13, 3, 2, 5] | [11, 24, 27, 29, 34] |

The second and third updates run to the end of the array, so they only touch `diff[l]`. Check the last row by hand: 34 = 35 + 1 − 2, and 24 = 20 + 3 + 1.

</details>

**3.5 ★★ Find the bug.** This function is supposed to return 1 if bit i is set and 0 otherwise. It compiles (with a warning that is easy to ignore) and passes a test that only checks bit 0.

```c
int is_set(const unsigned char *bits, int i) {
    return bits[i / 8] & 1 << i % 8 != 0;
}
```

What does it actually compute? Give inputs where it is wrong, and fix it.

<details>
<summary>Hint</summary>

In C, `!=` binds more tightly than `&`.

</details>

<details>
<summary>Solution</summary>

C precedence, from tightest: `%` then `<<` then `!=` then `&`. So the expression parses as

```c
bits[i / 8] & ((1 << (i % 8)) != 0)
```

`(1 << (i % 8)) != 0` is always 1, so the function returns `bits[i / 8] & 1`: **bit 0 of whichever byte holds bit i**, no matter which bit was asked for.

With `bits = {0x01, 0x04}` (bits 0 and 10 set), `is_set(bits, 3)` returns 1 (wrong, bit 3 is clear) and `is_set(bits, 10)` returns 0 (wrong, bit 10 is set). Any test that only probes bits 0, 8, 16, ... passes.

Fix with explicit parentheses, as in Section 3.5:

```c
int is_set(const unsigned char *bits, int i) {
    return (bits[i / 8] & (1 << (i % 8))) != 0;
}
```

The warning `gcc -Wall` prints here ("suggest parentheses around comparison in operand of '&'") points at exactly this line. Bit manipulation is where operator precedence bites most often, because `&`, `|` and `^` sit below the comparison operators, against most people's intuition.

</details>

**3.6 ★★★ Appends with no slow ones.** Doubling gives amortized O(1) appends, but one append in a while copies the whole array. A real-time system (an audio callback, a game frame) cannot afford that single O(n) append. Design a dynamic array whose append does O(1) work in the worst case, while indexing stays O(1). Assume allocating an uninitialized array takes O(1) time.

<details>
<summary>Hint</summary>

When the array of capacity m fills, allocate the 2m array but don't copy yet. Move a couple of old elements on each subsequent append, and make sure the move finishes before the new array fills.

</details>

<details>
<summary>Solution</summary>

Keep two arrays during a migration: `old` (capacity m, full) and `new` (capacity 2m). New elements go straight into `new` at their final index. Each append also copies 2 elements from `old` to `new`. Copying m elements at 2 per append takes m/2 appends, and by then `new` holds m + m/2 < 2m elements, so the migration always finishes before `new` is full and the next migration is needed. Indexing checks which array currently holds position i.

```python
class IncrementalArray:
    """Dynamic array whose append does O(1) work in the worst case."""

    def __init__(self):
        self.new = [None] * 2   # array that receives appends
        self.old = None         # array being drained, or None
        self.moved = 0          # old[0:moved] already copied into new
        self.n = 0

    def append(self, x):
        if self.old is None and self.n == len(self.new):
            # Start a migration. (Python's [None] * k is not O(1);
            # in C this would be an uninitialized malloc.)
            self.old, self.new, self.moved = self.new, [None] * (2 * self.n), 0
        self.new[self.n] = x
        self.n += 1
        if self.old is not None:
            for _ in range(2):                  # copy two old elements per append
                if self.moved < len(self.old):
                    self.new[self.moved] = self.old[self.moved]
                    self.moved += 1
            if self.moved == len(self.old):
                self.old = None                 # migration finished

    def __getitem__(self, i):
        if not 0 <= i < self.n:
            raise IndexError(i)
        if self.old is not None and self.moved <= i < len(self.old):
            return self.old[i]                  # not copied yet
        return self.new[i]

    def __len__(self):
        return self.n


a = IncrementalArray()
for k in range(2000):
    a.append(k)
    assert a.old is None or a.n < len(a.new)   # migration ends before new fills
assert [a[i] for i in range(len(a))] == list(range(2000))
```

The tradeoff: every append now does a little more work (up to 3 writes instead of 1), indexing has an extra branch, and during a migration both arrays are live, so peak memory is 3m instead of 2m. Total work is the same Θ(n) as plain doubling; the technique only moves the cost so that no single operation pays for it. This is called deamortization, and the same move-a-little-each-time idea shows up in incremental hash table resizing (Redis does it) and in incremental garbage collectors.

</details>

**3.7 ★ Find the bug.** This binary search returns the index of x in the sorted list a, or −1. It passes `search([1, 3, 5], 3)` and `search([1, 3, 5], 0)`. Find an input where it fails, explain the failure using the invariant from Section 3.7, and fix it.

```python
def search(a, x):
    lo, hi = 0, len(a)
    while lo <= hi:
        mid = (lo + hi) // 2
        if a[mid] == x:
            return mid
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
```

<details>
<summary>Hint</summary>

Decide what `hi` means: the last candidate index, or one past it. Then check whether each line agrees.

</details>

<details>
<summary>Solution</summary>

The function mixes two conventions. `hi = len(a)` sets up a half-open interval [lo, hi), where hi is one past the last candidate. But `lo <= hi` and `hi = mid - 1` belong to a closed interval [lo, hi], where hi itself is a candidate. Under the closed reading the initial interval includes index len(a), which does not exist.

`search([1, 3, 5], 7)`: lo = 0, hi = 3, mid = 1, 3 < 7 so lo = 2; mid = 2, 5 < 7 so lo = 3; now lo = hi = 3, the loop runs again, and `a[3]` raises `IndexError`. `search([], 1)` fails the same way on its first probe. Any x larger than every element triggers it; the passing tests never searched past the end.

Either convention works if used consistently. Closed: start with `hi = len(a) - 1` and keep the rest. Half-open, matching `lower_bound`:

```python
def search(a, x):
    lo, hi = 0, len(a)              # x, if present, is in a[lo:hi]
    while lo < hi:
        mid = (lo + hi) // 2
        if a[mid] == x:
            return mid
        if a[mid] < x:
            lo = mid + 1
        else:
            hi = mid                # a[mid] > x: exclude mid, keep [lo, mid)
    return -1


assert search([1, 3, 5], 7) == -1 and search([], 1) == -1
assert [search([1, 3, 5], x) for x in range(7)] == [-1, 0, -1, 1, -1, 2, -1]
```

Note that with duplicates this returns *some* index of x, like Java's `Arrays.binarySearch`. Use `lower_bound` when you need the first.

</details>

**3.8 ★★ Subarray sums with negative numbers.** Count the contiguous runs `a[l:r]` (with l < r) whose sum is exactly k. Explain why the variable-size sliding window of Section 3.7 cannot do this when a has negative elements, then give an O(n) expected-time algorithm, and run it on `a = [3, 4, -7, 1, 3, 3, 1, -4]` with k = 7.

<details>
<summary>Hint</summary>

The sum of `a[l:r]` is p[r] − p[l]. For each r, how many earlier l have p[l] = p[r] − k?

</details>

<details>
<summary>Solution</summary>

The window method shrinks from the left as soon as the sum is large enough, and grows on the right while it is too small. That is only correct if adding an element never lowers the sum and removing one never raises it. Here `[3, 4]` already sums to 7, yet `[3, 4, -7, 1, 3, 3]` also sums to 7: extending a window past a negative element can bring the sum back down and up again, so no decision about lo or hi is final.

Prefix sums turn the question into counting pairs: `a[l:r]` sums to k exactly when p[l] = p[r] − k. Scan r from left to right, keeping a hash map from each prefix sum seen so far to how many times it occurred:

```python
from collections import Counter


def count_subarrays_with_sum(a, k):
    seen = Counter({0: 1})          # prefix sums so far; p[0] = 0
    p = count = 0
    for x in a:
        p += x
        count += seen[p - k]        # each earlier p[l] == p - k is one run a[l:r]
        seen[p] += 1
    return count


assert count_subarrays_with_sum([3, 4, -7, 1, 3, 3, 1, -4], 7) == 4
```

The prefix sums are p = `[0, 3, 7, 0, 1, 4, 7, 8, 4]`. Matches: p[2] = 7 pairs with p[0] = 0 (`[3, 4]`); p[6] = 7 pairs with p[0] and with p[3] = 0 (`[3, 4, -7, 1, 3, 3]` and `[1, 3, 3]`); p[7] = 8 pairs with p[4] = 1 (`[3, 3, 1]`). That is **4** runs, which a brute-force check over all 36 runs confirms. Each step is one hash lookup and one update, so the whole scan is O(n) expected time and O(n) extra space, against O(n²) for checking every run with prefix sums and O(n³) without them.

</details>

**3.9 ★★ Integer square root.** Using `first_true` from Section 3.7, write `isqrt(n)`, the largest integer v with v² ≤ n, for any n ≥ 0. Trace it for n = 40. How many iterations does it take for n = 10¹⁸, and what changes if you port it to C with 64-bit integers?

<details>
<summary>Solution</summary>

"v² > n" is monotone in v, so the answer is one less than the first v for which it is true. That first v is at most n + 1 (for n ≥ 2 it is at most n, since n² > n; for n = 0 and n = 1 it is 1 and 2), so searching [0, n + 1) is safe: if nothing in range is true, `first_true` returns hi = n + 1, which is then the right first v.

```python
import math


def first_true(lo, hi, pred):
    while lo < hi:
        mid = (lo + hi) // 2
        if pred(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


def isqrt(n):
    """Largest v with v * v <= n, for n >= 0."""
    return first_true(0, n + 1, lambda v: v * v > n) - 1


assert [isqrt(n) for n in range(10)] == [0, 1, 1, 1, 2, 2, 2, 2, 2, 3]
assert all(isqrt(n) == math.isqrt(n) for n in range(10_000))
assert isqrt(10**18) == 10**9
```

Trace for n = 40:

| lo | hi | mid | mid² | > 40? |
|----|----|-----|------|-------|
| 0 | 41 | 20 | 400 | yes, hi = 20 |
| 0 | 20 | 10 | 100 | yes, hi = 10 |
| 0 | 10 | 5 | 25 | no, lo = 6 |
| 6 | 10 | 8 | 64 | yes, hi = 8 |
| 6 | 8 | 7 | 49 | yes, hi = 7 |
| 6 | 7 | 6 | 36 | no, lo = 7 |

`first_true` returns 7, so isqrt(40) = 6.

For n = 10¹⁸ the interval starts with 10¹⁸ + 1 values, so at most ⌈log₂(10¹⁸ + 2)⌉ = 60 iterations. Starting from hi = 2³², which is enough for any 64-bit n, would cut that to at most 33.

In C, two lines overflow. `mid * mid` exceeds 2⁶³ − 1 once mid > about 3.04 × 10⁹, which happens on the first probe for n = 10¹⁸ (mid = 5 × 10¹⁷); test `mid > n / mid` instead, which is equivalent for integer division and cannot overflow (mid is 0 only when n = 0, so handle that case first). And `lo + hi` can overflow for n near 2⁶³, so use `lo + (hi - lo) / 2`, as in Section 3.7. Python avoids both because its integers are unbounded, at the cost of arbitrary-precision arithmetic on every step.

</details>

**3.10 ★ Choosing containers.** Using the Roaring rules of Section 3.5, give the chunks, the container type of each, and the total container size for each set below. Compare with a sorted array of 32-bit integers.

(a) The 5000 even numbers 0, 2, 4, ..., 9998.

(b) The 100,000 consecutive values 0, 1, ..., 99,999.

(c) The 1000 values 0, 65,536, 2 × 65,536, ..., 999 × 65,536.

<details>
<summary>Solution</summary>

**(a)** All values are below 65,536, so there is one chunk (high half 0) with 5000 values. That is more than 4096, so an array container is ruled out (it would need 10,000 bytes, more than a bitmap). No two values are consecutive, so a run container needs 5000 runs, 20,000 bytes. The bitmap container wins at **8192 bytes**, about 13 bits per value, against 20,000 bytes for the sorted array.

**(b)** Two chunks. Chunk 0 is full (0 to 65,535): one run, 4 bytes, against 8192 for a bitmap. Chunk 1 holds 65,536 to 99,999, low halves 0 to 34,463: again one run, 4 bytes. Total **8 bytes** of containers, against 400,000 bytes for the array. A plain bitmap or an array container could not get close; this is what run containers are for.

**(c)** 1000 chunks, each holding a single value with low half 0, so 1000 array containers of 2 bytes each. The containers total only 2000 bytes, but every chunk also needs its 2-byte key in the top level, plus a pointer (in memory) or an offset and a cardinality (on disk). That is already 4 bytes per value (2 for the key, 2 for the container) before counting any pointer, offset or cardinality, as much as the 4000-byte sorted array, so here Roaring **loses**. Its 16-bits-per-value guarantee holds inside containers; when every chunk holds one value, the top level dominates.

```python
r = Roaring(range(0, 10000, 2))
assert [c[0] for c in r.chunks.values()] == ["bitmap"]
r = Roaring(range(100000))
assert {hi: c for hi, c in r.chunks.items()} == {0: ("run", [(0, 65535)]),
                                                 1: ("run", [(0, 34463)])}
r = Roaring(x * 65536 for x in range(1000))
assert len(r.chunks) == 1000 and all(c == ("array", [0]) for c in r.chunks.values())
```

</details>

**3.11 ★★ Roaring on random data.** n distinct 32-bit integers are drawn uniformly at random. Estimate the size of a Roaring bitmap for n = 10⁶ and for n = 10⁹, and compare each with a sorted array of 32-bit integers and with a plain bitmap of 2³² bits. Count 8 bytes of overhead per container, as Roaring's standard serialized format does (a 2-byte key, a 2-byte cardinality and a 4-byte offset). At what n do the containers switch from arrays to bitmaps?

<details>
<summary>Hint</summary>

There are 65,536 chunks, and with uniform data each gets about n / 65,536 values.

</details>

<details>
<summary>Solution</summary>

**n = 10⁶.** Each chunk gets about 10⁶ / 65,536 ≈ 15 values, so practically every chunk is non-empty (the chance that one is empty is about e⁻¹⁵) and every container is an array. Containers: 10⁶ × 2 bytes = 2 MB. Overhead: 65,536 × 8 bytes = 512 KB. Total about **2.5 MB**, against 4 MB for the sorted array and 512 MB for the plain bitmap. Random data has no runs and no dense regions, so the saving over the sorted array comes only from not repeating the high half, which every value in a chunk shares.

**n = 10⁹.** Each chunk gets about 15,259 values, more than 4096, so every container is an 8 KB bitmap: 65,536 × 8 KB = **512 MB** plus 512 KB of overhead, the same as the plain bitmap (which is the right representation at this density), against 4 GB for the sorted array.

**The switch** happens when a chunk's expected count crosses 4096, a density of 4096 / 65,536 = 1/16, so at about n = 2³² / 16 ≈ 2.7 × 10⁸. Below that Roaring costs about 16 bits per value plus overhead; above it, a fixed 512 MB. Either way it is never far from the better of the sorted array and the plain bitmap, which is the point of choosing the container per chunk.

</details>

---

## Where this connects

- [Chapter 4: Linked Lists—The Art of Distributed Storage](ch04-linked-lists-the-art-of-distributed-storage.md). The same sequence problem solved with pointers instead of contiguity
- [Chapter 16: External Memory and Cache-Oblivious Structures](../volume-3/ch16-external-memory-and-cache-oblivious-structures.md). Why contiguous layout beats pointer-chasing by more than the asymptotics suggest
