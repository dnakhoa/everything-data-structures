# Chapter 13: String Data Structures

Strings break the assumptions the rest of this book runs on. A comparison is no longer O(1). Comparing two strings costs up to their length. And the queries people actually want are different in kind: not "is this key present" but "which keys start with this", "where does this pattern occur", "what is the longest repeated section". Hash tables answer none of those, because hashing destroys exactly the structure the questions are about.

The structures here exploit the one property strings have that opaque keys don't: **shared prefixes**. The first half of the chapter is about ways of storing a set of strings so that common prefixes are stored once. The rest covers the other side of string work: finding one pattern in a text that streams past (Section 13.5), many patterns at once (Section 13.6), and holding a string that is being edited (Section 13.7).

## 13.1 Tries (Prefix Trees)

A trie stores strings by their prefixes. Each edge carries a character, and a string is a path from the root:

```
Trie for {"cat", "car", "card", "do", "dog", "done"}:

root
 │
 ├── c
 │   └── a
 │       ├── t ●          "cat"
 │       └── r ●          "car"
 │           └── d ●      "card"
 │
 └── d
     └── o ●              "do"
         ├── g ●          "dog"
         └── n
             └── e ●      "done"

● marks a node where a stored word ends.
```

The end-of-word marks matter more than they look. `car` and `card` both terminate, and `car`'s marker sits on an *internal* node, so "is this node a leaf" is not the same question as "does a word end here". A trie that conflates the two cannot store a word that is a prefix of another word, which is a common bug.

```python
class TrieNode:
    __slots__ = ("children", "is_word")

    def __init__(self):
        self.children = {}      # char -> TrieNode
        self.is_word = False

class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word):                       # O(L)
        node = self.root
        for ch in word:
            node = node.children.setdefault(ch, TrieNode())
        node.is_word = True

    def search(self, word):                       # O(L)
        node = self._walk(word)
        return node is not None and node.is_word

    def starts_with(self, prefix):                # O(P)
        return self._walk(prefix) is not None

    def with_prefix(self, prefix):                # O(P + output)
        """Every stored word beginning with `prefix`. The autocomplete query."""
        node = self._walk(prefix)
        if node is None:
            return
        stack = [(node, prefix)]
        while stack:
            n, s = stack.pop()
            if n.is_word:
                yield s
            for ch, child in n.children.items():
                stack.append((child, s + ch))

    def _walk(self, s):
        node = self.root
        for ch in s:
            node = node.children.get(ch)
            if node is None:
                return None
        return node
```

**The complexity is the selling point.** Lookup is O(L) in the length of the *query*, completely independent of how many strings are stored. A trie holding ten strings and a trie holding ten million answer a 12-character lookup in the same time. No hash table can promise that, because hashing the key is already O(L) and then collisions depend on n.

| Operation | Trie | Hash set | Balanced BST |
|-----------|------|----------|--------------|
| Insert | O(L) | O(L) average | O(L log n) |
| Search | O(L) | O(L) average | O(L log n) |
| Prefix query | O(P + output) | Impossible | O(L log n + output) |
| Sorted iteration | O(total chars) | Impossible | O(n) |
| Worst-case lookup | O(L) guaranteed | O(nL) | O(L log n) |

Note the BST column: string comparison is O(L), so a BST of strings is O(L log n), not O(log n). A detail that reference tables routinely get wrong.

**Space is the problem.** A node with a 256-entry array per character costs 2KB per node before storing anything. For a dictionary of English words that is wildly wasteful, since most nodes have one or two children. The mitigations, in increasing order of sophistication: a hash map per node (what the code above does. Flexible, one indirection), a sorted array of children (compact, binary search), a 256-bit bitmap plus a packed child array (succinct, the approach in [Chapter 24](../volume-4/ch24-research-grade-data-structures.md)), or compressing the paths outright, which is the next section.

## 13.2 Radix Trees (Compressed Tries)

Compress any chain of single-child nodes into one edge holding a whole substring:

```
Radix tree, same words:

root
 │
 ├── "ca"
 │   ├── "t" ●            "cat"
 │   └── "r" ●            "car"
 │       └── "d" ●        "card"
 │
 └── "do" ●               "do"
     ├── "g" ●            "dog"
     └── "ne" ●           "done"

The chain c→a became one edge "ca".
```

The guarantee this buys: **every internal node either ends a word or has at least two children**, so a radix tree over n strings has at most n−1 branching nodes regardless of how long the strings are. Space becomes proportional to the number of strings, not the number of characters. For sparse key sets (long keys with little overlap, like URLs or file paths) the saving is enormous.

**PATRICIA tries** take it further by storing, at each node, only the *bit position* that distinguishes the subtrees, skipping the intervening bits entirely. A lookup descends on those bit tests alone and performs exactly one full key comparison at the end. This makes them ideal for fixed-width binary keys, which is why they index IP routing tables. An IP lookup is a longest-prefix match over 32 or 128 bits, and the Linux kernel's routing table (`fib_trie`) is a PATRICIA variant.

**Adaptive Radix Trees (ART)** are the modern refinement: node size adapts to the number of children (4, 16, 48, or 256 slots), so sparse and dense regions each get an appropriate layout. ART is competitive with hash tables on lookups while preserving ordering, and is used in HyPer, DuckDB, and several key-value stores.

## 13.3 Suffix Trees

The structures so far index a *set of strings*. A suffix tree indexes **one string, by all of its suffixes**, which is what makes arbitrary substring search possible, because every substring is a prefix of some suffix.

The terminal `$` (a character not otherwise in the alphabet) guarantees no suffix is a prefix of another, so every suffix ends at a leaf:

```
Suffix tree for "banana$": a compressed trie of all 7 suffixes.
Leaf labels are the starting positions of each suffix.

root
 ├── "$"                                  → 6
 ├── "a"
 │    ├── "$"                             → 5
 │    └── "na"
 │         ├── "$"                        → 3
 │         └── "na$"                      → 1
 ├── "banana$"                            → 0
 └── "na"
      ├── "$"                             → 4
      └── "na$"                           → 2
```

Read a path from the root and you have a substring of "banana". The node reached by "ana" has two leaves below it (3 and 1), which says immediately that "ana" occurs twice, at positions 3 and 1. That is the general pattern: **internal nodes correspond to repeated substrings, and the number of leaves below a node is the number of occurrences.**

This is why so many string problems collapse to tree traversals:

| Problem | Solution on a suffix tree | Time |
|---------|--------------------------|------|
| Does pattern P occur? | Walk P from the root | O(m) |
| How many times? | Count leaves below that node | O(m + occ) |
| Longest repeated substring | Deepest internal node | O(n) |
| Longest common substring of A and B | Build over `A#B$`; deepest node with leaves from both | O(n) |
| Longest palindromic substring | Suffix tree of `A#reverse(A)$` + LCA queries | O(n) |

Ukkonen's 1995 algorithm builds the tree in **O(n)** for a constant alphabet: online, one character at a time. It is genuinely difficult to implement correctly; the suffix links and the "active point" bookkeeping are notorious.

That difficulty, plus the memory cost, is why suffix trees are less used than their power suggests. A suffix tree needs roughly 20 bytes per character in a practical implementation. Indexing a 3-billion-character genome would take 60GB. The next section is the response to that.

## 13.4 Suffix Arrays

A suffix array is just the sorted list of suffix starting positions: the same information as a suffix tree's leaf order, in a flat integer array:

```
String: "banana$"

Suffixes:  0:"banana$"  1:"anana$"  2:"nana$"  3:"ana$"
           4:"na$"      5:"a$"      6:"$"

Sorted lexicographically:
  rank 0:  "$"          → position 6
  rank 1:  "a$"         → position 5
  rank 2:  "ana$"       → position 3
  rank 3:  "anana$"     → position 1
  rank 4:  "banana$"    → position 0
  rank 5:  "na$"        → position 4
  rank 6:  "nana$"      → position 2

Suffix array: [6, 5, 3, 1, 0, 4, 2]
```

