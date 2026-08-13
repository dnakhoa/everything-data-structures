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

The idea is best understood as a compromise between two extremes. **Direct addressing** — one array slot per possible key — gives genuine O(1) access but needs an array the size of the key space, which for 64-bit integers or arbitrary strings is impossible. **A sorted array** needs only n slots but costs O(log n) per lookup.

A hash table takes the array indexing of the first and the space of the second, and pays for it with **collisions**: squeezing a large key space into m slots guarantees that different keys sometimes land on the same one. Everything difficult about hash tables follows from that single consequence.

Worth being precise about the guarantee, since "O(1) lookup" is repeated so often it stops being examined. It is O(1) *average case*, under the assumption that keys distribute uniformly. The worst case is O(n) — every key colliding — and that worst case is reachable by an adversary who knows your hash function. This is not hypothetical: collision-flooding denial of service against PHP, Java, Python, and Ruby web frameworks was demonstrated in 2011 and forced all of them to change their hashing.

## 12.2 Hash Functions

A hash function maps keys to array indices.

### Requirements

1. **Deterministic**: Same key always maps to same index
2. **Uniform**: Keys distribute evenly across indices
3. **Fast**: O(1) computation

A fourth requirement belongs on that list for anything handling untrusted input: **unpredictable**. An attacker who can compute your hash function offline can generate thousands of keys that all collide, turning every operation into a linear scan. Uniformity over *random* input is not the same as uniformity over *chosen* input.

There is also a subtle correctness requirement that causes real bugs: **equal keys must hash equally**. In languages where you can override both equality and hashing, overriding one without the other produces a container that loses entries — the key is there, but the lookup goes to the wrong bucket. This is the single most common hash-table bug in application code.

### Common Methods

**Division Method:**
```
h(k) = k mod m
```
Choose m as a prime not near a power of 2.

The reason for the prime matters. If m is a power of two, `k mod m` keeps only the low bits of k and discards everything else — so keys differing only in their high bits all collide. Pointers and aligned addresses have predictable low bits, which is exactly the case where this fails badly. A prime m mixes all the bits of k into the result.

Implementations that *do* want a power-of-two table size (because masking is faster than division) must therefore mix the bits first — Java's `HashMap` XORs the high 16 bits into the low 16 before masking, precisely for this reason.

**Multiplication Method:**
```
h(k) = floor(m × (k × A mod 1))
```
Knuth's A = (√5 - 1)/2 ≈ 0.618

The value of A is the reciprocal of the golden ratio, and it is chosen because it is the irrational number *hardest to approximate with a fraction* — which means successive multiples spread across the interval as evenly as possible rather than clustering. Unlike the division method, this works with any m, including powers of two.

**Universal Hashing:**
```
h(k) = ((a × k + b) mod p) mod m
```
Random a, b from large prime field.

This is the principled defense against adversarial input, and the guarantee is stronger than it looks: for *any* two distinct keys, the probability of collision over a random choice of (a, b) is at most 1/m. No fixed input is bad, because the function is not fixed until runtime. Carter and Wegman's 1979 result is the reason modern languages seed their hash functions randomly at process start.

**String Hashing:**
```c
/* Signed overflow is undefined behaviour in C, and a negative
   intermediate makes `% m` negative — an out-of-bounds index.
   Use unsigned, and mask or mod only at the end. */
unsigned long hash_string(const char *s, unsigned long m) {
    unsigned long h = 5381;
    while (*s) {
        h = h * 33 + (unsigned char)*s;   /* djb2; wraps harmlessly */
        s++;
    }
    return h % m;
}
```

The original version of this function used `int` and applied `% m` inside the loop. Both are bugs: signed overflow is undefined behaviour, and a negative `h` yields a negative index in C. Hash arithmetic should always be done in unsigned types.

