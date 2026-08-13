# Chapter 13: String Data Structures

Strings break the assumptions the rest of this book runs on. A comparison is no longer O(1) — comparing two strings costs up to their length. And the queries people actually want are different in kind: not "is this key present" but "which keys start with this", "where does this pattern occur", "what is the longest repeated section". Hash tables answer none of those, because hashing destroys exactly the structure the questions are about.

The structures here exploit the one property strings have that opaque keys don't: **shared prefixes**. Every structure in this chapter is a way of storing a set of strings so that common prefixes are stored once.

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

The end-of-word marks matter more than they look. `car` and `card` both terminate, and `car`'s marker sits on an *internal* node — so "is this node a leaf" is not the same question as "does a word end here". A trie that conflates the two cannot store a word that is a prefix of another word, which is a common bug.

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
        """Every stored word beginning with `prefix` — the autocomplete query."""
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

Note the BST column: string comparison is O(L), so a BST of strings is O(L log n), not O(log n) — a detail that reference tables routinely get wrong.

**Space is the problem.** A node with a 256-entry array per character costs 2KB per node before storing anything. For a dictionary of English words that is wildly wasteful, since most nodes have one or two children. The mitigations, in increasing order of sophistication: a hash map per node (what the code above does — flexible, one indirection), a sorted array of children (compact, binary search), a 256-bit bitmap plus a packed child array (succinct, the approach in [Chapter 24](../volume-4/ch24-research-grade-data-structures.md)), or compressing the paths outright — which is the next section.

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

The guarantee this buys: **every internal node either ends a word or has at least two children**, so a radix tree over n strings has at most n−1 branching nodes regardless of how long the strings are. Space becomes proportional to the number of strings, not the number of characters. For sparse key sets — long keys with little overlap, like URLs or file paths — the saving is enormous.

**PATRICIA tries** take it further by storing, at each node, only the *bit position* that distinguishes the subtrees, skipping the intervening bits entirely. A lookup descends on those bit tests alone and performs exactly one full key comparison at the end. This makes them ideal for fixed-width binary keys, which is why they index IP routing tables — an IP lookup is a longest-prefix match over 32 or 128 bits, and the Linux kernel's routing table (`fib_trie`) is a PATRICIA variant.

**Adaptive Radix Trees (ART)** are the modern refinement: node size adapts to the number of children (4, 16, 48, or 256 slots), so sparse and dense regions each get an appropriate layout. ART is competitive with hash tables on lookups while preserving ordering, and is used in HyPer, DuckDB, and several key-value stores.

## 13.3 Suffix Trees

The structures so far index a *set of strings*. A suffix tree indexes **one string, by all of its suffixes** — which is what makes arbitrary substring search possible, because every substring is a prefix of some suffix.

The terminal `$` (a character not otherwise in the alphabet) guarantees no suffix is a prefix of another, so every suffix ends at a leaf:

