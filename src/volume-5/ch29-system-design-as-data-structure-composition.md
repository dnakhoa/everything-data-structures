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

### LFU-D with Dynamic Aging

Frequency-based with aging to prioritize recency:
```python
class LFUD:
    def __init__(self):
        self.freq = {}  # key -> frequency count
        self.min_freq = 0

    def access(self, key):
        self.freq[key] = self.freq.get(key, 0) + 1
        self.min_freq = min(self.freq.values())

    def evict(self):
        # Evict lowest frequency, age all frequencies
        for key in list(self.freq.keys()):
            self.freq[key] -= self.min_freq
            if self.freq[key] <= 0:
                del self.freq[key]
        self.min_freq = 0
```

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

---

## Where this connects

- [Chapter 10: Multiway Search Trees and B-Trees](../volume-1/ch10-multiway-search-trees-and-b-trees.md). The B-trees inside every storage engine described here
- [Chapter 14: Probabilistic Data Structures](../volume-3/ch14-probabilistic-data-structures.md). The probabilistic structures these systems rely on