**What production code actually uses.** The classic multiply-and-add hashes (djb2, FNV, the `h*31` in Java's `String.hashCode`) are fine for well-behaved keys and weak against chosen ones. Modern defaults:

| Hash | Used by | Property |
|------|---------|----------|
| SipHash-1-3 | Rust, Python, Perl | Keyed, resists collision attacks |
| xxHash / wyhash | Databases, caches | Very fast, not attack-resistant |
| MurmurHash3 | Cassandra, Elasticsearch | Good distribution, fast, not keyed |
| CityHash / FarmHash | Google | Fast on long keys |

Choose by threat model: keyed hashes for anything reachable by user input, fast unkeyed hashes for internal maps with trusted keys. Rust makes this explicit — the default `HashMap` uses SipHash, and swapping in `FxHashMap` for internal use is often a 2× speedup.

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

Because chains can grow without bound, α may exceed 1 — a chained table never "fills up", it just degrades. Deletion is straightforward, which is chaining's main advantage over the alternative.

Java's `HashMap` adds a refinement worth knowing: once a chain exceeds 8 entries it converts to a red-black tree, capping the worst case at O(log n) instead of O(n). That single change neutralises collision-flooding attacks without requiring a keyed hash.

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

The clustering problems are worth distinguishing. **Primary clustering** is the serious one: with linear probing, any run of occupied slots grows at both ends, and longer runs are more likely to be extended — so clusters feed on themselves and probe sequences lengthen non-linearly. **Secondary clustering** is milder: keys with the same initial hash follow identical probe sequences, but keys with different hashes do not interfere.

Despite the theory favouring double hashing, **linear probing usually wins in practice** below about 70% load, because its probe sequence is sequential memory access — the next slot is almost always in the same cache line already fetched. Double hashing jumps randomly through the table and misses cache on nearly every probe. This is [Chapter 16](../volume-3/ch16-external-memory-and-cache-oblivious-structures.md)'s lesson applied: an algorithm with more operations can be faster if the operations are cheaper.

Two constraints specific to open addressing. **Load factor must stay below 1**, and performance collapses as it approaches — at α = 0.9 linear probing averages about 50 probes per unsuccessful search, versus about 2.5 at α = 0.5. Resize at 0.7 or below.

And **deletion requires tombstones**. Simply clearing a slot breaks the probe chain for any key that probed past it, making entries unreachable. The slot must be marked "deleted but occupied" instead — and tombstones accumulate, eventually requiring a rehash to clear.

## 12.4 Hash Table Operations

A complete open-addressing table, with the resize and tombstone handling that the sketch version omits:

```python
_EMPTY = object()      # never written
_DELETED = object()    # tombstone: probe past it, but reuse on insert

class HashTable:
    def __init__(self, capacity=16):
        self._keys = [_EMPTY] * capacity
        self._values = [None] * capacity
        self._count = 0            # live entries
        self._used = 0             # live entries + tombstones

    def _probe(self, key):
        """Yield indices in probe order. Linear probing: cache-friendly."""
        i = hash(key) % len(self._keys)
        for _ in range(len(self._keys)):
            yield i
            i = (i + 1) % len(self._keys)

    def __setitem__(self, key, value):
        first_tombstone = None
        for i in self._probe(key):
            k = self._keys[i]
            if k is _EMPTY:
                # Reuse an earlier tombstone if we passed one.
                slot = first_tombstone if first_tombstone is not None else i
                if first_tombstone is None:
                    self._used += 1
                self._keys[slot], self._values[slot] = key, value
                self._count += 1
                break
            if k is _DELETED:
                if first_tombstone is None:
                    first_tombstone = i
            elif k == key:
                self._values[i] = value        # overwrite, no count change
                return
        # Resize on *used*, not count — tombstones lengthen probes too.
        if self._used > len(self._keys) * 0.7:
            self._resize(len(self._keys) * 2)

    def __getitem__(self, key):
        for i in self._probe(key):
            k = self._keys[i]
            if k is _EMPTY:
                raise KeyError(key)            # probe chain ended
            if k is not _DELETED and k == key:
                return self._values[i]
        raise KeyError(key)

    def __delitem__(self, key):
        for i in self._probe(key):
            k = self._keys[i]
            if k is _EMPTY:
                raise KeyError(key)
            if k is not _DELETED and k == key:
                self._keys[i] = _DELETED       # tombstone, not _EMPTY
                self._values[i] = None
                self._count -= 1
                return
        raise KeyError(key)

    def _resize(self, new_capacity):
        """Every key must be rehashed — indices depend on table size."""
        old = [(k, v) for k, v in zip(self._keys, self._values)
               if k is not _EMPTY and k is not _DELETED]
        self._keys = [_EMPTY] * new_capacity
        self._values = [None] * new_capacity
        self._count = self._used = 0
        for k, v in old:
            self[k] = v                        # tombstones dropped here
```

Four details in that code are the ones people get wrong:

- **`_EMPTY` terminates a probe chain; `_DELETED` does not.** Confusing the two makes entries unreachable after a deletion.
- **Resize triggers on `_used`, not `_count`.** A table churning through insertions and deletions can be mostly tombstones with few live entries; if you only watch the live count, probe sequences grow without ever triggering a rehash.
- **Insertion reuses the first tombstone it passed**, rather than the empty slot at the end — otherwise the table fills with tombstones even when entries are being replaced.
- **Resizing rehashes everything.** Indices are computed modulo the table size, so nothing carries over. This makes a single insertion O(n) occasionally, which is why the bound is amortized O(1) — the same argument as the dynamic array in [Chapter 3](../volume-1/ch03-arrays-the-foundation-of-contiguous-storage.md).

That last point has a consequence for latency-sensitive systems: a hash table's *average* insert is O(1), but one insert in every n takes O(n). If tail latency matters, either pre-size the table or use an incremental-resize scheme that migrates a few entries per operation, as Redis does.

## 12.5 Perfect Hashing

If all keys are known in advance, we can construct a hash table with no collisions.

**Two-level scheme:**
- First level: Hash to buckets
- Second level: Hash each bucket with no collisions (requires more slots)

The FKS scheme (Fredman, Komlós, Szemerédi, 1984) makes this concrete and gives the surprising result: **O(1) worst-case lookup in O(n) total space.** The trick is the second level. A bucket holding bᵢ keys gets a table of size bᵢ², where a randomly chosen hash function is collision-free with probability above ½ — so a few retries always find one. Squaring sounds wasteful, but the expected sum of bᵢ² across all buckets is O(n) when the first level is chosen well.

**Minimal perfect hashing** goes further, mapping n keys to exactly n slots with no gaps. Modern constructions (CHD, BBHash, PTHash) achieve about 2–3 bits of overhead per key. These are used where a key set is fixed and lookups are hot: compiler keyword recognition, `gperf`-generated parsers, static routing tables, and the term dictionaries in search indexes.

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

The LRU cache is worth expanding, because it is the canonical example of composing two structures to get properties neither has alone. A hash table gives O(1) lookup but no notion of recency; a doubly linked list gives O(1) reordering but no lookup. Combine them — hash key → list node, list ordered by recency — and every operation is O(1): find the node by hash, unlink it, move it to the head. Python's `functools.lru_cache` and every production cache are built this way.

**Where hash tables are the wrong choice**, which is easy to forget given how good the average case is: any workload needing ordered iteration, range queries, nearest-key lookups, or prefix matching. Those need a tree or a trie. The failure mode is insidious because a hash table works fine until the day someone asks for "all records between these two dates".

## 12.7 Historical Context

Hash tables were invented independently by multiple researchers in the 1950s-1960s. The term "hash" comes from the idea of "hashing" (mixing up) the keys.

The first published description is Arnold Dumey's in 1956, though Hans Peter Luhn had described chaining in an internal IBM memorandum in 1953, and Gene Amdahl, Elaine McGraw, and Arthur Samuel had implemented linear probing for the IBM 701 assembler in 1954 — making it one of the few fundamental data structures whose invention is documented in code before it appeared in a paper.

Donald Knuth's analysis in *The Art of Computer Programming* Volume 3 (1973) established the mathematics of both methods and remains the standard reference. Carter and Wegman introduced universal hashing in 1979, which turned adversarial resistance from a hope into a theorem, and Fredman, Komlós, and Szemerédi gave the first O(1) worst-case scheme in 1984. Pagh and Rodler's cuckoo hashing (2001) achieved the same worst-case guarantee with a far simpler structure.

---

## Where this connects

- [Chapter 14: Probabilistic Data Structures](../volume-3/ch14-probabilistic-data-structures.md) — trading exactness for a 10-100x memory reduction
- [Chapter 18: Concurrent Data Structures](../volume-3/ch18-concurrent-data-structures.md) — what it takes to make a hash table concurrent
