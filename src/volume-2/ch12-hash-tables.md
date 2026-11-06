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

The idea is best understood as a compromise between two extremes. **Direct addressing** (one array slot per possible key) gives genuine O(1) access but needs an array the size of the key space, which for 64-bit integers or arbitrary strings is impossible. **A sorted array** needs only n slots but costs O(log n) per lookup.

A hash table takes the array indexing of the first and the space of the second, and pays for it with **collisions**: squeezing a large key space into m slots guarantees that different keys sometimes land on the same one. Everything difficult about hash tables follows from that single consequence.

Worth being precise about the guarantee, since "O(1) lookup" is repeated so often it stops being examined. It is O(1) *average case*, under the assumption that keys distribute uniformly. The worst case is O(n) (every key colliding), and that worst case is reachable by an adversary who knows your hash function. This is not hypothetical: collision-flooding denial of service against PHP, Java, Python, and Ruby web frameworks was demonstrated in 2011 and forced all of them to change their hashing or limit their input (Section 12.2).

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

### Hash Flooding

A web framework parses every POST request into a hash table of form fields before application code runs. If the attacker can choose field names that all have the same hash, n fields cost Θ(n²) comparisons to insert, and the server burns CPU on a request that took milliseconds to send. Crosby and Wallach described these *algorithmic complexity attacks* in 2003. At the 28th Chaos Communication Congress (28C3) in December 2011, Alexander Klink and Julian Wälde showed that the default hash tables in PHP, ASP.NET, Java, Python, Ruby and JavaScript platforms were all exploitable this way.

Building the colliding keys is easy when the hash is a fixed polynomial. Java's `String.hashCode` computes s₀·31ⁿ⁻¹ + ... + sₙ₋₁, and the two-character strings `"Aa"` and `"BB"` have the same hash (65 · 31 + 97 = 66 · 31 + 66 = 2112). Because the hash of a concatenation depends only on the hashes and lengths of its parts, any string made of k such blocks collides with all 2ᵏ of them:

```python
from itertools import product

def java_string_hash(s):
    """Java's String.hashCode, reduced to 32 bits."""
    h = 0
    for ch in s:
        h = (31 * h + ord(ch)) & 0xFFFFFFFF
    return h

assert java_string_hash("Aa") == java_string_hash("BB") == 2112
keys = ["".join(blocks) for blocks in product(["Aa", "BB"], repeat=16)]
assert len(keys) == 65536
assert len({java_string_hash(k) for k in keys}) == 1    # one hash value
```

The *full* hash values are equal, so these keys collide for every table size, and resizing does not help. Inserting all 65,536 into a chained table makes about 65,536² / 2 ≈ 2 × 10⁹ key comparisons.

The responses came in layers:

- **Limit the input.** PHP added `max_input_vars` (default 1,000 fields) in December 2011. This caps the damage for one entry point and fixes nothing else.
- **Randomize the seed.** Python made a per-process random hash seed the default in 3.3. A random seed alone is not enough if the function has collisions that do not depend on the seed: at 29C3 (2012), Aumasson, Bernstein and Boßlet built seed-independent multicollisions for MurmurHash2, MurmurHash3 and CityHash64, the functions Ruby and others had just adopted as their randomized fix.
- **Use a keyed pseudorandom function.** SipHash (Aumasson and Bernstein, 2012) takes a secret 128-bit key chosen at startup. It is a pseudorandom function: without the key its outputs are unpredictable, so an attacker cannot compute colliding inputs offline, and it is still fast on the short keys hash tables see. Ruby switched to it in 2012, Python in 3.4 (PEP 456), and Rust and Perl use it too.
- **Bound the worst case structurally.** Java 8's tree bins (Section 12.3) turn a flooded chain into a red-black tree, so even a successful attack costs O(log n) per operation instead of O(n).

The defences compose: Rust uses SipHash with randomly generated keys, and Java uses a predictable hash but caps the damage with trees.

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

## 12.5 Modern Open Addressing

The table in Section 12.4 is linear probing much as it was implemented in 1954, and it has three weaknesses that show up in production. Probe lengths have a long tail: the average is small but a few unlucky keys sit dozens of slots from home. Unsuccessful searches scan all the way to an empty slot. And every probe compares a full key, which for strings means a memory access and a comparison loop per slot. The two designs that dominate modern libraries attack these directly. Robin Hood hashing fixes the tail and the deletion problem; Swiss tables make each probe so cheap that the tail barely matters.

