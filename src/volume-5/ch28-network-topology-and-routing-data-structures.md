# Chapter 28: Network Topology and Routing Data Structures

## 28.1 Graph Representations for Networks

Network topology is fundamentally a graph problem. The choice of graph representation determines routing efficiency, memory usage, and update complexity.

### Adjacency Matrix vs Adjacency List

**Adjacency matrix** (O(V²) space):
```
  Router | A | B | C | D |
  -------|---|---|---|---|
     A   | 0 | 1 | 1 | 0 |
     B   | 1 | 0 | 0 | 1 |
     C   | 1 | 0 | 0 | 1 |
     D   | 0 | 1 | 1 | 0 |
```
- O(1) edge existence check
- O(V²) space even for sparse graphs
- Good for dense networks

**Adjacency list** (O(V + E) space):
```
A: B → 10, C → 5
B: A → 10, D → 3
C: A → 5, D → 7
D: B → 3, C → 7
```
- O(degree) neighbor enumeration
- Space proportional to actual edges
- Standard for network routing

### Compressed Representations for Large Networks

**CSR (Compressed Sparse Row)**: Store edges in three arrays:
- `offsets`: Starting position for each vertex's edges
- `edges`: Destination vertex IDs
- `weights`: Edge weights (optional)

**Routing tables** can use trie-like compression for hierarchical networks:
```
Hierarchical trie for routing:
           [root]
          /  |  \
        [A] [B] [C]
       /  \    /  \
    [A1][A2] [C1][C2]
```

## 28.2 Routing Table Structures

Routing tables map network prefixes to next hops. The data structure must support fast longest prefix match (LPM), the core operation of IP forwarding.

### Trie for Routing

Binary trie for IP addresses:
- Each level represents one bit
- 32 levels for IPv4, 128 for IPv6
- LPM: traverse bits until reaching longest matching prefix

**Memory explosion**: 2^32 possible leaves = 4 billion nodes. Solution: **compressed tries (Radix Tree / Patricia Tree)**.

### Radix Tree (Patricia Tree)

Collapse unary nodes (nodes with only one child) to reduce depth:

```
Standard trie path: 0→1→1→1→1
Radix tree: [01111] - single node representing this path

Example: 192.168.0.0/16, 192.168.1.0/24
  [192.168]   ← stores the /16 route
      |
    [.1]      ← stores the /24 route (the /16 contains it)
```

