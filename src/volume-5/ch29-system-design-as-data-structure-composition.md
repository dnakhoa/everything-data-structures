# Chapter 29: System Design as Data Structure Composition

## 29.1 The Unifying Theory

System design is the art of composing data structures and algorithms to solve real-world problems at scale. Every complex system reduces to foundational building blocks.

**The System Design Equation**:
```
System = Data Structures + Concurrency Control + Replication + Consistency + APIs

Where:
- Data Structures: How information is organized
- Concurrency Control: Managing simultaneous access
- Replication: Duplicating data for reliability
- Consistency: Maintaining truth across copies
- APIs: The interface to the outside world
```

## 29.2 Key-Value Stores

Key-value stores are the simplest non-trivial data structure composition: a hash table extended with persistence and replication.

### Memcached Architecture

In-memory hash table with LRU eviction:
```
Client request:
1. Hash key → server selection (consistent hash)
2. Connect to server (TCP)
3. Send GET/SET command
4. Parse response
5. Return to client

Server internal:
- Hash table: O(1) lookup
- LRU chain: O(1) insertion/deletion
- Slab allocator: Reduce fragmentation
```

**Slab allocation**: Pre-allocate size classes (64B, 128B, ..., 1MB). Items assigned to smallest sufficient class. Reduces fragmentation but may waste space.

### Redis Data Structures

Redis implements rich data types on top of key-value:
- **String**: Binary-safe value (bitmap operations available)
- **List**: Linked list, O(1) push/pop at both ends
- **Hash**: Field-value map, O(1) field operations
- **Set**: Hash set (no duplicates), O(1) membership
- **Sorted Set**: Score-ordered, O(log N) insert, O(log N + M) to return a range of M items

**Persistence**: RDB (point-in-time snapshots) + AOF (append-only log). Trade-off: performance vs durability.

## 29.3 Message Queues as Persistent Queues

Message queues are persistent FIFO structures with durability and ordering guarantees.

### Apache Kafka Architecture

Log-structured storage with consumer groups:
```
Topic: ordered, immutable sequence of records
    ↓ (partitioned)
Partition: sequential log on disk
    ↓ (replicated)
Leader + Followers (ISR - In-Sync Replicas)

Producer: batch writes to partition leader
Consumer: offset-based consumption, committed to disk
```

**Offset management**: Consumer tracks position in partition. Enables:
- **At-least-once**: Commit offset after processing
- **At-most-once**: Commit offset before processing
- **Exactly-once**: Transactional commits (Kafka transactions)

**Segment files**: Logs split into segments (~1GB). Index file maps offset → position. Enables efficient seeking.

### RabbitMQ

Queue-based with exchange routing:
```
Exchange (topic/direct/fanout)
    → Binding
    → Queue
    → Consumer

Persistence levels:
- Queue durable: Survive broker restart
- Message persistent: Written to disk
- Publisher confirms: Wait for replication acknowledgment
```

## 29.4 Database Storage Engines

Storage engines choose data structures for disk efficiency.

### B-Tree Storage (InnoDB, PostgreSQL)

B-trees optimized for disk with large block sizes:
```
Page structure (16KB typical):
- Page header (metadata, checksum)
- User data area
- Free space
- Slot directory (pointers to entries)

B-tree optimizations:
- Page directory for 2-level index
- Leaf page chaining for range scans
- Write-ahead log (WAL) for durability
- Buffer pool for caching
```

**Double-write buffer**: InnoDB writes to temporary area before final location. Prevents torn writes on crash.

### LSM-Tree Storage (LevelDB, RocksDB, Cassandra)

Log-Structured Merge trees optimize write throughput:
```
Write path:
1. Write to WAL (durability)
2. Insert into memtable (in-memory skip list)
3. When memtable fills, sort and write to L0 SSTable

Compaction:
- L0 → L1: Sort by key, merge files
- L1 → L2: Key range partitioned, merge
- Classic: Size-tiered (Cassandra)
- Modern: Level-based (RocksDB)
```

**Trade-offs vs B-trees**:
- Writes: 3-10x faster (sequential writes)
- Reads: Slower (check multiple structures)
- Space: Higher (stale versions persist until compaction removes them)

## 29.5 Load Balancing Algorithms

Load balancers distribute requests across backend servers. Each algorithm uses different data structures for state tracking.

### Round Robin

Simple rotation with no state:
```
Server list: [A, B, C]
Request 1 → A
Request 2 → B
Request 3 → C
Request 4 → A (wrap)
```

**Weighted round robin**: Servers with higher weight receive more requests.

### Least Connections

Track active connections per server:
```python
class LeastConnections:
    def __init__(self, servers):
        self.connections = {s: 0 for s in servers}  # server -> count

    def select(self):
        return min(self.connections, key=self.connections.get)

    def add_request(self, server):
        self.connections[server] += 1

    def remove_request(self, server):
        self.connections[server] -= 1
```

**Problem**: Treats every connection as equal cost. Two connections to a slow or overloaded server count the same as two to a fast one, and `select` is an O(S) scan over S servers.

### Least Loaded with Load Scoring

Multi-metric scoring:
```python
def score_server(server):
    cpu_score = server.cpu_usage / 100
    mem_score = server.memory_usage / 100
    conn_score = server.active_connections / server.max_connections

    # Weighted combination
    return (0.4 * cpu_score + 0.3 * mem_score + 0.3 * conn_score)
```

### Power of Two Choices

Least connections answers "which server is least loaded?" exactly, by looking at every server. The power of two choices asks a cheaper question: pick two servers uniformly at random and send the request to the less loaded of the two. On top of the `LeastConnections` bookkeeping above, only `select` changes:

```python
import random


class PowerOfTwoChoices(LeastConnections):
    def __init__(self, servers, rng=random):
        super().__init__(servers)
        self.servers = list(servers)
        self.rng = rng

    def select(self):
        a, b = self.rng.sample(self.servers, 2)  # two distinct servers
        return a if self.connections[a] <= self.connections[b] else b
```

`select` now reads two counters instead of S, so it is O(1) worst case, and it needs no ordering structure over the servers at all: no heap, no buckets.

