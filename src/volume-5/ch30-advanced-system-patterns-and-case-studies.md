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
def als(R, k, iterations):
    m, n = R.shape
    U = random(m, k)
    V = random(n, k)

    for _ in range(iterations):
        # Fix U, solve for V
        for j in range(n):
            users = R[:, j].nonzero()
            V[j] = solve(
                U[users].T @ U[users] + lambda*I,
                U[users].T @ R[users, j]
            )
        # Fix V, solve for U
        for i in range(m):
            items = R[i, :].nonzero()
            U[i] = solve(
                V[items].T @ V[items] + lambda*I,
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
        self.graph = {}  # node_id -> [neighbors]
        self.layers = []  # layer -> [node_ids]

    def insert(self, vector, max_layers=6):
        # Random layer selection (geometric distribution)
        level = int(-log(random()) % max_layers)

        # Search from top layer to find insert position
        for l in reversed(range(level + 1)):
            candidates = self._search_layer(vector, ef=1, layer=l)
            # Connect to m nearest unconnected nodes
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
shard = hash(key) % (num_physical × num_vnodes)
owner = virtual_node_ring[shard]
```

**Rebalancing**: When adding nodes, only O(1/k) keys move where k is virtual node count.

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
        self.start_time = time.now()
        self.end_time = None
        self.tags = {}
        self.annotations = []

    def finish(self):
        self.end_time = time.now()

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
