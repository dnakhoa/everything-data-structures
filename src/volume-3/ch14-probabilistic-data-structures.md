# Chapter 14: Probabilistic Data Structures

## 14.1 The Probabilistic Approach

Sometimes we don't need exact answers—we need fast, space-efficient approximate answers. Probabilistic data structures trade accuracy for speed and space.

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

**False positive probability:**
```
p ≈ (1 - e^(-kn/m))^k

Optimal k = (m/n) × ln 2
```

**Properties:**
- False positives possible
- False negatives impossible
- Cannot delete (Counting Bloom Filter needed)
- Space: ~1.44 × log₂(1/p) bits per element

## 14.3 Counting Bloom Filters

Store counters instead of bits to enable deletion:

```
Standard Bloom:     [1] [0] [1] [0]
Counting Bloom:     [3] [0] [2] [0]

After deleting one "apple" (counters decrement):
Counting Bloom:     [2] [0] [1] [0]
```

## 14.4 Cuckoo Filters

Modern alternative to Bloom filters:
- Better space efficiency
- Supports deletion
- O(1) expected operations
- Uses cuckoo hashing internally

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

Final estimate: E = α × m² / Σ(2^(-M[i]))
```

## 14.6 Count-Min Sketch

Estimates frequency of items:

```
Structure: d rows, w columns
Each row has its own hash function

Add x: increment position h_i(x) in row i
Estimate count of x: min over all rows of count at h_i(x)

Always overestimates (never underestimates)
```

## 14.7 Applications

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

---

## Where this connects

- [Chapter 12: Hash Tables](../volume-2/ch12-hash-tables.md) — the exact structure these approximate
- [Chapter 30: Advanced System Patterns and Case Studies](../volume-5/ch30-advanced-system-patterns-and-case-studies.md) — where sketches are deployed in production systems