**The result.** The clean model is balls into bins: n balls (requests) are placed one at a time into n bins (servers), and none leave. If each ball goes to one bin chosen at random, the fullest bin ends up with (1 + o(1)) ln n / ln ln n balls with high probability, which is Θ(log n / log log n). If each ball looks at d ≥ 2 random bins and joins the least loaded, the maximum drops to ln ln n / ln d + Θ(1), which is Θ(log log n) (Azar, Broder, Karlin and Upfal, 1994). Going from one choice to two is an exponential improvement. Going from two to three only divides the leading term by ln 3 / ln 2 ≈ 1.58.

The reason is squaring. Let βᵢ be the fraction of bins with load at least i. A ball can raise a bin to load i + 1 only if both of its choices already have load at least i, which happens with probability about βᵢ². So, heuristically, βᵢ₊₁ ≈ βᵢ². There are only n balls, so at most half the bins can hold two or more: β₂ ≤ 1/2, and the sequence is at most 1/2, 1/4, 1/16, 1/256, 1/65,536, and so on. The exponent doubles at every level, so after about log₂ log₂ n levels the expected number of bins that high falls below one. With one choice, the load of a bin is roughly Poisson with mean 1, and the fraction of bins with load at least k is about 1/(e·k!), which shrinks only factorially. (The real proof is a layered induction that makes this heuristic rigorous by bounding the deviation at every level.)

A seeded simulation shows the difference:

```python
import random


def throw(n_bins, n_balls, d, seed=1):
    """Each ball goes to the least loaded of d bins chosen at random."""
    rng = random.Random(seed)
    load = [0] * n_bins
    for _ in range(n_balls):
        best = min((rng.randrange(n_bins) for _ in range(d)), key=load.__getitem__)
        load[best] += 1
    return load


for n in (10**3, 10**4, 10**5, 10**6):
    print(n, [max(throw(n, n, d)) for d in (1, 2, 3)])

for d in (1, 2):  # how many of 10**6 bins reach load >= k, for k = 1..8
    load = throw(10**6, 10**6, d)
    print(d, [sum(x >= k for x in load) for k in range(1, 9)])

for m in (10**4, 10**5, 10**6):  # 1,000 bins, m balls: excess over the mean
    print(m, [max(throw(1000, m, d)) - m // 1000 for d in (1, 2)])
```

It prints the following (the code takes a few seconds):

| n = number of balls = number of bins | 1,000 | 10,000 | 100,000 | 1,000,000 |
|---|---|---|---|---|
| max load, one choice | 5 | 6 | 7 | 8 |
| max load, two choices | 3 | 3 | 4 | 4 |
| max load, three choices | 2 | 3 | 3 | 3 |

| bins with load ≥ k (n = 10⁶) | k = 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|
| one choice | 264,128 | 80,618 | 19,032 | 3,702 | 562 | 84 | 8 |
| two choices | 229,701 | 9,014 | 6 | 0 | 0 | 0 | 0 |

The second table is the squaring argument in action: with one choice each level holds only about k times fewer bins than the level below it (the factorial at work), and with two choices the count collapses from 9,014 to 6 in one step. The absolute numbers in the first table are small because both bounds grow slowly, but a load balancer cares about a different regime, where there are far more requests than servers. There the gap widens:

| 1,000 bins, m balls: max load minus the mean m/n | m = 10⁴ | 10⁵ | 10⁶ |
|---|---|---|---|
| one choice | 11 | 42 | 105 |
| two choices | 2 | 2 | 3 |

With one choice the excess grows like √(m log n / n). With two choices it stays at ln ln n / ln 2 + O(1) no matter how many balls are thrown (Berenbrink, Czumaj, Steger and Vöcking, 2000): the fullest server is never more than a few requests above average.

**Why not just pick the least loaded?** With exact, instantly updated load and a single balancer, least loaded is better than two choices. Real balancers have neither. Load figures arrive by periodic health checks or load reports, and a fleet of independent balancers (or worker processes inside one) cannot see each other's decisions between updates. Every one of them sees the same server as least loaded and sends it everything until the next update arrives: the server that looked idle is buried, and the next update moves the herd to a different victim. Two random choices cannot herd like this, because any given server is one of the two candidates for only about 2/S of the requests, so it receives at most about twice its fair share no matter how attractive its stale load looks. Mitzenmacher ("How Useful Is Old Information?", 2000) analysed exactly this. A small queueing simulation reproduces it: 100 servers, 90 new jobs per tick, each busy server finishing a job with probability 0.95 per tick (so the servers are about 95% utilised), and the balancer sees a load snapshot refreshed every `period` ticks.

```python
import random


def mean_queue(policy, period, n=100, arrivals=90, p_serve=0.95, ticks=10_000, seed=1):
    """Average jobs queued per server when the balancer sees loads refreshed every `period` ticks."""
    rng = random.Random(seed)
    queue = [0] * n
    total = 0
    for t in range(ticks):
        if t % period == 0:
            seen = queue[:]  # the stale view
            low = min(seen)
            lowest = [i for i in range(n) if seen[i] == low]
        for _ in range(arrivals):
            if policy == "random":
                s = rng.randrange(n)
            elif policy == "least loaded":
                s = rng.choice(lowest)  # ties broken at random
            else:  # "two choices"
                a, b = rng.randrange(n), rng.randrange(n)
                s = a if seen[a] <= seen[b] else b
            queue[s] += 1
        for i in range(n):
            if queue[i] and rng.random() < p_serve:
                queue[i] -= 1
        total += sum(queue)
    return total / (ticks * n)


for period in (1, 5, 20, 50):
    print(period, [round(mean_queue(p, period), 2)
                   for p in ("random", "least loaded", "two choices")])
```

| snapshot refreshed every | random | least loaded | two choices |
|---|---|---|---|
| 1 tick | 8.61 | **1.03** | 1.28 |
| 5 ticks | 8.61 | 16.93 | **2.30** |
| 20 ticks | 8.61 | 130.30 | **5.38** |
| 50 ticks | **8.61** | 702.69 | 10.99 |