**BSD-derived kernels** use this structure (Sklower's radix tree) for their routing tables. Memory per prefix: O(L) where L is number of bits until first branching.

### LC-Trie (Level Compressed Trie)

**Idea**: Path-compress unary chains as a radix tree does, and replace each dense, nearly complete subtree of height k with a single node holding an array of 2^k children.

```
Level 0-7: Compressed into single node (2^8 children)
Level 8-15: Second level compression
...
```

Used in the **Linux kernel's IPv4 forwarding table** (`fib_trie`). Few levels means few memory accesses per lookup, with modest memory.

### Multi-bit Trie

Process multiple bits per step:
- 4-bit trie: Process 4 bits at a time (8 steps for IPv4 vs 32)
- 16-bit trie: Process 16 bits (2 steps for IPv4)

Trade-off: More memory (2^4 = 16 children per node) but faster lookup.

## 28.3 BGP Routing Data Structures

Border Gateway Protocol (BGP) routes between Autonomous Systems (AS). BGP routing tables are massive (~900K IPv4 prefixes as of 2024).

### BGPRIB (Routing Information Base)

BGP stores paths in a multi-attributed structure:
```
Prefix: 10.0.0.0/8
  └─ AS_PATH: [1239, 701, 80]
  └─ NEXT_HOP: 192.0.2.1
  └─ LOCAL_PREF: 100
  └─ MED: 50
  └─ ORIGIN: IGP
```

**Selection criteria** (in order):
1. Highest LOCAL_PREF
2. Shortest AS_PATH
3. Lowest ORIGIN (IGP < EGP < Incomplete)
4. Lowest MED
5. eBGP over iBGP
6. Lowest IGP metric to NEXT_HOP
7. Lowest router ID

### Path Vector Storage

AS_PATH is a sequence, not a set. Multiple paths to same destination create branching structures:

```
Per-prefix best-path selection (BGP is path-vector; it runs no Dijkstra):
- Adj-RIB-In: every path learned from each neighbor
- Decision process: compare candidate paths by the criteria above
- Loc-RIB: the winner for each prefix; only the winner is advertised (Adj-RIB-Out)
- On UPDATE or WITHDRAW: re-run selection for the affected prefix only
```

## 28.4 Software-Defined Networking (SDN) Tables

OpenFlow switch tables store flow entries with wildcard matching:

### TCAM (Ternary Content-Addressable Memory)

Hardware structure for wildcard matching:
- 0 = match bit exactly
- 1 = match bit exactly
- * = don't care (wildcard)

**Priority**: All entries are compared in parallel and the first matching entry in TCAM order wins, so entries are kept sorted by priority (for IP routing, by prefix length, so the longest match comes first).

```
Flow entry structure:
{
    match: {
        src_ip: 10.0.*.*,
        dst_ip: *.168.1.*,
        protocol: TCP,
        src_port: *,
        dst_port: 443
    },
    action: OUTPUT(port=3),
    priority: 100,
    stats: { packets: 1000, bytes: 50000 }
}
```

### Wildcard Compression

Multiple rules can be merged if they differ only on don't-care fields:
```
Rule 1: 10.0.0.0/8 with action A
Rule 2: 10.0.0.0/16 with action B
→ Cannot merge (Rule 2 is more specific)
```

## 28.5 Network Measurement Data Structures

### Count-Min Sketch

Estimate traffic flow frequencies:
```python
class CountMinSketch:
    def __init__(self, width, depth):
        self.width = width
        self.depth = depth
        self.table = [[0] * width for _ in range(depth)]
        self.hash_functions = [generate_hash() for _ in range(depth)]

    def add(self, item, count=1):
        for i, h in enumerate(self.hash_functions):
            self.table[i][h(item) % self.width] += count

    def estimate(self, item):
        return min(
            self.table[i][h(item) % self.width]
            for i, h in enumerate(self.hash_functions)
        )
```

**Accuracy**: With width w and depth d, error ≤ ε·N with probability 1-δ where w = e/ε, d = ln(1/δ).

### Heavy Hitter Detection

Identify flows exceeding threshold T:
```python
import heapq

class SpaceSaving:
    def __init__(self, k):
        self.k = k
        self.counters = {}  # flow_id -> count
        self.min_heap = []  # (count, flow_id); may hold stale entries

    def add(self, item):
        if item in self.counters:
            self.counters[item] += 1
            heapq.heappush(self.min_heap, (self.counters[item], item))
        elif len(self.counters) < self.k:
            self.counters[item] = 1
            heapq.heappush(self.min_heap, (1, item))
        else:
            # Evict the true minimum, skipping stale heap entries
            while True:
                min_count, evict_item = heapq.heappop(self.min_heap)
                if self.counters.get(evict_item) == min_count:
                    break
            del self.counters[evict_item]
            self.counters[item] = min_count + 1
            heapq.heappush(self.min_heap, (min_count + 1, item))

    def top_k(self):
        return sorted(self.counters.items(), key=lambda x: -x[1])[:self.k]
```

## 28.6 Gossip Protocol Data Structures

Gossip-based systems use epidemic algorithms for dissemination. Each node periodically exchanges state with random peers.

### Anti-entropy

Periodic comparison and reconciliation:
```python
def anti_entropy(node, peer):
    # Exchange digests (summary of owned data)
    local_digest = node.compute_digest()
    remote_digest = peer.compute_digest()

    # Find differences
    differences = compare_digests(local_digest, remote_digest)

    # Synchronize
    for key, version in differences:
        if local_version < remote_version:
            node.request(key, peer)
        elif local_version > remote_version:
            peer.request(key, node)
```

**Convergence time**: O(log N) rounds for O(N log N) messages total.

### Broadcast Trees

Gossip can be organized into spanning trees for efficiency:
```
Root node creates spanning tree across cluster
Messages flow down tree (log N depth)
Negative acknowledgments flow up for reliability
```

**Swim protocol** for failure detection: Incremental membership updates with suspicion mechanism.

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**28.1 ★ Build the CSR arrays.** Convert the weighted adjacency list from §28.1 (A: B→10, C→5; B: A→10, D→3; C: A→5, D→7; D: B→3, C→7) into CSR form, numbering A = 0, B = 1, C = 2, D = 3. Then estimate the memory for an AS-level graph with 75,000 nodes and 500,000 undirected links stored (a) as an adjacency matrix with one bit per cell and (b) in CSR with 4-byte integers and no weights.

<details>
<summary>Solution</summary>

Each vertex's edges are stored contiguously, and `offsets[v]` to `offsets[v+1]` is the slice belonging to v:

```
offsets = [0, 2, 4, 6, 8]
edges   = [1, 2, 0, 3, 0, 3, 1, 2]
weights = [10, 5, 10, 3, 5, 7, 3, 7]
```

The neighbors of C (vertex 2) are `edges[4:6] = [0, 3]`, that is A and D, with weights 5 and 7.

(a) Matrix: 75,000² = 5.625 × 10⁹ bits, about 703 MB, almost all zeros.

(b) CSR: an undirected link is stored once in each direction, so `edges` holds 1,000,000 entries × 4 B = 4 MB, plus `offsets` with 75,001 × 4 B ≈ 0.3 MB. About 4.3 MB in total, roughly 160 times smaller, and neighbor enumeration is a sequential scan of one contiguous slice.

</details>

**28.2 ★★ Longest prefix match on a binary trie.** A router has these routes: 0.0.0.0/0 → D, 10.0.0.0/8 → A, 10.1.0.0/16 → B, 10.1.2.0/24 → C. (a) Give the next hop for 10.1.2.3, 10.1.3.4, 10.2.0.1 and 11.0.0.1. (b) Implement `insert(prefix, next_hop)` and `lookup(addr)` on a one-bit-per-level trie. (c) How many trie nodes does the lookup for 10.1.3.4 visit below the root before it stops?

<details>
<summary>Hint</summary>

During lookup, remember the last next hop you passed. The answer is that remembered value when you run out of trie, not the value at the node where you stop.

</details>

<details>
<summary>Solution</summary>

(a) 10.1.2.3 → C (matches /24). 10.1.3.4 → B (the third octet 3 differs from 2, so the /24 does not match, but the /16 does). 10.2.0.1 → A. 11.0.0.1 → D (only the default route matches).

(b)

```python
import ipaddress

class TrieNode:
    def __init__(self):
        self.children = [None, None]
        self.next_hop = None  # set if a prefix ends here


class RoutingTrie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, prefix, next_hop):
        net = ipaddress.IPv4Network(prefix)
        value = int(net.network_address)
        node = self.root
        for i in range(net.prefixlen):
            bit = (value >> (31 - i)) & 1
            if node.children[bit] is None:
                node.children[bit] = TrieNode()
            node = node.children[bit]
        node.next_hop = next_hop

    def lookup(self, addr):
        value = int(ipaddress.IPv4Address(addr))
        node, best = self.root, self.root.next_hop
        for i in range(32):
            node = node.children[(value >> (31 - i)) & 1]
            if node is None:
                break
            if node.next_hop is not None:
                best = node.next_hop  # longest match so far
        return best


t = RoutingTrie()
t.insert("0.0.0.0/0", "D")
t.insert("10.0.0.0/8", "A")
t.insert("10.1.0.0/16", "B")
t.insert("10.1.2.0/24", "C")
assert t.lookup("10.1.2.3") == "C"
assert t.lookup("10.1.3.4") == "B"
assert t.lookup("10.2.0.1") == "A"
assert t.lookup("11.0.0.1") == "D"
```

(c) 10.1.3.4 and 10.1.2.0 agree on their first 23 bits (they differ in the last bit of the third octet). The lookup walks 23 nodes along the /24's path, picking up A at depth 8 and B at depth 16, then finds no child for bit 24 and returns B. That is 23 dependent memory reads for one packet, which is the reason routers do not use a plain binary trie.

</details>

**28.3 ★★ Prefix expansion in a multi-bit trie.** A 16-8-8 multi-bit trie indexes its first level by the top 16 bits of the address, then uses 8 bits at each of two lower levels. Routes: 10.0.0.0/12 → X, 10.4.0.0/14 → Y, 10.5.128.0/17 → Z. Show which first-level slots hold what, and what the second-level table under 10.5 contains. How many memory accesses do lookups for 10.6.1.1, 10.5.1.1 and 10.5.200.1 take, and what do they return?

<details>
<summary>Hint</summary>

A prefix shorter than a level boundary is expanded into every slot it covers. When two expanded prefixes land on the same slot, the longer original prefix wins.

</details>

<details>
<summary>Solution</summary>

The /12 fixes the first 12 bits: 10 and the top four bits of the second octet are 0000, so it covers second octets 0 to 15, which is 2^(16−12) = 16 first-level slots. The /14 fixes the top six bits of the second octet as 000001, covering 4 to 7, which is 4 slots. Being longer, Y overrides X on those four:

| first-level slot | contents |
|---|---|
| 10.0 to 10.3 | X |
| 10.4 | Y |
| 10.5 | pointer to a level-2 table |
| 10.6, 10.7 | Y |
| 10.8 to 10.15 | X |

The /17 does not end on the 16-bit boundary, so slot 10.5 becomes a pointer to a 256-entry table indexed by the third octet. The /17 fixes the top bit of the third octet as 1: entries 128 to 255 hold Z. Entries 0 to 127 must still hold Y, because the /14 covers them. This is called pushing the shorter prefix down.

Lookups: 10.6.1.1 reads slot 10.6 and returns Y in one access. 10.5.1.1 reads slot 10.5, follows the pointer, reads entry 1, returns Y: two accesses. 10.5.200.1 does the same and reads entry 200: Z, two accesses. The worst case is three accesses for any IPv4 address, at the cost of a 65,536-entry first level and duplicated entries wherever a short prefix is expanded.

</details>

**28.4 ★ Apply BGP best-path selection.** A router has four paths to 203.0.113.0/24. Using the selection order in §28.3, which one wins, and at which step is each loser eliminated?

| path | LOCAL_PREF | AS_PATH | ORIGIN | MED | learned via |
|---|---|---|---|---|---|
| P1 | 100 | 701 80 | IGP | 50 | eBGP |
| P2 | 100 | 701 80 | IGP | 10 | eBGP |
| P3 | 90 | 80 | IGP | 0 | eBGP |
| P4 | 100 | 3356 174 80 | IGP | 0 | eBGP |

<details>
<summary>Solution</summary>

Step 1, highest LOCAL_PREF: P3 has 90, the others 100. P3 is out, even though it has the shortest AS_PATH. Local policy beats path length; this is how an operator prefers a cheaper transit provider.

Step 2, shortest AS_PATH among P1, P2, P4: P1 and P2 have length 2, P4 has 3. P4 is out.

Step 3, lowest ORIGIN: P1 and P2 are both IGP. Tie.

Step 4, lowest MED: P2 has 10, P1 has 50. **P2 wins.**

One real-world detail: routers compare MED by default only between paths received from the same neighboring AS, because MED is a hint from that neighbor about which of its entry points it prefers. Here P1 and P2 both come from AS 701, so the comparison applies.

</details>

**28.5 ★★ Trace a Count-Min sketch.** Use width w = 4 and depth d = 2 with h1(x) = x mod 4 and h2(x) = ⌊x/4⌋ mod 4. Insert the flow IDs 1, 5, 2, 1, 9, 3, 1, 6 (count 1 each). Give the final table and the estimates for 1, 5, 9 and 7. Then size a sketch for ε = 0.001 and δ = 0.01 using the formulas in §28.5.

<details>
<summary>Solution</summary>

Bucket of each ID in (row 1, row 2): 1 → (1, 0), 5 → (1, 1), 2 → (2, 0), 9 → (1, 2), 3 → (3, 0), 6 → (2, 1).

Final table:

```
row 1: [0, 5, 2, 1]
row 2: [5, 2, 1, 0]
```

Row 1, bucket 1 received 1, 5, 1, 9, 1. Row 2, bucket 0 received 1, 2, 1, 3, 1.

| ID | row 1 | row 2 | estimate | true |
|---|---|---|---|---|
| 1 | 5 | 5 | 5 | 3 |
| 5 | 5 | 2 | 2 | 1 |
| 9 | 5 | 1 | 1 | 1 |
| 7 | 1 | 2 | 1 | 0 |

Every estimate is at least the true count, because a counter only ever receives additions from its own item and from colliding ones. The minimum picks the row with the fewest collisions: 9 is exact because row 2 isolates it, while 1 collides in both rows and is over by 2. Flow 7 was never seen but gets 1, so a Count-Min sketch can report traffic for a flow that does not exist; it cannot report zero for one that does.

Sizing: w = ⌈e/ε⌉ = ⌈2718.3⌉ = 2,719 and d = ⌈ln(1/δ)⌉ = ⌈4.61⌉ = 5. That is 13,595 counters, about 54 KB with 4-byte counters, for an error of at most 0.1% of total traffic with 99% probability, regardless of how many distinct flows there are.

</details>

**28.6 ★★★ Space-Saving: trace and guarantee.** (a) Trace the `SpaceSaving` class from §28.5 with k = 2 on the stream a, a, b, c, c, c, a, giving the counters after each item, and compare with the true counts. (b) The `add` method pushes a fresh heap entry on every increment and, when evicting, pops until it finds an entry whose count matches the current counter. What would go wrong without that check? (c) Prove that after N items, any item that occurred more than N/k times is in the summary.

<details>
<summary>Hint</summary>

For (c), show three facts: the counters always sum to N; a monitored item's counter never underestimates its true count; and an unmonitored item's true count never exceeds the current minimum counter.

</details>

<details>
<summary>Solution</summary>

(a)

| item | counters | note |
|---|---|---|
| a | {a: 1} | |
| a | {a: 2} | |
| b | {a: 2, b: 1} | summary now full |
| c | {a: 2, c: 2} | evict b (min 1), c gets 1 + 1 |
| c | {a: 2, c: 3} | |
| c | {a: 2, c: 4} | |
| a | {a: 3, c: 4} | |

True counts: a = 3, b = 1, c = 3. The counter for c is 1 too high: it inherited b's count when it took b's slot. The error of any counter is at most the minimum it replaced.

(b) The heap is not updated in place when a counter is incremented, so it holds old entries such as (1, a) after a's counter has become 2. Without the check, k = 1 on the stream a, a, b would pop (1, a) and give b the count 1 + 1 = 2, though the true minimum was 2 and b should get 3. Worse, a popped entry might name an item that was already evicted. The check `counters.get(evict_item) == min_count` discards such stale entries. It never discards the live entry, because an item's count only grows while it is monitored, and when it is evicted and later re-added its new count exceeds every count it had before (the minimum never decreases, as shown below), so an old entry can never match.

(c) Let m be the smallest counter.

1. The counters sum to N. Each `add` raises the total by exactly 1: an increment adds 1, a new item with a free slot adds 1, and an eviction removes m and inserts m + 1.
2. m never decreases. Counters only increase, and an eviction replaces the minimum with something larger.
3. A monitored item's counter is at least its true count, and an unmonitored item's true count f is at most m. By induction: when x is evicted, its counter equalled the minimum at that moment and was at least f, so f ≤ m then and, by fact 2, forever after until x reappears. When x reappears and evicts the minimum m, its new counter is m + 1 ≥ f + 1, which is its new true count.

With k counters summing to N, the minimum satisfies m ≤ N/k. If x occurred more than N/k times, then f > N/k ≥ m, so by fact 3 x cannot be unmonitored. The summary therefore contains every heavy hitter, using only k counters, though some items it contains may not be heavy (b's slot went to c with an inflated count). A second pass, or the bound count − m ≤ true count ≤ count, tells which candidates are real.

</details>

---

## Where this connects

- [Chapter 11: Graphs—Modeling Relationships](../volume-2/ch11-graphs-modeling-relationships.md). The graph fundamentals underneath routing
- [Chapter 13: String Data Structures](../volume-2/ch13-string-data-structures.md). The tries that routing tables actually are
