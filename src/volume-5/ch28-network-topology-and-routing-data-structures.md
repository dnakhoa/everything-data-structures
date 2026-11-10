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

### Longest-Prefix Match

A route is a prefix and a next hop: `10.20.0.0/16 → C` means "any address whose first 16 bits are those of 10.20.0.0 goes to neighbor C". Prefixes nest, so one address usually matches several routes, and the rule is that the most specific one (the longest prefix) wins. Take this table:

| prefix | next hop | role |
|---|---|---|
| 0.0.0.0/0 | A | default route: matches every address |
| 10.0.0.0/8 | B | a large block |
| 10.20.0.0/16 | C | one site inside it |
| 10.20.128.0/17 | D | the upper half of that site, routed differently |
| 10.20.200.0/24 | E | one subnet inside the /17 |
| 192.168.0.0/16 | F | an unrelated block |

| address | routes that match | longest | next hop |
|---|---|---|---|
| 10.20.200.7 | /0, /8, /16, /17, /24 | 10.20.200.0/24 | E |
| 10.20.201.7 | /0, /8, /16, /17 | 10.20.128.0/17 | D |
| 10.20.5.5 | /0, /8, /16 | 10.20.0.0/16 | C |
| 10.99.1.1 | /0, /8 | 10.0.0.0/8 | B |
| 192.168.1.1 | /0, 192.168.0.0/16 | 192.168.0.0/16 | F |
| 8.8.8.8 | /0 | 0.0.0.0/0 | A |

10.20.5.5 misses the /17 because its third octet, 5 = 00000101, has a 0 in the bit the /17 fixes to 1. "Longest" is what makes the table composable: the /8 can be announced once for a whole block while a more specific route carves out an exception, without either route knowing about the other. A first-match scan in the order listed would send every one of these addresses to the default route A.

A **binary trie** does LPM directly. A route of length *l* is stored at the node reached by following its first *l* bits from the root, so the root holds the /0 and a node at depth *d* holds the route (if any) whose prefix is the *d*-bit string on its path. A lookup follows the address bit by bit and remembers the last route it passed; when the path runs out, the remembered route is the longest match, because every route that matches the address lies on that path and deeper nodes are longer prefixes.

```python
import ipaddress
import random

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


def lpm_scan(routes, addr):
    """Reference answer: test every route and keep the longest that matches."""
    a = ipaddress.IPv4Address(addr)
    best, best_len = None, -1
    for prefix, hop in routes:
        net = ipaddress.IPv4Network(prefix)
        if a in net and net.prefixlen > best_len:
            best, best_len = hop, net.prefixlen
    return best


table = [("0.0.0.0/0", "A"), ("10.0.0.0/8", "B"), ("10.20.0.0/16", "C"),
         ("10.20.128.0/17", "D"), ("10.20.200.0/24", "E"), ("192.168.0.0/16", "F")]
t = RoutingTrie()
for prefix, hop in table:
    t.insert(prefix, hop)
for addr, want in [("10.20.200.7", "E"), ("10.20.201.7", "D"), ("10.20.5.5", "C"),
                   ("10.99.1.1", "B"), ("192.168.1.1", "F"), ("8.8.8.8", "A")]:
    assert t.lookup(addr) == lpm_scan(table, addr) == want


def random_route(rng):
    net = ipaddress.IPv4Network((rng.getrandbits(32), rng.randint(0, 32)), strict=False)
    return str(net)

rng = random.Random(28)
for _ in range(200):
    routes = list({random_route(rng): hop for hop in range(rng.randint(1, 60))}.items())
    trie = RoutingTrie()
    for prefix, hop in routes:
        trie.insert(prefix, hop)
    for _ in range(100):
        if rng.random() < 0.5:  # uniform addresses rarely hit long prefixes,
            addr = ipaddress.IPv4Address(rng.getrandbits(32))
        else:                   # so half are drawn from inside a route
            net = ipaddress.IPv4Network(rng.choice(routes)[0])
            addr = net.network_address + rng.randrange(net.num_addresses)
        assert trie.lookup(str(addr)) == lpm_scan(routes, str(addr))
```

Trace 10.20.201.7: the root gives A, depth 8 gives B, depth 16 gives C and depth 17 gives D. The walk then continues down the path the /24 created, because 201 = 11001001 and 200 = 11001000 agree on their first seven bits, and at depth 23 there is no child for the final 1. Twenty-three nodes visited below the root, answer D.

**Cost.** Insert and lookup take O(W) time in the worst case, W = 32 for IPv4 and 128 for IPv6, independent of the number of routes N. The trie does not allocate the 2^32 possible addresses: it holds at most 1 + N·W nodes, and the six routes above take 41. Memory is not the problem; speed is. Each step is a dependent memory read, likely a cache miss, and a 100 Gb/s port receiving minimum-size Ethernet frames (64 bytes plus 20 bytes of preamble and inter-frame gap) delivers about 148.8 million packets per second, 6.7 ns per packet. Thirty-two pointer chases do not fit in that. The structures below exist to cut the number of reads: path compression removes nodes that do not branch, and multibit tries (§28.3) read several bits per step.

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