Even at a period of one tick the balancer routes 90 jobs on the same snapshot; least loaded still wins there because, with queues this short, many servers tie at the minimum and the random tie-break spreads the batch. At five ticks it is already twice as bad as ignoring load entirely, and at 50 ticks the queues grow without bound: the system is unstable. Two choices degrades gracefully. With very stale information it ends up slightly worse than random, which is also what Mitzenmacher found: old data is still mildly misleading, but it can no longer cause a stampede.

**Where it is used.** NGINX's `random two` directive (since 1.15.1) picks two servers at random, honouring weights, and sends the request to the one with fewer active connections. HAProxy's `balance random(<draws>)` defaults to 2 draws and its documentation names the technique. Envoy's least request balancer, when all hosts have equal weight, samples a configurable number of hosts (2 by default) and picks the one with the fewest active requests; it calls this P2C. The same idea appears outside load balancing: Redis evicts by sampling a few keys and dropping the best candidate among them (see the eviction policies in §29.6), and two-choice hashing places each key in the emptier of two buckets.

### Consistent Hash for Load Balancing

Ensure session affinity without sticky sessions:
```
Key space: 0 to 2^32-1
Nodes placed at hash(node_ip) positions
Virtual nodes at hash(node_ip + ":replica" + i)
Request routed to first node clockwise from hash(request_id)
```

## 29.6 CDN and Caching Hierarchies

CDNs create multi-level caching hierarchies for content distribution.

### Cache Invalidation Strategies

**TTL-based expiration**:
```python
def is_valid(cached_item, max_age):
    return time.time() - cached_item.timestamp < max_age
```

**Active invalidation**: Purge signals propagate through cache hierarchy.

**Probabilistic early expiration**: Reduce cache stampedes:
```python
def should_revalidate(item, beta=1.0):
    # XFetch (Vattani et al.): item.delta is how long the last
    # recomputation took; beta > 1 favors earlier refreshes.
    # -log(u) is exponentially distributed, so a rare request refreshes
    # early, more often as expiry nears, instead of all at once after it.
    u = 1.0 - random.random()  # in (0, 1], avoids log(0)
    return time.time() - item.delta * beta * math.log(u) >= item.expires
```

### Eviction Policies as Data Structures

A cache with a size limit needs a rule for which entry to drop when a new one arrives. Each rule is a data structure: what it records per entry and what it must touch on every hit decide its cost as much as its hit rate does. All the policies below keep a hash map from key to entry (expected O(1)); what differs is the structure beside it.

**LRU** evicts the entry whose last use is oldest. A hash map points into a doubly linked list kept in recency order: a hit unlinks the node and pushes it to the front, and eviction removes the tail, both in O(1). Chapter 12 builds it in [Exercise 12.6](../volume-2/ch12-hash-tables.md), and memcached's "LRU chain" in §29.2 is this list. LRU has two weaknesses, and both come from the list. Every hit is a write: the node moves, so a cache shared by many threads must take a lock on the list even to serve a read. And LRU remembers only recency: one scan over more distinct keys than the cache holds (a backup, a full table scan, a crawler) evicts every hot entry, and each of them must miss once to come back.

### LFU in O(1), and Making It Forget

LFU evicts the entry with the fewest accesses. The obvious structure is a min-heap keyed by count, at O(log n) per hit, because every hit changes a key. But counts only ever change by +1 and a new entry always starts at 1, so the heap can be replaced by buckets: a map from each count to the keys that have it, kept in recency order to break ties, plus the current minimum count (Shah, Mitra and Matani, 2010; the same trick as Exercise 29.7). A hit moves a key from bucket f to bucket f + 1. If bucket f was the minimum and is now empty, the new minimum is f + 1, because no count lies in between. An insertion sets the minimum back to 1. Eviction pops the oldest key from the minimum bucket.

```python
from collections import OrderedDict, defaultdict


class LFUCache:
    """O(1) LFU: keys grouped by frequency; ties go to the least recently used."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.entry = {}                          # key -> [value, freq]
        self.by_freq = defaultdict(OrderedDict)  # freq -> keys, oldest first
        self.min_freq = 0

    def _bump(self, key):
        e = self.entry[key]
        f = e[1]
        del self.by_freq[f][key]
        if not self.by_freq[f]:
            del self.by_freq[f]
            if self.min_freq == f:
                self.min_freq = f + 1  # nothing lies between f and f + 1
        e[1] = f + 1
        self.by_freq[f + 1][key] = None

    def get(self, key):
        if key not in self.entry:
            return None
        self._bump(key)
        return self.entry[key][0]

    def put(self, key, value):
        if key in self.entry:
            self.entry[key][0] = value
            self._bump(key)
            return
        if len(self.entry) == self.capacity:
            bucket = self.by_freq[self.min_freq]
            victim, _ = bucket.popitem(last=False)
            if not bucket:
                del self.by_freq[self.min_freq]
            del self.entry[victim]
        self.entry[key] = [value, 1]
        self.by_freq[1][key] = None
        self.min_freq = 1
```

Every operation is a constant number of dictionary operations: O(1) expected. The original paper uses a doubly linked list of frequency nodes, each holding a linked list of keys; `OrderedDict` is that inner list.

LFU resists scans by construction: scanned keys enter with count 1 and evict each other, never the hot keys with large counts. Its failure is the opposite one: it never forgets. A key that was hot yesterday keeps its count, while a key that is hot today enters at 1 and is the first to go. Two fixes are common. **Decay** periodically halves every count, as W-TinyLFU's sketch does below (Redis's LFU mode also decays its small per-key counters as time passes). **Dynamic aging** (LFU-DA) keeps one cache-wide value L, sets it to the priority of each entry it evicts, and gives an entry priority L + count whenever it is inserted or hit. A newcomer starts at L + 1, just above the last victim, so an entry whose count has stopped growing is eventually overtaken. Squid offers this as `heap LFUDA`, after work at HP Labs on web proxy caches in the late 1990s. Priorities now jump by more than one, so the buckets no longer apply and LFU-DA needs a heap: O(log n) per access. Exercise 29.10 builds it.