```
Suffix tree for "banana$" — a compressed trie of all 7 suffixes.
Leaf labels are the starting positions of each suffix.

root
 ├── "$"                                  → 6
 ├── "a"
 │    ├── "$"                             → 5
 │    └── "na"
 │         ├── "$"                        → 3
 │         └── "na$"                      → 1
 └── "banana$"                            → 0
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

Ukkonen's 1995 algorithm builds the tree in **O(n)** for a constant alphabet — online, one character at a time. It is genuinely difficult to implement correctly; the suffix links and the "active point" bookkeeping are notorious.

That difficulty, plus the memory cost, is why suffix trees are less used than their power suggests. A suffix tree needs roughly 20 bytes per character in a practical implementation — indexing a 3-billion-character genome would take 60GB. The next section is the response to that.

## 13.4 Suffix Arrays

A suffix array is just the sorted list of suffix starting positions — the same information as a suffix tree's leaf order, in a flat integer array:

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

Kasai's algorithm computes the LCP array in O(n) once the suffix array is known. Together, the suffix array and LCP array carry all the information in a suffix tree — the LCP array encodes the tree's internal node structure implicitly, so any suffix-tree algorithm can be rewritten to use them.

**Construction** is a solved problem: **SA-IS** (Nong, Zhang, Chan, 2009) builds a suffix array in O(n) worst case, is straightforward compared to Ukkonen's algorithm, and is fast in practice. The simpler O(n log n) doubling approach — sort by first character, then by first 2, then 4, then 8 — is what most people implement in contests and is usually fast enough.

**Searching** with a plain suffix array is O(m log n): binary search, comparing up to m characters at each of log n steps. With the LCP array and a little extra bookkeeping this drops to O(m + log n).

Suffix arrays are the practical default. The [FM-index](../volume-4/ch24-research-grade-data-structures.md) goes one step further, compressing the suffix array to the text's own entropy while keeping it searchable — which is how BWA and Bowtie fit a human genome index in a few gigabytes.

## 13.5 Aho–Corasick: Searching for Many Patterns at Once

Everything so far searches for one pattern. The common real problem is the opposite: given ten thousand patterns — a spam word list, a malware signature set, a set of banned URLs — find every occurrence of any of them in one pass over the text.

Running a single-pattern search once per pattern is O(k·n) for k patterns. Aho–Corasick does it in **O(n + total pattern length + occurrences)**, independent of k.

The construction is a trie of all patterns, augmented with **failure links**. A failure link from a node points to the node representing the longest proper suffix of the current match that is also a prefix of some pattern — exactly the generalization of the KMP failure function to a set of patterns.

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

When a character doesn't match, follow the failure link instead of restarting — the automaton never re-reads a character of the text, which is where the linear bound comes from. This is the algorithm behind `grep -F`, most intrusion detection systems, and content filters.

## 13.6 Choosing a String Structure

| Need | Use | Why |
|------|-----|-----|
| Autocomplete, prefix queries | Trie or radix tree | O(P) prefix descent |
| Dictionary with tight memory | Radix tree, or succinct trie | Nodes proportional to strings, not characters |
| IP longest-prefix match | PATRICIA / ART | Bit-level tests, ordered |
| Substring search in one fixed text | Suffix array + LCP | Suffix-tree power at 4 bytes per character |
| Same, with minimal memory | FM-index | Compressed to text entropy, still searchable |
| Many patterns, one text | Aho–Corasick | O(n) regardless of pattern count |
| One pattern, one pass, no preprocessing of text | KMP or Boyer–Moore | O(n + m), no index to build |
| Exact set membership only, no prefix queries | Hash set | Simpler and faster when you don't need order |

The decisive question is **which side you preprocess**. Index the text (suffix array, FM-index) when the text is fixed and queries are many — a genome, a codebase, a document corpus. Index the pattern (KMP, Aho–Corasick) when the text streams past once and the patterns are fixed — a log pipeline, a packet filter.

## 13.7 Applications

**Autocomplete**: Trie prefix matching
**Spell checking**: Dictionary lookup
**IP routing**: Longest prefix match
**DNA sequencing**: Pattern matching
**Search engines**: Inverted indexes

In shipped systems: Elasticsearch and Lucene store their term dictionaries as finite-state transducers, a compressed-trie variant that shares suffixes as well as prefixes; the Linux kernel routes packets through `fib_trie`, a PATRICIA variant; BWA and Bowtie align sequencing reads against an FM-index of the reference genome; `grep -F` and Snort use Aho–Corasick; Redis implements its stream IDs and cluster key routing over radix trees; and DuckDB and HyPer index with ART.

## 13.8 Historical Context

Tries were described by Axel Thue in 1912 in a paper on repetition-free strings, long before computers existed to store them. René de la Briandais rediscovered them for file searching in 1959, and Edward Fredkin named them in 1960 — from *retrieval*, which is why the original pronunciation is "tree" and why nobody agrees about it.

Donald Morrison published PATRICIA in 1968 ("Practical Algorithm To Retrieve Information Coded In Alphanumeric"), one of the better backronyms in computing.

Peter Weiner gave the first linear-time suffix tree construction in 1973, in a paper Knuth reportedly called "the algorithm of the year." McCreight simplified it in 1976, and Ukkonen produced the online version in 1995 that most implementations follow.

Udi Manber and Gene Myers introduced suffix arrays in 1990 explicitly as the space-efficient answer to suffix trees, and were candid that they were trading a little query time for a large memory saving — a trade that looks better every year as datasets grow faster than RAM.

Alfred Aho and Margaret Corasick published their multi-pattern algorithm in 1975 while at Bell Labs, where it went straight into `fgrep`.

---

## Where this connects

- [Chapter 24: Research-Grade Data Structures](../volume-4/ch24-research-grade-data-structures.md) — the compressed, succinct versions of these indexes
- [Chapter 23: Advanced Competitive Programming Data Structures](../volume-4/ch23-advanced-competitive-programming-data-structures.md) — suffix automata and palindromic trees for contests