### Robin Hood Hashing

For an entry stored at slot i whose home slot is h = hash(k) mod m, its **probe-sequence length** (PSL) is (i − h) mod m: how many slots past home it sits. A lookup that finds the entry costs PSL + 1 probes. Plain linear probing gives each slot to whichever key arrives first, so a key's PSL depends on luck.

Robin Hood hashing (Celis, 1985) changes one rule. Insertion walks forward from home, tracking the PSL d the new entry would have at the current slot. If the occupant's PSL is *smaller* than d, the occupant is "richer" (closer to home), so the new entry takes the slot and the evicted occupant continues the walk with its own PSL. The rich give to the poor.

This maintains an invariant: **moving from one occupied slot to the next, PSL rises by at most one.** Equivalently, within a run of occupied slots, entries are sorted by home slot. Two consequences follow.

- **Unsuccessful lookups stop early.** Suppose a search for k reaches slot i at distance d and the occupant's PSL is less than d. If k were stored further on, at slot j, its PSL there would be d + (j − i), so PSL would have to rise by more than j − i over j − i steps, which the invariant forbids. So the search can stop without reaching an empty slot. (An empty slot can be treated as PSL −1, which makes it the same test.)
- **Deletion needs no tombstones.** Remove the entry, then shift each following entry back one slot, reducing its PSL by one, until reaching an empty slot or an entry with PSL 0 (already at home, so it cannot move closer). This is **backward-shift deletion**. The run stays sorted and the table never accumulates tombstones.

The code keeps the conventions of `HashTable` above, with a third array holding each slot's PSL:

```python
class RobinHoodTable:
    """Linear probing where the entry farther from home keeps the slot."""

    def __init__(self, capacity=16):
        self._keys = [None] * capacity
        self._values = [None] * capacity
        self._dist = [-1] * capacity      # probe-sequence length; -1 marks empty
        self._count = 0

    def __len__(self):
        return self._count

    def _home(self, key):
        return hash(key) % len(self._keys)

    def _find(self, key):
        """Slot holding key, or None. Stops early at an empty or richer slot."""
        m = len(self._keys)
        i, d = self._home(key), 0
        while self._dist[i] >= d:         # empty (-1) is < d too, so it also stops
            if self._dist[i] == d and self._keys[i] == key:
                return i
            i, d = (i + 1) % m, d + 1
        return None

    def __getitem__(self, key):
        i = self._find(key)
        if i is None:
            raise KeyError(key)
        return self._values[i]

    def __setitem__(self, key, value):
        i = self._find(key)
        if i is not None:
            self._values[i] = value           # overwrite in place
            return
        if self._count + 1 > len(self._keys) * 0.9:
            self._resize(len(self._keys) * 2)
        m = len(self._keys)
        i, d = self._home(key), 0
        while self._dist[i] != -1:
            if self._dist[i] < d:             # occupant is closer to home: rob it
                key, self._keys[i] = self._keys[i], key
                value, self._values[i] = self._values[i], value
                d, self._dist[i] = self._dist[i], d
            i, d = (i + 1) % m, d + 1
        self._keys[i], self._values[i], self._dist[i] = key, value, d
        self._count += 1

    def __delitem__(self, key):
        i = self._find(key)
        if i is None:
            raise KeyError(key)
        m = len(self._keys)
        j = (i + 1) % m
        while self._dist[j] > 0:              # backward shift: pull the run left
            self._keys[i], self._values[i] = self._keys[j], self._values[j]
            self._dist[i] = self._dist[j] - 1
            i, j = j, (j + 1) % m
        self._keys[i], self._values[i], self._dist[i] = None, None, -1
        self._count -= 1

    def _resize(self, new_capacity):
        old = [(k, v) for k, v, d in zip(self._keys, self._values, self._dist)
               if d != -1]
        self.__init__(new_capacity)
        for k, v in old:
            self[k] = v
```

Two details. `_find` compares the stored PSL before the key: an entry with a different PSL at this slot has a different home, so it cannot be k, and the expensive key comparison is skipped. Production tables store part of the hash per slot for the same reason. And `__setitem__` searches for an existing key first, so the displacement walk never needs to compare keys: every entry it carries is known to be unique.

