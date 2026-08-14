# Bibliography and Further Reading

## Classic Textbooks

1. Knuth, D. E. (1997). *The Art of Computer Programming, Volume 1: Fundamental Algorithms* (3rd ed.). Addison-Wesley.

2. Knuth, D. E. (1998). *The Art of Computer Programming, Volume 3: Sorting and Searching* (2nd ed.). Addison-Wesley.

3. Cormen, T. H., Leiserson, C. E., Rivest, R. L., & Stein, C. (2022). *Introduction to Algorithms* (4th ed.). MIT Press.

4. Sedgewick, R., & Wayne, K. (2011). *Algorithms* (4th ed.). Addison-Wesley.

5. Okasaki, C. (1998). *Purely Functional Data Structures*. Cambridge University Press.

6. Tarjan, R. E. (1983). *Data Structures and Network Algorithms*. SIAM.

7. Morin, P. (2013). *Open Data Structures*. Athabasca University Press. Freely available at [opendatastructures.org](https://opendatastructures.org).

## By Level

| Book | Author | Level |
|------|--------|-------|
| Open Data Structures | Morin | Introductory (free) |
| Algorithms (4th ed.) | Sedgewick & Wayne | Introductory |
| Introduction to Algorithms | CLRS | Foundational |
| Guide to Competitive Programming | Laaksonen | Intermediate |
| Competitive Programming Handbook | Halim & Halim | Intermediate |
| The Art of Computer Programming, Vol. 4A | Knuth | Advanced |
| Compact Data Structures | Navarro | Research |
| Purely Functional Data Structures | Okasaki | Research |
| The Art of Multiprocessor Programming | Herlihy & Shavit | Research (concurrency) |

## Foundational Papers

**Trees and search structures**

- Adelson-Velsky, G., & Landis, E. (1962). An algorithm for the organization of information. *Soviet Mathematics Doklady*, 3, 1259–1263. *(AVL trees)*
- Bayer, R., & McCreight, E. (1972). Organization and maintenance of large ordered indexes. *Acta Informatica*, 1(3), 173–189. *(B-trees)*
- Guibas, L. J., & Sedgewick, R. (1978). A dichromatic framework for balanced trees. *FOCS*. *(Red-black trees)*
- Sleator, D. D., & Tarjan, R. E. (1985). Self-adjusting binary search trees. *Journal of the ACM*, 32(3), 652–686. *(Splay trees)*
- Pugh, W. (1990). Skip lists: A probabilistic alternative to balanced trees. *Communications of the ACM*, 33(6), 668–676.
- Seidel, R., & Aragon, C. R. (1996). Randomized search trees. *Algorithmica*, 16(4/5), 464–497. *(Treaps)*

**Heaps and priority queues**

- Williams, J. W. J. (1964). Algorithm 232: Heapsort. *Communications of the ACM*, 7(6), 347–348.
- Fredman, M. L., & Tarjan, R. E. (1987). Fibonacci heaps and their uses in improved network optimization algorithms. *Journal of the ACM*, 34(3), 596–615.
- Fredman, M. L., Sedgewick, R., Sleator, D. D., & Tarjan, R. E. (1986). The pairing heap. *Algorithmica*, 1(1), 111–129.

**Hashing and probabilistic structures**

- Bloom, B. H. (1970). Space/time trade-offs in hash coding with allowable errors. *Communications of the ACM*, 13(7), 422–426.
- Carter, J. L., & Wegman, M. N. (1979). Universal classes of hash functions. *JCSS*, 18(2), 143–154.
- Pagh, R., & Rodler, F. F. (2004). Cuckoo hashing. *Journal of Algorithms*, 51(2), 122–144.
- Cormode, G., & Muthukrishnan, S. (2005). An improved data stream summary: The count-min sketch. *Journal of Algorithms*, 55(1), 58–75.
- Flajolet, P., Fusy, É., Gandouet, O., & Meunier, F. (2007). HyperLogLog: The analysis of a near-optimal cardinality estimation algorithm. *AOFA*.

**Spatial structures**

- Finkel, R. A., & Bentley, J. L. (1974). Quad trees: A data structure for retrieval on composite keys. *Acta Informatica*, 4(1), 1–9.
- Bentley, J. L. (1975). Multidimensional binary search trees used for associative searching. *Communications of the ACM*, 18(9), 509–517. *(KD-trees)*
- Guttman, A. (1984). R-trees: A dynamic index structure for spatial searching. *SIGMOD*.
- Malkov, Y. A., & Yashunin, D. A. (2016). Efficient and robust approximate nearest neighbor search using HNSW graphs. *arXiv:1603.09320*.

**Persistence and functional structures**

- Driscoll, J. R., Sarnak, N., Sleator, D. D., & Tarjan, R. E. (1986). Making data structures persistent. *STOC*.
- Okasaki, C. (1996). *Purely Functional Data Structures* (PhD thesis). Carnegie Mellon University.
- Bagwell, P. (2001). Ideal hash trees. *EPFL Technical Report*. *(HAMTs)*

**Concurrency**

- Lamport, L. (1979). How to make a multiprocessor computer that correctly executes multiprocess programs. *IEEE Transactions on Computers*, C-28(9), 690–691.
- Herlihy, M., & Wing, J. (1990). Linearizability: A correctness condition for concurrent objects. *TOPLAS*, 12(3), 463–492.
- Herlihy, M. (1991). Wait-free synchronization. *TOPLAS*, 13(1), 124–149.
- Michael, M. M., & Scott, M. L. (1996). Simple, fast, and practical non-blocking and blocking concurrent queue algorithms. *PODC*.
- Michael, M. M. (2004). Hazard pointers: Safe memory reclamation for lock-free objects. *IEEE TPDS*, 15(6), 491–504.

**External memory and cache-obliviousness**

- Aggarwal, A., & Vitter, J. S. (1988). The input/output complexity of sorting and related problems. *Communications of the ACM*, 31(9), 1116–1127.
- Frigo, M., Leiserson, C. E., Prokop, H., & Ramachandran, S. (1999). Cache-oblivious algorithms. *FOCS*.
- O'Neil, P., Cheng, E., Gawlick, D., & O'Neil, E. (1996). The log-structured merge-tree (LSM-tree). *Acta Informatica*, 33(4), 351–385.

**Succinct and compressed structures**

- Jacobson, G. (1989). Space-efficient static trees and graphs. *FOCS*.
- Munro, J. I., & Raman, V. (1997). Succinct representation of balanced parentheses, static trees and planar graphs. *FOCS*.
- Ferragina, P., & Manzini, G. (2000). Opportunistic data structures with applications. *FOCS*. *(FM-index)*
- Raman, R., Raman, V., & Rao, S. S. (2002). Succinct indexable dictionaries. *SODA*.
- Grossi, R., Gupta, A., & Vitter, J. S. (2003). High-order entropy-compressed text indexes. *SODA*. *(Wavelet trees)*

**Distributed structures**

- Karger, D., et al. (1997). Consistent hashing and random trees. *STOC*.
- Stoica, I., et al. (2001). Chord: A scalable peer-to-peer lookup service. *SIGCOMM*.
- Holm, J., de Lichtenberg, K., & Thorup, M. (2001). Poly-logarithmic deterministic fully-dynamic algorithms. *Journal of the ACM*, 48(4), 723–760.
- DeCandia, G., et al. (2007). Dynamo: Amazon's highly available key-value store. *SOSP*.
- Shapiro, M., Preguiça, N., Baquero, C., & Zawirski, M. (2011). Conflict-free replicated data types. *SSS*.
- Corbett, J. C., et al. (2012). Spanner: Google's globally-distributed database. *OSDI*.
- Kleppmann, M., & Beresford, A. R. (2017). A conflict-free replicated JSON datatype. *IEEE TPDS*, 28(10), 2733–2746.

**Learned and emerging**

- Kraska, T., Beutel, A., Chi, E. H., Dean, J., & Polyzotis, N. (2018). The case for learned index structures. *SIGMOD*.
- Ferragina, P., & Vinciguerra, G. (2020). The PGM-index. *VLDB*, 13(8), 1162–1175.

## Competitive Programming Resources

| Resource | Focus |
|----------|-------|
| [CP-Algorithms](https://cp-algorithms.com) | Implementation guides with proofs |
| [AtCoder Library](https://atcoder.github.io/ac-library/) | Reference implementations in C++ |
| [USACO Guide](https://usaco.guide) | Structured curriculum by difficulty |
| [Codeforces](https://codeforces.com) | Problems, editorials, and blog posts |
| Stanford ICPC Notebook | Competition templates |

## Online Resources

- [Visualgo](https://visualgo.net). Step-through animations of most structures in this book
- [Open Data Structures](https://opendatastructures.org). Pat Morin's free textbook, with code in several languages
- [Big-O Cheat Sheet](https://www.bigocheatsheet.com). Quick complexity reference
- [GeeksforGeeks](https://www.geeksforgeeks.org). Implementation tutorials; verify against a primary source
- [Papers We Love](https://paperswelove.org). Curated CS papers with discussion
