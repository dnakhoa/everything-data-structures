# Chapter 14: Probabilistic Data Structures

## 14.1 The Probabilistic Approach

Sometimes we don't need exact answers, we need fast, space-efficient approximate answers. Probabilistic data structures trade accuracy for speed and space.

That trade is worth stating precisely, because the amount of accuracy given up is small and the amount of space saved is not. Tracking the unique visitors to a website exactly means storing every visitor ID: 100 million IDs at 16 bytes each is 1.6GB. A HyperLogLog answers the same question to within about 2% using **12 kilobytes**: a factor of 130,000. For a dashboard, 2% error is invisible and 1.6GB is not.

The general shape of every structure in this chapter:

- **Hash the input.** A good hash turns arbitrary data into uniformly distributed bits, and uniformity is what makes the statistics work.
- **Keep a lossy summary of the hashes** rather than the data itself. Bits set, maximum leading-zero counts, counter minima.
- **Accept a bounded, quantifiable error** in exchange for space that grows far more slowly than n, often not at all.

The critical design question for any of them is **which direction the error goes**, because a one-sided error is usually safe to build on and a two-sided one usually isn't:

| Structure | Answers | Error direction | Space |
|-----------|---------|-----------------|-------|
| Bloom filter | Is x in the set? | False positives only | ~10 bits/element at 1% |
| Counting Bloom | Same, with deletion | False positives only | 4× a Bloom filter |
| Cuckoo filter | Same, with deletion | False positives only | ~20% less than Bloom |
| HyperLogLog | How many distinct? | ±2% both directions | ~12KB, fixed |
| Count-Min Sketch | How often is x? | Overestimates only | O((1/ε)·log(1/δ)) |
| MinHash | How similar are two sets? | ±ε both directions | k hashes per set |
| t-digest | What is the 99th percentile? | Accurate at the tails | ~kilobytes |

"False positives only" is what makes a Bloom filter safe as a cache filter: a false positive costs one wasted lookup, while a false negative would mean losing data. Match the error direction to what a mistake costs you.

## 14.2 Bloom Filters

