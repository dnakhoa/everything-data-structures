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
- **Sorted Set**: Score-ordered, O(log N) insert/range

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
- Space: Higher (overwrite on read)

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
    def __init__(self):
        self.connections = {}  # server -> count

    def select(self):
        return min(self.connections, key=self.connections.get)

    def add_request(self, server):
        self.connections[server] += 1

    def remove_request(self, server):
        self.connections[server] -= 1
```

**Problem**: Doesn't account for varying request durations.

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
    return time.now() - cached_item.timestamp < max_age
```

**Active invalidation**: Purge signals propagate through cache hierarchy.

**Probabilistic early expiration**: Reduce cache stampedes:
```python
def should_revalidate(item, beta=1.0):
    # Beta = fuzziness parameter
    grace_time = item.ttl * beta
    if time.now() - item.expires > grace_time:
        return random.random() < 0.5  # Probabilistic revalidate
    return False
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
        self.last_update = time.now()

    def allow(self, tokens=1):
        now = time.now()
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
    def __init__(self, window_size):
        self.window_size = window_size
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

---

## Where this connects

- [Chapter 10: Multiway Search Trees and B-Trees](../volume-1/ch10-multiway-search-trees-and-b-trees.md) — the B-trees inside every storage engine described here
- [Chapter 14: Probabilistic Data Structures](../volume-3/ch14-probabilistic-data-structures.md) — the probabilistic structures these systems rely on