Four bytes per character instead of twenty. Same queries, far better cache behavior, because a binary search over a contiguous integer array is about as friendly to hardware as a search gets.

**The LCP array** stores the longest common prefix between each suffix and the one before it in sorted order, with `LCP[0] = 0` by convention:

```
rank:  0     1      2       3        4          5      6
suffix "$"   "a$"   "ana$"  "anana$" "banana$"  "na$"  "nana$"
LCP:    0     0      1       3        0          0      2
              ↑      ↑       ↑                          ↑
           "$" vs   "a$" vs  "ana$" vs               "na$" vs
           "a$"     "ana$"   "anana$"                "nana$"
           share    share    share "ana"             share "na"
           nothing  "a"
```

Kasai's algorithm computes the LCP array in O(n) once the suffix array is known. Together, the suffix array and LCP array carry all the information in a suffix tree: the LCP array encodes the tree's internal node structure implicitly, so any suffix-tree algorithm can be rewritten to use them.

**Construction** is a solved problem: **SA-IS** (Nong, Zhang, Chan, 2009) builds a suffix array in O(n) worst case, is straightforward compared to Ukkonen's algorithm, and is fast in practice. The simpler O(n log n) doubling approach (sort by first character, then by first 2, then 4, then 8) is what most people implement in contests and is usually fast enough.

**Searching** with a plain suffix array is O(m log n): binary search, comparing up to m characters at each of log n steps. With the LCP array and a little extra bookkeeping this drops to O(m + log n).

Suffix arrays are the practical default. The [FM-index](../volume-4/ch24-research-grade-data-structures.md) goes one step further, compressing the suffix array to the text's own entropy while keeping it searchable, which is how BWA and Bowtie fit a human genome index in a few gigabytes.

## 13.5 Single-Pattern Matching: Prefix Function, Z-Array, Rolling Hash

Sections 13.3 and 13.4 index the *text*. The opposite case is just as common: one pattern P of length m, one text T of length n that is read once (a log line, a network packet, a file being scanned), and no index worth building. The naive method tries every alignment and compares up to m characters at each, which is O(nm) in the worst case. P = `aaaab` against T = `aaaa…a` reads four `a`s at every one of the n alignments before failing.

The three structures below are built from the pattern (or from P and T together) in linear time and remove that worst case. Each is an array of integers, or a single number, that summarizes how the string overlaps itself.

### The prefix function (KMP's failure function)

A **border** of a string is a proper prefix that is also a suffix: `abab` has the borders `ab` and the empty string. The **prefix function** stores, for every prefix of P, the length of its longest border:

```
π[i] = length of the longest proper prefix of P[0..i] that is also a suffix of P[0..i]

P  =  a  b  a  b  a  c  a
i  =  0  1  2  3  4  5  6
π  =  0  0  1  2  3  0  1
```

π[4] = 3 because `ababa` begins and ends with `aba`. π[5] = 0 because no prefix of `ababac` ends in `c`.

Why this is the right thing to store: suppose the last k characters of the text match P[0..k), and the next text character c is not P[k]. The alignment that just failed is dead, but a later alignment can only still succeed if the part of it already read is both a suffix of the matched text P[0..k) and a prefix of P. That is a border of P[0..k). The longest one has length π[k−1]; if c does not extend that either, the next candidate is the longest border of the border, π[π[k−1]−1], and so on. A border of a border is itself a border, and this chain visits every border of P[0..k) from longest to shortest, so no possible alignment is skipped. The text pointer never moves backwards. Computing π is the same procedure run on P against itself:

```python
def prefix_function(p):
    """pi[i] = length of the longest proper prefix of p[:i+1] that is also its suffix."""
    pi = [0] * len(p)
    k = 0                                  # length of the current border
    for i in range(1, len(p)):
        while k > 0 and p[i] != p[k]:
            k = pi[k - 1]                  # fall back to the next shorter border
        if p[i] == p[k]:
            k += 1
        pi[i] = k
    return pi

def kmp_search(text, pattern):
    """Start positions of every occurrence of pattern in text. O(n + m) worst case."""
    pi = prefix_function(pattern)
    m, k, hits = len(pattern), 0, []
    for i, ch in enumerate(text):
        while k > 0 and ch != pattern[k]:
            k = pi[k - 1]
        if ch == pattern[k]:
            k += 1
        if k == m:
            hits.append(i - m + 1)
            k = pi[k - 1]                  # keep going: occurrences may overlap
    return hits

assert prefix_function("ababaca") == [0, 0, 1, 2, 3, 0, 1]
assert kmp_search("abababacab", "ababaca") == [2]
assert kmp_search("aaaa", "aa") == [0, 1, 2]
```

A trace of that search, with `k` the number of pattern characters currently matched:

| i | text[i] | k before | Fallbacks | k after |
|---|---------|----------|-----------|---------|
| 0–4 | a b a b a | 0 → 5 | | 5 |
| 5 | b | 5 | needs `c`; k = π[4] = 3, and P[3] = `b` matches | 4 |
| 6 | a | 4 | | 5 |
| 7 | c | 5 | | 6 |
| 8 | a | 6 | | 7 = m: **match at 2**, then k = π[6] = 1 |
| 9 | b | 1 | | 2 |

At i = 5 the naive method would restart at alignment 1 and re-read four characters. KMP keeps the three it knows are right (`aba`, the longest border of `ababa`) and continues.

**Complexity.** Building π is O(m) and searching is O(n), both worst case. The argument is amortized over the run: k grows by at most 1 per character, each fallback shrinks it by at least 1, and it never goes below 0, so the total number of fallbacks is at most the total number of increments, n. The bound is on the total, not per character: with P = `aaaab` and text `aaaac`, the single `c` triggers four fallbacks (k = 4, 3, 2, 1, 0). That matters only for hard real-time stream processing, and Knuth's refinement of the failure function, which skips borders followed by the same character that just failed, cuts the per-character delay to O(log m). Memory is m integers, and the text is consumed one character at a time, so KMP works on a stream that is never stored.

A side result used constantly: the smallest period of P (the least p with P[i] = P[i + p] for every valid i) is m − π[m−1]. For `abababab`, π[7] = 6, so the period is 2.

**The connection to Aho–Corasick.** Build the Aho–Corasick automaton of Section 13.6 from a single pattern. The trie is a path of m + 1 nodes, and the failure link of the node at depth q points to the node at depth π[q−1]. The construction is the same loop, too: Aho–Corasick computes failure links in breadth-first order by following the parent's failure link until it reaches a node with an outgoing edge labelled c, which is `while k > 0 and p[i] != p[k]: k = pi[k - 1]` with "has a child labelled c" in place of `p[k] == c`. Aho–Corasick is the prefix function computed over a trie instead of a string.

### The Z-array

The **Z-array** measures self-overlap from the other direction: Z[i] is the length of the longest common prefix of S and S[i:], with Z[0] = n by convention.

```
S  =  a  a  b  x  a  a  b
i  =  0  1  2  3  4  5  6
Z  =  7  1  0  0  3  1  0
```

Z[4] = 3 because S[4:] = `aab` matches the first three characters of S, and the string ends there.

Computing every Z[i] by direct comparison is O(n²). The linear algorithm keeps the **Z-box** [l, r): among the matches found so far, the one reaching furthest right, so S[l:r] = S[0:r−l]. For i inside the box, S[i:r] is a copy of S[i−l : r−l], whose Z value is already known, so Z[i] ≥ min(r − i, Z[i − l]) without looking at a character. Only characters at or beyond r are compared, and each successful comparison moves r right.