**A trace.** Take m = 8 and h(k) = k mod 8 (small integers hash to themselves in CPython), and insert 2, 3, 8, 16, 24. The first four go to slots 2, 3, 0, 1 with no conflict. Key 24 has home 0:

| Slot | Occupant (PSL) | 24's distance | Action |
|------|----------------|---------------|--------|
| 0 | 8 (0) | 0 | 0 is not < 0, move on |
| 1 | 16 (1) | 1 | 1 is not < 1, move on |
| 2 | 2 (0) | 2 | 0 < 2: 24 takes slot 2, carry 2 at distance 0 |
| 3 | 3 (0) | 1 | 0 < 1: 2 takes slot 3, carry 3 at distance 0 |
| 4 | empty | 1 | 3 settles here with PSL 1 |

Compare the two layouts:

```
slot:              0   1   2   3   4   5   6   7
linear probing:    8  16   2   3  24   .   .   .     PSLs 0 1 0 0 4
Robin Hood:        8  16  24   2   3   .   .   .     PSLs 0 1 2 1 1
```

Both PSL lists sum to 5, so the average successful lookup costs the same, but the worst entry dropped from 4 to 2. An unsuccessful search for 32 (home 0) scans slots 0 to 5 under linear probing, 6 probes. Under Robin Hood it stops at slot 3, where it is at distance 3 but the occupant has PSL 1: 4 probes. Deleting 16 from the Robin Hood table shifts 24, 2 and 3 back one slot each, giving `8 24 2 3 . . . .` with PSLs 0 1 0 0, which is exactly the table you would get if 16 had never been inserted.

**Why it works: the mean is fixed, the variance is not.** The equal sums in the trace are not a coincidence. Under linear probing, Robin Hood never changes the total PSL of a set of keys, only who pays it (Exercise 12.9). What it changes is the spread. Measured on one table of m = 65,536 slots filled with random hash values:

| α | Mean PSL (both) | PSL variance, LP / RH | Max PSL, LP / RH | Probes per miss, LP / RH |
|---|---|---|---|---|
| 0.50 | 0.50 | 1.6 / 0.7 | 29 / 7 | 2.5 / 1.7 |
| 0.75 | 1.5 | 18.6 / 3.9 | 115 / 24 | 8.2 / 2.9 |
| 0.90 | 4.3 | 234 / 19 | 467 / 36 | 44.5 / 5.7 |

At α = 0.9 the longest probe drops by a factor of 13 and misses get 8 times cheaper, which is what lets Robin Hood tables run at a load factor of 0.9 where plain linear probing has collapsed. All operations remain O(1) *expected* time for a fixed α < 1, O(n) worst case, with insertion O(1) amortized across resizes. The costs are an extra field per slot (a byte is enough for the PSL in practice), more writes per insertion because of the swaps, and deletions that may shift a whole run.

Robin Hood hashing was the design of Rust's standard `HashMap` until Rust 1.36 (2019), and it is used by C++ libraries such as `tsl::robin_map`, which combines it with backward-shift deletion.

### Swiss Tables

Robin Hood still compares keys slot by slot. A Swiss table, the design behind Google's Abseil `flat_hash_map`, moves the search out of the key array altogether.

**Layout.** Alongside the array of slots (each holding a key and value) sits a separate array of **control bytes**, one per slot. A control byte says what the slot holds:

| Control byte | Meaning |
|--------------|---------|
| `0b1000_0000` (0x80) | empty |
| `0b1111_1110` (0xFE) | deleted (tombstone) |
| `0b0xxx_xxxx` | full; the low 7 bits are H2 of the key's hash |

These are Abseil's values (Abseil also has a sentinel, 0xFF, marking the end of the array for iteration). The essential rule is that special states have the top bit set and full slots have it clear, so "is this slot free?" is a single bit test.

