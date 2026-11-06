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

The idea is best understood as a compromise between two extremes. **Direct addressing** (one array slot per possible key)gives genuine O(1) access but needs an array the size of the key space, which for 64-bit integers or arbitrary strings is impossible. **A sorted array** needs only n slots but costs O(log n) per lookup.

A hash table takes the array indexing of the first and the space of the second, and pays for it with **collisions**: squeezing a large key space into m slots guarantees that different keys sometimes land on the same one. Everything difficult about hash tables follows from that single consequence.

Worth being precise about the guarantee, since "O(1) lookup" is repeated so often it stops being examined. It is O(1) *average case*, under the assumption that keys distribute uniformly. The worst case is O(n) (every key colliding)and that worst case is reachable by an adversary who knows your hash function. This is not hypothetical: collision-flooding denial of service against PHP, Java, Python, and Ruby web frameworks was demonstrated in 2011 and forced all of them to change their hashing.

## 12.2 Hash Functions

A hash function maps keys to array indices.

### Requirements

1. **Deterministic**: Same key always maps to same index
2. **Uniform**: Keys distribute evenly across indices
3. **Fast**: O(1) computation

A fourth requirement belongs on that list for anything handling untrusted input: **unpredictable**. An attacker who can compute your hash function offline can generate thousands of keys that all collide, turning every operation into a linear scan. Uniformity over *random* input is not the same as uniformity over *chosen* input.

There is also a subtle correctness requirement that causes real bugs: **equal keys must hash equally**. In languages where you can override both equality and hashing, overriding one without the other produces a container that loses entries. The key is there, but the lookup goes to the wrong bucket. This is the single most common hash-table bug in application code.

### Common Methods

**Division Method:**
```
h(k) = k mod m
```
Choose m as a prime not near a power of 2.

The reason for the prime matters. If m is a power of two, `k mod m` keeps only the low bits of k and discards everything else, so keys differing only in their high bits all collide. Pointers and aligned addresses have predictable low bits, which is exactly the case where this fails badly. A prime m mixes all the bits of k into the result.

Implementations that *do* want a power-of-two table size (because masking is faster than division) must therefore mix the bits first: Java's `HashMap` XORs the high 16 bits into the low 16 before masking, precisely for this reason.

**Multiplication Method:**
```
h(k) = floor(m × (k × A mod 1))
```
Knuth's A = (√5 - 1)/2 ≈ 0.618

The value of A is the reciprocal of the golden ratio, and it is chosen because it is the irrational number *hardest to approximate with a fraction*, which means successive multiples spread across the interval as evenly as possible rather than clustering. Unlike the division method, this works with any m, including powers of two.

**Universal Hashing:**
```
h(k) = ((a × k + b) mod p) mod m
```
Random a, b from large prime field.

This is the principled defense against adversarial input, and the guarantee is stronger than it looks: for *any* two distinct keys, the probability of collision over a random choice of (a, b) is at most 1/m. No fixed input is bad, because the function is not fixed until runtime. Carter and Wegman's 1979 result is the reason modern languages seed their hash functions randomly at process start.