```python
def z_array(s):
    """z[i] = length of the longest common prefix of s and s[i:]; z[0] = len(s)."""
    n = len(s)
    z = [0] * n
    if n:
        z[0] = n
    l = r = 0                              # s[l:r] matches s[0:r-l], r maximal so far
    for i in range(1, n):
        if i < r:
            z[i] = min(r - i, z[i - l])    # reuse what the box already tells us
        while i + z[i] < n and s[z[i]] == s[i + z[i]]:
            z[i] += 1                      # extend by direct comparison
        if i + z[i] > r:
            l, r = i, i + z[i]
    return z

def z_search(text, pattern, sep="\0"):
    """sep must occur in neither string. O(n + m) worst case."""
    m = len(pattern)
    z = z_array(pattern + sep + text)
    return [i - m - 1 for i in range(m + 1, len(z)) if z[i] >= m]

assert z_array("aabxaab") == [7, 1, 0, 0, 3, 1, 0]
assert z_search("abababacab", "ababaca") == [2]
```

r only increases and never exceeds n, so the comparisons that extend a match total at most n, and each i adds at most one failed comparison: **O(n) worst case**. To search, compute Z over P + separator + T; the separator caps every value at m, and the occurrences are exactly the positions in the T part where Z reaches m.

The prefix function and the Z-array carry the same information (each can be converted to the other in O(n)), and both give O(n + m) matching. The practical differences: KMP is online with O(m) memory, while the Z approach as written holds all of P + T. Z values are often easier to reason with, though, because each one directly answers "how far does the text at i agree with the pattern". Matching with at most one mismatch, for example, is two Z computations: one forward over P + sep + T, one over the reversed strings, and an alignment qualifies when the forward and backward agreements together cover at least m − 1 characters.

### Rolling hashes and Rabin–Karp

The third approach turns each length-m window of the text into a number and compares numbers. The **polynomial hash** of a string s of length m, for a prime p and a base b in [0, p), is

```
H(s) = (s[0]·b^(m-1) + s[1]·b^(m-2) + ... + s[m-1]) mod p
```

What makes it useful is that the next window's hash follows from the current one in O(1): remove the leading character's term, shift everything by one power of b, add the new character.

```
H(T[i+1 .. i+m]) = ((H(T[i .. i+m-1]) - T[i]·b^(m-1))·b + T[i+m]) mod p
```

With small numbers (digits as their own values, b = 10, p = 13), searching for P = `14` in T = `3141592`: H(P) = 14 mod 13 = 1. The windows hash to 31 → 5, then (5 − 3·10)·10 + 4 = −246 ≡ 1, then 2, 2, 7, and for `92`, (7 − 5·10)·10 + 2 = −428 ≡ 1. Two windows hash to 1: `14` at position 1 is a real match, and `92` at position 5 is a **spurious hit**, two different strings with the same hash. Rabin–Karp therefore checks the characters whenever the hashes agree:

```python
import random

MOD = (1 << 61) - 1                        # a Mersenne prime, about 2.3 * 10**18

def rabin_karp(text, pattern, base=None):
    """Start positions of pattern in text. Expected O(n + m) when matches are few."""
    n, m = len(text), len(pattern)
    if m == 0 or m > n:
        return []
    if base is None:
        base = random.randrange(256, MOD - 1)   # drawn after the input is fixed
    high = pow(base, m - 1, MOD)          # weight of the character leaving the window
    hp = ht = 0
    for i in range(m):
        hp = (hp * base + ord(pattern[i])) % MOD
        ht = (ht * base + ord(text[i])) % MOD
    hits = []
    for i in range(n - m + 1):
        if ht == hp and text[i:i + m] == pattern:   # verify, so never a false match
            hits.append(i)
        if i + m < n:                       # roll: drop text[i], append text[i+m]
            ht = ((ht - ord(text[i]) * high) * base + ord(text[i + m])) % MOD
    return hits

assert rabin_karp("abababacab", "ababaca") == [2]
assert rabin_karp("3141592", "14") == [1]
```

All three functions in this section were checked against a brute-force search on thousands of random texts over small alphabets, where overlaps and near-misses are most frequent.

**How likely is a collision?** Fix two different strings x and y of length m *before* the base is chosen. H(x) − H(y) = Σ (x[i] − y[i])·b^(m−1−i) mod p is a nonzero polynomial in b of degree at most m − 1. Over the integers mod a prime, which form a field, such a polynomial has at most m − 1 roots. So for b drawn uniformly at random, **Pr[H(x) = H(y)] ≤ (m − 1)/p**. Summed over the n − m + 1 windows, the expected number of spurious hits is at most about nm/p. With p = 2⁶¹ − 1, n = 10⁹ and m = 1,000, that is about 4 × 10⁻⁷ for the entire scan. With a 30-bit prime such as 10⁹ + 7, the same scan expects about 1,000 spurious hits, each costing an m-character check.

There are two ways to use the hash:

- **Las Vegas** (the code above): verify every hash hit. Never wrong, expected O(n + m + m·occ) time. Its worst case is a text full of real matches, `a`ⁿ against `a`ᵐ, where verification costs O(nm). KMP reports the same matches in O(n).
- **Monte Carlo**: trust the hash and skip verification. O(n + m) worst case, wrong with probability at most about nm/p.

**Why the base must be random.** The bound above is a probability over the choice of b, for inputs fixed before b is drawn. With b and p hard-coded, nothing is random: two given strings either collide or they don't, and anyone who can read the code can pick inputs that do. This is the hash-flooding problem from [Section 12.1](ch12-hash-tables.md) in another form. The most common way to get this wrong is to drop the modulus and let 64-bit arithmetic overflow, which computes the hash mod 2⁶⁴. 2⁶⁴ is not prime, the root-counting argument no longer applies, and there are strings of length 1,024 that collide for *every* odd base (Exercise 13.9). An even base is worse: b⁶⁴ ≡ 0 mod 2⁶⁴, so only the last 64 characters affect the hash at all.

**Double hashing** runs two hashes with independently drawn bases (and usually two different primes p₁, p₂) and treats a hit as real only when both agree. For a fixed pair of strings the collision probability becomes at most (m/p₁)·(m/p₂), so two primes near 10⁹ behave like one modulus near 10¹⁸. This is the standard technique in languages without cheap 128-bit multiplication. (It is unrelated to double hashing as an open-addressing probe sequence in [Section 12.3](ch12-hash-tables.md).)

**Beyond one pattern.** A rolling hash turns any substring into a number in O(1): with prefix hashes h[i] = H(S[0..i)), the hash of S[l..r) is h[r] − h[l]·b^(r−l) mod p, so after O(n) preprocessing any two substrings can be compared for equality in O(1) with small error probability. That one primitive gives longest repeated substring by binary search on the length, matching many patterns of the same length through a hash set of their hashes, and two-dimensional matching. In shipped systems, rsync finds moved blocks with a rolling checksum (a sum-based cousin of the polynomial hash) backed by a strong hash; LBFS and backup tools such as restic cut files into content-defined chunks at positions chosen by a rolling Rabin fingerprint (polynomial hashing over GF(2) rather than mod a prime), so an insertion only changes nearby chunks; and MOSS detects plagiarism by "winnowing" the hashes of every k-gram.

| | Prefix function (KMP) | Z-array | Rolling hash (Rabin–Karp) |
|-|-----------------------|---------|---------------------------|
| Extra space | m integers | n + m integers | O(1) plus the current window |
| Matching time | O(n + m) worst case | O(n + m) worst case | O(n + m) expected with few matches (Las Vegas); O(n + m) worst case if unverified (Monte Carlo) |
| Can report a false match | No | No | Only if unverified, probability ≤ about nm/p |
| Reads the text as a stream | Yes | Not as written | Yes |
| Generalizes to | Many patterns (Aho–Corasick) | Matching with one mismatch | O(1) substring equality, many equal-length patterns, 2D |

## 13.6 Aho–Corasick: Searching for Many Patterns at Once

Everything so far searches for one pattern. The common real problem is the opposite: given ten thousand patterns (a spam word list, a malware signature set, a set of banned URLs) find every occurrence of any of them in one pass over the text.

