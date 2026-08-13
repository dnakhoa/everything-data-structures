# Appendix D: Network and System Design Quick Reference

## D.1 Distributed Consistency Levels

| Level | Guarantees | Use Case |
|-------|------------|----------|
| Linearizability | All operations appear atomic | Financial transactions |
| Sequential | Operations appear in order | Inventory management |
| Causal | Causally related operations in order | Social feeds |
| Eventual | Convergence without guarantees | Caching, logging |
| Read-your-writes | Own writes visible immediately | User sessions |

## D.2 CAP Theorem Variations

| System | Consistency | Latency | Example |
|--------|--------------|---------|---------|
| CP | Strong | Higher | Zookeeper, etcd |
| CA | Strong | Higher | Traditional RDBMS |
| AP | Eventual | Lower | Cassandra, Dynamo |

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

**Author**: MiniMax Agent
**Version**: 3.0 (Complete Edition with Network and System Design)
**Date**: March 2026
**License**: Educational Use

This book now represents the most comprehensive reference on data structures, from fundamental concepts through distributed systems and production system design. Every system you've ever used reduces to these building blocks. May this knowledge empower you to build the systems of tomorrow.