**String Hashing:**
```c
/* Signed overflow is undefined behaviour in C, and a negative
   intermediate makes `% m` negative, an out-of-bounds index.
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

Choose by threat model: keyed hashes for anything reachable by user input, fast unkeyed hashes for internal maps with trusted keys. Rust makes this explicit. The default `HashMap` uses SipHash, and swapping in `FxHashMap` for internal use is often a 2× speedup.

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

Because chains can grow without bound, α may exceed 1. A chained table never "fills up", it just degrades. Deletion is straightforward, which is chaining's main advantage over the alternative.

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

The clustering problems are worth distinguishing. **Primary clustering** is the serious one: with linear probing, any run of occupied slots grows at both ends, and longer runs are more likely to be extended, so clusters feed on themselves and probe sequences lengthen non-linearly. **Secondary clustering** is milder: keys with the same initial hash follow identical probe sequences, but keys with different hashes do not interfere.

Despite the theory favouring double hashing, **linear probing usually wins in practice** below about 70% load, because its probe sequence is sequential memory access. The next slot is almost always in the same cache line already fetched. Double hashing jumps randomly through the table and misses cache on nearly every probe. This is [Chapter 16](../volume-3/ch16-external-memory-and-cache-oblivious-structures.md)'s lesson applied: an algorithm with more operations can be faster if the operations are cheaper.

Two constraints specific to open addressing. **Load factor must stay below 1**, and performance collapses as it approaches: at α = 0.9 linear probing averages about 50 probes per unsuccessful search, versus about 2.5 at α = 0.5. Resize at 0.7 or below.

And **deletion requires tombstones**. Simply clearing a slot breaks the probe chain for any key that probed past it, making entries unreachable. The slot must be marked "deleted but occupied" instead, and tombstones accumulate, eventually requiring a rehash to clear.

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
        # Resize on *used*, not count, since tombstones lengthen probes too.
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
        """Every key must be rehashed; indices depend on table size."""
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
- **Insertion reuses the first tombstone it passed**, rather than the empty slot at the end. Otherwise the table fills with tombstones even when entries are being replaced.
- **Resizing rehashes everything.** Indices are computed modulo the table size, so nothing carries over. This makes a single insertion O(n) occasionally, which is why the bound is amortized O(1): the same argument as the dynamic array in [Chapter 3](../volume-1/ch03-arrays-the-foundation-of-contiguous-storage.md).

That last point has a consequence for latency-sensitive systems: a hash table's *average* insert is O(1), but one insert in every n takes O(n). If tail latency matters, either pre-size the table or use an incremental-resize scheme that migrates a few entries per operation, as Redis does.

## 12.5 Perfect Hashing

If all keys are known in advance, we can construct a hash table with no collisions.

**Two-level scheme:**
- First level: Hash to buckets
- Second level: Hash each bucket with no collisions (requires more slots)

The FKS scheme (Fredman, Komlós, Szemerédi, 1984) makes this concrete and gives the surprising result: **O(1) worst-case lookup in O(n) total space.** The trick is the second level. A bucket holding bᵢ keys gets a table of size bᵢ², where a randomly chosen hash function is collision-free with probability above ½, so a few retries always find one. Squaring sounds wasteful, but the expected sum of bᵢ² across all buckets is O(n) when the first level is chosen well.

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

The LRU cache is worth expanding, because it is the canonical example of composing two structures to get properties neither has alone. A hash table gives O(1) lookup but no notion of recency; a doubly linked list gives O(1) reordering but no lookup. Combine them (hash key → list node, list ordered by recency)and every operation is O(1): find the node by hash, unlink it, move it to the head. Python's `functools.lru_cache` and every production cache are built this way.

**Where hash tables are the wrong choice**, which is easy to forget given how good the average case is: any workload needing ordered iteration, range queries, nearest-key lookups, or prefix matching. Those need a tree or a trie. The failure mode is insidious because a hash table works fine until the day someone asks for "all records between these two dates".

## 12.7 Historical Context

Hash tables were invented independently by multiple researchers in the 1950s-1960s. The term "hash" comes from the idea of "hashing" (mixing up) the keys.

The first published description is Arnold Dumey's in 1956, though Hans Peter Luhn had described chaining in an internal IBM memorandum in 1953, and Gene Amdahl, Elaine McGraw, and Arthur Samuel had implemented linear probing for the IBM 701 assembler in 1954: making it one of the few fundamental data structures whose invention is documented in code before it appeared in a paper.

Donald Knuth's analysis in *The Art of Computer Programming* Volume 3 (1973) established the mathematics of both methods and remains the standard reference. Carter and Wegman introduced universal hashing in 1979, which turned adversarial resistance from a hope into a theorem, and Fredman, Komlós, and Szemerédi gave the first O(1) worst-case scheme in 1984. Pagh and Rodler's cuckoo hashing (2001) achieved the same worst-case guarantee with a far simpler structure.

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**12.1 ★ Trace linear probing.** A table has m = 11 slots, h(k) = k mod 11, and uses linear probing. Insert the keys 22, 1, 13, 11, 24, 33 in that order. Show the final table and the number of probes each insertion took. Then count the probes for an unsuccessful search for 44. For comparison, how many key comparisons would the same search cost in a chained table with the same hash function?

<details>
<summary>Solution</summary>

| Key | h(k) | Slots probed | Lands in | Probes |
|-----|------|--------------|----------|--------|
| 22 | 0 | 0 | 0 | 1 |
| 1 | 1 | 1 | 1 | 1 |
| 13 | 2 | 2 | 2 | 1 |
| 11 | 0 | 0, 1, 2, 3 | 3 | 4 |
| 24 | 2 | 2, 3, 4 | 4 | 3 |
| 33 | 0 | 0, 1, 2, 3, 4, 5 | 5 | 6 |

Final table: `[22, 1, 13, 11, 24, 33, _, _, _, _, _]`.

Searching for 44 starts at 44 mod 11 = 0 and must walk the whole run 0..5 before reaching the empty slot 6: **7 probes**, to learn that the key is absent.

With chaining, bucket 0 holds only the keys that hash to 0 (22, 11, 33), so the search costs 3 comparisons. The difference is primary clustering: keys hashing to 0, 1 and 2 merged into a single run, and every search that lands anywhere in that run pays for all of it. Only 6 of 11 slots are full (α ≈ 0.55), yet this search already costs 7 probes.

</details>

**12.2 ★ Why not a power of two?** The keys are 16 aligned addresses: 4096, 4160, 4224, ..., 4096 + 64 × 15 (consecutive multiples of 64). (a) How many distinct buckets does h(k) = k mod 16 use? (b) How many does h(k) = k mod 17 use? (c) Java's `HashMap` computes `h ^ (h >>> 16)` before masking to a power-of-two size. Does that rescue these keys in a 16-slot table?

<details>
<summary>Hint</summary>

Write 64 in binary. For (b), ask whether 64 mod 17 shares a factor with 17.

</details>

<details>
<summary>Solution</summary>

(a) **One.** Every key is a multiple of 64, so its low 6 bits are zero, and `k mod 16` reads only the low 4 bits. All 16 keys land in bucket 0, and every operation is a scan of one 16-long chain.

(b) **Sixteen, all different.** The keys are 4096 + 64i. Modulo 17, the step 64 is 13, and since 17 is prime, multiples of 13 cycle through every residue before repeating. Sixteen consecutive steps therefore hit sixteen distinct buckets (in fact every residue except 3).

(c) **No.** The spreader XORs the high 16 bits into the low 16, but every key here is below 2¹⁶, so `h >>> 16` is 0 and the XOR changes nothing. The keys still differ only in bits 6 to 9, and a 16-slot mask reads bits 0 to 3. The spreader helps keys that differ in their *high* half; it does nothing for keys that differ only in middle bits. (Java's fallback for this case is the one described in Section 12.3: the overlong chain becomes a red-black tree.)

</details>

**12.3 ★★ Tombstones by hand.** Using the `HashTable` from Section 12.4 with capacity 8 and integer keys (in CPython, `hash(k) == k` for small non-negative integers), run:

```python
t = HashTable(8)
t[3] = "a"
t[11] = "b"
t[19] = "c"
del t[11]
t[27] = "d"
```

(a) Show the key array after the three inserts. (b) Show it after the delete, and what `t[19]` would do if `__delitem__` wrote `_EMPTY` instead of `_DELETED`. (c) Where does 27 go, and what are `_count` and `_used` at the end?

<details>
<summary>Hint</summary>

3, 11, 19 and 27 all hash to slot 3. Follow `first_tombstone` through `__setitem__`.

</details>

<details>
<summary>Solution</summary>

(a) All three keys hash to 3 mod 8 = 3, so linear probing places them in slots 3, 4, 5:

```
slot:  0  1  2  3  4   5   6  7
keys:  E  E  E  3  11  19  E  E      E = _EMPTY
```

(b) Deleting 11 writes a tombstone into slot 4:

```
slot:  0  1  2  3  4  5   6  7
keys:  E  E  E  3  T  19  E  E       T = _DELETED
```

`t[19]` probes 3 (key 3, not a match), 4 (tombstone, keep going), 5 (match). If the delete had written `_EMPTY`, the probe would stop at slot 4 and raise `KeyError(19)` even though 19 is sitting in slot 5. That is the bug the tombstone exists to prevent.

(c) Inserting 27 probes slot 3 (key 3, no match), slot 4 (tombstone: `first_tombstone = 4`), slot 5 (key 19, no match), slot 6 (`_EMPTY`). It stops there because it has now proven 27 is not already present, then writes 27 into the remembered tombstone at slot 4, not into slot 6:

```
slot:  0  1  2  3  4   5   6  7
keys:  E  E  E  3  27  19  E  E
```

`_count` is 3 (live keys 3, 27, 19). `_used` is also 3: it went to 3 after the inserts, stayed at 3 on the delete (the tombstone still occupies a slot), and stayed at 3 on the final insert because it reused a slot that was already counted.

</details>

**12.4 ★★ Find the bug.** This class is meant to make usernames case-insensitive. What does the snippet print, and why? Fix it.

```python
class Username:
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return self.name.lower() == other.name.lower()

    def __hash__(self):
        return hash(self.name)

