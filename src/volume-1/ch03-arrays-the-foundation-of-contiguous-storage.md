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

## 3.7 Performance Characteristics

| Operation | Static Array | Dynamic Array | Bit Array |
|-----------|-------------|---------------|-----------|
| Random Access | O(1) | O(1) | O(1) |
| Sequential Scan | O(n) | O(n) | O(n/word_size) |
| Insert at End | O(n) | O(1)* | O(1) |
| Insert at Position | O(n) | O(n) | O(n/word_size) |
| Delete at Position | O(n) | O(n) | O(n/word_size) |
| Memory | Fixed | 1× to 2× | 1/bit_size |
| Cache Efficiency | Excellent | Excellent | Good |

## 3.8 Real-World Applications

**Database Systems**: Column stores use columnar arrays for analytical queries
**Scientific Computing**: Dense matrix operations (BLAS, LAPACK)
**Image Processing**: Pixel arrays with convolution operations
**Signal Processing**: Sample buffers with circular buffer patterns
**Compilers**: Symbol tables using open addressing
**Networking**: Packet buffers, ring buffers in device drivers

## 3.9 Historical Context

The array concept predates electronic computers. In mathematics, matrices and vectors have been studied for centuries. The FORTRAN language (1957) introduced multi-dimensional arrays as a first-class concept, heavily influencing scientific computing.

The dynamic array (vector) concept emerged with languages supporting heap allocation. The Ada language (1983) provided array slicing; modern languages provide richer array operations.

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

---

## Where this connects

- [Chapter 4: Linked Lists—The Art of Distributed Storage](ch04-linked-lists-the-art-of-distributed-storage.md). The same sequence problem solved with pointers instead of contiguity
- [Chapter 16: External Memory and Cache-Oblivious Structures](../volume-3/ch16-external-memory-and-cache-oblivious-structures.md). Why contiguous layout beats pointer-chasing by more than the asymptotics suggest
