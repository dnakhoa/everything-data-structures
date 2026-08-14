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

With capacity doubling:
- Insert 1: Copy 1 element
- Insert 2: Copy 2 elements
- Insert 4: Copy 4 elements
- Insert 8: Copy 8 elements
- ...
- Insert 2^k: Copy 2^k elements

Total copies for n insertions:
1 + 2 + 4 + ... + 2^k where 2^k ≥ n
≤ 2 × 2^k (geometric series)
≤ 2n (since 2^k ≤ 2n)

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
     front                     rear
       │                        │
       ▼                        ▼
┌────┬────┬────┬────┬────┬────┬────┬────┐
│ 30 │ 40 │ 50 │ -- │ -- │ -- │ 10 │ 20 │
└────┴────┴────┴────┴────┴────┴────┴────┘
                ▲                        ▲
              empty                    full
             slots                    slots
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
Original becomes: [10, 23, 28, 33, 35]
Difference becomes: [10, 13, 5, 5, 5]
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

The dynamic array (vector) concept emerged with languages supporting heap allocation. The Ada language (1983) provided array slicing; modern languages provide richer array operations. The Ruby language introduced the "push" and "pop" terminology that spread to Python and JavaScript.

---

## Where this connects

- [Chapter 4: Linked Lists—The Art of Distributed Storage](ch04-linked-lists-the-art-of-distributed-storage.md). The same sequence problem solved with pointers instead of contiguity
- [Chapter 16: External Memory and Cache-Oblivious Structures](../volume-3/ch16-external-memory-and-cache-oblivious-structures.md). Why contiguous layout beats pointer-chasing by more than the asymptotics suggest