Running a single-pattern search once per pattern is O(k·n) for k patterns. Aho–Corasick does it in **O(n + total pattern length + occurrences)**, independent of k.

The construction is a trie of all patterns, augmented with **failure links**. A failure link from a node points to the node representing the longest proper suffix of the current match that is also a prefix of some pattern: exactly the generalization of the KMP failure function (the prefix function of Section 13.5) to a set of patterns.

```
Patterns: {"he", "she", "his", "hers"}

        root
       /    \
      h      s
     / \      \
    e●  i      h
    |    \      \
    r     s●     e●        ● = a pattern ends here
    |
    s●

Failure link: the node for "she" fails to the node for "he",
because "he" is the longest suffix of "she" that is also a prefix
of a pattern. So on matching "she" you also report "he" for free.
```

When a character doesn't match, follow the failure link instead of restarting. The automaton never re-reads a character of the text, which is where the linear bound comes from. This is the algorithm behind `grep -F`, most intrusion detection systems, and content filters.

## 13.7 Text Editor Buffers: Gap Buffer, Rope, Piece Table

Everything so far treats the string as fixed. A text editor holds one string that changes constantly: a stream of small insertions and deletions, interleaved with reads by position (drawing the screen), by line number ("go to line 50,000"), and undo. Files can be hundreds of megabytes (logs, generated JSON). The obvious representation, one contiguous array of characters, costs O(n − i) to insert at position i because everything after i shifts. Typing near the top of a 100 MB file would move 100 MB per keystroke.

