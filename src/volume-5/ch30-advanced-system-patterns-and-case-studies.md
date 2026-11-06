# Chapter 30: Advanced System Patterns and Case Studies

## 30.1 Search Infrastructure: Inverted Index

Full-text search engines use inverted indexes for efficient keyword lookups.

### Inverted Index Structure

```
Document collection:
Doc1: "data structures are fundamental"
Doc2: "data structures enable efficient algorithms"

Forward index (doc → terms):
Doc1 → ["data", "structures", "are", "fundamental"]
Doc2 → ["data", "structures", "enable", "efficient", "algorithms"]

Inverted index (term → docs):
"data"      → [Doc1, Doc2]
"structures"→ [Doc1, Doc2]
"are"       → [Doc1]
"fundamental" → [Doc1]
"enable"    → [Doc2]
"efficient" → [Doc2]
"algorithms"→ [Doc2]
```

**Posting list**: Each term points to a sorted list of document IDs.

Real postings carry more than the ID: the term frequency in that document (BM25 needs it, below) and often the positions of each occurrence (for phrase queries). The ID part is the hard part to make small and fast, and the rest of this section is about it: how the lists are compressed, how two of them are intersected, how the best k documents are found without scoring every match, and how an index made of immutable compressed lists absorbs inserts and deletes.

### Compressing Posting Lists

A common term in a large index has a posting list of hundreds of millions of doc IDs, and a query reads every posting it touches. Stored as 32-bit integers, most of those bits are wasted, because the list is sorted: the information is in the distance from one ID to the next.

**Step 1: d-gaps (delta encoding).** Replace each ID by its difference from the previous one, keeping the first as it is. The gaps of a list sum to its last ID, so a term that appears in a fraction f of the documents has an average gap of about 1/f: a term in 10% of documents has gaps around 10, which fit in 4 bits. Rare terms have large gaps, but their lists are short, so they cost little either way. Decoding is a running sum, which means a list can only be decoded forward from a known starting point (its beginning, or a block boundary recorded in the skip data below).

**Step 2: variable-byte (varint) encoding.** Write each gap 7 bits at a time, lowest-order group first, and use the top bit of each byte as a continuation flag: 1 means another byte of this number follows, 0 means this is the last. Values below 128 take one byte, below 16,384 two, below 2,097,152 three. This is the layout of Lucene's VInt, the varint of Protocol Buffers, and LEB128 in DWARF and WebAssembly. (The variable-byte code in Manning, Raghavan and Schütze's *Introduction to Information Retrieval* puts the flag on the last byte instead and writes the high-order group first; the idea and the sizes are the same.)