<figure>
{{#include ../images/bloom-filter.svg}}
<figcaption>Why a Bloom filter can produce false positives but never false negatives.</figcaption>
</figure>

A Bloom filter tells you if an element is "probably in the set" or "definitely not."

**Structure:**
- m-bit array, all initially 0
- k hash functions
- Insert: Set bits at h₁(x), h₂(x), ..., hₖ(x)
- Query: Check if all bits at h₁(x), h₂(x), ..., hₖ(x) are 1

```
Bloom filter with m=12, k=3:

After inserting "apple", "banana":
bits: [1] [0] [1] [0] [0] [1] [0] [1] [0] [1] [0] [1]
       0   1   2   3   4   5   6   7   8   9  10  11

Query "grape": bits 2,5,9 all 1 → "Probably present" (false positive!)
Query "mango": bit 3 is 0 → "Definitely not present"
```

The asymmetry is structural, not a limitation to be engineered away. Insertion only ever sets bits to 1 and never clears them, so a bit that is 0 proves that nothing which hashes there was inserted, "definitely not present" is a proof. A bit that is 1 only proves *something* set it, which may have been a different element. Hence: no false negatives, ever; false positives at a rate you choose.

```python
class BloomFilter:
    def __init__(self, expected_items, false_positive_rate=0.01):
        # These two formulas are the whole design.
        self.m = math.ceil(-expected_items * math.log(false_positive_rate)
                           / (math.log(2) ** 2))
        self.k = max(1, round(self.m / expected_items * math.log(2)))
        self.bits = bytearray((self.m + 7) // 8)

    def _positions(self, item):
        # Kirsch-Mitzenmacher: two real hashes simulate k of them
        # with no loss in the false-positive bound.
        h1, h2 = mmh3.hash64(item)
        for i in range(self.k):
            yield (h1 + i * h2) % self.m

    def add(self, item):
        for pos in self._positions(item):
            self.bits[pos // 8] |= 1 << (pos % 8)

    def __contains__(self, item):
        return all(self.bits[pos // 8] >> (pos % 8) & 1
                   for pos in self._positions(item))
```

**False positive probability:**
```
p ≈ (1 - e^(-kn/m))^k

Optimal k = (m/n) × ln 2
```

The optimal k balances two opposing pressures: more hash functions means more bits must coincidentally align for a false positive, but also more bits set per insertion, filling the array faster. The optimum falls where the array is exactly half full, which is a pleasing result. A Bloom filter operating at its design capacity has half its bits set.

What the formula implies in practice, which is the part worth memorising:

| Target false-positive rate | Bits per element | Hash functions |
|---------------------------|------------------|----------------|
| 10% | 4.8 | 3 |
| 1% | 9.6 | 7 |
| 0.1% | 14.4 | 10 |
| 0.01% | 19.2 | 13 |

**Bits per element is independent of element size.** Ten bits per element whether the elements are 8-byte integers or 2KB URLs. That property is why Bloom filters appear wherever the exact set would not fit in memory.

The `Kirsch-Mitzenmacher` trick in the code above matters for performance: computing seven independent hash functions is expensive, and it turns out two are enough. `h1 + i*h2` gives the same asymptotic false-positive rate. Every production implementation does this.

**Properties:**
- False positives possible
- False negatives impossible
- Cannot delete (Counting Bloom Filter needed)
- Space: ~1.44 × log₂(1/p) bits per element

Two further constraints that catch people. **You must size it in advance**. A Bloom filter cannot grow, and exceeding the expected count degrades the false-positive rate quickly rather than gracefully. (Scalable Bloom filters chain progressively larger filters to work around this.) And **you cannot enumerate the contents**: a Bloom filter can answer questions about membership but cannot tell you what it holds.

## 14.3 Counting Bloom Filters

Store counters instead of bits to enable deletion:

```
Standard Bloom:     [1] [0] [1] [0]
Counting Bloom:     [3] [0] [2] [0]

After deleting one "apple" (counters decrement):
Counting Bloom:     [2] [0] [1] [0]
```

Deleting from a standard Bloom filter is impossible because clearing a bit might erase evidence of a different element that happens to share it. Counters fix this by recording *how many* elements set each position.

The cost is 4× the space, since 4 bits per counter is the usual choice. Four bits caps a counter at 15, and **counter overflow is the failure mode to know about**: if a counter saturates it must stop incrementing, and thereafter decrements can take it below its true value, which reintroduces false negatives, the one guarantee the structure was supposed to keep. With good hashing, overflow at 4 bits is vanishingly rare, but the analysis assumes it never happens.

Delete only elements you actually inserted. Deleting an element that was never added decrements counters that belong to other elements and silently corrupts the filter.

## 14.4 Cuckoo Filters

Modern alternative to Bloom filters:
- Better space efficiency
- Supports deletion
- O(1) expected operations
- Uses cuckoo hashing internally

A cuckoo filter stores a short **fingerprint** of each element (typically 8 to 12 bits)in a cuckoo hash table with two candidate buckets per item. A query checks both buckets for the fingerprint.

The trick that makes it work is **partial-key cuckoo hashing**. Standard cuckoo hashing needs the original key to relocate an item, and a filter has thrown the key away. Cuckoo filters compute the second bucket as:

```
bucket2 = bucket1 XOR hash(fingerprint)
```

Because XOR is its own inverse, either bucket yields the other from the fingerprint alone, so items can be relocated without ever storing the key.

Versus a Bloom filter: about 20% less space at false-positive rates below 3%, genuine deletion support, and better cache behavior (two bucket probes instead of k scattered bit tests). Against: insertion can fail when eviction chains grow too long, so the table must stay below about 95% load, and like counting Bloom filters, deleting something never inserted corrupts it.

Use a cuckoo filter when you need deletion or the lowest false-positive rate per bit. Use a Bloom filter when you need guaranteed insertion and maximum simplicity.

## 14.5 HyperLogLog

Estimates the number of distinct elements with ~2% error using ~12KB:

```
Idea: Hash each element
If hash starts with k zeros, it's a rare event
The maximum number of leading zeros seen estimates n ≈ 2^R

Register-based improvement:
Split hash into:
- r bits → register index (2^r registers)
- (64-r) bits → count leading zeros
```

The intuition is worth dwelling on because it is genuinely clever. If hashes are uniformly random bit strings, then roughly half start with `0`, a quarter with `00`, an eighth with `000`. So seeing a hash with 10 leading zeros suggests you have probably looked at around 2¹⁰ distinct values. The rarest event you have observed tells you how many trials you have run.

Using only the single maximum is very noisy: one unlucky hash with 20 leading zeros would suggest a million elements when there were ten. The fix is **stochastic averaging**: use the first r bits of the hash to pick one of 2^r registers, track the maximum leading-zero count separately in each, and combine them. The registers partition the input, so their estimates are independent, and averaging 16,384 independent estimates cuts the error by √16384 = 128.

The combination uses a **harmonic** mean, not an arithmetic one, because the harmonic mean suppresses the influence of a single large outlier: precisely the failure mode being defended against:

```
E = α_m · m² / Σᵢ 2^(−M[i])

m = number of registers, M[i] = max leading zeros in register i
α_m ≈ 0.7213 / (1 + 1.079/m)     bias correction constant
```

Standard error is 1.04/√m. With m = 16,384 registers at 6 bits each (12KB)that is 0.81% error, for a set of any cardinality up to about 2⁶⁴.

**The mergeability is the underrated property.** The union of two HyperLogLogs is the element-wise maximum of their registers. That means cardinality across a hundred servers can be computed by each server keeping its own sketch and sending 12KB to a coordinator. No coordination, no shuffling of raw data, and the merge is exact. Merging sketches of A and B gives precisely the sketch you'd get from counting A ∪ B directly. This is why every distributed analytics system uses it.

Intersections, however, are *not* supported. Inclusion-exclusion (|A∩B| = |A| + |B| − |A∪B|) compounds the error of three estimates and produces garbage when the sets differ greatly in size.

## 14.6 Count-Min Sketch

Estimates frequency of items:

```
Structure: d rows, w columns
Each row has its own hash function

Add x: increment position h_i(x) in row i
Estimate count of x: min over all rows of count at h_i(x)

Always overestimates (never underestimates)
```

Where a Bloom filter answers "is x present", a Count-Min Sketch answers "how many times have I seen x": in fixed space, for a stream of unbounded length.

```
d=3 rows, w=6 columns. Adding "apple" three times:

row 0 (h₀):  [0] [3] [0] [0] [0] [0]     h₀(apple) = 1
row 1 (h₁):  [0] [0] [0] [3] [0] [0]     h₁(apple) = 3
row 2 (h₂):  [0] [0] [3] [0] [0] [0]     h₂(apple) = 2

Now add "banana" twice, and suppose h₀(banana) = 1 too:

row 0:  [0] [5] [0] [0] [0] [0]     ← collision inflates this cell
row 1:  [0] [0] [2] [3] [0] [0]
row 2:  [0] [0] [3] [2] [0] [0]

estimate("apple") = min(5, 3, 3) = 3   ✓ the collision is discarded
```

**Why the minimum works**: every cell for x contains x's true count plus whatever collided there. Collisions only ever add, so every row gives an overestimate, and the smallest is the least-contaminated. With d rows the chance that *every* row collided badly falls exponentially.

The error bound is additive relative to the total stream volume: with w = ⌈e/ε⌉ and d = ⌈ln(1/δ)⌉, the estimate exceeds the truth by more than ε·N with probability at most δ, where N is the total count of all items. The practical implication is that **heavy hitters are estimated accurately and rare items are not**. An item appearing 0.001% of the time may be swamped by noise. That is usually the right bias, since heavy hitters are what these are deployed to find.

Count-Min sketches are linear: adding two sketches element-wise gives the sketch of the combined stream. Same distributed benefit as HyperLogLog.

## 14.7 Two More Worth Knowing

**MinHash** estimates the Jaccard similarity of two sets (|A∩B|/|A∪B|)without comparing them. Hash every element of a set and keep the minimum hash. The probability that two sets share the same minimum is exactly their Jaccard similarity, so keeping k independent minima estimates it to within about 1/√k. Combined with locality-sensitive hashing, this is how near-duplicate detection works at web scale: Google used it for deduplicating crawled pages, and it remains standard for plagiarism detection and clustering.

**t-digest** estimates quantiles (medians, p95, p99)over a stream in a few kilobytes, with the crucial property that accuracy is *highest at the extremes*. Ordinary sampling gives uniform accuracy, which is backwards for latency monitoring: nobody cares about a precise median, and everyone cares about p99. t-digest is what Prometheus-adjacent tooling, Elasticsearch percentile aggregations, and most latency dashboards use.

## 14.8 Applications

**Bloom Filters:**
- Web caching (Akamai, Google Chrome)
- Database optimization (Google Bigtable)
- Bitcoin SPV nodes
- Spell checkers

**HyperLogLog:**
- Google BigQuery
- Redis (PFADD, PFCOUNT)
- Analytics dashboards

**Count-Min Sketch:**
- Network traffic analysis
- Database query optimization

The single highest-leverage deployment is in **LSM-tree storage engines**. A read in an LSM tree may need to check several sorted runs on disk, and most of them will not contain the key. A Bloom filter per run answers "definitely not here" from memory, skipping the disk read entirely. Cassandra, RocksDB, LevelDB, HBase, and Bigtable all do this, and it is the difference between an LSM read being one disk seek and being ten: see [Chapter 16](ch16-external-memory-and-cache-oblivious-structures.md).

Also worth noting: Chrome's Safe Browsing originally shipped a Bloom filter of malicious URLs so the browser could check locally and only consult Google's servers on a hit, privacy and latency from the same structure. Medium uses them to avoid re-recommending read articles; Ethereum puts one in every block header so light clients can skip blocks with no relevant logs.

## 14.9 Historical Context

Burton Bloom published his filter in 1970 in a two-page CACM paper about hyphenation dictionaries. The problem was that a full dictionary would not fit in the memory of the machines of the day. The structure sat quietly for two decades until networking and databases at scale made it indispensable.

Philippe Flajolet spent much of his career on this family. Probabilistic counting came in 1985 with Nigel Martin, LogLog in 2003, and HyperLogLog in 2007 with Fusy, Gandouet, and Meunier. Flajolet's approach: *analytic combinatorics*, using complex analysis to derive exact constants like that 0.7213. Is why these structures come with precise error bounds rather than empirical rules of thumb. He died in 2011; HyperLogLog now runs in essentially every large-scale analytics system.

Graham Cormode and S. Muthukrishnan introduced the Count-Min Sketch in 2005, and Andrei Broder developed MinHash at AltaVista in 1997 for exactly the problem the web had just created: too many near-identical pages.

---

## Where this connects

- [Chapter 12: Hash Tables](../volume-2/ch12-hash-tables.md). The exact structure these approximate
- [Chapter 16: External Memory and Cache-Oblivious Structures](ch16-external-memory-and-cache-oblivious-structures.md). Why Bloom filters are what make LSM-tree reads viable