users = {Username("Alice"): 1}
print(Username("alice") in users)
```

<details>
<summary>Solution</summary>

It prints `False`, even though `Username("Alice") == Username("alice")` is `True`.

This is the "equal keys must hash equally" rule from Section 12.2. `__hash__` uses the raw name, so `"Alice"` and `"alice"` get unrelated hashes and the lookup goes to a different slot from the one the entry was stored in. The dictionary never gets as far as calling `__eq__`. (CPython also compares stored full hash values before calling `__eq__`, so even an accidental slot collision would not save it.)

The fix is to hash exactly what equality compares:

```python
class Username:
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return self.name.lower() == other.name.lower()

    def __hash__(self):
        return hash(self.name.lower())
```

The general rule: `__hash__` may use *less* information than `__eq__` (that only adds collisions), but never information that `__eq__` ignores. Python partly enforces this by setting `__hash__ = None` when a class defines `__eq__` alone, which makes instances unhashable rather than silently wrong; overriding both, as here, bypasses that safety net.

</details>

**12.5 ★★ Clusters feed on themselves.** A linear-probing table has m = 10 slots, of which slots 2, 3, 4, 5 and 8 are occupied. The next key's hash is uniform over 0..9. For each empty slot, what is the probability that the new key ends up there? What does this say about the claim that "longer runs are more likely to be extended"?

<details>
<summary>Hint</summary>

A key lands in the first empty slot at or after its hash position. Which hash values lead to slot 6?

</details>

<details>
<summary>Solution</summary>

A key with hash h goes to the first empty slot at or after h (wrapping around).

| Empty slot | Hash values that land there | Probability |
|------------|-----------------------------|-------------|
| 0 | 0 | 1/10 |
| 1 | 1 | 1/10 |
| 6 | 2, 3, 4, 5, 6 | 5/10 |
| 7 | 7 | 1/10 |
| 9 | 8, 9 | 2/10 |

The probabilities sum to 1. The slot just past the run of length 4 catches half of all insertions, because every key that hashes anywhere into the run slides to its end. In general, the empty slot after a run of length L is hit with probability (L + 1)/m. Once slot 6 fills, the run becomes 2..6 and slot 7 catches 6/10 of the next insertions, so the run's capture probability grows with every key it absorbs. That positive feedback is primary clustering, and it is why probe counts rise non-linearly as α grows.

</details>

**12.6 ★★ Build the LRU cache.** Section 12.6 describes an LRU cache as a hash table pointing into a doubly linked list. Implement `LRUCache(capacity)` with `get(key)` (return the value or `None`, and mark the key most recently used) and `put(key, value)` (insert or update, evicting the least recently used key when full). Both must be O(1). Do not use `OrderedDict`.

<details>
<summary>Hint</summary>

Sentinel head and tail nodes remove every special case for an empty list. When you evict the tail node you must also delete it from the dictionary, so the node has to remember its key.

</details>

<details>
<summary>Solution</summary>

```python
class _Node:
    __slots__ = ("key", "value", "prev", "next")

    def __init__(self, key=None, value=None):
        self.key, self.value = key, value
        self.prev = self.next = None