### CLOCK (Second Chance)

CLOCK approximates LRU without moving anything on a hit. Entries sit in a fixed circular array of slots, each with one **reference bit**, and a "hand" points at one slot. A hit sets the entry's bit. To evict, the hand sweeps forward: a slot with its bit set gets a second chance (the bit is cleared and the hand moves on), and the first slot found with its bit clear is the victim.

```python
class ClockCache:
    """CLOCK (second chance): slots in a circle, one reference bit per slot."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.keys = [None] * capacity
        self.values = [None] * capacity
        self.ref = [False] * capacity
        self.slot = {}              # key -> slot index
        self.hand = 0

    def get(self, key):
        i = self.slot.get(key)
        if i is None:
            return None
        self.ref[i] = True          # a hit only sets a bit: nothing moves
        return self.values[i]

    def put(self, key, value):
        i = self.slot.get(key)
        if i is None:
            i = self._victim()
            if self.keys[i] is not None:
                del self.slot[self.keys[i]]
            self.keys[i] = key
            self.slot[key] = i
        self.values[i] = value
        self.ref[i] = True

    def _victim(self):
        while True:
            i = self.hand
            self.hand = (i + 1) % self.capacity
            if self.keys[i] is None or not self.ref[i]:
                return i
            self.ref[i] = False     # second chance: clear the bit, move on


c = ClockCache(3)
for k in "abc":
    c.put(k, k.upper())
c.put("d", "D")                     # every bit set: sweep clears all, evicts a
assert c.keys == ["d", "b", "c"] and c.ref == [True, False, False] and c.hand == 1
c.get("b")                          # b's bit set again
c.put("e", "E")                     # b gets a second chance, c is evicted
assert c.keys == ["d", "b", "e"] and c.ref == [True, False, True] and c.hand == 0
```

The trace: a, b and c fill slots 0 to 2 with their bits set. Inserting d sends the hand all the way round, clearing a, b and c, and back to slot 0, where a's bit is now clear: a is evicted and d takes its slot, with the hand left at slot 1. The hit on b sets its bit. Inserting e finds b's bit set at slot 1 (cleared, second chance) and c's bit clear at slot 2, so c is evicted. LRU would have evicted a and then c as well. The two differ when every bit is set: then the sweep clears them all and CLOCK evicts in slot order, which is FIFO (Exercise 29.9).

A hit is O(1) worst case and writes one bit. One eviction can sweep all c slots, but it is amortized O(1): each step of the hand either finds the victim or clears a bit, and each bit was set by an earlier access, so the total movement of the hand is at most the number of accesses plus the number of evictions.

This is why operating systems and databases use CLOCK-style approximations instead of true LRU. In a virtual memory system, the MMU sets an "accessed" bit in the page table entry on every memory reference; the kernel cannot run code on every load and store to relink a list, so all it can do is read and clear those bits later, which is exactly what the clock hand does. Linux keeps active and inactive page lists and moves pages between them using the same bits. PostgreSQL's shared buffer pool is used concurrently by many backend processes, and a true LRU list would put a lock on every buffer hit. PostgreSQL 8.0 shipped ARC (below), replaced it with the simpler 2Q in a later 8.0.x release because of IBM's pending patent on ARC, and moved to a clock sweep in 8.1 (2005), largely to remove that contention. Each buffer carries a small usage count instead of one bit: a hit increments it (capped at 5), the sweep decrements it, and a buffer is evicted when the sweep finds it at zero, so a buffer used often survives several passes. Redis goes further and keeps no eviction structure at all: in its LRU modes it samples a few keys (5 by default) and evicts the one idle longest, the eviction-side cousin of the power of two choices.

### ARC

ARC, the Adaptive Replacement Cache (Megiddo and Modha, IBM, 2003), balances recency against frequency and tunes the balance itself. It keeps two LRU lists of cached entries: T1 for keys seen once recently, T2 for keys seen at least twice. It also keeps two **ghost** lists, B1 and B2, which hold only the keys (no values) of entries recently evicted from T1 and T2. A target size p splits the c slots between T1 and T2. A miss that finds its key in B1 means T1 was too small (a recency-only entry would have hit), so p grows; a miss that finds its key in B2 means T2 was too small, so p shrinks. Every step is a constant number of hash and list operations, O(1), and the metadata is about twice LRU's, since the ghost lists track up to c evicted keys. A scan only passes through T1, so the frequently used entries in T2 survive it. ZFS's in-memory cache is an ARC and is named after it.

### W-TinyLFU

W-TinyLFU (Einziger, Friedman and Manes) separates two questions that LRU and LFU answer together: which entry to evict, and whether a new key deserves a place at all. Its structure, as used by Caffeine, the standard Java caching library:

- A small **window**, an LRU holding 1% of capacity at first, where every new key lands.
- A **main region**, a segmented LRU holding the rest: 20% *probation* and 80% *protected*. A hit in probation promotes the entry to protected; protected's overflow is demoted back to probation.
- An **admission filter**: a [Count-Min sketch](../volume-3/ch14-probabilistic-data-structures.md) that counts every access, hits and misses alike, including keys not in the cache.

When the window overflows, its LRU victim becomes a candidate for the main region and competes with the main region's own victim, the LRU entry of probation. The sketch estimates both frequencies, and the candidate gets in only if its estimate is higher; otherwise the candidate is the one dropped. The sketch is what makes this cheap: it remembers frequencies for keys the cache no longer holds, in a few bits per key. Caffeine's has four 4-bit counters per key (so a count saturates at 15) and halves every counter after a number of increments equal to ten times the cache's maximum size, so old popularity fades. It costs about 8 bytes per cache entry, and Caffeine resizes the window at run time by hill climbing on the observed hit rate. A scanned key has an estimated count near 1, loses every admission contest, and never displaces anything in the main region, while the window still gives a burst of new keys a short LRU life.

### Comparing Eviction Policies

Costs below are on top of the expected-O(1) hash lookup that every policy does.

