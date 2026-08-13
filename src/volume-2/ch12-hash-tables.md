# Chapter 12: Hash Tables

## 12.1 The Hash Table Idea

Hash tables provide O(1) average-case lookup by computing an index from a key via a hash function.

```
Key: "apple"
Hash function: h(key) → 3
Index 3 → Value stored

Direct addressing would need 26 slots for letters.
Hash table needs fewer slots with good hash function.
```

## 12.2 Hash Functions

A hash function maps keys to array indices.

### Requirements

1. **Deterministic**: Same key always maps to same index
2. **Uniform**: Keys distribute evenly across indices
3. **Fast**: O(1) computation

### Common Methods

**Division Method:**
```
h(k) = k mod m
```
Choose m as a prime not near a power of 2.

**Multiplication Method:**
```
h(k) = floor(m × (k × A mod 1))
```
Knuth's A = (√5 - 1)/2 ≈ 0.618

**Universal Hashing:**
```
h(k) = ((a × k + b) mod p) mod m
```
Random a, b from large prime field.

**String Hashing:**
```c
int hash_string(char *s, int m) {
    int h = 0;
    while (*s) {
        h = (h * 31 + *s) % m;
        s++;
    }
    return h;
}
```

## 12.3 Collision Resolution

<figure>
{{#include ../images/hash-collision.svg}}
<figcaption>The two collision strategies, and the tradeoff between them.</figcaption>
</figure>

When two keys hash to the same index, we need a strategy.

### Chaining

Store colliding elements in a linked list:

```
Index  ┌──────────────────────────────────┐
  0    │ NULL                             │
  1    │ [John:555] → [Mary:123] → NULL │
  2    │ NULL                             │
  3    │ [Alice:456] → NULL              │
  4    │ NULL                             │
  5    │ [Bob:789] → NULL                │
       └──────────────────────────────────┘
```

**Load factor** α = n/m (elements per bucket)
- Search: O(1 + α)
- Insert: O(1)
- Delete: O(1 + α)

### Open Addressing

Find another empty slot in the array.

**Linear Probing:**
```
h(k), h(k)+1, h(k)+2, ... (mod m)
```
Problem: Primary clustering

**Quadratic Probing:**
```
h(k), h(k)+1², h(k)+2², h(k)+3², ... (mod m)
```
Problem: Secondary clustering

**Double Hashing:**
```
h(k), h(k)+h₂(k), h(k)+2×h₂(k), ... (mod m)
```
Best clustering behavior.

## 12.4 Hash Table Operations

```python
class HashTable:
    def __init__(self, size=100):
        self.size = size
        self.table = [None] * size
        self.count = 0

    def _hash(self, key):
        return hash(key) % self.size

    def insert(self, key, value):
        index = self._hash(key)

        # Linear probing
        while self.table[index] is not None:
            if self.table[index][0] == key:
                self.table[index] = (key, value)
                return
            index = (index + 1) % self.size

        self.table[index] = (key, value)
        self.count += 1

        # Resize if load factor > 0.7
        if self.count / self.size > 0.7:
            self._resize()

    def get(self, key):
        index = self._hash(key)

        while self.table[index] is not None:
            if self.table[index][0] == key:
                return self.table[index][1]
            index = (index + 1) % self.size

        return None
```

## 12.5 Perfect Hashing

If all keys are known in advance, we can construct a hash table with no collisions.

**Two-level scheme:**
- First level: Hash to buckets
- Second level: Hash each bucket with no collisions (requires more slots)

## 12.6 Applications

**Dictionaries/Maps**:
- Python dict, Java HashMap, C++ unordered_map

**Sets**:
- Python set, Java HashSet

**Caches**:
- LRU cache with hash table + linked list

**Database indexing**:
- Hash indexes (for equality queries)

**Symbol tables**:
- Compiler symbol tables

**Counting/frequency**:
- Word frequency in text

## 12.7 Historical Context

Hash tables were invented independently by multiple researchers in the 1950s-1960s. The term "hash" comes from the idea of "hashing" (mixing up) the keys.

The division method was analyzed by Knuth. The multiplication method was popularized by Knuth in TAOCP.

---

## Where this connects

- [Chapter 14: Probabilistic Data Structures](../volume-3/ch14-probabilistic-data-structures.md) — trading exactness for a 10-100x memory reduction
- [Chapter 18: Concurrent Data Structures](../volume-3/ch18-concurrent-data-structures.md) — what it takes to make a hash table concurrent
