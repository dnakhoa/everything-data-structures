# Chapter 14: Probabilistic Data Structures

## 14.1 The Probabilistic Approach

Sometimes we don't need exact answers, we need fast, space-efficient approximate answers. Probabilistic data structures trade accuracy for speed and space.

That trade is worth stating precisely, because the amount of accuracy given up is small and the amount of space saved is not. Tracking the unique visitors to a website exactly means storing every visitor ID: 100 million IDs at 16 bytes each is 1.6GB. A HyperLogLog answers the same question with a standard error under 1% using **12 kilobytes**: a factor of 130,000. For a dashboard, an error of a percent or two is invisible and 1.6GB is not.

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

A cuckoo filter stores a short **fingerprint** of each element (typically 8 to 12 bits) in a cuckoo hash table with two candidate buckets per item. A query checks both buckets for the fingerprint.

The trick that makes it work is **partial-key cuckoo hashing**. Standard cuckoo hashing needs the original key to relocate an item, and a filter has thrown the key away. Cuckoo filters compute the second bucket as:

```
bucket2 = bucket1 XOR hash(fingerprint)
```

Because XOR is its own inverse, either bucket yields the other from the fingerprint alone, so items can be relocated without ever storing the key.

Versus a Bloom filter: about 20% less space at false-positive rates below 3%, genuine deletion support, and better cache behavior (two bucket probes instead of k scattered bit tests). Against: insertion can fail when eviction chains grow too long, so the table must stay below about 95% load, and like counting Bloom filters, deleting something never inserted corrupts it.

Use a cuckoo filter when you need deletion or the lowest false-positive rate per bit. Use a Bloom filter when you need guaranteed insertion and maximum simplicity.

## 14.5 HyperLogLog

Estimates the number of distinct elements with about 0.81% standard error using 12 KB (derived below):

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

Standard error is 1.04/√m. With m = 16,384 registers at 6 bits each (12KB), that is 0.81% error, for a set of any cardinality up to about 2⁶⁴.

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

**t-digest** estimates quantiles (medians, p95, p99) over a stream in a few kilobytes, with the crucial property that accuracy is *highest at the extremes*. Ordinary sampling gives uniform accuracy, which is backwards for latency monitoring: nobody cares about a precise median, and everyone cares about p99. t-digest is what Prometheus-adjacent tooling, Elasticsearch percentile aggregations, and most latency dashboards use.

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

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**14.1 ★ Size a Bloom filter, then overfill it.** You expect 1,000,000 items and want a 1% false-positive rate. (a) Using the formulas in the `BloomFilter` constructor, compute m (bits) and k. How much memory is that? (b) The estimate was wrong and 2,000,000 items arrive. What is the false-positive rate now? And at 3,000,000?

<details>
<summary>Solution</summary>

(a) m = ⌈−n ln p / (ln 2)²⌉ = ⌈1,000,000 × 4.6052 / 0.48045⌉ = **9,585,059 bits**, about 1.2 MB (9.6 bits per item, matching the table). k = round((m/n) ln 2) = round(6.64) = **7**.

(b) Plug into p ≈ (1 − e^(−kn/m))^k with m and k fixed:

| Items inserted | kn/m | Fraction of bits set | False-positive rate |
|----------------|------|----------------------|---------------------|
| 1,000,000 | 0.730 | 0.518 | 1.0% |
| 2,000,000 | 1.461 | 0.768 | 15.7% |
| 3,000,000 | 2.191 | 0.888 | 43.6% |

Doubling the load multiplies the false-positive rate by about 16, and tripling it makes the filter close to useless. This is what "degrades quickly rather than gracefully" means in Section 14.2: p is a k-th power of the fill fraction, so a modest rise in fill is amplified seven times over. Size for the load you will actually reach, or use a scalable Bloom filter.

</details>

**14.2 ★ Match the structure to the mistake.** For each task, pick a structure from the table in Section 14.1 and say which direction its error goes and why that direction is acceptable here. (a) Before querying the database, check whether a username might already be taken. (b) Count distinct daily visitors across 50 web servers. (c) Find the source IPs sending the most packets through a router. (d) Track which articles each user has already seen, where articles expire and must be removed.

<details>
<summary>Solution</summary>

(a) **Bloom filter.** False positives only. A false "maybe taken" costs one database query to confirm; a false negative would let a duplicate through, and a Bloom filter never produces one.

(b) **HyperLogLog**, one per server, merged at a coordinator by taking the register-wise maximum. Error is about ±1% in either direction, which is fine for a dashboard number, and the merge means no raw visitor IDs cross the network.

(c) **Count-Min Sketch.** Overestimates only, and the error is bounded by ε·N, so it is small relative to heavy hitters and large relative to rare items. That is the right bias for this task: the top talkers are estimated accurately, and nobody cares about precise counts for IPs that sent three packets.

(d) **Cuckoo filter** (or a counting Bloom filter). Still false positives only, which here means occasionally hiding an article the user has not actually seen: a mild cost. Expiry needs deletion, which a plain Bloom filter cannot do. The rule from Section 14.3 applies: delete only articles that were actually inserted.