| policy | per-access cost | metadata per entry | scan resistance |
|---|---|---|---|
| LRU | O(1); every hit relinks a shared list | 2 pointers | none: a scan larger than the cache flushes it |
| CLOCK | hit O(1), sets one bit; eviction amortized O(1), worst case O(c) sweep | 1 bit (PostgreSQL: a small usage count) | none, same as LRU |
| LFU (count buckets) | O(1); a hit moves the key to the next bucket | a count + 2 pointers | strong, but never forgets old popularity |
| LFU-DA | O(log n) heap update | a count + a priority + heap position | strong; aging lets new keys in |
| ARC | O(1) | 2 pointers, plus ghost keys for up to c evicted entries | yes: scans pass through T1 only |
| W-TinyLFU | O(1): a few sketch counters + an SLRU relink | 2 pointers + about 8 bytes of sketch (Caffeine) | strong: one-hit keys fail admission |

To see the differences in hit rates, the next simulation runs a cache of 1,000 entries over 200,000 requests to 10,000 keys with Zipf-like popularity (key of rank r requested with probability proportional to 1/r^0.9). It compares three workloads: the Zipf requests alone; the same requests with a scan of 3,000 never-repeated keys after every 2,000 requests; and a shift halfway through, after which a different set of keys is hot. Hit rates count only the Zipf requests, since a scan can never hit. LRU here is an `OrderedDict`, which has the same eviction behaviour as Chapter 12's hand-built version; `ClockCache` and `LFUCache` are the classes above.

```python
import itertools
import random
from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity):
        self.capacity, self.d = capacity, OrderedDict()

    def get(self, key):
        if key not in self.d:
            return None
        self.d.move_to_end(key)
        return self.d[key]

    def put(self, key, value):
        self.d[key] = value
        self.d.move_to_end(key)
        if len(self.d) > self.capacity:
            self.d.popitem(last=False)


N = 10_000  # keys 0..N-1 follow Zipf; keys >= N are scan keys


def workload(scan_len=0, shift=False, s=0.9, length=200_000, burst=2_000, seed=1):
    rng = random.Random(seed)
    cum = list(itertools.accumulate(1 / (r + 1) ** s for r in range(N)))
    scan_keys = itertools.count(N)  # a scan key is never requested again
    trace = []
    while len(trace) < length:
        offset = N // 2 if shift and len(trace) >= length // 2 else 0
        ranks = rng.choices(range(N), cum_weights=cum, k=burst)
        trace += [(r + offset) % N for r in ranks]  # the offset changes which keys are hot
        trace += [next(scan_keys) for _ in range(scan_len)]
    return trace


def hit_rate(cache, trace):
    hits = 0
    for key in trace:
        if cache.get(key) is not None:
            hits += key < N
        else:
            cache.put(key, True)
    return hits / sum(key < N for key in trace)


for label, trace in [("Zipf only", workload()),
                     ("Zipf + scans", workload(scan_len=3_000)),
                     ("hot set shifts", workload(shift=True))]:
    print(label, [round(hit_rate(c(1_000), trace), 3)
                  for c in (LRUCache, ClockCache, LFUCache)])
```

| workload | LRU | CLOCK | LFU |
|---|---|---|---|
| Zipf only | 0.554 | 0.541 | **0.627** |
| Zipf + scans | 0.454 | 0.453 | **0.615** |
| hot set shifts | **0.553** | 0.541 | 0.434 |

Three things show. CLOCK gives up about one point of hit rate against LRU, which is the price of the approximation, and in return a hit writes one bit instead of relinking a shared list. When popularity is fixed, LFU wins clearly: with independent requests from fixed probabilities, the best a cache can do is hold the most probable keys, and LFU's counts estimate exactly those probabilities. The scans take ten points off LRU and CLOCK and barely touch LFU. But when the hot set moves, LFU loses 19 points and finishes last, because the old hot keys keep their large counts and the new ones are evicted on arrival. No policy in this table wins all three rows, which is the case for adaptive designs: ARC and W-TinyLFU both aim for LFU's first two rows and LRU's third.

## 29.7 Rate Limiting Data Structures

Rate limiting controls request throughput.

### Token Bucket

```python
class TokenBucket:
    def __init__(self, rate, capacity):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()

    def allow(self, tokens=1):
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.rate
        )
        self.last_update = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
```

**Token bucket vs Leaky bucket**: Token bucket allows burstiness up to capacity; leaky bucket outputs at constant rate.

### Sliding Window Log

More accurate rate limiting:
```python
class SlidingWindowLog:
    def __init__(self, window_size, max_requests):
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests = []  # Timestamps of requests

    def allow(self):
        now = time.time()
        # Remove old entries
        self.requests = [
            t for t in self.requests
            if now - t < self.window_size
        ]

        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False
```

**Fixed window vs Sliding window vs Sliding log**: Trade-offs between accuracy, memory, and implementation complexity.

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**29.1 ★ Slab waste.** Memcached's slab allocator in §29.2 uses size classes that double: 64 B, 128 B, 256 B, and so on up to 1 MB. Items of 65 B, 129 B, 300 B and 1,000 B arrive. Which class does each go into, and how many bytes does each waste? What is the worst-case fraction of a slot that can be wasted with doubling classes, and what happens to it if the classes grow by a factor of 1.25 instead?

<details>
<summary>Solution</summary>

| item | class | wasted | wasted fraction |
|---|---|---|---|
| 65 B | 128 B | 63 B | 49% |
| 129 B | 256 B | 127 B | 50% |
| 300 B | 512 B | 212 B | 41% |
| 1,000 B | 1,024 B | 24 B | 2% |

The worst case is an item one byte larger than a class boundary, which lands in a slot twice its size: just under 50% waste. With growth factor f the worst case is just under 1 − 1/f, so f = 1.25 caps waste at about 20%. The price is more classes (about 3 times as many between 64 B and 1 MB), and memory assigned to one class's slabs cannot easily serve another, so a workload whose item sizes shift over time can strand memory in classes it no longer uses. Memcached's default growth factor is in fact 1.25.

</details>