**Splitting the hash.** A 64-bit hash is split into two parts. **H1**, 57 bits, chooses where in the table the probe starts. **H2**, the other 7 bits, is stored in the control byte. (The original design took H2 from the low 7 bits; current Abseil and Rust's hashbrown take the top 7. Either works if the hash is well mixed.)

**Probing a group at once.** Slots are examined in **groups** of 16. To look up k, start at the group H1 selects, load its 16 control bytes into one 128-bit SSE2 register, and compare all 16 against H2 in a single instruction (`_mm_cmpeq_epi8`, after broadcasting H2 to all 16 lanes). A second instruction (`_mm_movemask_epi8`) packs the result into a 16-bit mask with one bit per matching slot. Only those slots' keys are compared. If the group also contains an empty byte, the key is absent; otherwise move to the next group. For example, with H2 = 0x15:

```
slot j:        0     1     2     3     4     5     6     7    ...  15
control:     0x15  0x80  0x3A  0x15  0xFE  0x61  0x80  0x0C   ...
== H2?          1     0     0     1     0     0     0     0
match mask:  0b...1001  -> compare keys in slots 0 and 3 only
empty mask:  0b...0100_0010 (nonzero) -> if neither matches, k is absent
```

A full slot holding a different key matches a random 7-bit H2 with probability 1/128, so wasted key comparisons are rare. In the model below, filled to the maximum load of 7/8, a successful lookup inspected 1.1 groups and made 0.07 failed key comparisons on average, and an unsuccessful one inspected 2.1 groups and made 0.23.

**Why it wins on cache behaviour.** A probe step reads 16 *bytes* of contiguous metadata, a quarter of a 64-byte cache line, instead of 16 keys and values spread over several lines. A typical lookup touches one line of control bytes and then the one slot that matches: about two cache misses whatever the key type, and the key comparison, which for strings is the expensive part, almost always succeeds the first time it runs. Because one step covers 16 slots, clusters cost little, and the table runs comfortably at 7/8 load with only one byte of overhead per slot. No PSLs are stored, and nothing moves on insert.

Groups are visited in triangular order (offsets of 0, 1, 3, 6, 10, ... groups), which visits every group exactly once when the number of groups is a power of two. Deletion writes a tombstone, with one refinement: if the deleted slot's group still contains an empty byte, then that group has never been full, so no insertion ever probed past it, and the slot can be marked empty instead. Tombstones consume the growth budget like full slots, so a delete-heavy table eventually rehashes, often in place at the same size.

The following Python models that logic. It has no SIMD: `_match` loops over 16 bytes where the real code runs about three instructions. It also simplifies one thing: here groups are aligned blocks of 16, while Abseil and hashbrown load 16 bytes starting at any slot, copying the first group's control bytes to the end of the array so a load can wrap around. With unaligned groups, the never-full test for deletion has to look at the control bytes on both sides of the slot.

```python
GROUP = 16                    # slots per group: one 16-byte SSE2 register
EMPTY, DELETED = 0x80, 0xFE   # Abseil's values; a full slot holds 0x00-0x7F
MASK64 = (1 << 64) - 1

def _mix(h):
    """Scramble Python's hash: small ints hash to themselves, and both
    H1 and H2 need well-mixed bits."""
    h = (h * 0x9E3779B97F4A7C15) & MASK64
    return h ^ (h >> 29)

class SwissTable:
    def __init__(self, groups=1):                # groups must be a power of 2
        n = groups * GROUP
        self._ctrl = bytearray([EMPTY]) * n
        self._keys = [None] * n
        self._values = [None] * n
        self._count = 0
        self._growth_left = n * 7 // 8           # max load factor 7/8

    def __len__(self):
        return self._count

    @staticmethod
    def _split(key):
        h = _mix(hash(key))
        return h >> 7, h & 0x7F                  # H1: where to start, H2: 7-bit tag

    def _match(self, g, pred):
        """Bitmask of slots j in group g with pred(ctrl byte). Models one SIMD
        compare plus movemask: 16 bytes tested at once in hardware."""
        base, mask = g * GROUP, 0
        for j in range(GROUP):
            if pred(self._ctrl[base + j]):
                mask |= 1 << j
        return mask

    def _probe(self, h1):
        """Groups in triangular order g, g+1, g+3, g+6, ...: with a power-of-2
        number of groups this visits every group exactly once."""
        ngroups = len(self._ctrl) // GROUP
        g = h1 & (ngroups - 1)
        for i in range(ngroups):
            yield g
            g = (g + i + 1) & (ngroups - 1)

    def _find(self, key):
        h1, h2 = self._split(key)
        for g in self._probe(h1):
            m = self._match(g, lambda c: c == h2)
            while m:                              # usually 0 or 1 candidates
                i = g * GROUP + (m & -m).bit_length() - 1
                if self._keys[i] == key:
                    return i
                m &= m - 1                        # clear lowest set bit
            if self._match(g, lambda c: c == EMPTY):
                return None                       # nothing ever probed past here
        return None

    def __getitem__(self, key):
        i = self._find(key)
        if i is None:
            raise KeyError(key)
        return self._values[i]

    def __setitem__(self, key, value):
        i = self._find(key)
        if i is not None:
            self._values[i] = value
            return
        if self._growth_left == 0:               # full of entries or tombstones
            ngroups = len(self._ctrl) // GROUP
            grow = self._count >= len(self._ctrl) * 7 // 16
            self._rehash(2 * ngroups if grow else ngroups)
        h1, h2 = self._split(key)
        for g in self._probe(h1):
            m = self._match(g, lambda c: c & 0x80)   # EMPTY or DELETED: top bit set
            if m:
                i = g * GROUP + (m & -m).bit_length() - 1
                if self._ctrl[i] == EMPTY:
                    self._growth_left -= 1           # reusing a tombstone costs nothing
                self._ctrl[i] = h2
                self._keys[i], self._values[i] = key, value
                self._count += 1
                return

    def __delitem__(self, key):
        i = self._find(key)
        if i is None:
            raise KeyError(key)
        if self._match(i // GROUP, lambda c: c == EMPTY):
            self._ctrl[i] = EMPTY       # group was never full: no probe went past it
            self._growth_left += 1
        else:
            self._ctrl[i] = DELETED     # some key may have probed past: tombstone
        self._keys[i] = self._values[i] = None
        self._count -= 1

    def _rehash(self, groups):
        old = [(k, v) for c, k, v in zip(self._ctrl, self._keys, self._values)
               if not c & 0x80]
        self.__init__(groups)
        for k, v in old:
            self[k] = v
```

The `_mix` step is not decoration. With Python's identity hash for integers, the top bits of every small key would be zero and every key would share the same H2, turning each probe into a full scan of the group. Swiss tables need a hash whose every bit is well mixed, which is why Abseil and hashbrown ship their own hash functions rather than trusting the key type's. Complexity is the same as for any open-addressing table: O(1) expected per operation at bounded load, O(n) worst case, insertion O(1) amortized.

**Who uses what.** It is worth being precise, because "hash table" names a different structure in every language:

- **C++:** Abseil's `flat_hash_map` and `flat_hash_set` are Swiss tables. `std::unordered_map` uses chaining, because the standard requires that references to elements survive a rehash and exposes a bucket interface, which together rule out open addressing.
- **Rust:** `std::collections::HashMap` has been a Swiss table since Rust 1.36 (2019), when the standard library adopted the `hashbrown` crate. It uses 16-slot groups with SSE2 on x86 and 8-slot groups on other 64-bit targets. Its byte values differ from Abseil's (empty is 0xFF, deleted is 0x80), but the top-bit rule is the same.
- **Go:** the built-in `map` switched to a Swiss table in Go 1.24 (February 2025). It uses groups of 8 slots with a 64-bit control word, SIMD instructions on amd64 and portable bit arithmetic elsewhere (Exercise 12.10), and the same 7/8 load factor. Each map is a set of tables of at most 1,024 slots, with upper hash bits choosing the table, so growing the map splits one small table at a time and no single insertion pays for rehashing the whole map.
- **Python:** `dict` is neither linear probing nor a Swiss table. It probes with the recurrence i ← (5i + 1 + perturb) mod 2ᵏ, shifting `perturb` (initially the full hash) right by 5 bits each step, so the high bits of the hash influence the probe sequence; this matters because small integers hash to themselves. Since CPython 3.6 the table is also **compact**: the hashed array holds only small integer indices (1 byte each for small tables), pointing into a dense array of (hash, key, value) entries kept in insertion order. An empty slot then costs 1 byte instead of a 24-byte entry, and the dense array is why dicts iterate in insertion order, a guarantee of the language since 3.7. The index array is kept at most 2/3 full.
- **Java:** `HashMap` uses chaining with tree bins (Section 12.3).

### Choosing a Scheme

| | Chaining | Linear probing (12.4) | Robin Hood | Swiss table |
|---|---|---|---|---|
| **Memory per entry** | Node per entry (next pointer plus allocator overhead) and a bucket pointer per slot | Key and value only, but 1 − α of the slots are empty and full-sized | As linear probing, plus a PSL or stored hash per slot | Key and value plus 1 control byte per slot |
| **Probe behaviour** | One dependent pointer load per chain node, each a likely cache miss | Sequential and cache-friendly; primary clustering gives long tails; misses scan to an empty slot | Sequential with low variance; misses stop at the first richer occupant | 16 (or 8) control bytes tested per step; keys compared only on a 7-bit tag match |
| **Deletion** | Unlink the node; no tombstones | Tombstones, cleared only by rehashing | Backward shift; no tombstones | Tombstone, or empty if the group was never full |
| **Max useful α** | Above 1 still works; Java uses 0.75, C++ `unordered_map` 1.0 | About 0.7 | About 0.9 | 7/8 |
| **Used by** | Java `HashMap`, C++ `std::unordered_map` | Java `IdentityHashMap`, many hand-written tables | Rust before 1.36, `tsl::robin_map` | Abseil, Rust `HashMap`, Go 1.24+ |

All four are O(1) expected and O(n) worst case per operation; the differences are constant factors, memory, and tail behaviour. For open addressing, memory per *stored* entry is the slot size divided by α: at 7/8 load a Swiss table spends 8/7 of a slot per entry, at 0.7 linear probing spends 10/7. Chaining remains the right choice when elements must never move (other code holds pointers to them) or are large, since open addressing copies entries on every resize. When keys and values are small and lookups are hot, which is the common case, the Swiss table is the current default for good reason.

## 12.6 Perfect Hashing

If all keys are known in advance, we can construct a hash table with no collisions.

**Two-level scheme:**
- First level: Hash to buckets
- Second level: Hash each bucket with no collisions (requires more slots)

The FKS scheme (Fredman, Komlós, Szemerédi, 1984) makes this concrete and gives the surprising result: **O(1) worst-case lookup in O(n) total space.** The trick is the second level. A bucket holding bᵢ keys gets a table of size bᵢ², where a randomly chosen hash function is collision-free with probability above ½, so a few retries always find one. Squaring sounds wasteful, but the expected sum of bᵢ² across all buckets is O(n) when the first level is chosen well.

**Minimal perfect hashing** goes further, mapping n keys to exactly n slots with no gaps. Modern constructions (CHD, BBHash, PTHash) achieve about 2–3 bits of overhead per key. These are used where a key set is fixed and lookups are hot: compiler keyword recognition, `gperf`-generated parsers, static routing tables, and the term dictionaries in search indexes.

## 12.7 Applications

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

The LRU cache is worth expanding, because it is the canonical example of composing two structures to get properties neither has alone. A hash table gives O(1) lookup but no notion of recency; a doubly linked list gives O(1) reordering but no lookup. Combine them (hash key → list node, list ordered by recency), and every operation is O(1): find the node by hash, unlink it, move it to the head. Python's `functools.lru_cache` and every production cache are built this way.

**Where hash tables are the wrong choice**, which is easy to forget given how good the average case is: any workload needing ordered iteration, range queries, nearest-key lookups, or prefix matching. Those need a tree or a trie. The failure mode is insidious because a hash table works fine until the day someone asks for "all records between these two dates".

## 12.8 Historical Context

Hash tables were invented independently by multiple researchers in the 1950s-1960s. The term "hash" comes from the idea of "hashing" (mixing up) the keys.

The first published description is Arnold Dumey's in 1956, though Hans Peter Luhn had described chaining in an internal IBM memorandum in 1953, and Gene Amdahl, Elaine McGraw, and Arthur Samuel had implemented linear probing for the IBM 701 assembler in 1954: making it one of the few fundamental data structures whose invention is documented in code before it appeared in a paper.

Donald Knuth's analysis in *The Art of Computer Programming* Volume 3 (1973) established the mathematics of both methods and remains the standard reference. Carter and Wegman introduced universal hashing in 1979, which turned adversarial resistance from a hope into a theorem, and Fredman, Komlós, and Szemerédi gave the first O(1) worst-case scheme in 1984. Pagh and Rodler's cuckoo hashing (2001) achieved the same worst-case guarantee with a far simpler structure.

Robin Hood hashing comes from Pedro Celis's work with Per-Åke Larson and Ian Munro at Waterloo, published at FOCS in 1985 and in Celis's 1986 PhD thesis. Crosby and Wallach described algorithmic complexity attacks on hash tables in 2003; Klink and Wälde's 28C3 talk in December 2011 showed how widely web platforms were exposed, and Aumasson and Bernstein's SipHash (2012) became the standard response. Swiss tables were designed at Google by Sam Benzaquen, Alkis Evlogimenos, Matt Kulukundis and Roman Perepelitsa, presented by Kulukundis at CppCon 2017, and open-sourced in Abseil in 2018. Rust adopted the design through `hashbrown` in 2019 and Go in 2025.

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

**12.6 ★★ Build the LRU cache.** Section 12.7 describes an LRU cache as a hash table pointing into a doubly linked list. Implement `LRUCache(capacity)` with `get(key)` (return the value or `None`, and mark the key most recently used) and `put(key, value)` (insert or update, evicting the least recently used key when full). Both must be O(1). Do not use `OrderedDict`.

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

**12.8 ★★ Robin Hood by hand.** Use the `RobinHoodTable` from Section 12.5 with capacity 8, so h(k) = k mod 8. (a) Insert 5, 6, 13, 14, 21 in that order and show the keys and PSLs after each insertion. (b) How many probes does an unsuccessful search for 29 take, and how many would it take in the plain linear-probing table holding the same keys? (c) Delete 13 and show the result.

<details>
<summary>Hint</summary>

21's walk wraps from slot 7 to slot 0, and the entry it evicts keeps walking.

</details>

<details>
<summary>Solution</summary>

(a) Writing each slot as key(PSL):

| Insert | Home | Result (slots 0 to 7) | What happened |
|--------|------|------------------------|---------------|
| 5 | 5 | `. . . . . 5(0) . .` | empty home slot |
| 6 | 6 | `. . . . . 5(0) 6(0) .` | empty home slot |
| 13 | 5 | `. . . . . 5(0) 13(1) 6(1)` | at slot 6, 13 has distance 1 and 6 has PSL 0, so 13 takes it; 6 moves to slot 7 |
| 14 | 6 | `14(2) . . . . 5(0) 13(1) 6(1)` | slots 6 and 7 hold PSL 1 against 14's 0 and 1; wraps to slot 0 |
| 21 | 5 | `14(2) 6(3) . . . 5(0) 13(1) 21(2)` | at slot 7, 21 has distance 2 and 6 has PSL 1: swap. 6 continues at distance 2, cannot take slot 0 (14 has PSL 2), lands in slot 1 |

(b) 29 has home 5. It sees 5(0) at distance 0, 13(1) at distance 1, 21(2) at distance 2, then 14(2) at slot 0 at distance 3. Since 2 < 3, the search stops: **4 probes**. Plain linear probing puts the same keys at `14 21 . . . 5 6 13`, and the search scans slots 5, 6, 7, 0, 1 and stops at the empty slot 2: **6 probes**.

(c) 13 is in slot 6. Backward shift moves 21 to slot 6 (PSL 1), 14 to slot 7 (PSL 1) and 6 to slot 0 (PSL 2), then stops at the empty slot 2 and clears slot 1:

```
slot:  0     1  2  3  4  5     6      7
       6(2)  .  .  .  .  5(0)  21(1)  14(1)
```

No tombstone was written, and every entry that moved is now one slot closer to home.

</details>

**12.9 ★★★ Robin Hood cannot change the average.** Insert the same keys in the same order into a plain linear-probing table and a Robin Hood table of the same size, with no deletions or resizes. Prove that the sum of all PSLs is the same in both, so the average successful lookup costs the same. What does Robin Hood change, then?

<details>
<summary>Hint</summary>

First show both tables have the same set of occupied slots. Then, during a Robin Hood insertion, track the quantity T = (sum of PSLs of the entries in the table) + (current distance of the entry being carried).

</details>

<details>
<summary>Solution</summary>

**Same occupied slots.** By induction on insertions. Suppose both tables have the same occupied set and a key with home h arrives. Linear probing puts it in e, the first empty slot at or after h. Robin Hood's walk also starts at h and moves forward one slot at a time; swaps exchange which entry occupies a slot but never empty or fill one, so the walk ends by filling the same slot e. The occupied sets stay equal.

**Same total.** Linear probing adds one entry with PSL (e − h) mod m, so the total grows by (e − h) mod m. For Robin Hood, track T as in the hint. At the start of the walk T is the old total plus 0. A step to the next slot adds 1 to the carried entry's distance, so T grows by 1. A swap puts the carried entry, with distance d, into the slot and picks up the occupant with its PSL d′: the table's sum changes by d − d′ and the carried distance by d′ − d, so T is unchanged. The walk takes (e − h) mod m steps, and when it ends the carried entry is placed at e, so the new total is the old total plus (e − h) mod m, exactly as for linear probing.

(Without wraparound there is a one-line version: the total PSL is Σ(position − home) = Σ positions − Σ homes. The first sum depends only on the occupied set and the second only on the keys.)

So the mean PSL, and the average successful-search cost of 1 + mean PSL, is identical. Robin Hood only redistributes the total: it takes slots from entries near home and gives them to entries far from home, which shrinks the variance and the maximum, as the table in Section 12.5 shows. Separately, its invariant lets *unsuccessful* searches stop early, so those do get cheaper on average.

</details>

**12.10 ★★★ Matching without SIMD.** Go's map on architectures other than amd64, and hashbrown on targets without SSE2, use groups of 8 control bytes packed into one 64-bit integer and find matches with ordinary arithmetic. With `LSB = 0x0101010101010101` and `MSB = 0x8080808080808080`, the match is:

```
x = word XOR (h2 × LSB)
match = (x − LSB) AND (NOT x) AND MSB
```

(a) Implement it in Python (byte j of the group is bits 8j to 8j + 7) and run it on the group `0x15 0x80 0x3A 0x15 0xFE 0x61 0x80 0x0C` with H2 = 0x15. (b) Show that a byte equal to h2 is always flagged, and that an empty or deleted byte (top bit set) never is. (c) The test can flag a byte that does not equal h2. Find an example, say exactly when it happens, and explain why it is harmless.

<details>
<summary>Hint</summary>

XOR turns matching bytes into 0x00. Think about what subtracting 0x01 does to a 0x00 byte, and what the resulting borrow does to the byte above it.

</details>

<details>
<summary>Solution</summary>

(a)

```python
LSB = 0x0101010101010101            # 0x01 in every byte
MSB = 0x8080808080808080            # 0x80 in every byte
MASK64 = (1 << 64) - 1

def match_h2(word, h2):
    """0x80 in every byte of word that (probably) equals h2."""
    x = word ^ (h2 * LSB)            # bytes equal to h2 become 0x00
    return (x - LSB) & ~x & MSB & MASK64

group = bytes([0x15, 0x80, 0x3A, 0x15, 0xFE, 0x61, 0x80, 0x0C])
word = int.from_bytes(group, "little")
assert match_h2(word, 0x15) == 0x80000080        # bytes 0 and 3

fp = int.from_bytes(bytes([0x15, 0x14] + [0x80] * 6), "little")
assert match_h2(fp, 0x15) == 0x8080              # byte 1 is a false positive
```

(b) Take one byte b of x, ignoring borrows for now. If b = 0x00 (the control byte equals h2), then b − 1 = 0xFF with the top bit set, and NOT b = 0xFF also has it set, so the byte is flagged. A borrow coming in from below only makes b − 1 smaller, and 0x00 minus 1 or 2 still has the top bit set, so a true match is never missed. If the control byte is empty or deleted, its top bit is 1 and h2's is 0, so b has its top bit set and NOT b has it clear: the AND with NOT x removes it whatever the subtraction produced. Special bytes are never reported.

(c) The subtraction borrows across bytes. A matching byte (b = 0x00) borrows from the byte above it, which therefore has 2 subtracted instead of 1. If that byte is b = 0x01, then 0x01 − 2 = 0xFF (top bit set) and NOT 0x01 = 0xFE (top bit set), so it is flagged. That happens exactly when a full control byte equals h2 XOR 0x01 and sits directly above a true match (or above another such byte in a chain). In the example, byte 1 holds 0x14 = 0x15 XOR 0x01 just above the 0x15 in byte 0. It is harmless because every flagged slot has its key compared before anything is returned: a false positive costs one extra comparison and never a wrong answer, and by (b) it can never be an empty or deleted slot. Implementations accept it because the exact version needs more instructions on every probe.

</details>

---

## Where this connects

- [Chapter 14: Probabilistic Data Structures](../volume-3/ch14-probabilistic-data-structures.md). Trading exactness for a 10-100x memory reduction
- [Chapter 18: Concurrent Data Structures](../volume-3/ch18-concurrent-data-structures.md). What it takes to make a hash table concurrent
