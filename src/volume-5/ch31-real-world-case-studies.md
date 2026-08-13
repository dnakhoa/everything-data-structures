# Chapter 31: Real-World Case Studies

## 31.1 Google's Spanner: Globally Distributed SQL

Spanner combines B-tree storage with distributed systems innovations:

**Architecture**:
```
Universe (global deployment)
  ↓
Zone (data center)
  ↓
Spanserver (process)
  ↓
Tablet (range of rows, ~100GB)
  ↓
Colossus (distributed file system)
```

**TrueTime API**: GPS and atomic clocks provide bounded clock uncertainty (±1ms to ±7ms). This enables:
- External consistency (linearizable transactions)
- Snapshot reads without coordination
- Consistent schema changes

**Paxos consensus**: Data replicated via Paxos between zones. Two-phase commit with participant coordinators.

## 31.2 Amazon Dynamo: Highly Available Key-Value Store

Dynamo prioritizes availability over consistency:

**Design decisions**:
- "Always writable": Sloppy quorum + hinted handoff
- Vector clocks for causality tracking
- Quorum guarantees configurable per request

**Data distribution**:
```
Consistent hashing ring (N=3, R=2, W=2):
- N: Number of replicas
- R: Minimum read replicas
- W: Minimum write replicas
- Quorum: max(R,W) > N/2
```

**Anti-entropy**: Merkle trees for background synchronization. Each replica maintains local Merkle tree of its key range; trees compared to detect divergence.

## 31.3 Apache Kafka: Distributed Log as First-Class Citizen

Kafka treats the log as the primary data structure:

**Storage architecture**:
```
Topic: "orders"
  ↓
Partitions (16):
  Partition 0: [0 → 1MB] [1MB → 2MB] ...
  Partition 1: [0 → 1.2MB] [1.2MB → 2.1MB] ...
  ...

Each partition stored as:
  - .log file (actual data)
  - .index file (offset → position)
  - .timeindex file (timestamp → offset)
```

**Zero-copy I/O**: Kafka uses kernel sendfile() to avoid copying data to user space. DMA transfers data from disk directly to network.

**Page cache**: Linux page cache used for hot data. Sequential writes cause read-ahead, sequential reads cause readahead.

## 31.4 Databricks Delta Lake: ACID on Data Lakes

Combines streaming (append-only log) with batch processing:

**Transaction log**: JSON entries recording changes:
```json
{"add": "part-00000.snappy.parquet", "partitionValues": {"date": "2024-01-01"}, "size": 1234567}
{"remove": "part-00099.parquet"}
```

**Optimistic concurrency**: Delta Lake uses file-level locking. Transaction validation checks:

1. Read current protocol version
2. Verify read set files still exist
3. Write new files and transaction commit
4. If conflict, retry with exponential backoff

## 31.5 Cloudflare's Edge Cache: Global Caching Infrastructure

**Anycast routing**: All edge nodes announce same IP via BGP. Traffic routed to nearest PoP (Point of Presence).

**Cache hierarchy**:
```
User → Edge PoP (L1 cache, ~100GB)
           ↓ (miss)
        Regional DC (L2 cache, ~1TB)
           ↓ (miss)
        Origin Shield (L3 cache, ~10TB)
           ↓ (miss)
        Origin server
```

**Cache key normalization**:
- Strip query parameters (configurable)
- Normalize URL encoding
- Include vary headers in key
- TTL rules per content type