</details>

**14.3 ★★ Trace a Count-Min Sketch.** A sketch has d = 2 rows and w = 5 columns, with hashes

| Item | h₀ | h₁ |
|------|----|----|
| a | 0 | 1 |
| b | 2 | 1 |
| c | 0 | 3 |
| d | 4 | 3 |

Process the stream `a a a b c c d`. (a) Show both rows. (b) Give the estimate for each item and compare it to the true count. (c) For ε = 0.001 and δ = 0.01, what w and d does Section 14.6 prescribe?

<details>
<summary>Solution</summary>

(a) True counts: a = 3, b = 1, c = 2, d = 1.

```
row 0 (h₀):  [5] [0] [1] [0] [1]     cell 0 = a + c = 3 + 2
row 1 (h₁):  [0] [4] [0] [3] [0]     cell 1 = a + b, cell 3 = c + d
```

(b)

| Item | Row 0 | Row 1 | Estimate (min) | True | Error |
|------|-------|-------|----------------|------|-------|
| a | 5 | 4 | 4 | 3 | +1 |
| b | 1 | 4 | 1 | 1 | 0 |
| c | 5 | 3 | 3 | 2 | +1 |
| d | 1 | 3 | 1 | 1 | 0 |

Every estimate is ≥ the truth, as promised. `a` and `c` are overestimated because *both* of their rows had collisions; the minimum only helps when at least one row is clean. More rows make that more likely, which is what d buys.

(c) w = ⌈e/ε⌉ = ⌈2718.28⌉ = **2,719** and d = ⌈ln(1/δ)⌉ = ⌈ln 100⌉ = ⌈4.61⌉ = **5**, so 13,595 counters. With probability at least 99%, every estimate is within 0.001 × N of the truth, where N is the total stream length, regardless of how many distinct items there are.

</details>

**14.4 ★★ HyperLogLog arithmetic.** (a) Four registers hold maximum leading-zero counts M = [2, 3, 2, 10]. Compare the arithmetic mean and the harmonic mean of the per-register estimates 2^M[i]. Which better reflects the three "normal" registers? (b) How many registers does HyperLogLog need for a standard error of 1%, given that m must be a power of two? How much memory at 6 bits per register? (c) Explain why merging two sketches by register-wise maximum gives *exactly* the sketch of the union.

<details>
<summary>Solution</summary>

(a) The per-register estimates are 4, 8, 4, 1024.

- Arithmetic mean: (4 + 8 + 4 + 1024) / 4 = **260**.
- Harmonic mean: 4 / (1/4 + 1/8 + 1/4 + 1/1024) = 4 / 0.62598 ≈ **6.39**.

One unlucky register drags the arithmetic mean up by a factor of 50. In the harmonic mean, the outlier contributes 1/1024 to the denominator, almost nothing, so the result stays near the typical register. This is why the estimator in Section 14.5 sums 2^(−M[i]).

(b) Solve 1.04/√m ≤ 0.01: √m ≥ 104, so m ≥ 10,816. The next power of two is **2¹⁴ = 16,384** (2¹³ = 8,192 gives 1.15%, not good enough). At 6 bits each that is 16,384 × 6 / 8 = 12,288 bytes, **12 KB**, the figure the chapter quotes, with an actual standard error of 0.81%.

(c) A register's value depends only on the elements whose hashes route to it: M[i] = max of the leading-zero count over those elements. For the union, the elements routed to register i are those from A plus those from B, and the maximum over a union is the maximum of the two maxima. Duplicates do no harm, because the same element produces the same hash and the same count in both sketches. So max(M_A[i], M_B[i]) is not an approximation of the union's register; it is the union's register.

</details>

**14.5 ★★ Find the bug.** Someone replaces the Kirsch-Mitzenmacher positions in `BloomFilter` with a "simpler" version:

```python
def _positions(self, item):
    h = hash(item)
    for i in range(self.k):
        yield (h + i) % self.m
```

m and k are still sized for 1%. The filter has no false negatives and is still about half full after n insertions. What goes wrong, and roughly how badly?

<details>
<summary>Hint</summary>

Picture the bit array after many insertions. Does a run of 7 consecutive 1-bits now happen by coincidence?

</details>

<details>
<summary>Solution</summary>

The k positions are no longer independent: each item sets one *run* of k consecutive bits. The false-positive formula assumes the k positions of a query are scattered, so each is independently 1 with probability about ½, giving (½)⁷ ≈ 1%. Here the query also tests a run of 7 consecutive bits, and the set bits are clumped into runs, so a run of 7 ones is far more common than (½)⁷. In particular, any query whose start lands inside an existing run (or in a region where overlapping runs have merged) is a false positive with no coincidence required.

Simulating it (n = 1,000, m = 9,586, k = 7, uniform random h) gives a false-positive rate of about **22%**, against 1.05% for `h1 + i*h2` with the same m and k. The fill fraction is the same in both (about 50%); only the correlation changed.