**29.2 ★ When to commit the offset.** A Kafka consumer fetches offsets 100 to 109 from a partition, processes 100 to 104, and crashes. After restart it resumes from its last committed offset. What gets processed twice, and what never gets processed, if it (a) commits after processing the whole batch, or (b) commits 110 as soon as it fetches the batch?

<details>
<summary>Solution</summary>

(a) At-least-once. The last committed offset is still 100, so the restarted consumer re-reads 100 to 109. Records 100 to 104 are processed twice; nothing is lost. Processing must be idempotent (or deduplicated by offset) for the duplicates to be harmless.

(b) At-most-once. The committed offset is already 110, so the restarted consumer starts at 110. Records 105 to 109 are never processed; nothing is duplicated.

The offset is a single integer per partition per consumer group, so both behaviors come down to whether that integer is written before or after the side effects. Exactly-once requires the side effects and the offset commit to happen atomically, which is what Kafka transactions provide when the output also goes to Kafka.

</details>

**29.3 ★★ Trace a token bucket.** The `TokenBucket` in §29.7 is created at t = 0 with rate = 2 tokens per second and capacity = 5. Requests (one token each) arrive at t = 0 (five of them), t = 0.2, t = 1.0 (two), and t = 4.0 (six). Which are allowed? Give the token count after each time step.

<details>
<summary>Hint</summary>

Refill happens lazily, at the start of each `allow` call, and is capped at capacity. A denied request still updates `last_update`.

</details>

<details>
<summary>Solution</summary>

| time | tokens after refill | requests | allowed | tokens after |
|---|---|---|---|---|
| 0 | 5 | 5 | all 5 | 0 |
| 0.2 | 0 + 0.2 × 2 = 0.4 | 1 | denied | 0.4 |
| 1.0 | 0.4 + 0.8 × 2 = 2.0 | 2 | both | 0 |
| 4.0 | min(5, 0 + 3 × 2) = 5 | 6 | first 5, sixth denied | 0 |

At t = 4.0 the bucket would have earned 6 tokens but the cap keeps it at 5. That cap is the burst size: after any idle period, at most 5 requests go through at once, and after that the sustained rate is 2 per second. A leaky bucket with the same rate would have spread the t = 0 burst out over 2.5 seconds instead of admitting it.

</details>

**29.4 ★★ A faster sliding window log.** The `SlidingWindowLog` in §29.7 rebuilds its whole list on every call. What does `allow` cost per call? Rewrite it so that each call is amortized O(1), and check it against this trace: window 60 s, limit 3, requests at t = 0, 10, 20, 30, 60, 61, 70, 80 should give allowed, allowed, allowed, denied, allowed, denied, allowed, allowed.

<details>
<summary>Hint</summary>

Timestamps are appended in increasing order, so expired entries are always at the front.

</details>

<details>
<summary>Solution</summary>

The list comprehension scans every stored timestamp and allocates a new list, so each call costs O(L) for a limit of L requests per window, even when nothing has expired.

Because timestamps arrive in order, the expired ones form a prefix. A deque lets us drop them from the left in O(1) each. Each timestamp is appended once and popped at most once, so the total work over n calls is O(n): amortized O(1) per call.

```python
from collections import deque


class SlidingWindowLog:
    def __init__(self, window_size, max_requests, clock):
        self.window_size = window_size
        self.max_requests = max_requests
        self.clock = clock
        self.requests = deque()  # timestamps, oldest on the left

    def allow(self):
        now = self.clock()
        while self.requests and now - self.requests[0] >= self.window_size:
            self.requests.popleft()
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False


t = [0.0]
lim = SlidingWindowLog(window_size=60, max_requests=3, clock=lambda: t[0])
results = []
for now in [0, 10, 20, 30, 60, 61, 70, 80]:
    t[0] = now
    results.append(lim.allow())
assert results == [True, True, True, False, True, False, True, True]
assert len(lim.requests) == 3
```

The clock is passed in so the trace can be tested deterministically. At t = 30 the window holds 0, 10, 20 and the request is denied. At t = 60, timestamp 0 is exactly 60 s old and drops out, so the request is allowed. At t = 70, timestamp 10 drops out.

Memory is still O(L) per client, which is the real cost of the sliding log (see the next exercise).

</details>

**29.5 ★★ Probabilistic early expiration.** The `should_revalidate` function in §29.6 refreshes an item early when `now − delta × beta × ln(u) ≥ expires`, where u is uniform on (0, 1]. Take delta = 1 s (the recomputation takes one second), beta = 1, and an item that expires at t = 100. What is the probability that a single request refreshes early at t = 97, at t = 99, and at t = 99.5? If 1,000 requests per second hit the key, roughly when will the first early refresh happen, and why does this prevent a stampede?

<details>
<summary>Solution</summary>

Let g = expires − now, the time remaining. A refresh happens when −delta × beta × ln(u) ≥ g, that is ln(u) ≤ −g/(delta × beta), that is u ≤ e^(−g/(delta × beta)). With delta = beta = 1:

| now | g | P(refresh) = e^(−g) |
|---|---|---|
| 97 | 3 | 0.050 |
| 99 | 1 | 0.368 |
| 99.5 | 0.5 | 0.607 |

At 1,000 requests per second, refreshes happen at a rate of about 1,000 × e^(−g) per second when g seconds remain. Integrating, the expected number of early refreshes before the remaining time falls to g is about 1,000 × e^(−g). That equals 1 at g = ln 1000 ≈ 6.9 s, and the first refresh has a median of about 7.3 s before expiry (where the expected count is ln 2). So in practice one request, around seven seconds early, does the refresh.

Without early expiration, every request arriving in the second after t = 100 misses, and all of them recompute at once: up to 1,000 concurrent recomputations of a value that takes a second to build. With it, one request refreshes well before expiry and resets `expires`, and everyone else keeps getting hits. Scaling by delta means expensive values start refreshing earlier, which is what you want, because a stampede on an expensive value hurts more.

</details>

