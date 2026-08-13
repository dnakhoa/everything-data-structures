# Chapter 16: External Memory and Cache-Oblivious Structures

## 16.1 The Memory Hierarchy

Modern computers have multiple levels of memory:
- L1 cache: ~32KB, ~1ns
- L2 cache: ~256KB, ~4ns
- L3 cache: ~8MB, ~15ns
- Main memory: ~64GB, ~100ns
- SSD: ~100GB, ~100μs
- Hard disk: ~TB, ~10ms

## 16.2 External Memory Model

The I/O model accounts for disk access:
- B: Block size (elements per block)
- M: Internal memory size
- D: Disk access time relative to memory

Goal: Minimize block transfers.

## 16.3 Cache-Oblivious Structures

Cache-oblivious structures perform well at all cache levels without tuning:

**van Emde Boas Layout:**
```
Recursively divide at mid-level:

       ┌───────────────┐
       │       ○       │
       ├───────┬───────┤
       │   ○   │   ○   │
       ├───┬───┼───┬───┤
       │ ○ │ ○ │ ○ │ ○ │
       └───┴───┴───┴───┘
```
