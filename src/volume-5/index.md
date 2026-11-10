# Volume V: Network and System Design Data Structures

The previous volumes established data structures as fundamental building blocks of computation. This volume reveals a profound truth: **network topologies and system design patterns are simply data structures applied at scale**. When you examine distributed systems, load balancers, CDN architectures, and routing protocols through the lens of data structures, patterns emerge. A routing table is a trie for network paths. Consistent hashing is a modified hash ring. A distributed message queue is a persistent FIFO with durability guarantees. This volume bridges the gap between academic data structures and production system design, showing how foundational structures compose into the complex systems that power the internet.

## Chapters

| Chapter | After it you can |
|---------|------------------|
| [27: Distributed Data Structures](ch27-distributed-data-structures.md) | Explain DHTs and consistent hashing, order events with Lamport, vector and hybrid logical clocks, build CRDTs including a collaborative-text sequence CRDT, and reason about consensus and quorums |
| [28: Network Topology and Routing Data Structures](ch28-network-topology-and-routing-data-structures.md) | Implement longest-prefix match with binary and multibit tries, explain how routers reach one memory access per lookup (DIR-24-8), and balance flows with ECMP and Maglev hashing |
| [29: System Design as Data Structure Composition](ch29-system-design-as-data-structure-composition.md) | Decompose key-value stores, message queues and storage engines into their structures, and choose load-balancing, caching and rate-limiting structures |
| [30: Advanced System Patterns and Case Studies](ch30-advanced-system-patterns-and-case-studies.md) | Explain how a search engine compresses and intersects posting lists, plus vector search, time series storage, event sourcing and sharding |
| [31: Real-World Case Studies](ch31-real-world-case-studies.md) | Trace the structures inside Spanner, Dynamo, Kafka, Delta Lake and Cloudflare's edge cache |
| [32: Synthesis and Future Directions](ch32-synthesis-and-future-directions.md) | Place every structure in the book on one spectrum of trade-offs, and read new research with that map in hand |

**Before you start.** Volume I and the hash table and graph chapters of Volume II. Chapter 14 (probabilistic structures) and Chapter 16 (external memory) are used heavily in Chapters 29 to 31.