<figure>
{{#include ../images/posting-list-compression.svg}}
<figcaption>Delta encoding turns large sorted IDs into small gaps, and varint stores each gap in as few bytes as it needs: 9 bytes instead of 20.</figcaption>
</figure>

The worked example in the figure: the term "data" occurs in documents 70000, 70003, 70010, 70130 and 90000. The gaps are 70000, 3, 7, 120 and 19870. The first gap is 17 bits, `100 0100010 1110000` in binary, so it splits into three 7-bit groups; emitted lowest first with the flag prepended, they are `1·1110000` = F0, `1·0100010` = A2 and `0·0000100` = 04. The gaps 3, 7 and 120 are below 128 and take one byte each (03, 07, 78), and 19870 takes three (9E 9B 01). Total: 9 bytes, against 20 as 32-bit integers and 15 as varints of the raw IDs, since every raw ID here is at least 16,384.

```python
from itertools import accumulate


def delta_encode(doc_ids, base=0):
    """Sorted doc IDs -> d-gaps. The first gap is measured from `base`."""
    return [d - p for p, d in zip([base] + doc_ids, doc_ids)]


def delta_decode(gaps, base=0):
    return list(accumulate(gaps, initial=base))[1:]


def varint_encode(numbers):
    """7 data bits per byte, low-order group first; a set high bit means 'more bytes follow'."""
    out = bytearray()
    for n in numbers:
        while n >= 0x80:
            out.append((n & 0x7F) | 0x80)
            n >>= 7
        out.append(n)
    return bytes(out)


def varint_decode(data):
    numbers, n, shift = [], 0, 0
    for byte in data:
        n |= (byte & 0x7F) << shift
        if byte & 0x80:
            shift += 7
        else:
            numbers.append(n)
            n, shift = 0, 0
    return numbers


postings = [70000, 70003, 70010, 70130, 90000]
gaps = delta_encode(postings)
assert gaps == [70000, 3, 7, 120, 19870]
encoded = varint_encode(gaps)
assert encoded.hex(" ") == "f0 a2 04 03 07 78 9e 9b 01"
assert len(encoded) == 9 and len(varint_encode(postings)) == 15  # vs 20 bytes as int32
assert delta_decode(varint_decode(encoded)) == postings
```

Encoding and decoding are O(total bytes), linear in the list. A 32-bit gap takes at most 5 bytes.

**Bit-packing in blocks.** Varint has two weaknesses: it cannot use less than a byte (a gap of 3 still takes 8 bits), and its decoder takes a data-dependent branch on every byte, which the CPU mispredicts often when gap sizes vary. Modern engines instead cut the gap sequence into fixed-size blocks and pack each block at one bit width b, the width of the block's largest gap. A block of 128 gaps then takes exactly 16b bytes, and unpacking it is straight-line shifts and masks with no branches, which compilers unroll and vectorize with SIMD instructions. This is **frame-of-reference (FOR)** coding: each value is stored as a fixed-width offset from a per-block reference value; for d-gaps the reference is 0 and the choice of b is the whole scheme. Its weakness is outliers: one large gap forces every value in the block to the wide width. **PForDelta** ("patched" FOR, Zukowski, Héman, Nes and Boncz, 2006) picks b so that most of the block fits, say 90%, and stores the few values that do not fit as exceptions that are patched in after the fast unpacking pass. Lucene's postings format packs doc-ID gaps in blocks of 128 at one bit width per block, uses patched FOR for the term frequencies, and writes the final partial block of fewer than 128 entries as VInts.

```python
def for_pack(block):
    """Frame of reference: every value in the block is stored in the same b bits."""
    b = max(block).bit_length()
    packed = 0
    for i, v in enumerate(block):
        packed |= v << (i * b)
    return b, packed.to_bytes((len(block) * b + 7) // 8, "little")


def for_unpack(b, data, count):
    packed, mask = int.from_bytes(data, "little"), (1 << b) - 1
    return [(packed >> (i * b)) & mask for i in range(count)]


block = [3, 7, 1, 12, 5, 2, 9, 4] * 16          # 128 small gaps
b, data = for_pack(block)
assert (b, len(data)) == (4, 64)                # 4 bits each: 64 bytes
assert for_unpack(b, data, len(block)) == block
b, data = for_pack(block[:-1] + [19870])        # one outlier...
assert (b, len(data)) == (15, 240)              # ...and all 128 values pay 15 bits
```

The Python uses one arbitrary-precision integer as the bit buffer to stay short; real implementations shift values into 64-bit words, and Lucene generates a specialized unpacking routine for each width b.

**Why compression makes queries faster, not only smaller.** Intersecting or scoring a posting list does a few instructions per doc ID, so a scan over uncompressed IDs is limited by how fast bytes arrive from memory or disk, not by the CPU. Compression spends a few cheap instructions per ID to move several times fewer bytes, and lets more of the index stay in the CPU caches and in RAM (the operating system's page cache, for an index on disk). Block bit-packing decoders run at billions of integers per second per core (Lemire and Boytsov, "Decoding billions of integers per second through vectorization", 2015), so decoding costs less than the memory traffic it saves, and the smaller list is also the faster one. This is the memory-hierarchy argument of [Chapter 16](../volume-3/ch16-external-memory-and-cache-oblivious-structures.md) applied to lists of integers.

### Intersecting Posting Lists

An AND query ("fibonacci AND heap") needs the doc IDs that appear in every query term's list. Exercise 30.1 builds the **linear merge**: two pointers walk both sorted lists, always advancing the one at the smaller ID, for O(m + n) comparisons in the worst case. That is the right algorithm when the lists have similar lengths and the wrong one when they do not: for "fibonacci AND the", with m = 1,000 and n = 10,000,000 postings, the merge reads the entire long list to find at most 1,000 matches.

**Galloping (exponential) search.** Walk the short list, and for each element x, search the long list forward from where the previous search stopped: probe positions lo, lo + 1, lo + 3, lo + 7, ..., doubling the step, until a probe reaches a value ≥ x, then binary-search the last interval (Bentley and Yao, 1976, proposed this doubling search for unbounded lists).

```python
from bisect import bisect_left


def gallop_to(arr, target, lo=0):
    """Smallest i >= lo with arr[i] >= target, or len(arr).
    Probes lo, lo+1, lo+3, lo+7, ... then binary-searches the last gap."""
    hi, step = lo, 1
    while hi < len(arr) and arr[hi] < target:
        lo = hi + 1             # everything before lo is < target
        hi += step
        step *= 2
    return bisect_left(arr, target, lo, min(hi, len(arr)))


def intersect_gallop(short, long):
    """Each element of `short` gallops forward from where the last one stopped."""
    out, pos = [], 0
    for x in short:
        pos = gallop_to(long, x, pos)
        if pos == len(long):
            break
        if long[pos] == x:
            out.append(x)
    return out


def intersect_all(lists):
    """AND query: start from the rarest term; the candidate set only shrinks."""
    lists = sorted(lists, key=len)
    result = lists[0]
    for other in lists[1:]:
        if not result:
            break
        result = intersect_gallop(result, other)
    return result


long = [2, 5, 9, 12, 17, 21, 30, 44, 51, 63, 70, 88, 95, 120]
assert gallop_to(long, 63) == 9    # probes 0, 1, 3, 7 (15 is past the end), then bisects [8, 14)
assert intersect_all([long, [9, 63, 64], list(range(0, 100, 3))]) == [9, 63]
```

In the test, searching for 63 probes indices 0, 1, 3 and 7 (values 2, 5, 12, 44, all below 63), the next probe 15 is past the end, so it binary-searches indices 8 to 13 and stops at index 9.

**Cost.** Say the search for the i-th element of the short list moves the long-list position forward by g_i. Doubling reaches past that distance in about log₂ g_i probes, and the binary search over the last interval, of length below g_i, takes about log₂ g_i more, so the search costs O(1 + log g_i). The g_i sum to at most n, and since log is concave, a sum of m logarithms with a fixed total is largest when all the terms are equal, at n/m. The total is O(m log(n/m) + m) comparisons in the worst case. For m = 1,000 and n = 10⁷ that is about 1,000 × 2 × log₂(10⁴) ≈ 27,000 comparisons instead of 10⁷. When m ≈ n the gaps are tiny, each search is a probe or two, and galloping costs O(n), within a small constant factor of the merge, so it never loses badly.

**Shortest list first.** With more than two terms, `intersect_all` sorts the lists by length and folds the result through them. The running result can never be longer than the shortest list, so every step is a short list galloping through a longer one. The lengths are free: the term dictionary stores each term's document frequency, because BM25 needs it as n.

**Skip pointers.** Galloping assumes random access, and a compressed list does not have it: varints have variable length, and d-gaps decode only as a running sum from a known starting point. The fix is **skip data**: for every block of B postings, record the block's last doc ID and the byte offset where the block starts. To advance to a target x, search the small, uncompressed array of skip entries, jump to the one block that can contain x, and decode only that block. Blocks with no candidate are never decoded at all. Moffat and Zobel (1996) placed skips every √n postings or so; in block-packed formats the skip interval is simply the block size, and Lucene interleaves skip data with its 128-posting blocks, with a second, coarser level above it.

```python
from bisect import bisect_left


class CompressedPostings:
    """Doc IDs as varint d-gaps in blocks of `block`, plus one skip entry per
    block: the block's last doc ID and the byte offset where it starts."""

    def __init__(self, doc_ids, block=128):
        self.data, self.last_docs, self.offsets = bytearray(), [], []
        prev = 0
        for i in range(0, len(doc_ids), block):
            chunk = doc_ids[i:i + block]
            self.offsets.append(len(self.data))
            self.data += varint_encode(delta_encode(chunk, base=prev))
            prev = chunk[-1]
            self.last_docs.append(prev)
        self.offsets.append(len(self.data))
        self.blocks_decoded = 0

    def decode_block(self, k):
        self.blocks_decoded += 1
        base = self.last_docs[k - 1] if k else 0
        raw = self.data[self.offsets[k]:self.offsets[k + 1]]
        return delta_decode(varint_decode(raw), base)

    def intersect(self, short):
        """Decode only the blocks that could hold an element of `short`."""
        out, k, block_no, docs = [], 0, -1, []
        for x in short:
            k = bisect_left(self.last_docs, x, k)    # skip whole blocks
            if k == len(self.last_docs):
                break
            if k != block_no:
                block_no, docs = k, self.decode_block(k)
            i = bisect_left(docs, x)
            if docs[i] == x:
                out.append(x)
        return out


common = list(range(0, 1_000_000, 3))       # in a third of all documents
rare = [7, 300_000, 300_003, 999_999]       # in four documents
pl = CompressedPostings(common)
assert pl.intersect(rare) == [300_000, 300_003, 999_999]
assert len(pl.data) == 333_334            # 1 byte per gap, vs 1,333,336 as int32
assert len(pl.last_docs) == 2605 and pl.blocks_decoded == 3
```

The rare term's four IDs cost four searches of the skip array and three block decodes out of 2,605 blocks (300,000 and 300,003 share a block); the other 2,602 blocks are never decoded. With m short-list elements, the cost is O(m log(n/B)) for the skip searches (less if they gallop over the skip array instead of calling `bisect`) plus O(B) for each decoded block, and at most min(m, n/B) blocks are decoded. The `len(pl.data)` assertion is the compression side of the same example: a term in every third document out of a million has gaps of 3, one byte each, so the list takes a quarter of its 32-bit size.

### BM25 Scoring

Probabilistic relevance ranking:
```
Score(D, Q) = Σ IDF(qi) × (tf × (k1 + 1)) / (tf + k1 × (1 - b + b × |D|/avgdl))

Where:
- tf = term frequency in document
- |D| = document length
- avgdl = average document length
- k1 = term frequency saturation (typically 1.2-2.0)
- b = length normalization (typically 0.75)
- IDF = log((N - n + 0.5) / (n + 0.5))
```

### Top-k Retrieval: WAND and Block-Max WAND

A search page shows the k best documents by score, not every match, and for an OR query ("fibonacci heap data") nearly every document matches some term. Exhaustive evaluation scores every document in the union of the posting lists and keeps the best k in a size-k min-heap, the top-k pattern of [Chapter 9](../volume-1/ch09-heaps-and-priority-queues.md) §9.8. Its cost is proportional to the total length of all the lists, and that total is dominated by the common terms, which contribute least to any score.

The heap supplies the key quantity: the score θ of the current k-th best document, at its root. A new document matters only if it scores more than θ. **WAND** ("weak AND", Broder, Carmel, Herscovici, Soffer and Zien, 2003) adds one number per term, computed at index time: the upper bound UB_t, the largest score contribution term t makes to any document. (BM25's contribution is bounded for each term; Exercise 30.2(a) computes the limit.) A document's score is at most the sum of UB_t over the terms whose lists contain it. WAND keeps one cursor per term, pointing at its current doc ID, and repeats:

1. Sort the cursors by current doc ID.
2. Add up UB_t in that order until the sum exceeds θ. The cursor where that happens is the pivot, and its doc ID is the pivot document p. If no prefix exceeds θ, stop: no remaining document can enter the top k.
3. A document d < p can only appear in the lists of cursors before the pivot (every other cursor is already past d), and those bounds sum to at most θ. So no document before p can qualify. If some cursors are still before p, move them directly to p, using skip pointers, so the postings in between are never decoded.
4. Otherwise every cursor up to the pivot is on p: score p in full, and push it into the heap if it beats θ.

The answer is exactly the exhaustive top k, not an approximation, because WAND only skips documents it has proved cannot qualify. As the heap fills with good documents θ rises, and more is skipped.

```python
import heapq
from bisect import bisect_left


def wand_top_k(index, k):
    """index: term -> (doc_ids, scores), the term's posting list with each
    document's precomputed score contribution. Returns the top k (score, doc)."""
    ub = {t: max(sc) for t, (_, sc) in index.items()}   # stored at index time
    pos = {t: 0 for t in index}
    heap = []                                             # min-heap of (score, doc)
    fully_scored = 0

    def cur(t):
        docs = index[t][0]
        return docs[pos[t]] if pos[t] < len(docs) else float("inf")

    while True:
        theta = heap[0][0] if len(heap) == k else float("-inf")
        terms = sorted(index, key=cur)
        pivot, bound = None, 0.0
        for t in terms:                     # smallest prefix that could beat theta
            if cur(t) == float("inf"):
                break
            bound += ub[t]
            if bound > theta:
                pivot = cur(t)
                break
        if pivot is None:
            break                           # no remaining document can enter the top k
        if cur(terms[0]) == pivot:          # every term up to the pivot is on it
            score = 0.0
            for t in terms:
                if cur(t) == pivot:
                    score += index[t][1][pos[t]]
                    pos[t] += 1
            fully_scored += 1
            if len(heap) < k:
                heapq.heappush(heap, (score, pivot))
            elif score > theta:
                heapq.heapreplace(heap, (score, pivot))
        else:                               # nothing before the pivot can win: skip
            for t in terms:
                if cur(t) < pivot:
                    pos[t] = bisect_left(index[t][0], pivot, pos[t])
    return sorted(heap, reverse=True), fully_scored


index = {
    "fibonacci": ([3, 9], [4.0, 3.5]),
    "heap": ([1, 3, 5, 7, 9, 11], [1.5, 2.0, 1.0, 1.8, 1.2, 2.0]),
    "data": (list(range(1, 13)), [0.5] * 12),
}
top, fully_scored = wand_top_k(index, k=2)
assert top == [(6.5, 3), (5.2, 9)] and fully_scored == 6   # docs 1, 2, 3, 5, 7, 9
```

The trace of that example, with k = 2:

| term | doc IDs | score contribution | UB |
|---|---|---|---|
| fibonacci | 3, 9 | 4.0, 3.5 | 4.0 |
| heap | 1, 3, 5, 7, 9, 11 | 1.5, 2.0, 1.0, 1.8, 1.2, 2.0 | 2.0 |
| data | 1 to 12 | 0.5 each | 0.5 |

Docs 1 (score 2.0) and 2 (0.5) fill the heap, so θ = 0.5. Doc 3 scores 6.5 and evicts doc 2: θ = 2.0. The cursors are now data at 4, heap at 5, fibonacci at 9. The bound of data alone is 0.5 ≤ 2.0, data plus heap is 2.5 > 2.0, so the pivot is heap's cursor and p = 5: data jumps from 4 to 5, and doc 4 is never scored (it contains only "data", worth at most 0.5). Doc 5 scores 1.5 and does not get in. Doc 6 is skipped the same way, doc 7 scores 2.3 and evicts doc 1 (θ = 2.3), doc 8 is skipped, and doc 9 scores 5.2 (θ = 5.2). Now fibonacci is exhausted and data plus heap is 2.5 ≤ 5.2: no remaining document can reach the top 2, so WAND stops. It fully scored 6 of the 12 matching documents; docs 10, 11 and 12 were never touched, although doc 11 matches two of the three terms.

**Block-max WAND.** The weakness of WAND is that UB_t is a maximum over the whole list: if "heap" scores 2.0 in one document, every "heap" posting looks as if it could be worth 2.0. Block-max WAND (Ding and Suel, 2011) also stores the maximum score within each block of postings, next to that block's skip entry. After WAND picks a pivot with the global bounds, it adds up the block maxima of the blocks containing p in the pivot terms' lists. If that tighter bound is still ≤ θ, no document from p up to the nearest of those block ends (or up to the next cursor after the pivot, if that comes first) can qualify, so the cursors skip there without decoding anything. Lucene 8.0 (2019) added block-max WAND, storing per-block "impacts" in the skip data (the competitive pairs of term frequency and document length, from which a block's maximum BM25 score follows). The price of skipping is that the engine no longer knows the exact number of matching documents; Elasticsearch 7.0 changed its default to count hits exactly only up to 10,000 for this reason.

WAND has no better worst-case bound than exhaustive evaluation: if every document scores close to θ, nothing can be skipped. Its gains depend on the score distribution, and on real queries, where a few documents score far above the rest, θ rises fast and most postings of the common terms are skipped.

### Segments, Merging, and Deletes

Everything so far describes a static index: sorted, compressed, block-packed lists with skip data and block maxima. That layout cannot absorb an insert in the middle of a packed block. Lucene's answer (and so that of Elasticsearch, OpenSearch and Solr, which are built on it) is the same as the LSM tree's in [Chapter 29](ch29-system-design-as-data-structure-composition.md) §29.4 and [Chapter 16](../volume-3/ch16-external-memory-and-cache-oblivious-structures.md) §16.4: never modify anything in place; write new immutable pieces and merge them in the background.

- **Segments.** A segment is a complete, self-contained inverted index over a subset of the documents: its own term dictionary, compressed posting lists and stored fields, with doc IDs 0 to n − 1 local to the segment. Dense local IDs are also what keeps the d-gaps small. New documents are buffered in memory and flushed as a new, small segment; in Elasticsearch this is the refresh, every second by default, which is what makes a new document searchable within a second ("near-real-time" search). A query runs against every segment and combines the per-segment results; a document's global ID is its segment's base offset plus its local ID.
- **Deletes as bitsets.** A segment's files are never rewritten, so a delete cannot remove postings. Instead each segment has a live-docs bitset ([Chapter 3](../volume-1/ch03-arrays-the-foundation-of-contiguous-storage.md) §3.5) with one bit per document, written as a new generation of a small file when deletes arrive. Queries still decode the postings of deleted documents and drop them with one bit test each. An update is a delete of the old version plus an add of the new one, which lands in a new segment.
- **Merging.** A background merge reads several segments and writes one. It merges their sorted term dictionaries (a k-way merge, [Chapter 9](../volume-1/ch09-heaps-and-priority-queues.md) §9.8), and for each term concatenates the posting lists while renumbering doc IDs: each source segment's documents get a new base offset, deleted documents are dropped, and later IDs shift down to fill the holes. Each source segment's documents become one contiguous range of IDs in the result, so the concatenated lists are already sorted and the merge is a single sequential pass, linear in the size of its input. Lucene's default `TieredMergePolicy` merges segments of similar size (by default it tolerates about 10 segments per size tier), so each document is rewritten a logarithmic number of times over the life of the index, as in a size-tiered LSM tree, and it favors segments with many deletions, because a merge is the only way to reclaim their space.

| LSM tree (Chapter 29) | Lucene index |
|---|---|
| memtable | in-memory indexing buffer |
| immutable SSTable | immutable segment |
| compaction | segment merge |
| delete = tombstone written to a newer run | delete = bit cleared in the live-docs bitset of the segment that holds the document |
| point read checks runs newest first and can stop early | every query visits every segment |

The last two rows differ because of the access pattern. A key-value read wants the newest version of one key, so an LSM tree records a delete as a tombstone in the newest run and resolves versions at read time. A search reads all the matching documents in all the segments anyway, so Lucene resolves the delete once, when the buffered deletes are applied, by finding the document in the older segments and clearing its bit; after that a query needs only a bit test and never compares versions across segments. The cost pressure differs too: an LSM point read can stop at the first run that holds the key (and skip most runs with Bloom filters), but a search pays for every segment on every query. Keeping the segment count small is therefore as much about query latency as about disk space, and an index that will not change again is often force-merged down to a single segment.

### Fenced and Sharded Indexes

**Sharding by document**: Different shards contain different documents. Parallel query all shards, merge results.

**Sharding by term (router)**: One shard responsible for a term range. Queries routed based on first term. Problem: hot terms cause imbalance.

## 30.2 Recommendation System Data Structures

### Collaborative Filtering with Matrix Factorization

User-item matrix decomposition:
```
R ≈ U × V^T

R: m×n user-item rating matrix
U: m×k user latent factors
V: n×k item latent factors
k: latent dimension (typical 50-200)
```

**Alternating Least Squares (ALS)**:
```python
def als(R, k, iterations, reg=0.1):
    """`reg` is the L2 regularization weight, spelled `lambda` in the papers,
    which is a reserved word in Python."""
    m, n = R.shape
    U = random(m, k)
    V = random(n, k)
    I = identity(k)

    for _ in range(iterations):
        # Fix U, solve for V
        for j in range(n):
            users = R[:, j].nonzero()
            V[j] = solve(
                U[users].T @ U[users] + reg * I,
                U[users].T @ R[users, j]
            )
        # Fix V, solve for U
        for i in range(m):
            items = R[i, :].nonzero()
            U[i] = solve(
                V[items].T @ V[items] + reg * I,
                V[items].T @ R[i, items].T
            )
    return U, V
```

### Approximate Nearest Neighbors

Vector search for embedding similarity:
```python
class HNSW:
    def __init__(self, m=16, ef_construction=200):
        self.m = m
        self.ef = ef_construction
        self.mL = 1 / log(m)  # level multiplier from the HNSW paper
        self.graph = {}  # node_id -> [neighbors]
        self.layers = []  # layer -> [node_ids]

    def insert(self, vector, max_layers=6):
        # Random layer selection (geometric): P(level >= l) = m ** -l
        level = min(int(-log(random()) * self.mL), max_layers - 1)

        # (Greedy ef=1 descent through the layers above `level` omitted.)
        # On each layer from `level` down to 0, search with ef_construction
        for l in reversed(range(level + 1)):
            candidates = self._search_layer(vector, ef=self.ef, layer=l)
            # Connect to the m nearest candidates
            self._connect(vector, candidates, l)
```

**ANN benchmarks**: HNSW, ScaNN, DiskANN, FAISS. Trade-offs: query speed vs recall vs memory.

## 30.3 Time Series Databases

Time series data requires specialized structures for append-heavy workloads and time-range queries.

### Columnar Storage with Time Partitioning

```
Partitioning scheme:
/data/year=2024/month=01/day=15/hour=12/
    segment_000.parquet
    segment_001.parquet
    segment_002.parquet

Within segment (columnar):
| timestamp | cpu | memory | disk_io |
| 1705312800 | 45 | 32 | 1200 |
| 1705312801 | 47 | 31 | 1150 |
```

**Benefits**:
- Columnar: Efficient aggregation (only read needed columns)
- Time partitioning: Prune irrelevant partitions
- Segment size: Balance between query efficiency and write buffering

### Downsampling and Aggregation

**Tiered storage**: Raw data → Downsampled → Long-term retention
```
Raw (second precision) → 1 hour rollup → 1 day rollup → 1 month rollup
Retention: 1 week         6 months        2 years          forever
```

**Aggregation algorithms**:
- **LTTB**: Largest Triangle Three Buckets for visual fidelity
- **Min/max sketches**: Approximate aggregates with space efficiency

## 30.4 Event Sourcing and CQRS

Event sourcing stores state as a sequence of events rather than current state.

### Event Store Structure

```python
class EventStore:
    def __init__(self):
        self.streams = {}  # aggregate_id -> [event]

    def append(self, aggregate_id, event):
        self.streams.setdefault(aggregate_id, []).append(event)

    def get_stream(self, aggregate_id, from_version=0):
        return self.streams.get(aggregate_id, [])[from_version:]

    def rebuild_state(self, aggregate_id):
        state = {}
        for event in self.get_stream(aggregate_id):
            state = apply_event(state, event)
        return state
```

**Benefits**: Complete audit trail, temporal queries, easy replay for debugging.

**Challenges**: Event schema evolution, eventual consistency, query complexity.

### CQRS (Command Query Responsibility Segregation)

Separate read and write models:
```
Command side (write):
- Handle commands (not queries)
- Aggregate events into state
- Publish to event bus

Query side (read):
- Maintain read models optimized for specific queries
- Subscribe to events for projection updates
- Materialized views for fast access
```

## 30.5 Sharding Patterns

Horizontal partitioning across multiple databases.

### Consistent Hash Ring with Virtual Nodes

```
Virtual node mapping:
Physical Node A → VNode_1, VNode_5, VNode_12, VNode_23
Physical Node B → VNode_3, VNode_8, VNode_15, VNode_19
Physical Node C → VNode_2, VNode_11, VNode_17, VNode_24

Shard calculation:
vnode = hash(key) % NUM_VNODES   (fixed for the life of the cluster)
owner = vnode_owner[vnode]
```

**Rebalancing**: A new node takes over whole vnodes from existing nodes, and only the keys in those vnodes move: about 1/(n+1) of the data when growing from n to n+1 nodes. The vnode count controls how evenly load spreads, not how much data moves.

### Skip Hash for Hot Data

```
Hot data (top 1% of access):
- Replicated 3-5x across nodes
- Stored in memory or fast SSDs

Warm data (next 19%):
- Partitioned across cluster
- Standard replication factor (3)

Cold data (bottom 80%):
- Archived to cheaper storage
- Reduced replication (2)
- Accessed rarely
```

## 30.6 Consistency Patterns in Practice

### Saga Pattern for Distributed Transactions

Choreography vs orchestration:
```
Choreography (event-driven):
OrderCreated → InventoryReserve → PaymentCapture → OrderConfirmed
            ↓              ↓              ↓
         (rollback)     (rollback)     (rollback)

Orchestration (centralized):
Saga Orchestrator:
  1. Send ReserveInventory
  2. Receive InventoryReserved
  3. Send CapturePayment
  4. Receive PaymentCaptured
  5. Send ConfirmOrder
  (On failure, send compensating transactions)
```

### Two-Phase Commit (2PC)

Distributed transaction protocol:
```
Phase 1 - Prepare:
1. Coordinator asks all participants to prepare
2. Participants vote Yes/No (locks resources)
3. If all Yes, proceed to commit; otherwise abort

Phase 2 - Commit:
1. Coordinator sends commit to all participants
2. Participants apply changes, release locks
3. Coordinator confirms completion
```

**Problems**: Blocking, coordinator failure, latency.

## 30.7 Observability Data Structures

### Distributed Tracing

Span graph for request flow:
```python
class Span:
    def __init__(self, name, trace_id, span_id, parent_id=None):
        self.name = name
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent_id = parent_id
        self.start_time = time.time()
        self.end_time = None
        self.tags = {}
        self.annotations = []

    def finish(self):
        self.end_time = time.time()

    def duration_ms(self):
        return (self.end_time - self.start_time) * 1000
```

**Trace assembly**: Child spans attached to parents via span_id/parent_id. Hierarchical tree represents causal relationship.

### Metric Aggregation

Time-series aggregation with downsampling:
```
Raw metrics (every 10s):
[23, 25, 22, 28, 24, ...]

1-minute rollup:
avg: 24.4, max: 28, min: 22, p50: 24, p95: 27, p99: 28

1-hour rollup:
avg: 24.1, max: 45 (spike during incident), p99: 38
```

**Cardinality management**: High-cardinality labels (user IDs, request IDs) must be aggregated before storage.

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**30.1 ★ Answer a Boolean query.** Add a third document, Doc3: "efficient data pipelines", to the collection in §30.1. Write the posting lists for "data", "structures", "efficient" and "pipelines" (document IDs 1, 2, 3). Then write a function that intersects two sorted posting lists, and use it to answer "data AND efficient" and "structures AND pipelines". What does the intersection cost?

<details>
<summary>Solution</summary>

Posting lists: data → [1, 2, 3], structures → [1, 2], efficient → [2, 3], pipelines → [3].

Because both lists are sorted, two pointers can walk them together, always advancing the one pointing at the smaller ID:

```python
def intersect(a, b):
    """Intersect two sorted posting lists in O(len(a) + len(b))."""
    i = j = 0
    out = []
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            out.append(a[i])
            i += 1
            j += 1
        elif a[i] < b[j]:
            i += 1
        else:
            j += 1
    return out


index = {
    "data": [1, 2, 3],
    "structures": [1, 2],
    "efficient": [2, 3],
    "pipelines": [3],
}
assert intersect(index["data"], index["efficient"]) == [2, 3]
assert intersect(index["structures"], index["pipelines"]) == []
```

"data AND efficient" returns [2, 3]; "structures AND pipelines" returns []. The cost is O(|a| + |b|) comparisons. When one list is far shorter than the other (a rare term AND a common one), searching the long list for each element of the short one, by binary search or galloping, costs O(|short| × log |long|) instead, which is why engines intersect the rarest term first and store skip pointers in long posting lists.

</details>

**30.2 ★★ Compute a BM25 score.** A collection has N = 1,000 documents with average length avgdl = 200 terms. The query term "trie" appears in n = 10 documents. Document D has |D| = 100 terms and contains "trie" tf = 3 times. With k1 = 1.2 and b = 0.75, compute the IDF, the term-frequency factor, and the score, using the natural log. Then answer: (a) what is the largest score this term can contribute however large tf gets, for a document of this length? (b) What happens to the score if D were 400 terms long? (c) What IDF does a term found in 600 of the 1,000 documents get, and why is that a problem?

<details>
<summary>Hint</summary>

Compute the length normalization 1 − b + b × |D|/avgdl first; it multiplies k1 in the denominator.

</details>

<details>
<summary>Solution</summary>

IDF = ln((1000 − 10 + 0.5) / (10 + 0.5)) = ln(990.5 / 10.5) = ln(94.33) ≈ 4.547.

Length normalization: 1 − 0.75 + 0.75 × 100/200 = 0.625, so k1 × 0.625 = 0.75.

Term-frequency factor: 3 × (1.2 + 1) / (3 + 0.75) = 6.6 / 3.75 = 1.76.

Score ≈ 4.547 × 1.76 ≈ 8.00.

(a) As tf → ∞ the factor tf × (k1 + 1) / (tf + constant) approaches k1 + 1 = 2.2, so the score saturates at 4.547 × 2.2 ≈ 10.0. Going from tf = 3 to tf = 100 only raises the factor from 1.76 to about 2.18. This saturation is the point of k1: the hundredth occurrence of a word says much less than the first.

(b) With |D| = 400 the normalization is 1 − 0.75 + 0.75 × 2 = 1.75, so the factor is 6.6 / (3 + 2.1) ≈ 1.29 and the score drops to about 5.88. Three occurrences in a long document are weaker evidence than three in a short one.

(c) ln((1000 − 600 + 0.5) / (600 + 0.5)) = ln(400.5 / 600.5) ≈ −0.405. Any term in more than half the documents gets a negative IDF, so matching it lowers a document's score. Lucene and most modern engines use ln(1 + (N − n + 0.5)/(n + 0.5)) instead, which stays positive.

</details>

**30.3 ★★ How tall is an HNSW graph?** The `insert` method in §30.2 picks level = ⌊−ln(u) × mL⌋ with u uniform on (0, 1] and mL = 1/ln(m). (a) Show that P(level ≥ l) = m^(−l). (b) For m = 16 and one million vectors, how many vectors do you expect on layer 1 and above, layer 2 and above, and so on? How many layers does the graph have? (c) Why is a level distribution that decays this fast what makes search fast?

<details>
<summary>Solution</summary>

(a) level ≥ l exactly when −ln(u) × mL ≥ l, that is −ln(u) ≥ l × ln(m), that is u ≤ e^(−l ln m) = m^(−l). Since u is uniform, that event has probability m^(−l).

(b) Expected count on layer l and above = 10⁶ × 16^(−l):

| layer l | expected nodes at level ≥ l |
|---|---|
| 0 | 1,000,000 |
| 1 | 62,500 |
| 2 | 3,906 |
| 3 | 244 |
| 4 | 15 |
| 5 | about 1 |

So the graph has about five or six layers, roughly log base 16 of a million, which is 5.

(c) Each layer has about 1/m as many nodes as the one below, like the levels of a skip list with promotion probability 1/m. A greedy search on a sparse upper layer covers large distances in a few hops and lands near the target; each lower layer refines the position. With a constant number of hops per layer and log_m(N) layers, the expected search cost grows logarithmically. If the distribution decayed slowly, upper layers would be nearly as large as layer 0 and would no longer give long-range shortcuts; that is exactly the bug in a version that computed the level as `-log(random()) % max_layers`, which puts about 37% of nodes above layer 0 instead of 1/16.

</details>

**30.4 ★★ Snapshots for an event store.** Rebuilding an aggregate from the `EventStore` in §30.4 replays its entire stream. Add a `take_snapshot(aggregate_id)` method that stores (version, state), and change `rebuild_state` to start from the snapshot and replay only later events. Test it on a bank account with events deposited 100, withdrew 30, (snapshot), deposited 50. What property must `apply_event` have for the snapshot to stay valid?

<details>
<summary>Hint</summary>

Consider what happens to the stored snapshot if `apply_event` updates the dictionary it is given in place.

</details>

<details>
<summary>Solution</summary>

```python
def apply_event(state, event):
    # Pure: returns a new dict and never mutates its input
    kind, amount = event
    balance = state.get("balance", 0)
    if kind == "deposited":
        return {**state, "balance": balance + amount}
    if kind == "withdrew":
        return {**state, "balance": balance - amount}
    return state


class EventStore:
    def __init__(self):
        self.streams = {}    # aggregate_id -> [event]
        self.snapshots = {}  # aggregate_id -> (version, state)

    def append(self, aggregate_id, event):
        self.streams.setdefault(aggregate_id, []).append(event)

    def get_stream(self, aggregate_id, from_version=0):
        return self.streams.get(aggregate_id, [])[from_version:]

    def take_snapshot(self, aggregate_id):
        version = len(self.streams.get(aggregate_id, []))
        self.snapshots[aggregate_id] = (version, self.rebuild_state(aggregate_id))

    def rebuild_state(self, aggregate_id):
        version, state = self.snapshots.get(aggregate_id, (0, {}))
        for event in self.get_stream(aggregate_id, from_version=version):
            state = apply_event(state, event)
        return state


store = EventStore()
store.append("acct-1", ("deposited", 100))
store.append("acct-1", ("withdrew", 30))
store.take_snapshot("acct-1")
assert store.snapshots["acct-1"] == (2, {"balance": 70})
store.append("acct-1", ("deposited", 50))
assert store.rebuild_state("acct-1") == {"balance": 120}
assert store.rebuild_state("acct-1") == {"balance": 120}  # snapshot untouched
assert store.snapshots["acct-1"] == (2, {"balance": 70})
```

Rebuilding now costs O(events since the snapshot) instead of O(all events). The version stored with the snapshot is the number of events it covers, so `get_stream(..., from_version=version)` returns exactly the events not yet folded in.

`apply_event` must be pure: it must return a new state and never mutate its argument. `rebuild_state` starts from the very dictionary stored in `self.snapshots`; if `apply_event` did `state["balance"] += amount` in place, the first rebuild would silently add the deposit of 50 into the stored snapshot, and every later rebuild would add it again, giving 170, 220, and so on. The assertion that the snapshot is still (2, {"balance": 70}) after two rebuilds catches exactly this. (A defensive alternative is to deep-copy the snapshot state before replaying.)

This is the same log-plus-checkpoint pattern as a Raft snapshot or a Delta Lake checkpoint: the log stays the source of truth, and the snapshot is a cache of a prefix of it.

</details>

**30.5 ★ How much data moves?** A cluster maps keys to 24 fixed vnodes as in §30.5, and three physical nodes own 8 vnodes each. (a) A fourth node joins and the vnodes are rebalanced evenly. What fraction of keys move? (b) Compare with `owner = hash(key) % num_physical` going from 3 to 4 nodes. (c) Suppose the vnode were instead computed as `hash(key) % (num_physical × 8)`, so the vnode count grows with the cluster. What fraction of keys end up in a different vnode when going from 3 to 4 nodes?

<details>
<summary>Solution</summary>

(a) Each node should own 24/4 = 6 vnodes, so the new node takes 2 from each existing node: 6 vnodes, 6/24 = 25% of the keys, all moving to the new node. That is the minimum possible: the new node must end up with its fair share of 1/4.

(b) A key keeps its owner only if h mod 3 = h mod 4, which holds when h mod 12 is 0, 1 or 2: 3 values in 12, so 75% of keys move, most of them between old nodes.

(c) A key stays in the same vnode only if h mod 24 = h mod 32. Over one period of lcm(24, 32) = 96 this holds only for h in 0 to 23, so again 75% of keys move. The vnode layer only helps if the number of vnodes is fixed; changing the modulus brings back mod-N's behavior.

</details>

**30.6 ★★★ Where two-phase commit blocks.** In the 2PC protocol of §30.6, participants P1, P2 and P3 all vote Yes, and the coordinator crashes before any of them receives the decision. (a) Can P1 commit on its own? Abort on its own? (b) P1 contacts P2 and P3. In which situations can they resolve the transaction without the coordinator, and when are they stuck? (c) Why must the coordinator write its decision to its own durable log before sending it? (d) How does a saga avoid this blocking, and what does it give up?

<details>
<summary>Hint</summary>

After voting Yes, a participant has promised it can commit, but it does not know whether everyone else promised too.

</details>

<details>
<summary>Solution</summary>

(a) Neither. P1 cannot commit, because some other participant might have voted No, in which case the coordinator decided abort. P1 cannot abort, because the coordinator might have decided commit and already told someone, or recorded it; aborting would then break atomicity. Having voted Yes, P1 must hold its locks and wait. That is the blocking problem.

(b) If any reachable participant received the decision, everyone adopts it. If any participant has not yet voted, it can unilaterally abort (no Yes vote means no promise), so everyone aborts. If any participant voted No, the outcome must be abort. But in this scenario all three voted Yes and none received the decision, so the outcome depends only on what the crashed coordinator decided, possibly commit. They are stuck holding locks until the coordinator recovers. Participants that are themselves unreachable make it worse: a silent one might be the one that received the decision.

(c) On recovery the coordinator must give the same answer it may already have sent to some participants. If it decided commit, told P1, then crashed and recovered with no record, it might abort when asked again by P2, leaving P1 committed and P2 aborted. Logging the decision durably before sending it is what makes the decision recoverable. (Protocols that replicate the coordinator's decision with consensus, such as Paxos Commit, remove the single point of blocking.)

(d) A saga commits each local step immediately and never holds locks across services. If a later step fails, it runs compensating actions (release the inventory, refund the payment) for the steps already done. Nothing blocks, but there is no isolation: other transactions can observe the intermediate state (stock reserved for an order that will be cancelled), and every step needs a compensation that is correct to run after arbitrary interleavings.

</details>

**30.7 ★★ Rollups that lie.** §30.7 rolls 10-second samples up into 1-minute and 1-hour summaries. Minute 1 sees 100 requests: 98 at 10 ms and 2 at 300 ms. Minute 2 sees 100 requests, all at 10 ms. Using the nearest-rank percentile (the ⌈0.99 × n⌉-th smallest value), compute each minute's p99, the true p99 of the two minutes combined, and the two "rollups" someone might compute from the per-minute p99s: their average and their maximum. Which summary statistics can be rolled up exactly from per-minute values, and what should you store to roll up percentiles?

<details>
<summary>Solution</summary>

Minute 1: the 99th smallest of 100 values. The 98 values at 10 ms come first, so the 99th is 300 ms. Minute 2: 10 ms.

Combined: 200 values, 198 at 10 ms and 2 at 300 ms. The ⌈0.99 × 200⌉ = 198th smallest is 10 ms.

Average of the per-minute p99s: (300 + 10)/2 = 155 ms. Maximum: 300 ms. Both are wrong: the true answer is 10 ms. With other data the average of p99s can just as easily be far too low.

Exact rollups: count, sum, min and max combine exactly (add, add, min, max), and the mean is sum/count, which needs both; averaging the per-minute averages is only correct when every minute has the same count. Percentiles do not combine from percentiles at all. To roll them up, store a mergeable summary per interval: a histogram with fixed bucket boundaries (merge by adding bucket counts, the Prometheus approach) or a mergeable sketch such as a t-digest or DDSketch. The percentile is then computed from the merged summary, with error set by the bucket or sketch resolution rather than by the rollup.

</details>

**30.8 ★ Compress a posting list by hand.** A term occurs in documents 5, 130, 131 and 16515. (a) Write the d-gaps and their varint bytes in hex, using the encoding of §30.1. How many bytes is that, against 32-bit integers and against varints of the raw IDs? (b) Pack the four gaps as one frame-of-reference block. What bit width does the block need, and how many bytes? (c) What would PForDelta do with this block?

<details>
<summary>Hint</summary>

16,384 is 2¹⁴, the smallest number that needs a third varint byte.

</details>

<details>
<summary>Solution</summary>

(a) The gaps are 5, 125, 1 and 16384. 5, 125 and 1 are below 128, so they take one byte each: 05, 7D, 01. 16384 = 2¹⁴ is `1 0000000 0000000` in binary, three 7-bit groups; lowest first with continuation flags, that is 80 80 01. Total 6 bytes, against 16 as 32-bit integers. The raw IDs as varints are 05, 82 01, 83 01, 83 81 01, 8 bytes: 130 and 131 need two bytes and 16515 three.

(b) The width is that of the largest gap: 16384 needs 15 bits, so 4 × 15 = 60 bits, 8 bytes, worse than varint. The other three gaps need at most 7 bits (125 < 128) but pay for the outlier.

(c) PForDelta picks the width that fits most of the block, here 7 bits: 4 × 7 = 28 bits, 4 bytes, and records 16384 separately as an exception (its position in the block and its value), patched in after the block is unpacked. On a real block of 128 gaps a single exception costs a few bytes, while widening the whole block from 7 to 15 bits would cost 128 extra bytes.

```python
# Checked with the functions from §30.1
assert varint_encode(delta_encode([5, 130, 131, 16515])).hex(" ") == "05 7d 01 80 80 01"
assert len(varint_encode([5, 130, 131, 16515])) == 8
assert for_pack([5, 125, 1, 16384])[0] == 15 and for_pack([5, 125, 1])[0] == 7
```

</details>

**30.9 ★★ When does galloping pay?** (a) Intersect a list of m = 1,000 doc IDs with one of n = 10,000,000. Estimate the comparisons for the linear merge and for galloping. (b) Prove the O(m log(n/m) + m) bound from §30.1 for the case where every one of the m searches advances the long-list position by the same amount, and explain why unequal advances cannot cost more. (c) When the two lists have about the same length, which method is faster in practice, and how do implementations choose between them?

<details>
<summary>Solution</summary>

(a) The merge advances one of the two pointers on every comparison and can end only when one list runs out, so it does up to m + n ≈ 10⁷ comparisons (it may stop early if the short list's last element is small, but in general it reads most of the long list). Galloping does about 2 log₂(n/m) = 2 log₂(10⁴) ≈ 27 comparisons per element of the short list, about 27,000 in total: a 370-fold reduction.

(b) If every search advances the position by g = n/m, each search costs about log₂ g probes to overshoot and log₂ g more to binary-search the last interval, so the total is about 2m log₂(n/m), plus O(1) per element for the first probe. With unequal advances g₁, ..., g_m summing to at most n, the cost is Σ O(1 + log g_i). Since log is concave, Jensen's inequality gives (1/m) Σ log g_i ≤ log((1/m) Σ g_i) ≤ log(n/m), so Σ log g_i ≤ m log(n/m): spreading the same total distance unevenly can only lower the sum of logs.

(c) The merge. When n ≈ m the gaps are about 1, so galloping does O(1) work per element and has the same O(n) bound, but each search still costs a probe or two plus the loop and `bisect` setup, while the merge does one comparison and one pointer increment per step. Both are linear, and the merge has the smaller constant. Implementations choose by the length ratio: merge when the lists are close in size, gallop when one is much shorter. (Python's `list.sort` uses the same idea in reverse: its merge switches into galloping mode once one run keeps winning.) Search engines rarely face this choice on raw arrays; they advance through compressed blocks with skip data, and the shortest-list-first rule keeps the driving list short.

</details>

**30.10 ★★ Merge two segments.** Represent a segment as `(postings, live)`, where `postings` maps each term to its sorted local doc IDs and `live` is a list of booleans, one per document (False means deleted). Write `merge_segments(segments)` that returns the postings of a single merged segment containing only live documents, with IDs renumbered 0, 1, 2, ... in segment order, plus the merged document count. Test it on segment A with `{"data": [0, 1, 2], "heap": [1]}`, live `[True, False, True]`, and segment B with `{"data": [1], "trie": [0, 1]}`, live `[True, True]`. Why does no posting list need re-sorting?

<details>
<summary>Solution</summary>

```python
def merge_segments(segments):
    """segments: list of (postings, live) with postings: term -> sorted local
    doc IDs and live: list of bools, one per document in the segment.
    Returns the postings of one merged segment with no deleted documents."""
    remaps, base = [], 0
    for _, live in segments:
        remap = {}
        for local, alive in enumerate(live):
            if alive:
                remap[local] = base
                base += 1
        remaps.append(remap)
    merged = {}
    for (postings, _), remap in zip(segments, remaps):   # segment order = ID order
        for term, docs in postings.items():
            new_ids = [remap[d] for d in docs if d in remap]
            if new_ids:
                merged.setdefault(term, []).extend(new_ids)
    return dict(sorted(merged.items())), base


seg_a = ({"data": [0, 1, 2], "heap": [1]}, [True, False, True])
seg_b = ({"data": [1], "trie": [0, 1]}, [True, True])
merged, n_docs = merge_segments([seg_a, seg_b])
assert n_docs == 4
assert merged == {"data": [0, 1, 3], "trie": [2, 3]}       # "heap" only had a deleted doc
```

The remap gives A's live documents 0 and 2 the new IDs 0 and 1, and B's documents 0 and 1 the IDs 2 and 3. Deleted document A1 gets no new ID, so its postings disappear, and "heap", which occurred only there, disappears from the merged dictionary: this is how a merge reclaims the space of deletes.

No list needs re-sorting because the renumbering preserves order twice over: within a segment, the remap is increasing (later live documents get larger IDs), and across segments, every ID from A is smaller than every ID from B. So appending each segment's remapped list in segment order produces a sorted list, and the whole merge is one sequential pass over the inputs, O(total postings + total documents). A real merge also streams the term dictionaries in sorted order (a k-way merge of the segments' sorted term lists) instead of building a dictionary and sorting it at the end, and writes the merged lists straight into compressed blocks.

</details>

---

## Where this connects

- [Chapter 29: System Design as Data Structure Composition](ch29-system-design-as-data-structure-composition.md). The component structures these patterns compose
- [Chapter 19: Emerging and Specialized Structures](../volume-3/ch19-emerging-and-specialized-structures.md). The vector-search structures behind modern recommendation