**29.6 ★★ Rate limiter memory at scale.** You must limit 10 million users to 100 requests per minute each. Estimate the memory for (a) a sliding window log with 8-byte timestamps, (b) a token bucket storing two 8-byte numbers, (c) a fixed window counter. Fixed windows have a known flaw: give a request pattern that gets 200 requests through within about one second while never exceeding 100 in any single window.

<details>
<summary>Solution</summary>

(a) Sliding log: up to 100 timestamps × 8 B = 800 B per active user, so up to 8 GB for 10 million users, before any per-object or per-key overhead.

(b) Token bucket: tokens and last-update time, 16 B per user, 160 MB.

(c) Fixed window: a counter and a window start, also about 16 B per user, 160 MB.

The flaw: windows are aligned to clock minutes. A client sends 100 requests at 12:00:59.5, all admitted because the 12:00 window has room, and 100 more at 12:01:00.0, all admitted because the 12:01 window just started. That is 200 requests in half a second.

The sliding log is exact but costs 50 times the memory. The common compromise is the sliding window counter: keep the counts for the current and previous fixed windows and estimate the sliding count as current + previous × (fraction of the previous window still inside the sliding window). That is O(1) memory per user, like the fixed window, and removes most of the boundary burst, at the cost of assuming requests in the previous window were evenly spread. The token bucket is also O(1) and allows bursts only up to its capacity, which you choose.

</details>

**29.7 ★★★ O(1) least connections.** The `LeastConnections` balancer in §29.5 makes `select` an O(S) scan over S servers, and a min-heap would make updates O(log S). Use the fact that connection counts only change by ±1 to make `select`, `add_request` and `remove_request` all O(1). Implement it and test it against a brute-force minimum.

<details>
<summary>Hint</summary>

Group servers by their current count, as an O(1) LFU cache groups keys by frequency. When the minimum count changes, it can only move by one.

</details>

<details>
<summary>Solution</summary>

Keep a map from count to the set of servers with that count, plus the current minimum count. Incrementing moves a server from bucket c to bucket c + 1. If it was the last server in the minimum bucket, the new minimum is c + 1, because no server has a count between c and c + 1. Decrementing moves a server to c − 1, which becomes the minimum if it is below the old one. Every step is a constant number of hash-set operations.

```python
class LeastConnections:
    def __init__(self, servers):
        self.count = {s: 0 for s in servers}
        self.buckets = {0: set(servers)}  # connection count -> servers
        self.min_count = 0

    def _move(self, server, old, new):
        self.buckets[old].discard(server)
        if not self.buckets[old]:
            del self.buckets[old]
        self.buckets.setdefault(new, set()).add(server)
        self.count[server] = new

    def select(self):
        return next(iter(self.buckets[self.min_count]))

    def add_request(self, server):
        c = self.count[server]
        self._move(server, c, c + 1)
        if c == self.min_count and self.min_count not in self.buckets:
            self.min_count = c + 1

    def remove_request(self, server):
        c = self.count[server]
        self._move(server, c, c - 1)
        if c - 1 < self.min_count:
            self.min_count = c - 1


import random
lb = LeastConnections(["a", "b", "c", "d"])
active = []
for _ in range(10000):
    if active and random.random() < 0.45:
        lb.remove_request(active.pop(random.randrange(len(active))))
    else:
        s = lb.select()
        assert lb.count[s] == min(lb.count.values())
        lb.add_request(s)
        active.append(s)
    assert lb.min_count == min(lb.count.values())
```

Each operation does O(1) expected work (hash-set insert and delete), and the randomized test checks after every step that `select` returns a true minimum and that `min_count` matches a brute-force scan. This is the same trick that makes an LFU cache O(1): when keys change priority by exactly one step, a list of buckets replaces a heap.

</details>

**29.8 ★★ Counting levels.** §29.5 argues that with two choices the fraction βᵢ of bins with load at least i roughly squares at each level, starting from β₂ ≤ 1/2, while with one choice the fraction with load at least k is about 1/(e·k!). Use these to estimate the maximum load (the highest level whose expected number of bins is at least about 1) for n = 10⁶ and n = 10¹² balls in as many bins, with one choice and with two. How much does multiplying n by a million add in each case? The simulation measured a maximum of 4 for two choices at n = 10⁶; why does the estimate come out higher?

<details>
<summary>Hint</summary>

Write βᵢ as a power of two: β₂ = 2⁻¹, and squaring doubles the exponent. 10⁶ ≈ 2²⁰ and 10¹² ≈ 2⁴⁰.

</details>

<details>
<summary>Solution</summary>

Two choices: β₂ = 2⁻¹, β₃ = 2⁻², β₄ = 2⁻⁴, β₅ = 2⁻⁸, β₆ = 2⁻¹⁶, β₇ = 2⁻³², β₈ = 2⁻⁶⁴.

| n | n·β₆ | n·β₇ | n·β₈ | estimated max |
|---|---|---|---|---|
| 10⁶ | 15.3 | 0.0002 | | 6 |
| 10¹² | 1.5 × 10⁷ | 233 | 5 × 10⁻⁸ | 7 |

One choice: the expected number of bins with load at least k is about n/(e·k!).

| n | k = 9 | k = 10 | k = 14 | k = 15 | estimated max |
|---|---|---|---|---|---|
| 10⁶ | 1.01 | 0.10 | | | 9 |
| 10¹² | | | 4.2 | 0.28 | 14 |

Multiplying n by a million adds five levels with one choice and one level with two. That is the gap between log n / log log n and log log n: squaring n (10⁶ to 10¹²) adds one to log₂ log₂ n, while it multiplies ln n / ln ln n by about 1.6 (from 5.3 to 8.3).

The estimate for two choices is loose because β₂ = 1/2 is the worst case allowed by counting. In the simulation only 229,701 of 10⁶ bins (β₂ ≈ 0.23) reached load 2, and that is the value at the end; during most of the run β₂ was smaller still, and a ball reaches level 3 only if both of its choices were at level 2 at that moment. Starting the recurrence from the observed β₃ ≈ 0.009 gives n·β₃² ≈ 81 bins at level 4 (6 were observed) and n·β₄² far below 1 at level 5, which matches the measured maximum of 4. The one-choice estimate is accurate because the Poisson approximation is accurate: the simulation's 562, 84 and 8 bins at loads of at least 6, 7 and 8 compare with 594, 83 and 10 predicted.