**BSD-derived kernels** use this structure (Sklower's radix tree) for their routing tables. Every node either holds a prefix or branches, so N prefixes need fewer than 2N nodes, against up to N·W for the plain binary trie. The depth can still reach W, so path compression helps memory more than worst-case lookup time.

### LC-Trie (Level Compressed Trie)

**Idea**: Path-compress unary chains as a radix tree does, and replace each dense, nearly complete subtree of height k with a single node holding an array of 2^k children.

```
Level 0-7: Compressed into single node (2^8 children)
Level 8-15: Second level compression
...
```

Used in the **Linux kernel's IPv4 forwarding table** (`fib_trie`). Few levels means few memory accesses per lookup, with modest memory.

## 28.3 Multibit Tries and Router Lookups

A binary trie spends one memory read per address bit. A **multibit trie** reads *s* bits at a time, the **stride**: each node is an array of 2^s slots indexed directly by the next *s* bits, so an IPv4 lookup with strides 8-8-8-8 takes at most four reads, and with 16-8-8 at most three. Each slot can hold a next hop and a pointer to a child node.

### Controlled Prefix Expansion

The difficulty is prefixes whose length does not fall on a level boundary. With stride 8, the trie can only store prefixes of length 8, 16, 24 and 32 directly; a /17 ends one bit into the third level. **Controlled prefix expansion** (Srinivasan and Varghese, 1999) rewrites each prefix as the set of longer prefixes, of the next allowed length, that together cover exactly the same addresses. A prefix of length *l* that ends inside a level covering bits up to *b* becomes 2^(b−l) slots in that level's node. Two rules make it correct:

- **Expansion.** 10.20.128.0/17 fixes the top bit of the third octet to 1, so in the level-3 node under 10.20 it fills the 2^(24−17) = 128 slots 128 to 255.
- **Capture.** When expansions of two different prefixes land on the same slot, the longer original prefix wins. 10.20.200.0/24 lands exactly on slot 200, which the /17 also covers, and since 24 > 17 the slot holds E. The slot therefore stores the original length beside the next hop, which also makes the result independent of insertion order.

<figure>
{{#include ../images/multibit-trie.svg}}
<figcaption>The same six prefixes in a binary trie and in a stride-2 trie: expansion copies short prefixes into several slots, and the lookup for 1011 drops from a read per bit to a read per level.</figcaption>
</figure>

The figure shows both rules on a toy table of bit strings with 4-bit addresses. For the six-route table of §28.2 with strides 8-8-8-8, the /0 expands into all 256 slots of the root, the /8 sits in root slot 10, the two /16s are aligned and sit in one level-2 slot each (20 under 10, 168 under 192), and the level-3 node under 10.20 holds D in slots 128 to 255 except slot 200, which holds E. Looking up 10.20.201.7 reads root slot 10 (B, follow the child), level-2 slot 20 (C, follow the child) and level-3 slot 201 (D, no child): three reads, against 23 nodes in the binary trie. The price is memory: four nodes of 256 slots, 1,024 slots for six routes, where the binary trie needed 41 nodes of two pointers.

```python
class MultibitTrie:
    """Fixed-stride trie with controlled prefix expansion.

    A node is a list of 2**stride slots; a slot is [next_hop, length, child],
    where length is the original prefix length that set next_hop.
    """

    def __init__(self, strides=(8, 8, 8, 8)):
        assert sum(strides) == 32
        self.strides = strides
        self.root = self._node(0)

    def _node(self, level):
        return [[None, -1, None] for _ in range(1 << self.strides[level])]

    def insert(self, prefix, next_hop):
        net = ipaddress.IPv4Network(prefix)
        value, plen = int(net.network_address), net.prefixlen
        node, start = self.root, 0
        for level, stride in enumerate(self.strides):
            end = start + stride
            index = (value >> (32 - end)) & ((1 << stride) - 1)
            if plen <= end:  # the prefix ends inside this level: expand it
                first = index >> (end - plen) << (end - plen)
                for slot in node[first:first + (1 << (end - plen))]:
                    if slot[1] <= plen:  # capture: the longer original prefix wins
                        slot[0], slot[1] = next_hop, plen
                return
            if node[index][2] is None:
                node[index][2] = self._node(level + 1)
            node, start = node[index][2], end

    def lookup(self, addr):
        value = int(ipaddress.IPv4Address(addr))
        node, start, best = self.root, 0, None
        for stride in self.strides:  # one memory read per level
            start += stride
            hop, _, child = node[(value >> (32 - start)) & ((1 << stride) - 1)]
            if hop is not None:
                best = hop
            if child is None:
                break
            node = child
        return best


m = MultibitTrie((8, 8, 8, 8))
for prefix, hop in table:
    m.insert(prefix, hop)
level3 = m.root[10][2][20][2]  # the node under 10.20
assert [level3[i][:2] for i in (127, 128, 200, 201)] == \
    [[None, -1], ["D", 17], ["E", 24], ["D", 17]]

for strides in [(8, 8, 8, 8), (16, 8, 8), (4,) * 8, (1,) * 32]:
    for _ in range(30):
        routes = list({random_route(rng): hop for hop in range(rng.randint(1, 50))}.items())
        rng.shuffle(routes)  # insertion order must not matter
        mt = MultibitTrie(strides)
        for prefix, hop in routes:
            mt.insert(prefix, hop)
        for _ in range(50):
            net = ipaddress.IPv4Network(rng.choice(routes)[0])
            addr = str(net.network_address + rng.randrange(net.num_addresses))
            assert mt.lookup(addr) == lpm_scan(routes, addr)
```

Like the binary trie, the lookup remembers the best next hop seen on the way down, so an empty slot (slot 5 of the level-3 node for 10.20.5.5) falls back to C from level 2.

**Cost.** A lookup takes at most k reads for k levels, worst case. Inserting a prefix walks at most k levels and writes up to 2^s slots of one node, so a short prefix in a wide level is expensive: the /0 above writes 256 slots, and in a 16-8-8 trie it would write 65,536. Deletion is harder than insertion, because the slots a deleted prefix captured must revert to the next-longest prefix covering them, and the trie does not record what that was. Implementations keep the original prefixes in a separate table to answer that question.

### Choosing the Strides

Bigger strides mean fewer levels and more memory, but how much more depends on the table. A node starting at bit *s* exists for each distinct *s*-bit string that begins some route longer than *s*, so the number of nodes at each possible start position can be counted once from the routes, and the slots of any stride choice are the sum of nodes × 2^stride over its levels. Srinivasan and Varghese observed that the cheapest strides for a given number of levels then follow from a dynamic program over the start positions, O(k·W²) time for k levels:

```python
from functools import lru_cache

def level_nodes(routes):
    """nodes[s]: trie nodes starting at bit s, one per distinct s-bit string
    that begins a route longer than s; nodes[0] = 1, the root."""
    keys = [(int(n.network_address), n.prefixlen)
            for n in (ipaddress.IPv4Network(p) for p, _ in routes)]
    return [1] + [len({v >> (32 - s) for v, plen in keys if plen > s})
                  for s in range(1, 32)]

def expansion_cost(nodes, strides):
    """Slots a fixed-stride trie allocates: sum of nodes[start] * 2**stride."""
    total, start = 0, 0
    for stride in strides:
        total += nodes[start] << stride
        start += stride
    return total

def best_strides(nodes, levels):
    """Cheapest (slots, strides) using at most `levels` levels."""
    @lru_cache(maxsize=None)
    def cost(start, left):
        if start == 32:
            return 0, ()
        if left == 0:
            return float("inf"), ()
        return min((c + (nodes[start] << (end - start)), (end - start,) + rest)
                   for end in range(start + 1, 33)
                   for c, rest in [cost(end, left - 1)])
    return cost(0, levels)

assert expansion_cost(level_nodes(table), (8, 8, 8, 8)) == 1024  # the four nodes above


def synthetic_table(seed=2024, n=50_000):
    """BGP-like length mix (60% /24s), clustered in 3,000 random /16 blocks."""
    r = random.Random(seed)
    mix = {8: 0.1, 12: 0.2, 14: 0.4, 15: 0.4, 16: 2.5, 17: 1, 18: 1.5, 19: 3,
           20: 4, 21: 5, 22: 11, 23: 9, 24: 60, 25: 0.4, 26: 0.4, 27: 0.3,
           28: 0.3, 29: 0.3, 30: 0.2, 32: 0.1}
    blocks = [r.randrange(1 << 8, 224 << 8) for _ in range(3000)]
    routes = {}
    while len(routes) < n:
        plen = r.choices(list(mix), list(mix.values()))[0]
        value = (r.choice(blocks) << 16) | r.getrandbits(16)
        routes[str(ipaddress.IPv4Network((value, plen), strict=False))] = len(routes)
    return list(routes.items())

nodes = level_nodes(synthetic_table())
for strides in [(1,) * 32, (4,) * 8, (8, 8, 8, 8), (16, 8, 8), (24, 8), (16, 16)]:
    print(strides, expansion_cost(nodes, strides))
print(best_strides(nodes, 3), best_strides(nodes, 4))
```

On this synthetic 50,000-route table (real tables differ, but the shape of the trade-off is typical):

| strides | worst-case reads | slots |
|---|---|---|
| 1 × 32 (binary trie) | 32 | 366,042 |
| 4 × 8 | 8 | 562,832 |
| 8-8-8-8 | 4 | 1,076,736 |
| 16-8-8 | 3 | 1,084,928 |
| 24-8 | 2 | 17,048,320 |
| 16-16 | 2 | 191,627,264 |

The binary trie is the smallest and the slowest. Going from 32 reads to 4 costs about three times the memory, and going from 4 to 3 costs almost nothing here, because the 65,536-slot root of 16-8-8 replaces the first two levels of 8-8-8-8, which already used 224 nodes and 57,344 slots. Going to 2 levels costs another factor of 16, and the wrong two levels are worse again: 16-16 needs 11 times the memory of 24-8, because it allocates a 65,536-slot node for each of the 2,923 /16 blocks that contain a longer route. The program confirms that 16-8-8 is the cheapest three-level choice and finds 16-6-3-7 (627,928 slots) for four levels. Letting each subtree pick its own strides, which the same paper also optimizes by dynamic programming, does better still.

### DIR-24-8: Usually One Read

Gupta, Lin and McKeown (INFOCOM 1998) took the 24-8 row of that table seriously. Their observation was that on a backbone table of the time (MAE-EAST, January 1998), 99.93% of prefixes were 24 bits or shorter, and that 2^24 entries of DRAM was cheap. Their DIR-24-8-BASIC scheme is a two-level multibit trie with strides 24 and 8, laid out as two flat arrays:

- **TBL24** has 2^24 entries of 2 bytes, 32 MB, indexed by the top 24 bits of the address. An entry whose first bit is 0 holds a next hop in its other 15 bits. An entry whose first bit is 1 holds a 15-bit index into the second table.
- **TBLlong** is made of 256-entry blocks of 1-byte next hops, one block for each /24 that contains a route longer than /24, indexed by the last 8 bits of the address.

A lookup reads TBL24; only if the flag is set does it make a second read. Instead of remembering the best match on the way down, the scheme pushes it down: when a /24's block is allocated, all 256 entries are first filled with whatever the /24 entry held, so each entry is a complete answer by itself. The paper's example uses 10.54.0.0/16, 10.54.34.0/24 and 10.54.34.192/26:

```python
from array import array

EXT = 1 << 31  # flag bit: the low bits index a tbl8 group, not a next hop

def build_dir_24_8(routes):
    """Static build. routes: (prefix, hop), hop an int >= 1; 0 means no route."""
    tbl24 = array("I", [0]) * (1 << 24)
    tbl8 = array("I")
    nets = sorted(((ipaddress.IPv4Network(p), h) for p, h in routes),
                  key=lambda r: r[0].prefixlen)  # shorter first; longer overwrite
    for net, hop in nets:
        lo, n = int(net.network_address), net.num_addresses
        if net.prefixlen <= 24:
            tbl24[lo >> 8:(lo + n) >> 8] = array("I", [hop]) * (n >> 8)
            continue
        entry = tbl24[lo >> 8]
        if not entry & EXT:  # first long route under this /24: allocate a group
            group = len(tbl8) >> 8
            tbl8.extend(array("I", [entry]) * 256)  # push the /24's answer down
            entry = tbl24[lo >> 8] = EXT | group
        base = ((entry & ~EXT) << 8) | (lo & 0xFF)
        tbl8[base:base + n] = array("I", [hop]) * n
    return tbl24, tbl8

def lookup_dir_24_8(tbl24, tbl8, addr):
    a = int(ipaddress.IPv4Address(addr))
    entry = tbl24[a >> 8]                                  # read 1
    if entry & EXT:
        entry = tbl8[((entry & ~EXT) << 8) | (a & 0xFF)]   # read 2, rarely
    return entry

tbl24, tbl8 = build_dir_24_8([("10.54.0.0/16", 1), ("10.54.34.0/24", 2),
                              ("10.54.34.192/26", 3)])
assert lookup_dir_24_8(tbl24, tbl8, "10.54.22.147") == 1   # one read
assert lookup_dir_24_8(tbl24, tbl8, "10.54.34.14") == 2    # two reads
assert lookup_dir_24_8(tbl24, tbl8, "10.54.34.194") == 3   # two reads
assert len(tbl8) == 256  # one group, for 10.54.34
```

The /16 fills the 256 TBL24 entries 10.54.0 to 10.54.255. The /24 overwrites entry 10.54.34, and the /26 then turns that entry into a pointer to group 0, whose entries 0 to 191 hold the /24's next hop and 192 to 255 the /26's. (The code uses 32-bit entries with the flag in the top bit, as DPDK does, rather than the paper's 16.)

Lookup is at most two reads, worst case, and one read for any address whose /24 has no longer route, which is nearly all of them: most networks do not accept routes longer than /24 from the global table. Because the reads are to fixed locations with no pointer chasing beyond the second, a hardware pipeline can complete one lookup per memory access; the paper estimated 20 million lookups per second with the 50 ns DRAM of the day. The costs are on the other side. TBL24 is 32 MB however small the table is. The 15-bit pointer limits TBLlong to 32,768 blocks; the paper suggested 1 MB of it, 4,096 blocks. And updates are slow: adding a /8 rewrites 65,536 TBL24 entries, a default route all 16.7 million, and a later insertion must not overwrite entries that a longer prefix already set. Exercise 28.7 works through what that requires.

**In production.** DPDK's `rte_lpm` library, used by software routers built on it, is DIR-24-8: a `tbl24` of 2^24 four-byte entries (64 MB) and 256-entry `tbl8` groups whose number is fixed when the table is created. Each entry packs a 24-bit next hop (or group index), a valid bit, a `valid_group` bit that marks an extended entry, and a 6-bit `depth`, the length of the prefix that wrote it; the depth is what lets insertion and deletion run incrementally. **Poptrie** (Asai and Ohara, SIGCOMM 2015) goes the other way and makes the table small enough to stay in CPU cache: a directly indexed first level of 16 or 18 bits, then 64-way nodes (stride 6) that store only their non-empty children contiguously, with a 64-bit bitmap per node; the index of a child is the population count (`popcnt`) of the bitmap bits below it. Both trade update cost for a lookup with few, predictable reads, which is the right trade for a forwarding table that sees millions of lookups per update.

## 28.4 ECMP and Maglev Hashing

The lookup of §28.3 often returns not one next hop but a group of them. In a data-center fabric built as a Clos network, a leaf switch has the same route to every remote rack through each of its spine switches, all at equal cost. **Equal-cost multipath** (ECMP) forwarding spreads traffic across the group, and the data structure question becomes: which packet goes to which member?

### Per-Flow Hashing

Sending successive packets to successive members (per-packet spraying) balances perfectly and breaks TCP. The paths have different queueing delays, so the packets of one connection arrive out of order; the receiver acknowledges each out-of-order segment with a duplicate ACK, and the sender treats three duplicate ACKs as a loss, retransmits and halves its congestion window. So routers hash per flow: the flow's 5-tuple (source and destination address, source and destination port, protocol) is hashed, and every packet of the flow takes member `group[hash(5-tuple) mod k]`. One flow stays on one path, in order. Balance is then over flows, not bytes: two large flows that hash to the same member share it while another member idles.

### The Remapping Problem

`hash mod k` fails badly when the group changes. If one of k next hops fails, the flows on it must move, 1/k of all flows. But the survivors are renumbered and every flow is now taken mod k − 1, and a flow stays put only if its member under mod k is the same as under mod k − 1. Exactly 1/k of flows stay, whichever member failed (Exercise 28.9), so (k − 1)/k of flows move: 75% with 4 next hops, 99% with 100. For a router the cost is a burst of reordering. For a load balancer that spreads connections over servers by the same hashing, it is worse: a connection moved to a server without its TCP state is reset.

The fix is a level of indirection: a table of M buckets, M much larger than k, filled with members, and each flow goes to `table[hash mod M]`. When a member fails, only its buckets are reassigned. Many switches and Linux's resilient next-hop groups work this way. The ring of consistent hashing ([§27.3](ch27-distributed-data-structures.md)) is the same idea with buckets placed by hashing: it guarantees that only the failed member's keys move, but the arcs are uneven. For 100 backends with *v* points each on the ring, measured below, the most-loaded backend owns 5.67 times its fair share of the ring with *v* = 1, 2.09 times with *v* = 10 and 1.21 times with *v* = 100. Every backend must be provisioned for the most-loaded one.

### Maglev Hashing

Maglev is Google's software network load balancer (Eisenbud et al., NSDI 2016). Its hashing builds the bucket table to be balanced first and stable second. Each backend *i* gets a preference list over the M table positions, a permutation built from two hashes of its name:

```
offset = h1(name) mod M
skip   = h2(name) mod (M − 1) + 1
permutation[i][j] = (offset + j × skip) mod M
```

M is prime, so every skip in 1..M−1 is coprime to M and the list visits every position exactly once. The backends then take turns: each in round-robin order claims the first position on its list that is still empty, until the table is full. A lookup is one hash and one array read.

**Worked example.** This is the paper's own: M = 7 and three backends with (offset, skip) = (3, 4), (0, 2) and (3, 1).

| backend | preference list |
|---|---|
| B1 | 3, 0, 4, 1, 5, 2, 6 |
| B2 | 0, 2, 4, 6, 1, 3, 5 |
| B3 | 3, 4, 5, 6, 0, 1, 2 |

Round 1: B1 takes 3, B2 takes 0, B3 finds 3 taken and takes 4. Round 2: B1 skips 0 and 4 and takes 1, B2 takes 2, B3 takes 5. Round 3: B1 skips 5 and 2 and takes 6, and the table is full: `[B2, B1, B2, B1, B3, B3, B1]`, three entries for B1 and two for each of the others. Remove B2 and rebuild: B1 takes 3, 0, 1 and 2, B3 takes 4, 5 and 6, giving `[B1, B1, B1, B1, B3, B3, B3]`. Positions 0 and 2 had to change because B2 owned them. Position 6 changed too: without B2 taking turns, B3 reached 6 on its list before B1 did. That is the one extra disruption.

```python
import hashlib
from collections import Counter

def h64(text):
    return int.from_bytes(hashlib.blake2b(text.encode(), digest_size=8).digest(), "big")

def populate(prefs, M):
    """Maglev's table fill. prefs[i] = (offset, skip) for backend i; M prime."""
    nxt = [0] * len(prefs)  # next index into each backend's preference list
    entry = [-1] * M
    filled = 0
    while True:
        for i, (offset, skip) in enumerate(prefs):
            c = (offset + nxt[i] * skip) % M
            while entry[c] >= 0:  # walk i's preference list to a free slot
                nxt[i] += 1
                c = (offset + nxt[i] * skip) % M
            entry[c] = i
            nxt[i] += 1
            filled += 1
            if filled == M:
                return entry

def maglev_table(backends, M=65537):
    prefs = [(h64("offset:" + b) % M, h64("skip:" + b) % (M - 1) + 1) for b in backends]
    return [backends[i] for i in populate(prefs, M)]

assert populate([(3, 4), (0, 2), (3, 1)], 7) == [1, 0, 1, 0, 2, 2, 0]  # B2 B1 B2 B1 B3 B3 B1
assert populate([(3, 4), (3, 1)], 7) == [0, 0, 0, 0, 1, 1, 1]          # B1 x4, B3 x3

backends = [f"backend-{i}" for i in range(100)]
for M in (65537, 655373):
    before = maglev_table(backends, M)
    after = maglev_table([b for b in backends if b != "backend-37"], M)
    counts = Counter(before)
    forced = counts["backend-37"]
    moved = sum(x != y for x, y in zip(before, after))
    print(M, min(counts.values()), max(counts.values()), forced, moved)

def ring_shares(backends, vnodes):
    """Chapter 27's ring: each point owns the arc back to the previous point."""
    points = sorted((h64(f"{b}#{j}"), b) for b in backends for j in range(vnodes))
    share = Counter()
    for k, (p, b) in enumerate(points):
        share[b] += (p - points[k - 1][0]) % (1 << 64)
    return share

for v in (1, 10, 100):
    print(v, max(ring_shares(backends, v).values()) / ((1 << 64) / len(backends)))
```

The hashes are deterministic, so the output is reproducible:

| table size M | entries per backend | entries of backend-37 | entries changed on removing it | extra |
|---|---|---|---|---|
| 65,537 | 655 or 656 | 655 | 1,009 | 354 (0.54% of the table) |
| 655,373 | 6,553 or 6,554 | 6,554 | 7,572 | 1,018 (0.16%) |

**Balance.** Because the backends take strict turns and the fill stops when the table is full, every backend owns ⌊M/N⌋ or ⌈M/N⌉ entries, a guarantee rather than an expectation; the paper picks M > 100·N so that this rounding is under 1% of a backend's share. Against the ring's 1.21 with 100 points per backend, Maglev's most-loaded backend here carries 1.001 times its fair share.

**Disruption.** It is not minimal. Removing one backend of 100 reassigns its 655 entries plus 354 others, so about 1.5% of flows move where 1% must. The extras come from the turn order shifting, as in the worked example, and they shrink as a fraction of the table when M grows, which matches the paper's measurements. Maglev accepts this trade deliberately: over-provisioning every backend for an imbalanced hash costs capacity all the time, while extra moves happen only when backends change, and Maglev also keeps a per-machine connection-tracking table so that packets of an established connection keep going to their backend. The paper reports that, with 1,000 backends and a 65,537-entry table, Karger's ring and rendezvous hashing would have needed backends over-provisioned by 29.7% and 49.5% to absorb their imbalance.

**Cost.** Lookup is O(1). Building the table takes O(M log M) expected time: when n of M positions are full, a backend expects M/(M − n) tries to find an empty one, and the sum of those terms is M·H_M. The worst case is O(M²), when the backends have nearly identical preference lists and N approaches M, which choosing M ≫ N avoids. The paper reports 1.8 ms to build a 65,537-entry table and 22.9 ms for 655,373, which is why the default is the smaller one.

## 28.5 BGP Routing Data Structures

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

## 28.6 Software-Defined Networking (SDN) Tables

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

## 28.7 Network Measurement Data Structures

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

## 28.8 Gossip Protocol Data Structures

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

**28.2 ★★ Longest prefix match on a binary trie.** A router has these routes: 0.0.0.0/0 → D, 10.0.0.0/8 → A, 10.1.0.0/16 → B, 10.1.2.0/24 → C. (a) Give the next hop for 10.1.2.3, 10.1.3.4, 10.2.0.1 and 11.0.0.1. (b) Add a `delete(prefix)` method to the `RoutingTrie` of §28.2 that removes a route and frees the nodes that no longer lead to any route. After deleting 10.1.2.0/24, what does 10.1.2.3 return, and how many nodes are left below the root? (c) How many trie nodes does the lookup for 10.1.3.4 visit below the root before it stops?

<details>
<summary>Hint</summary>

During lookup, remember the last next hop you passed. The answer is that remembered value when you run out of trie, not the value at the node where you stop.

</details>

<details>
<summary>Solution</summary>

(a) 10.1.2.3 → C (matches /24). 10.1.3.4 → B (the third octet 3 differs from 2, so the /24 does not match, but the /16 does). 10.2.0.1 → A. 11.0.0.1 → D (only the default route matches).

(b) Record the path on the way down, clear the route, then walk back up unlinking every node that now holds no route and has no children. Stop at the first node that still holds a route or still has a child: everything above it is needed.

```python
def delete(self, prefix):
    net = ipaddress.IPv4Network(prefix)
    value = int(net.network_address)
    path = [self.root]
    for i in range(net.prefixlen):
        child = path[-1].children[(value >> (31 - i)) & 1]
        if child is None:
            return False  # no such route
        path.append(child)
    if path[-1].next_hop is None:
        return False
    path[-1].next_hop = None
    for i in range(net.prefixlen - 1, -1, -1):  # path[i + 1] hangs off path[i]
        node = path[i + 1]
        if node.next_hop is not None or node.children != [None, None]:
            break
        path[i].children[(value >> (31 - i)) & 1] = None
    return True

RoutingTrie.delete = delete

t = RoutingTrie()
for prefix, hop in [("0.0.0.0/0", "D"), ("10.0.0.0/8", "A"),
                    ("10.1.0.0/16", "B"), ("10.1.2.0/24", "C")]:
    t.insert(prefix, hop)
assert t.delete("10.1.2.0/24") and not t.delete("10.1.2.0/24")
assert t.lookup("10.1.2.3") == "B"
```

10.1.2.3 now falls back to the /16, B. Before the delete there were 24 nodes below the root, one per bit of the longest route. The /24's nodes at depths 17 to 24 lead to no other route, so all eight are unlinked, and the walk stops at depth 16 because that node holds B. Sixteen nodes remain. Deletion is O(W) in the worst case, like insertion. Nothing has to be rewritten to make the fallback work, because the shorter routes are still on the path; the expanded tables of §28.3 lose exactly that property.

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

**28.4 ★ Apply BGP best-path selection.** A router has four paths to 203.0.113.0/24. Using the selection order in §28.5, which one wins, and at which step is each loser eliminated?

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

**28.5 ★★ Trace a Count-Min sketch.** Use width w = 4 and depth d = 2 with h1(x) = x mod 4 and h2(x) = ⌊x/4⌋ mod 4. Insert the flow IDs 1, 5, 2, 1, 9, 3, 1, 6 (count 1 each). Give the final table and the estimates for 1, 5, 9 and 7. Then size a sketch for ε = 0.001 and δ = 0.01 using the formulas in §28.7.

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

**28.6 ★★★ Space-Saving: trace and guarantee.** (a) Trace the `SpaceSaving` class from §28.7 with k = 2 on the stream a, a, b, c, c, c, a, giving the counters after each item, and compare with the true counts. (b) The `add` method pushes a fresh heap entry on every increment and, when evicting, pops until it finds an entry whose count matches the current counter. What would go wrong without that check? (c) Prove that after N items, any item that occurred more than N/k times is in the summary.

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

**28.7 ★★ Updating a DIR-24-8 table.** Start from the table built in §28.3: 10.54.0.0/16 → 1, 10.54.34.0/24 → 2, 10.54.34.192/26 → 3. (a) The route 10.0.0.0/8 → 4 arrives. Which TBL24 entries must it write, which must it leave alone, and why can't `build_dir_24_8`'s rule (sort by length, later writes overwrite) be applied to a single insertion? (b) Then 10.54.34.0/24 is withdrawn. What must group 0's entries hold afterwards, and what information do the two tables lack to work that out? (c) Show how storing in every entry the length of the prefix that wrote it (its depth, as DPDK does) makes both updates local.

<details>
<summary>Solution</summary>

(a) The /8 covers TBL24 entries 10.0.0 to 10.255.255, 2^16 = 65,536 of them. The 256 entries 10.54.0 to 10.54.255 were written by longer prefixes (the /16, and at 10.54.34 the /24 and then the /26's group pointer), so they must keep their values; the /8 writes the other 65,280. The static build gets this right only because it processes every shorter prefix before any longer one. A single insertion arrives after the longer routes are in place, and an entry holding 1 looks the same whether a /16 or an /8 wrote it, so a blind write of the range would erase the /16.

(b) Entries 0 to 191 held 2, the /24's answer pushed down when the group was created. They must now hold 1, from 10.54.0.0/16, the longest remaining route covering them. Entries 192 to 255 keep 3, and TBL24 entry 10.54.34 stays a pointer because the /26 still needs the group. The tables store only next hops: nothing in them says that 2 came from a /24, or that a /16 covers it. The router has to find the replacement in a separate list of the routes themselves, which is why DPDK keeps one beside the tables.

(c) Give each entry a (next hop, depth) pair. To insert a prefix of length d, write each entry in its range only if the entry is empty or its depth is at most d; when the entry is a group pointer, apply the same test to the group's 256 entries. In (a), the 10.54.x entries have depth 16 or are pointers into a group whose entries have depth 24 and 26, so the /8 (depth 8) skips them all. To delete a prefix P of length d, look up its replacement R, the longest remaining route that covers P, and rewrite only the entries in P's range whose depth equals d, with R's next hop and depth (or empty if there is no R). Entries with greater depth belong to longer routes and are left alone. In (b), the 192 entries with depth 24 become (1, 16) and the 64 with depth 26 are untouched. When every entry of a group ends up with depth 24 or less and the same next hop, the group can be folded back into its TBL24 entry and freed; DPDK's delete does this check.

</details>

**28.8 ★★ Maglev by hand.** Add a fourth backend B4 with (offset, skip) = (5, 3) to the worked example of §28.4 (M = 7). (a) Write B4's preference list and build the table. (b) How many entries differ from the three-backend table `[B2, B1, B2, B1, B3, B3, B1]`, and what is the fewest any scheme could change while keeping every backend within one entry of the others? (c) Why must M be prime? Show what goes wrong with M = 8 and a backend whose skip is 2.

<details>
<summary>Solution</summary>

(a) B4's list is (5 + 3j) mod 7 for j = 0 to 6: 5, 1, 4, 0, 3, 6, 2. Round 1: B1 takes 3, B2 takes 0, B3 finds 3 taken and takes 4, B4 takes 5. Round 2: B1 skips 0 and 4 and takes 1, B2 takes 2, B3 skips 5 and takes 6. That is 7 entries, so the fill stops before B4's second turn: `[B2, B1, B2, B1, B3, B4, B3]`, with 2, 2, 2 and 1 entries.

(b) Two entries changed: position 5 (B3 to B4) and position 6 (B1 to B3). The minimum is one: B4 must get at least ⌊7/4⌋ = 1 entry, and taking one of B1's three gives the balanced 2, 2, 2, 1 with a single change. Maglev spent an extra change because B4 claimed position 5, which B3 used to take in round 2, so B3 went further down its list to 6, which B1 used to take in round 3. The extra moves are the price of building the table from the current backend set alone, with no memory of the previous table.

(c) The list (offset + j·skip) mod M visits every position exactly when gcd(skip, M) = 1. With M = 8, skip = 2 and offset 0 the list is 0, 2, 4, 6, 0, 2, ..., so the backend can only ever claim even positions. Once those are full, its `while entry[c] >= 0` loop never finds an empty slot and the build never finishes. With M prime, every skip from 1 to M − 1 is coprime to M, so the simple formula is always safe.

</details>

**28.9 ★★ Why hash mod k moves almost every flow.** An ECMP group has next hops h_0, ..., h_(k−1), and a flow with hash x uses h_(x mod k). Hop h_v fails; the survivors keep their order, are renumbered 0 to k − 2, and flows now use x mod (k − 1). (a) Prove that, over a full period of x, exactly 1/k of flows keep their next hop, whatever v is. (b) A simpler repair keeps k slots and puts some survivor into the dead hop's slot. What fraction of flows move, and what does it cost? (c) How does a table of M ≫ k buckets avoid both problems, and why does Maglev rebuild its table from scratch instead of patching it?

<details>
<summary>Solution</summary>

(a) Take x over k(k − 1) consecutive values. Because gcd(k, k − 1) = 1, the Chinese remainder theorem says each pair (a, b) = (x mod k, x mod (k − 1)) occurs exactly once. A flow keeps its next hop when a ≠ v and b is the new index of h_a: b = a if a < v, b = a − 1 if a > v. That is exactly one b for each of the k − 1 surviving values of a, so k − 1 of the k(k − 1) pairs, a fraction 1/k. The other (k − 1)/k of flows move, although only the 1/k that were on h_v had to.

(b) Only the flows of the dead hop move, 1/k, the minimum. But they all land on the one survivor put in the slot, which now carries 2/k of the traffic, twice its share, and a second failure can make it worse.

(c) With `table[x mod M]` and roughly M/k buckets per hop, the dead hop's buckets can be handed out one at a time across all survivors: only its flows move, and each survivor's share grows by about 1/(k(k − 1)), staying within one bucket (1/M of traffic) of the others. Maglev rebuilds rather than patches because many load-balancer machines must map the same flow to the same backend without talking to each other. A table that depends only on the current set of backends, not on the order in which failures happened, is one every machine computes identically. The cost is the small extra disruption measured in §28.4.

</details>

---

## Where this connects

- [Chapter 11: Graphs—Modeling Relationships](../volume-2/ch11-graphs-modeling-relationships.md). The graph fundamentals underneath routing
- [Chapter 13: String Data Structures](../volume-2/ch13-string-data-structures.md). The tries that routing tables actually are
- [Chapter 27: Distributed Data Structures](ch27-distributed-data-structures.md). Ring-based consistent hashing, the minimal-disruption but less balanced alternative to Maglev's table