class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.map = {}                      # key -> _Node
        self.head = _Node()                # sentinel: most recent side
        self.tail = _Node()                # sentinel: least recent side
        self.head.next, self.tail.prev = self.tail, self.head

    def _unlink(self, node):
        node.prev.next, node.next.prev = node.next, node.prev

    def _push_front(self, node):
        node.prev, node.next = self.head, self.head.next
        self.head.next.prev = node
        self.head.next = node

    def get(self, key):
        node = self.map.get(key)
        if node is None:
            return None
        self._unlink(node)                 # O(1): the hash gave us the node
        self._push_front(node)
        return node.value

    def put(self, key, value):
        node = self.map.get(key)
        if node is not None:
            node.value = value
            self._unlink(node)
            self._push_front(node)
            return
        if len(self.map) == self.capacity:
            lru = self.tail.prev           # least recently used
            self._unlink(lru)
            del self.map[lru.key]          # why the node stores its key
        node = _Node(key, value)
        self.map[key] = node
        self._push_front(node)

c = LRUCache(2)
c.put("a", 1)
c.put("b", 2)
assert c.get("a") == 1          # order now: a, b
c.put("c", 3)                   # evicts b
assert c.get("b") is None
assert c.get("a") == 1 and c.get("c") == 3
```

Every operation is one dictionary operation (O(1) average) plus a constant number of pointer updates. Neither structure alone could do this: the dictionary cannot find the oldest entry without a scan, and the list cannot find a key without a scan. The list must be *doubly* linked because `_unlink` needs the predecessor, and the only handle we have is the node itself.

</details>

**12.7 ★★★ Why FKS fits in O(n) space.** Assume a universal family: for any two distinct keys, a randomly chosen function into m slots makes them collide with probability at most 1/m. (a) Show that hashing a bucket's b keys into a table of size b² is collision-free with probability greater than ½. (b) The first level hashes all n keys into m = n buckets, giving bucket sizes b₁, ..., bₙ. Show that E[Σ bᵢ²] < 2n, and explain how this yields O(n) total space with an expected constant number of retries.

<details>
<summary>Hint</summary>

Count colliding *pairs* and use Markov's inequality, Pr[X ≥ t] ≤ E[X]/t for non-negative X. For (b), note that b² = b + 2 · C(b, 2).

</details>

<details>
<summary>Solution</summary>

(a) Let X be the number of pairs of keys that collide. There are C(b, 2) = b(b − 1)/2 pairs, each colliding with probability at most 1/b², so

E[X] ≤ b(b − 1) / (2b²) = (b − 1) / (2b) < ½.

X is a non-negative integer, so by Markov, Pr[X ≥ 1] ≤ E[X] < ½. The table is collision-free with probability greater than ½, and the expected number of random functions tried before finding a good one is less than 2.

(b) For each bucket, bᵢ² = bᵢ + 2 · C(bᵢ, 2), and C(bᵢ, 2) counts the pairs that collided into bucket i. Summing over buckets:

Σ bᵢ² = n + 2C, where C is the total number of colliding pairs at the first level.

There are C(n, 2) pairs, each colliding with probability at most 1/n, so E[C] ≤ (n − 1)/2 and

E[Σ bᵢ²] ≤ n + (n − 1) < 2n.

By Markov again, Pr[Σ bᵢ² ≥ 4n] < ½. So the construction picks a first-level function, checks whether Σ bᵢ² < 4n, and retries if not (expected fewer than 2 attempts); then builds each second-level table (expected fewer than 2 attempts each). Total space is n first-level slots plus Σ bᵢ² < 4n second-level slots, which is O(n), and a lookup is exactly two hash evaluations, which is O(1) worst case. Squaring each bucket's size looks extravagant, but the squares are small because large buckets are rare.

</details>

---

## Where this connects

- [Chapter 14: Probabilistic Data Structures](../volume-3/ch14-probabilistic-data-structures.md). Trading exactness for a 10-100x memory reduction
- [Chapter 18: Concurrent Data Structures](../volume-3/ch18-concurrent-data-structures.md). What it takes to make a hash table concurrent