Three access patterns decide which structure fits: edits **at the cursor** (ordinary typing, with strong locality), edits **at scattered positions** (multiple cursors, search-and-replace, a formatter, a collaborator's edits arriving over the network), and **reads** by offset or by line.

### The gap buffer

Keep one array, but leave the free space in the middle, at the cursor, instead of at the end. The text is everything outside the gap: `buf[:gap_start] + buf[gap_end:]`, and the cursor is `gap_start`. Typing writes into the gap; moving the cursor moves the gap by copying the characters it passes over to the other side.

```
GapBuffer("hello world"): capacity 22, cursor at the end, _ marks the gap

       h e l l o ␣ w o r l d _ _ _ _ _ _ _ _ _ _ _     gap = [11, 22)

move_to(5): the 6 characters " world" are copied to the far end of the array
       h e l l o _ _ _ _ _ _ _ _ _ _ _ ␣ w o r l d     gap = [5, 16)

insert(","): one write into the gap, nothing shifts
       h e l l o , _ _ _ _ _ _ _ _ _ _ ␣ w o r l d     gap = [6, 16)
```

```python
class GapBuffer:
    """Text = buf[:gap_start] + buf[gap_end:]. The cursor sits at gap_start."""

    def __init__(self, text="", capacity=16):
        cap = max(capacity, 2 * len(text))
        self.buf = list(text) + [None] * (cap - len(text))
        self.gap_start, self.gap_end = len(text), cap

    def __len__(self):
        return len(self.buf) - (self.gap_end - self.gap_start)

    def __getitem__(self, i):                     # O(1)
        if not 0 <= i < len(self):
            raise IndexError(i)
        if i < self.gap_start:
            return self.buf[i]
        return self.buf[i + self.gap_end - self.gap_start]

    def move_to(self, pos):                       # O(|pos - cursor|)
        if not 0 <= pos <= len(self):
            raise IndexError(pos)
        while self.gap_start > pos:               # carry characters left of the gap to its right
            self.gap_start -= 1
            self.gap_end -= 1
            self.buf[self.gap_end] = self.buf[self.gap_start]
        while self.gap_start < pos:               # carry characters right of the gap to its left
            self.buf[self.gap_start] = self.buf[self.gap_end]
            self.gap_start += 1
            self.gap_end += 1

    def insert(self, s):                          # O(len(s)) amortized, at the cursor
        for ch in s:
            if self.gap_start == self.gap_end:
                self._grow()
            self.buf[self.gap_start] = ch
            self.gap_start += 1

    def delete(self, k=1):                        # O(1): backspace k characters
        self.gap_start = max(0, self.gap_start - k)

    def _grow(self):                              # double the array: O(n), rare
        old_cap = len(self.buf)
        tail = self.buf[self.gap_end:]
        self.buf = self.buf[:self.gap_start] + [None] * old_cap + tail
        self.gap_end = self.gap_start + old_cap

    def __str__(self):
        return "".join(self.buf[:self.gap_start] + self.buf[self.gap_end:])

g = GapBuffer("hello world")
g.move_to(5)
g.insert(",")
assert str(g) == "hello, world" and (g.gap_start, g.gap_end) == (6, 16)
g.delete(1)
assert str(g) == "hello world" and g[6] == "w"
```

**Costs.** Insertion at the cursor is O(1) amortized (the gap is refilled by doubling, the same argument as the dynamic array in [Section 3.4](../volume-1/ch03-arrays-the-foundation-of-contiguous-storage.md)); backspace is O(1), just widening the gap; indexing is O(1), one comparison and one array read. An edit at an arbitrary position first moves the gap there, O(distance), so **O(n) worst case**. That is the whole tradeoff: typing produces long runs of edits in one place, so gap moves are rare and short, and the gap buffer has the best constant factors of anything here, because the text is one contiguous array. It degrades when edits alternate between distant positions, which is exactly what multiple cursors and some search-and-replace orders do (Exercise 13.10). Nothing in it helps find line k (you scan for newlines or keep a separate index), and it has no undo of its own: overwritten gap contents are gone, so editors keep a separate log of (position, text inserted or deleted) records. Emacs is the best-known gap-buffer editor; its buffer text is a gap buffer (`GPT` and `GAP_SIZE` in its C source), and its undo log is the Lisp-visible `buffer-undo-list`.

### The rope

A **rope** (Boehm, Atkinson and Plass, 1995) is a balanced binary tree whose leaves hold short strings. The text is the left-to-right concatenation of the leaves, and each internal node stores its **weight**, the length of its left subtree:

```
                [9]                   weight = length of the left subtree
              /     \
           [4]       [6]
          /   \     /    \
     "the " "quick" " brown" " fox"        text: "the quick brown fox"

index(12): 12 >= 9, go right with 12 - 9 = 3; 3 < 6, go left;
           " brown"[3] = 'o'.
```

The operations are built from two primitives. **Concat** makes a new root over two ropes: O(1), plus O(log n) to rebalance. **Split** at position i walks down to i, cuts the leaf there in two, and separates the tree along that root-to-leaf path: O(log n). Insert is split, then two concats; delete is two splits and one concat. On a balanced rope every one of these is **O(log n) worst case wherever the edit lands**: the cursor gives no advantage, and scattered edits cost no more. Indexing is O(log n) instead of O(1), and sequential reads use an iterator that walks leaves rather than descending from the root per character.

Two extensions make ropes the structure of choice for modern editors:

- **Augmented counts.** Each node can store, besides the character count, the number of newlines in its subtree. "Offset of line k" and "line containing offset i" then descend the tree in O(log n), the same subtree-summary trick as the weights.
- **Persistence.** If nodes are never modified in place, an edit creates only the O(log n) nodes on the split paths and shares everything else with the previous version, which is path copying from [Chapter 17](../volume-3/ch17-persistent-data-structures.md). An old root is a complete old version, so undo is "keep the root", and a background thread (syntax highlighting, saving, a language server) can read a consistent snapshot while the user keeps typing.

Production ropes put chunks of tens to about a thousand bytes in each leaf and use a B-tree rather than a binary tree, so the tree is shallow and the per-character work is a copy within one small array. xi-editor's `xi-rope` is a B-tree rope, Helix uses the Ropey library, and Zed's rope is a B+ tree of chunks (its `SumTree`) whose nodes carry summaries including line counts and UTF-16 lengths; Zed takes a snapshot of a buffer for a background thread by copying the root and incrementing reference counts. The cost is constant factors: more memory per character than an array, and pointer chasing on every access.

### The piece table

A **piece table** never moves or overwrites text. It keeps two buffers: the **original** buffer, the file exactly as loaded and never modified, and the **add** buffer, to which every typed character is appended. The document is a sequence of **pieces**, each a (buffer, start, length) triple naming a span of one buffer; the text is the concatenation of the spans in piece order.

Load `the fox jumped`, insert `quick brown ` at offset 4, delete the final `ed`, then type `s`:

```
start:                 [(orig, 0, 14)]                                   "the fox jumped"
insert(4, "quick brown "): split the piece at 4, add a piece for the new text
                       [(orig, 0, 4), (add, 0, 12), (orig, 4, 10)]       "the quick brown fox jumped"
delete(24, 2):         split at 24, drop the piece covering "ed"
                       [(orig, 0, 4), (add, 0, 12), (orig, 4, 8)]        "the quick brown fox jump"
insert(24, "s"):       [(orig, 0, 4), (add, 0, 12), (orig, 4, 8), (add, 12, 1)]
                                                                         "the quick brown fox jumps"
```

<figure>
{{#include ../images/piece-table.svg}}
<figcaption>Each piece points into one of the two buffers; the deleted "ed" is still in the original buffer, just no longer referenced, which is what makes undo free.</figcaption>
</figure>

```python
class PieceTable:
    """Text = concatenation of pieces; each piece is (buffer, start, length)."""
    ORIGINAL, ADD = 0, 1

    def __init__(self, text=""):
        self.buffers = (text, [])                 # original is read-only, add is append-only
        self.pieces = [(self.ORIGINAL, 0, len(text))] if text else []
        self.history = []                         # earlier piece lists, for undo

    def _split(self, pos):
        """Make pos fall on a piece boundary; return the index of the piece starting there."""
        offset = 0
        for i, (buf, start, length) in enumerate(self.pieces):
            if pos == offset:
                return i
            if pos < offset + length:             # pos is inside this piece: cut it in two
                k = pos - offset
                self.pieces[i:i + 1] = [(buf, start, k), (buf, start + k, length - k)]
                return i + 1
            offset += length
        if pos == offset:
            return len(self.pieces)
        raise IndexError(pos)

    def insert(self, pos, s):                     # O(number of pieces)
        if not s:
            return
        self.history.append(list(self.pieces))
        add = self.buffers[self.ADD]
        i = self._split(pos)
        prev = self.pieces[i - 1] if i > 0 else None
        if prev and prev[0] == self.ADD and prev[1] + prev[2] == len(add):
            self.pieces[i - 1] = (self.ADD, prev[1], prev[2] + len(s))   # typing: extend
        else:
            self.pieces.insert(i, (self.ADD, len(add), len(s)))
        add.extend(s)                             # text is only ever appended

    def delete(self, pos, length):                # O(number of pieces)
        if length <= 0:
            return
        self.history.append(list(self.pieces))
        i = self._split(pos)
        j = self._split(pos + length)
        del self.pieces[i:j]                      # the characters stay in their buffers

    def undo(self):
        if self.history:
            self.pieces = self.history.pop()

    def __getitem__(self, i):                     # O(number of pieces)
        for buf, start, length in self.pieces:
            if i < length:
                return self.buffers[buf][start + i]
            i -= length
        raise IndexError(i)

    def __len__(self):
        return sum(length for _, _, length in self.pieces)

    def __str__(self):
        return "".join("".join(self.buffers[b][s:s + n]) for b, s, n in self.pieces)

pt = PieceTable("the fox jumped")
pt.insert(4, "quick brown ")
pt.delete(24, 2)
pt.insert(24, "s")
assert str(pt) == "the quick brown fox jumps"
assert pt.pieces == [(0, 0, 4), (1, 0, 12), (0, 4, 8), (1, 12, 1)]
pt.undo()
assert str(pt) == "the quick brown fox jump"
pt.undo()
assert str(pt) == "the quick brown fox jumped"
```

Both classes were tested against a plain Python string on thousands of random edit sequences, including undo for the piece table.

**Costs.** With k pieces in a list, finding the piece that contains an offset is O(k), and so are insert, delete and indexing. k grows with the number of separate edits, not with the number of characters: each insert adds at most two pieces and each delete at most one net, so k ≤ 2e + 1 after e edits. Ordinary typing adds none, because the `prev` check extends the piece that ends at the end of the add buffer; editors also cache the cursor's piece, so typing is O(1) amortized. Loading is O(1) beyond reading the file: the original buffer is the file's bytes, never copied or split into lines, and can be memory-mapped. Memory is the original file plus every character ever typed (deleted text is never reclaimed while undo can reach it) plus the pieces.

**Undo comes free.** The buffers only ever grow, so every past version of the document is still fully described by its piece list. Undo restores an earlier list, and the code above simply snapshots the list (O(k) per edit). Real implementations record the few piece-level changes each edit made and invert them, but the principle is the same: no text is ever copied to support undo.

**The piece tree.** Replacing the list with a balanced search tree of pieces, each node caching the total length (and newline count) of its left subtree, makes locating an offset or a line O(log k). VS Code switched to exactly this in 2018 (release 1.21): a piece table whose pieces live in a red-black tree, with each node storing its left subtree's length and line-feed count. The old representation, an array of line objects, cost roughly 40 to 60 bytes per line; a 35 MB file of 13.7 million lines took about 600 MB, while the piece tree's memory after loading is close to the file size.

### Comparing the three

n is the document length and k the number of pieces.

| | Gap buffer | Rope (balanced) | Piece table (list) | Piece tree |
|-|-----------|-----------------|--------------------|------------|
| Insert/delete at the cursor | O(1) amortized | O(log n) worst case | O(1) amortized with a cached cursor piece | O(log k) worst case |
| Insert/delete elsewhere | O(n) worst case (gap move) | O(log n) worst case | O(k) | O(log k) worst case |
| Character at offset i | O(1) | O(log n) | O(k) | O(log k) |
| Offset of line j | O(n) scan, unless indexed separately | O(log n) with newline counts | O(n) scan | O(log k) with line-feed counts |
| Undo | Separate edit log | Keep old roots (persistent) | Restore old piece lists; text never destroyed | Same as piece table |
| Memory beyond the text | The gap | Node per chunk | All deleted text, plus pieces | Same, plus tree nodes |
| Used by | Emacs | xi-editor, Zed, Helix (Ropey) | Bravo; Word's "fast save" format | VS Code |

For one person typing into a file of a few megabytes, all three are instantaneous and the gap buffer is the simplest. The differences appear with large files (load time and memory favour the piece table), with edits scattered across the document (the gap buffer loses), and with concurrency (a persistent rope or piece tree lets other threads read snapshots without locking out the user).

## 13.8 Choosing a String Structure

| Need | Use | Why |
|------|-----|-----|
| Autocomplete, prefix queries | Trie or radix tree | O(P) prefix descent |
| Dictionary with tight memory | Radix tree, or succinct trie | Nodes proportional to strings, not characters |
| IP longest-prefix match | PATRICIA / ART | Bit-level tests, ordered |
| Substring search in one fixed text | Suffix array + LCP | Suffix-tree power at 4 bytes per character |
| Same, with minimal memory | FM-index | Compressed to text entropy, still searchable |
| Many patterns, one text | Aho–Corasick | O(n) regardless of pattern count |
| One pattern, one pass, no preprocessing of text | KMP or Boyer–Moore | O(n + m), no index to build |
| Many substring-equality checks on one string | Rolling hash with prefix hashes | O(1) per comparison after O(n) setup, random base |
| A string being edited (an editor buffer) | Gap buffer, rope, or piece table | Section 13.7: by locality of edits, file size, and need for snapshots |
| Exact set membership only, no prefix queries | Hash set | Simpler and faster when you don't need order |

The decisive question is **which side you preprocess**. Index the text (suffix array, FM-index) when the text is fixed and queries are many: a genome, a codebase, a document corpus. Index the pattern (KMP, Aho–Corasick) when the text streams past once and the patterns are fixed: a log pipeline, a packet filter.

## 13.9 Applications

**Autocomplete**: Trie prefix matching
**Spell checking**: Dictionary lookup
**IP routing**: Longest prefix match
**DNA sequencing**: Pattern matching
**Search engines**: Inverted indexes

In shipped systems: Elasticsearch and Lucene store their term dictionaries as finite-state transducers, a compressed-trie variant that shares suffixes as well as prefixes; the Linux kernel routes packets through `fib_trie`, a PATRICIA variant; BWA and Bowtie align sequencing reads against an FM-index of the reference genome; `grep -F` and Snort use Aho–Corasick; Redis implements its stream IDs and cluster key routing over radix trees; and DuckDB and HyPer index with ART. Editors split three ways: Emacs keeps text in a gap buffer, VS Code in a piece tree, and Zed, xi-editor and Helix in ropes; rsync and content-defined chunking in backup tools rest on rolling hashes.

## 13.10 Historical Context

Tries were described by Axel Thue in 1912 in a paper on repetition-free strings, long before computers existed to store them. René de la Briandais rediscovered them for file searching in 1959, and Edward Fredkin named them in 1960. From *retrieval*, which is why the original pronunciation is "tree" and why nobody agrees about it.

Donald Morrison published PATRICIA in 1968 ("Practical Algorithm To Retrieve Information Coded In Alphanumeric"), one of the better backronyms in computing.

Peter Weiner gave the first linear-time suffix tree construction in 1973, in a paper Knuth reportedly called "the algorithm of the year." McCreight simplified it in 1976, and Ukkonen produced the online version in 1995 that most implementations follow.

Udi Manber and Gene Myers introduced suffix arrays in 1990 explicitly as the space-efficient answer to suffix trees, and were candid that they were trading a little query time for a large memory saving: a trade that looks better every year as datasets grow faster than RAM.

Alfred Aho and Margaret Corasick published their multi-pattern algorithm in 1975 while at Bell Labs, where it went straight into `fgrep`.

James Morris and Vaughan Pratt found the linear-time single-pattern algorithm in 1970, and Donald Knuth found it independently; the three published it together in 1977 as the Knuth–Morris–Pratt algorithm. Richard Karp and Michael Rabin published randomized fingerprint matching in 1987. The Z-algorithm reached most students through Dan Gusfield's 1997 textbook *Algorithms on Strings, Trees, and Sequences*, which builds linear-time matching on it.

Editor buffers have their own lineage. Bravo (Butler Lampson and Charles Simonyi, Xerox PARC, 1974) used a piece table, and Simonyi went on to lead Microsoft Word. Hans Boehm, Russ Atkinson and Michael Plass described ropes in 1995, drawing on the Cedar environment at PARC, where ropes had been the standard string representation almost from the start. Charles Crowley's 1998 survey *Data Structures for Text Sequences* compared gap buffers, piece tables and their relatives and argued for the piece table, and VS Code's 2018 rewrite to a piece tree brought the idea back into the mainstream.

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**13.1 ★ Trie versus radix tree.** Insert the words `test`, `team`, `toast`, `to` into the `Trie` from Section 13.1. (a) Draw the trie and count its nodes, excluding the root. (b) Draw the radix tree for the same words and count its nodes. (c) Which node is the reason `is_word` cannot be replaced by "is a leaf"?

<details>
<summary>Solution</summary>

(a) The trie has **10** nodes:

```
root
 └── t
     ├── e
     │   ├── s
     │   │   └── t ●      "test"
     │   └── a
     │       └── m ●      "team"
     └── o ●              "to"
         └── a
             └── s
                 └── t ●  "toast"
```

(b) Compressing every chain of single-child nodes that do not end a word gives **6** nodes:

```
root
 └── "t"
     ├── "e"
     │   ├── "st" ●       "test"
     │   └── "am" ●       "team"
     └── "o" ●            "to"
         └── "ast" ●      "toast"
```

The chains s→t, a→m and a→s→t each collapse to one edge. Note that `"o"` cannot be merged with `"ast"` even though it has a single child: it ends a word, and merging would lose that fact. That is the radix-tree invariant from Section 13.2 (every internal node ends a word or has at least two children). Here the branching nodes are `"t"` and `"e"`: 2, within the bound of n − 1 = 3.

(c) The `o` node. It ends `to` but is internal, because `toast` continues below it. A trie that treats "leaf" as "end of word" would report `to` as absent.

</details>

**13.2 ★ The hidden cost of comparing strings.** A colleague stores 1,000,000 URLs (about 80 characters each, most beginning with `https://www.`) in a balanced BST and argues: "a lookup is about 20 comparisons, a trie lookup is 80 steps, so the BST is four times faster." What is wrong with the argument, and what is the fair comparison?

<details>
<summary>Solution</summary>

A string comparison is not O(1). Each of the ~20 comparisons (log₂ 10⁶ ≈ 20) scans characters until the first difference, and URLs share long prefixes, so many comparisons read well past the common `https://www.` before deciding. Near the bottom of the tree, the keys being compared against are the query's sorted neighbours, which share the longest prefixes of all. The honest bound is the one in the Section 13.1 table: O(L log n), up to 20 × 80 = 1,600 character comparisons, against the trie's O(L) = 80 node steps.

The fair comparison also cuts the other way, which is worth saying plainly: the BST's character comparisons are sequential `memcmp`-style scans over contiguous bytes, while each trie step is a pointer hop to a node that is probably not in cache. Which wins on real hardware depends on how long the shared prefixes are and on memory layout, which is why radix trees and ART (fewer, fatter nodes) are the practical answer rather than a plain trie.

</details>

**13.3 ★★ Suffix array and LCP by hand.** Build the suffix array and LCP array for `mississippi$` (`$` sorts before every letter). Then use the LCP array to find the longest repeated substring, and say where it occurs.

<details>
<summary>Hint</summary>

Group the suffixes by first letter first: one `$`, four starting with `i`, one `m`, two `p`, four `s`. Sort within each group.

</details>

<details>
<summary>Solution</summary>

```
rank  pos  suffix          LCP with previous
  0    11  $               0
  1    10  i$              0
  2     7  ippi$           1   ("i")
  3     4  issippi$        1   ("i")
  4     1  ississippi$     4   ("issi")
  5     0  mississippi$    0
  6     9  pi$             0
  7     8  ppi$            1   ("p")
  8     6  sippi$          0
  9     3  sissippi$       2   ("si")
 10     5  ssippi$         1   ("s")
 11     2  ssissippi$      3   ("ssi")
```

Suffix array: `[11, 10, 7, 4, 1, 0, 9, 8, 6, 3, 5, 2]`.
LCP array: `[0, 0, 1, 1, 4, 0, 0, 1, 0, 2, 1, 3]`.

A substring repeats exactly when two suffixes share it as a prefix, and the longest common prefix of any two suffixes is achieved by some *adjacent* pair in sorted order. So the longest repeated substring has length max(LCP) = 4, at rank 4: suffixes 4 and 1 share **`issi`**, which occurs at positions 1 and 4 (`mississippi[1:5]` and `mississippi[4:8]`; the two occurrences overlap in the `i` at position 4). This is the suffix-array version of "deepest internal node" from the Section 13.3 table.

</details>

**13.4 ★★ Count occurrences with a suffix array.** Write `count_occurrences(text, sa, pattern)` that returns how many times `pattern` occurs in `text`, using two binary searches over the suffix array. What is its running time?

<details>
<summary>Hint</summary>

All suffixes that start with the pattern are contiguous in the suffix array. Find the first rank whose suffix (cut to m characters) is ≥ the pattern, and the first whose suffix is > it.

</details>

<details>
<summary>Solution</summary>

```python
def count_occurrences(text, sa, pattern):
    """Number of times `pattern` occurs in `text`. O(m log n)."""
    m = len(pattern)

    def first_at_least(target):
        # First rank whose suffix, cut to m characters, is >= target.
        lo, hi = 0, len(sa)
        while lo < hi:
            mid = (lo + hi) // 2
            if text[sa[mid]:sa[mid] + m] < target:
                lo = mid + 1
            else:
                hi = mid
        return lo

    def first_greater(target):
        # First rank whose suffix, cut to m characters, is > target.
        lo, hi = 0, len(sa)
        while lo < hi:
            mid = (lo + hi) // 2
            if text[sa[mid]:sa[mid] + m] <= target:
                lo = mid + 1
            else:
                hi = mid
        return lo

    return first_greater(pattern) - first_at_least(pattern)

text = "banana$"
sa = [6, 5, 3, 1, 0, 4, 2]
assert count_occurrences(text, sa, "ana") == 2
assert count_occurrences(text, sa, "a") == 3
assert count_occurrences(text, sa, "nab") == 0
```

Cutting each suffix to m characters is what makes the matches contiguous: every suffix that starts with the pattern compares *equal* to it, so they form one block, and the two searches find its ends. The ranks in that block are the occurrences, so `sa[lo:hi]` lists their positions if you need them.

Each binary search takes O(log n) steps, each comparing up to m characters, so the total is **O(m log n)**, independent of how many occurrences there are. (With the LCP array this improves to O(m + log n), as Section 13.4 notes.)

</details>

**13.5 ★★ Aho–Corasick failure links.** For the patterns `{"he", "she", "his", "hers"}` from Section 13.6, give the failure link of every trie node. Then run the automaton over the text `ushers` and list every match it reports, with the position where each match starts.

<details>
<summary>Hint</summary>

The failure link of a node spelling s goes to the node for the longest proper suffix of s that is also a path from the root. For each node, try the suffixes from longest to shortest.

</details>

<details>
<summary>Solution</summary>

| Node | Proper suffixes tried | Failure link |
|------|-----------------------|--------------|
| h | (empty) | root |
| he | e | root |
| hi | i | root |
| his | is, s | s |
| her | er, r | root |
| hers | ers, rs, s | s |
| s | (empty) | root |
| sh | h | h |
| she | he | he |

Because `she` fails to `he`, which ends a pattern, the output set of `she` is {she, he}.

Running over `ushers`, following the goto edge when it exists and the failure link otherwise:

| i | char | State after | Reported |
|---|------|-------------|----------|
| 0 | u | root (no edge) | |
| 1 | s | s | |
| 2 | h | sh | |
| 3 | e | she | `she` at 1, `he` at 2 |
| 4 | r | she has no `r` edge; fail to he, take `r`: her | |
| 5 | s | hers | `hers` at 2 |

Three matches: `she` at 1, `he` at 2, `hers` at 2. Note step 4: the automaton never moved backwards in the text. It moved from `she` to `her` by following one failure link, which is why the total work is linear.

</details>

**13.6 ★★ Find the bug.** This `delete` for the Section 13.1 `Trie` is meant to unmark a word and prune nodes that no longer lead to any word. Starting from the chapter's trie of `{"cat", "car", "card", "do", "dog", "done"}`, what does the trie contain after `delete("car")`? After `delete("do")` (on a fresh copy)? Fix it.

```python
def delete(self, word):
    path = [self.root]
    for ch in word:
        nxt = path[-1].children.get(ch)
        if nxt is None:
            return False
        path.append(nxt)
    if not path[-1].is_word:
        return False
    path[-1].is_word = False
    # Prune nodes that no longer lead anywhere.
    for i in range(len(word) - 1, -1, -1):
        node = path[i + 1]
        if node.is_word:
            break
        del path[i].children[word[i]]
    return True
```

<details>
<summary>Solution</summary>

The pruning loop stops only at a node that ends a word. It never checks whether the node still has children, so it cuts away live subtrees.

- `delete("car")`: the `r` node is no longer a word, so it is cut, taking `card` with it. Then `a` is cut (it is not a word), which also removes `cat`. Then `c` is cut. The trie now holds only `do`, `dog`, `done`.
- `delete("do")`: the `o` node is cut along with `dog` and `done` below it, then `d`. The trie holds only `cat`, `car`, `card`.

The loop happens to work for `delete("card")`, which is why a quick test can miss the bug.

The fix: a node may be pruned only if it ends no word **and** has no children.

```python
def delete(self, word):
    path = [self.root]
    for ch in word:
        nxt = path[-1].children.get(ch)
        if nxt is None:
            return False
        path.append(nxt)
    if not path[-1].is_word:
        return False
    path[-1].is_word = False
    for i in range(len(word) - 1, -1, -1):
        node = path[i + 1]
        if node.is_word or node.children:
            break
        del path[i].children[word[i]]
    return True
```

Once one node survives, every ancestor has at least that child, so stopping (rather than continuing) is correct. With the fix, `delete("car")` only clears the mark on `r`, since `r` still has the child `d`.

</details>

**13.7 ★★★ Longest common substring.** The Section 13.3 table says the longest common substring of A and B comes from a suffix structure over `A#B$`. Implement `longest_common_substring(a, b)` with a suffix array and Kasai's LCP algorithm. You may build the suffix array naively with `sorted`. Explain why it is enough to look only at *adjacent* suffixes, and why Kasai's algorithm runs in O(n).

<details>
<summary>Hint</summary>

A common substring is a common prefix of a suffix starting in A and a suffix starting in B. For Kasai: if suffix i shares h characters with its sorted predecessor, suffix i + 1 shares at least h − 1 with its own.

</details>

<details>
<summary>Solution</summary>

```python
def suffix_array(s):
    # Simple O(n^2 log n) construction; fine for an exercise.
    return sorted(range(len(s)), key=lambda i: s[i:])

def lcp_kasai(s, sa):
    """LCP[r] = common prefix length of suffixes at ranks r-1 and r. O(n)."""
    n = len(s)
    rank = [0] * n
    for r, i in enumerate(sa):
        rank[i] = r
    lcp = [0] * n
    h = 0
    for i in range(n):                 # suffixes in text order, not rank order
        r = rank[i]
        if r == 0:
            h = 0
            continue
        j = sa[r - 1]                  # the suffix just before i in sorted order
        while i + h < n and j + h < n and s[i + h] == s[j + h]:
            h += 1
        lcp[r] = h
        if h > 0:
            h -= 1                     # the next suffix keeps at least h-1
    return lcp

def longest_common_substring(a, b):
    s = a + "#" + b + "$"              # '#' and '$' occur in neither string
    sa = suffix_array(s)
    lcp = lcp_kasai(s, sa)
    boundary = len(a)                  # position of '#'
    best_len, best_pos = 0, 0
    for r in range(1, len(s)):
        i, j = sa[r - 1], sa[r]
        if (i < boundary) != (j < boundary) and lcp[r] > best_len:
            best_len, best_pos = lcp[r], sa[r]
    return s[best_pos:best_pos + best_len]

assert lcp_kasai("banana$", suffix_array("banana$")) == [0, 0, 1, 3, 0, 0, 2]
assert longest_common_substring("xabcdy", "zzbcdq") == "bcd"
assert longest_common_substring("banana", "ananas") == "anana"
assert longest_common_substring("abc", "xyz") == ""
```

**Why the separators.** `#` occurs once, so no common prefix of two suffixes can run across it; a match found between an A-suffix and a B-suffix lies entirely inside A and inside B.

**Why adjacent pairs suffice.** The LCP of the suffixes at ranks p < q is the minimum of `lcp[p+1..q]`. Take the best pair (one from A, one from B) with value L. Walking from rank p to rank q, the side (A or B) must switch at some adjacent pair, and every adjacent LCP in that range is at least L. So some adjacent cross-side pair also achieves L, and scanning adjacent pairs finds it.

**Why Kasai is O(n).** It visits suffixes in text order. If suffix i matches its predecessor for h characters, then dropping the first character gives suffix i + 1 a string (the predecessor minus its first character) that sorts before it and shares h − 1 characters, so `lcp[rank[i+1]] ≥ h − 1`. The algorithm therefore starts each comparison at h − 1 instead of 0. h decreases by at most 1 per step, never exceeds n, and so increases at most 2n times in total: the inner `while` loop does O(n) work over the whole run.

</details>

**13.8 ★★ Prefix function, Z-array and periods.** (a) Compute the prefix function π and the Z-array for `aabaaab`. (b) Use π to find the smallest period of `abcabcab`. (c) Explain why m − π[m−1] is always the smallest period of a string of length m.

<details>
<summary>Solution</summary>

(a)

```
S  =  a  a  b  a  a  a  b
i  =  0  1  2  3  4  5  6
π  =  0  1  0  1  2  2  3
Z  =  7  1  0  2  3  1  0
```

Two entries worth checking by hand. π[5] = 2: the prefix `aabaaa` ends in `aa`, which is also its start, but `aab` ≠ `aaa`, so 2 is the longest border. Computing it, the algorithm had k = 2 (border `aa` of `aabaa`), tried to extend with S[5] = `a` against S[2] = `b`, fell back to k = π[1] = 1, and extended `a` to `aa`. Z[3] = 2: S[3:] = `aaab` agrees with S = `aab…` for two characters, then `a` ≠ `b`.

(b) π for `abcabcab` is `[0, 0, 0, 1, 2, 3, 4, 5]`, so the period is 8 − 5 = 3: the string is `abc` repeated and cut off.

(c) P has period p exactly when P[i] = P[i + p] for every valid i, which says the prefix of length m − p equals the suffix of length m − p, that is, P has a border of length m − p. So periods and borders correspond one to one (p ↔ m − p), and the smallest period corresponds to the longest border, whose length is π[m−1].

```python
def smallest_period(p):
    return len(p) - prefix_function(p)[-1]

assert prefix_function("aabaaab") == [0, 1, 0, 1, 2, 2, 3]
assert z_array("aabaaab") == [7, 1, 0, 2, 3, 1, 0]
assert smallest_period("abcabcab") == 3
assert smallest_period("abcd") == 4
```

(This block uses `prefix_function` and `z_array` from Section 13.5.)

</details>

**13.9 ★★★ Breaking a 64-bit rolling hash.** A library computes polynomial hashes with 64-bit unsigned integers and lets them overflow, so all arithmetic is mod 2⁶⁴. The base is random but always odd. Let t₀ = `0`, u₀ = `1`, and t_{k+1} = t_k u_k, u_{k+1} = u_k t_k (concatenation), so t₁₀ and u₁₀ are 1,024 characters long (t is the Thue–Morse sequence, u its complement). Show that H(t₁₀) = H(u₁₀) for every odd base. Why does the collision bound of Section 13.5 not protect against this?

<details>
<summary>Hint</summary>

Let D_k = H(t_k) − H(u_k), computed over the integers. Write H(t_{k+1}) and H(u_{k+1}) in terms of H(t_k), H(u_k) and b^(2^k), and find a recurrence for D_k. Then count factors of 2.

</details>

<details>
<summary>Solution</summary>

For strings x and y with |y| = L, H(xy) = H(x)·b^L + H(y). With L = 2^k:

```
H(t_{k+1}) = H(t_k)·b^L + H(u_k)
H(u_{k+1}) = H(u_k)·b^L + H(t_k)
D_{k+1}    = D_k·b^L − D_k = D_k·(b^(2^k) − 1)
```

D₀ = 0 − 1 = −1, so D₁₀ = −(b − 1)(b² − 1)(b⁴ − 1)···(b^512 − 1).

Now count factors of 2 for odd b. b − 1 is even: at least 1. b² − 1 = (b − 1)(b + 1) is a product of two consecutive even numbers, so it is divisible by 8: at least 3. Each further factor is b^(2^(i+1)) − 1 = (b^(2^i) − 1)(b^(2^i) + 1), and the second factor is even, so the count grows by at least 1 each time: b^(2^i) − 1 has at least i + 2 factors of 2 for i ≥ 1. The total for i = 0 to 9 is at least 1 + (3 + 4 + ··· + 11) = 1 + 63 = 64. So 2⁶⁴ divides D₁₀, and the two strings collide mod 2⁶⁴ whatever the odd base. (For k = 9 the count is only 1 + 52 = 53, so 512 characters are not enough; that agrees with experiment.)

```python
import random

def h64(s, b):
    h = 0
    for c in s:
        h = (h * b + c) & ((1 << 64) - 1)   # what overflowing uint64 arithmetic computes
    return h

t, u = [0], [1]
for _ in range(10):
    t, u = t + u, u + t
assert len(t) == 1024 and t != u
for _ in range(1000):
    b = random.randrange(1, 1 << 64) | 1    # any odd base
    assert h64(t, b) == h64(u, b)
```

The Section 13.5 bound relies on the modulus being prime: over a field, a nonzero polynomial of degree m − 1 has at most m − 1 roots, so few bases are bad. The integers mod 2⁶⁴ are not a field, and a polynomial there can vanish at every odd input. Here D₁₀, viewed as a polynomial in b, is zero for all 2⁶³ odd bases. Choosing the base at random does not help when the modulus admits a polynomial that kills every base. Use a prime modulus such as 2⁶¹ − 1 (and still draw the base at random).

</details>

**13.10 ★★ Two cursors.** A 10 MB file is open in an editor. The user places two cursors, at offsets 1,000 and 9,000,000, and types 20 characters; each keystroke inserts one character at each cursor. Estimate the work for (a) a gap buffer, (b) a piece table using the Section 13.7 code (how many pieces are there at the end?), and (c) a balanced rope.

<details>
<summary>Solution</summary>

(a) Each keystroke inserts at the first cursor, then at the second, and the next keystroke returns to the first. Every visit moves the gap about 9 × 10⁶ characters, twice per keystroke: roughly 20 × 2 × 9 × 10⁶ ≈ 3.6 × 10⁸ character copies for 40 characters typed. With one cursor the same 20 keystrokes cost 20 writes. This is why multi-cursor editing is the gap buffer's weak spot.

(b) The first insertion splits the original piece at offset 1,000 and adds a piece; the second splits at the far cursor and adds another: 5 pieces. After that, every insertion lands right after an add-buffer piece, but that piece no longer ends at the end of the add buffer, because the other cursor's character was appended in between. The "extend" shortcut fails, and each insertion adds one piece: 5 + 19 × 2 = **43 pieces**. Each operation scans that list, so the work is trivial (a few thousand piece visits), and nothing proportional to the 10 MB file is ever touched. The interleaving shows up in the piece count, not in copying.

```python
pt = PieceTable("x" * 100)
c1, c2 = 10, 90
for _ in range(20):
    pt.insert(c1, "a"); c1 += 1; c2 += 1
    pt.insert(c2, "b"); c2 += 1
assert len(pt.pieces) == 43
```

(c) Each insertion is a split and two concatenations, O(log n): with leaves of about 1 KB, a 10 MB rope has about 10⁴ leaves and depth around 14 for a binary tree. 40 insertions cost a few hundred node visits plus copying within small leaves. Like the piece table, the rope does not care how far apart the cursors are.

</details>

---

## Where this connects

- [Chapter 24: Research-Grade Data Structures](../volume-4/ch24-research-grade-data-structures.md). The compressed, succinct versions of these indexes
- [Chapter 23: Advanced Competitive Programming Data Structures](../volume-4/ch23-advanced-competitive-programming-data-structures.md). Suffix automata and palindromic trees for contests