</details>

**29.9 ★ When CLOCK becomes FIFO.** A `ClockCache(3)` from §29.6 receives put a, put b, put c, get c, get b, get a, put d. Which key does it evict, and which would LRU evict? What does this say about how much recency information CLOCK keeps, and why do systems accept it?

<details>
<summary>Solution</summary>

After the three puts, a, b and c sit in slots 0, 1 and 2 with their bits set, and the hand is at slot 0. The three gets set bits that are already set. To insert d, the hand finds a's bit set (clears it), then b's (clears it), then c's (clears it), returns to slot 0, finds a's bit clear, and evicts a. LRU's recency order after the gets is c (oldest), b, a (newest), so LRU evicts c. CLOCK evicted the most recently used key.

The reference bit records only "used since the hand last passed", not when. When every entry has been used since the last sweep, the bits carry no information, and the sweep falls back to slot order, which is insertion order: FIFO. CLOCK's recency resolution is one revolution of the hand.

Systems accept this because the hit path is what they optimise. Under memory pressure the hand moves often, so the bits are a fair proxy for "used recently", and the occasional wrong choice costs one extra miss. True LRU would cost a list relink under a lock on every hit, which in an OS is not even possible (the hardware sets the accessed bit; no code runs on a hit). PostgreSQL's usage count, incremented on each use up to 5 and decremented by each pass of the hand, partly restores the missing information by letting often-used buffers survive several passes.

</details>

**29.10 ★★★ Make LFU forget.** Implement `LFUDACache(capacity)` with the same `get` and `put` as `LFUCache` in §29.6, using dynamic aging: a cache-wide value L, initially 0, set to the priority of each evicted entry; an entry's priority is L + count, recomputed with the current L whenever it is inserted or hit; ties go to the entry whose priority was set earliest. Make every operation O(log n) and keep memory O(n). Then trace a capacity-2 cache in which key a is put once and hit 9 times, followed by puts of new keys k1, k2, ...: how many newcomers does it take to evict a? What would plain LFU do?

<details>
<summary>Hint</summary>

Use `heapq` and do not try to update entries inside the heap. Push a new item whenever a priority changes and skip stale items when popping. To keep memory O(n), rebuild the heap from the live items when it grows past a constant multiple of the capacity.

</details>

<details>
<summary>Solution</summary>

```python
import heapq
import itertools


class LFUDACache:
    """LFU with dynamic aging: priority = L + count, L = priority of the last victim."""

    def __init__(self, capacity):
        self.capacity = capacity
        self.L = 0
        self.entry = {}                  # key -> [value, count, stamp of its live heap item]
        self.heap = []                   # (priority, stamp, key); stale items are skipped
        self.stamps = itertools.count()

    def _push(self, key):
        e = self.entry[key]
        e[2] = next(self.stamps)
        heapq.heappush(self.heap, (self.L + e[1], e[2], key))
        if len(self.heap) > 2 * self.capacity + 16:  # drop stale items
            self.heap = [item for item in self.heap
                         if item[2] in self.entry and self.entry[item[2]][2] == item[1]]
            heapq.heapify(self.heap)

    def get(self, key):
        e = self.entry.get(key)
        if e is None:
            return None
        e[1] += 1
        self._push(key)
        return e[0]

    def put(self, key, value):
        if key in self.entry:
            self.entry[key][0] = value
            self.get(key)
            return
        if len(self.entry) == self.capacity:
            while True:
                priority, stamp, victim = heapq.heappop(self.heap)
                if victim in self.entry and self.entry[victim][2] == stamp:
                    break
            self.L = priority            # newcomers now start at L + 1
            del self.entry[victim]
        self.entry[key] = [value, 1, None]
        self._push(key)


c = LFUDACache(2)
c.put("a", 1)
for _ in range(9):
    c.get("a")                           # count 10, priority 10
n = 0
while "a" in c.entry:
    n += 1
    c.put(f"k{n}", n)
assert n == 11 and c.L == 10
```

Each item carries a stamp, and an item is live only if its stamp matches the one stored in the entry, so stale items left by earlier hits are recognised and skipped. The stamp also breaks priority ties in favour of the item pushed earliest. A push is O(log n). The rebuild costs O(n), but it runs only after the heap has gained about n + 16 items since the last rebuild, so its amortized cost per push is O(1). Each pop is O(log n), and each item is popped at most once, so the skipping is paid for by the pushes. All operations are therefore O(log n) amortized, and the heap never holds more than 2n + 17 items.

The trace: a has priority 10. k1 fills the free slot with priority 0 + 1 = 1. k2 evicts k1, so L = 1 and k2 gets 2; in general k_j evicts k_(j−1), sets L = j − 1 and enters with priority j. k10 enters with priority 10, tied with a. k11 must evict one of them, the tie goes to a, whose priority was set earlier, and a is gone after 11 newcomers. Plain LFU never evicts a in this trace: every newcomer has count 1 and is always the minimum, so a, hit 10 times long ago, stays forever.

Run through the simulation in §29.6, LFU-DA scores 0.607, 0.502 and 0.582 on the three workloads, against LFU's 0.627, 0.615 and 0.434. Aging buys back most of the loss when the hot set shifts and costs some of LFU's scan resistance, because each eviction of a scan key raises L and lets newer scan keys outrank hot keys whose counts have not grown lately. A brute-force reference that recomputes the minimum (priority, time set) by scanning all entries agrees with this class on random operation sequences.

</details>

---

## Where this connects

- [Chapter 10: Multiway Search Trees and B-Trees](../volume-1/ch10-multiway-search-trees-and-b-trees.md). The B-trees inside every storage engine described here
- [Chapter 12: Hash Tables](../volume-2/ch12-hash-tables.md). The hash map plus linked list that every LRU cache in §29.6 is built from
- [Chapter 14: Probabilistic Data Structures](../volume-3/ch14-probabilistic-data-structures.md). The probabilistic structures these systems rely on