The fix is the chapter's version: two independent hashes, with positions h1 + i·h2. h2 must also be non-zero mod m, or every position collapses to h1 and that item behaves as if k = 1, so a careful implementation guards against it.

</details>

**14.6 ★★★ Derive the optimal k.** Starting from p = (1 − e^(−kn/m))^k, show that the false-positive rate is minimised at k = (m/n) ln 2, that the filter is then exactly half full, and that the bits per element needed for a target p is about 1.44 log₂(1/p). Use it to reproduce the 1% row of the table in Section 14.2.

<details>
<summary>Hint</summary>

Substitute q = e^(−kn/m), the expected fraction of bits still 0, and write ln p in terms of q alone.

</details>

<details>
<summary>Solution</summary>

Let q = e^(−kn/m). Then k = −(m/n) ln q, and

ln p = k · ln(1 − q) = −(m/n) · ln q · ln(1 − q).

For fixed m and n, minimising p means maximising f(q) = ln q · ln(1 − q) over 0 < q < 1. Both factors are negative, so f is positive, and f is symmetric: f(q) = f(1 − q). Its derivative, f′(q) = ln(1 − q)/q − ln q/(1 − q), vanishes at q = ½, and that is its only zero in (0, 1), so q = ½ is the maximum.

- q = ½ means half the bits are still 0: **the optimal filter is half full**.
- e^(−kn/m) = ½ gives **k = (m/n) ln 2**.
- The false-positive rate is then p = (1 − ½)^k = 2^(−k) = 2^(−(m/n) ln 2).

Solving for bits per element: log₂(1/p) = (m/n) ln 2, so

m/n = log₂(1/p) / ln 2 ≈ **1.44 · log₂(1/p)**,

which is the "Space" line in Section 14.2's properties list, and equals −ln p / (ln 2)², the formula in the constructor.

For p = 1%: log₂ 100 = 6.644, so m/n = 6.644 / 0.6931 = **9.59 bits**, and k = 9.59 × 0.6931 = 6.64, rounded to **7**. Each extra bit per element multiplies p by 2^(−ln 2) ≈ 0.62, which is why every 4.8 bits per element buys a factor of 10.

</details>

**14.7 ★★★ Why MinHash works.** (a) Let h be a random hash function with no ties, so the element of A ∪ B with the smallest hash is equally likely to be any of them. Prove that Pr[min h(A) = min h(B)] = |A ∩ B| / |A ∪ B|. (b) Implement `signature(items, k)` and `estimate_jaccard(sig_a, sig_b)`, and check it on A = {0, ..., 599} and B = {300, ..., 899}.

<details>
<summary>Hint</summary>

Look at the single element x of A ∪ B with the smallest hash. When is it the minimum of A? Of B? Of both?

</details>

<details>
<summary>Solution</summary>

(a) Let x be the element of A ∪ B with the smallest hash value. x is the minimum of A if x ∈ A (nothing in A can be smaller than the minimum of a superset), and similarly for B. If x ∈ A ∩ B, both minima equal h(x). If x is in only one set, say A, then min h(A) = h(x), while min h(B) is the hash of some other element and is strictly larger (no ties). So the minima agree **exactly** when x ∈ A ∩ B. Since x is uniform over A ∪ B,

Pr[min h(A) = min h(B)] = |A ∩ B| / |A ∪ B| = J(A, B).

Each of k independent hash functions gives an independent yes/no trial with success probability J, so the fraction of agreeing minima estimates J with standard error √(J(1 − J)/k) ≤ 1/(2√k).

(b)

```python
import hashlib

def h(seed, item):
    """One member of a family of hash functions, chosen by `seed`."""
    data = ("%d:%s" % (seed, item)).encode()
    return int.from_bytes(hashlib.blake2b(data, digest_size=8).digest(), "big")

def signature(items, k):
    return [min(h(seed, x) for x in items) for seed in range(k)]

def estimate_jaccard(sig_a, sig_b):
    return sum(x == y for x, y in zip(sig_a, sig_b)) / len(sig_a)

A = set(range(0, 600))
B = set(range(300, 900))                # |A & B| = 300, |A | B| = 900
est = estimate_jaccard(signature(A, 400), signature(B, 400))
assert abs(est - 1 / 3) < 0.07          # standard error is about 0.024
```

The true similarity is 300/900 = 1/3. The signatures are 400 integers each regardless of set size, and comparing them costs O(k), not O(|A| + |B|).

One trap worth knowing: the proof needs the minimum to be uniform over the set, and cheap linear hashes such as (a·x + b) mod p do not deliver that on structured keys like consecutive integers. On this exact example, a linear family with p = 2⁶¹ − 1 gives estimates around 0.28 to 0.29 instead of 0.33, and the bias stays when k is raised to 4,000, because it is in each hash function, not in the sampling. Use a well-mixed hash.

</details>

---

## Where this connects

- [Chapter 12: Hash Tables](../volume-2/ch12-hash-tables.md). The exact structure these approximate
- [Chapter 16: External Memory and Cache-Oblivious Structures](ch16-external-memory-and-cache-oblivious-structures.md). Why Bloom filters are what make LSM-tree reads viable
