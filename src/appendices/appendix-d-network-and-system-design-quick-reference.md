# Appendix D: Network and System Design Quick Reference

## D.1 Distributed Consistency Levels

| Level | Guarantees | Use Case |
|-------|------------|----------|
| Linearizability | All operations appear atomic | Financial transactions |
| Sequential | Operations appear in order | Inventory management |
| Causal | Causally related operations in order | Social feeds |
| Eventual | Convergence without guarantees | Caching, logging |
| Read-your-writes | Own writes visible immediately | User sessions |

## D.2 CAP and PACELC

CAP says that **when a network partition occurs**, a distributed system must sacrifice either consistency or availability. Partitions are not optional (they are a fact of networks)so the real choice is only ever between CP and AP:

| Choice | During a partition | Example |
|--------|-------------------|---------|
| CP | Reject requests rather than serve stale or divergent data | ZooKeeper, etcd, HBase, Spanner |
| AP | Keep serving; reconcile afterwards | Cassandra, DynamoDB, Riak |

"CA" is often listed as a third option with a single-node RDBMS as the example. That is a category error: a non-distributed system has no partitions to tolerate, so CAP does not classify it. There is no CA distributed system.

**PACELC** is the more useful formulation, because it also describes the normal case when nothing is broken: *if Partition, then A or C; Else, then L (latency) or C*:

| System | Partition behavior | Normal behavior | Reads as |
|--------|-------------------|-----------------|----------|
| Spanner | CP | Consistency over latency | PC/EC |
| DynamoDB | AP | Latency over consistency | PA/EL |
| Cassandra | AP | Latency over consistency (tunable) | PA/EL |
| MongoDB | CP | Consistency over latency | PC/EC |

The Else half is where most systems actually spend their time, and it is the half CAP says nothing about, which is why "we chose AP" explains far less about a system than people usually intend by it.

## D.3 Caching Patterns

| Pattern | Description | Consistency |
|---------|-------------|-------------|
| Cache-aside | Application manages cache | Stale reads possible |
| Read-through | Cache fetches on miss | Stale reads possible |
| Write-through | Synchronous cache + store | Strong |
| Write-back | Async cache to store | Weak until sync |

## D.4 Load Balancing Algorithms

| Algorithm | State Required | Hot Spot Risk | Session Affinity |
|-----------|---------------|---------------|------------------|
| Round Robin | None | Yes (variable load) | None |
| Least Connections | Per-node count | Lower | None |
| IP Hash | None | Yes (skewed) | Yes |
| Consistent Hash | Ring state | Lowest | Partial |
| Weighted | Weights | Lower | None |

## D.5 Data Structure → System Mapping

| Data Structure | System Application |
|----------------|-------------------|
| Hash table | Key-value stores (Redis, Memcached) |
| B-tree | Relational databases (PostgreSQL, InnoDB) |
| LSM tree | Time-series, write-heavy (RocksDB, Cassandra) |
| Trie | Routing tables, prefix matching |
| Graph | Social networks, recommendation systems |
| Log | Message queues (Kafka), event sourcing |
| Bloom filter | Cache, membership testing (web, CDNs) |
| Consistent hash | Distributed caching, load balancing |

---

Every system in Volume V reduces to the building blocks in Volumes I–IV. That is the argument the book makes, and this table is the short version of it.

*Everything Data Structures*: by Ngoc Anh Khoa Doan. Prose is [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); code is MIT.
