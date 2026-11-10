# Chapter 2: Primitive Types and Memory Organization

## 2.1 The Building Blocks: Primitive Data Types

Every data structure ultimately decomposes into primitive types, fundamental units that the hardware directly supports. Understanding these types, their properties, and their cost is essential for effective data structure design.

### Boolean Type

The boolean type represents truth values. While conceptually just two states (true and false), implementation varies:

- **C/C++**: Typically stored as one byte, with 0 representing false and 1 representing true
- **Java**: Strictly one bit conceptually, but one byte in arrays
- **Python**: Full objects with True/False keywords
- **Hardware**: Boolean operations are fundamental CPU operations

Boolean operations (AND, OR, NOT, XOR) are typically constant-time hardware operations. However, boolean arrays (bitsets) can be significantly more space-efficient than boolean objects.

### Integer Types

Integer types represent whole numbers with various ranges:

| Type | Typical Size | Range (signed) | Range (unsigned) |
|------|--------------|----------------|------------------|
| byte | 8 bits | -128 to 127 | 0 to 255 |
| short | 16 bits | -32,768 to 32,767 | 0 to 65,535 |
| int | 32 bits | -2.1B to 2.1B | 0 to 4.3B |
| long | 64 bits | -9.2Q to 9.2Q | 0 to 18.4Q |

The "long" type illustrates how naming varies across languages:
- Java: long is always 64 bits
- C/C++: long may be 32 or 64 bits depending on platform
- Python: integers are arbitrary precision (bignums)

Integer overflow is a subtle source of bugs. In two's complement representation (virtually universal), adding 1 to the maximum value wraps to the minimum value. This has caused real-world bugs:

- Ariane 5 rocket explosion (1996): 64-bit to 16-bit conversion overflow
- Boeing 787 (2015): a 32-bit counter in the generator control units overflowed after 248 days of continuous power, which could shut down all AC power
- YouTube (2014): the view counter for "Gangnam Style" exceeded 2,147,483,647, the largest signed 32-bit integer

### Floating-Point Types

Floating-point numbers represent real numbers with limited precision:

| Type | Typical Size | Precision | Range |
|------|--------------|------------|-------|
| float | 32 bits | ~7 decimal digits | ±10^38 |
| double | 64 bits | ~15 decimal digits | ±10^308 |
| extended | 80 bits | ~19 decimal digits | Platform-dependent |

IEEE 754 standardizes floating-point representation:
- 1 bit: sign
- 8 bits: exponent (biased)
- 23 bits: mantissa (fraction)

This gives the familiar scientific notation: (-1)^sign × 1.mantissa × 2^(exponent − 127) for normal numbers. A 64-bit double has the same layout with an 11-bit exponent (bias 1023) and a 52-bit fraction.

Key considerations for data structures:
- Floating-point equality is problematic (0.1 + 0.2 ≠ 0.3)
- NaN (Not a Number) propagates through operations
- Infinity arithmetic has special rules
- Denormalized numbers provide gradual underflow

**Why 0.1 + 0.2 ≠ 0.3.** A double holds a 53-bit binary significand, and 1/10 has no finite binary expansion (0.0001100110011... in binary, repeating forever), so the literal `0.1` is rounded to the nearest double. `float.hex` and `decimal.Decimal` show exactly what is stored:

```python
from decimal import Decimal

for x in (0.1, 0.2, 0.3, 0.1 + 0.2):
    print(x.hex(), Decimal(x))
```

```
0x1.999999999999ap-4 0.1000000000000000055511151231257827021181583404541015625
0x1.999999999999ap-3 0.200000000000000011102230246251565404236316680908203125
0x1.3333333333333p-2 0.299999999999999988897769753748434595763683319091796875
0x1.3333333333334p-2 0.3000000000000000444089209850062616169452667236328125
```

The repeating hex digit 9 ends in a rounded-up `a`, so `0.1` and `0.2` are both stored slightly too large, while `0.3` is stored slightly too small. The exact sum of the two stored values is 0.3000000000000000166533453693773481063544750213623046875. Doubles between 0.25 and 0.5 are 2^−54 ≈ 5.55 × 10^−17 apart, and this sum lies exactly halfway between the double for `0.3` (significand ending in hex 3) and the next one up (ending in hex 4). IEEE 754's default rounding breaks ties toward the even significand, the one ending in 4, so `0.1 + 0.2` is one unit in the last place above `0.3`. Every step was correctly rounded; the inputs were never the decimal numbers they were written as. Compare with a tolerance (`math.isclose`), or compute in integers (cents, not dollars) or `decimal` when exact decimal results matter. Exercise 2.5 shows what the difference does to a hash table.

### Character Types

Characters represent text elements:

- **ASCII**: 7 bits (128 characters), includes control characters and basic Latin
- **Extended ASCII**: 8 bits (256 characters), various ISO-8859 pages
- **Unicode**: Variable-width, includes virtually all writing systems
- **UTF-8**: Variable 1-4 bytes, ASCII-compatible, dominant on the web
- **UTF-16**: 2 or 4 bytes, used in Java, Windows, JavaScript strings

The choice of character encoding affects string data structure design significantly.

## 2.2 Memory Organization and Addressing

Understanding how memory is organized helps in designing efficient data structures.

### Byte-Addressable Memory

Modern computers are byte-addressable: each byte has a unique address. Larger types (ints, floats) occupy multiple consecutive bytes.

The endianness question: which byte is stored at the lowest address?

- **Little-endian** (Intel, ARM): Least significant byte first
  - Value 0x01234567 stored as 67 45 23 01 at addresses 0,1,2,3
- **Big-endian** (Network order, some RISC): Most significant byte first
  - Value 0x01234567 stored as 01 23 45 67 at addresses 0,1,2,3

Mixed-endian architectures exist but are rare. The choice affects:
- Network protocol compatibility
- Binary file formats
- Debugging (hex dumps appear "reversed" on little-endian)
- Type punning through memory

### Alignment and Padding

Modern CPUs are optimized to access memory at aligned addresses. A 4-byte int should be at an address divisible by 4; an 8-byte double should be at an address divisible by 8.

When structures contain multiple types, compilers insert padding to maintain alignment:

```c
struct Example {
    char a;      // 1 byte, offset 0
    // 3 bytes padding
    int b;       // 4 bytes, offset 4
    char c;      // 1 byte, offset 8
    // 3 bytes padding (struct alignment is 4, from int)
};
// sizeof(Example) = 12 (on common 32- and 64-bit ABIs)
```

The #pragma pack directive and __attribute__((packed)) can eliminate padding, but at a cost: unaligned accesses may be slower or even cause hardware exceptions on some architectures.

### Stack vs. Heap Memory

Two primary memory regions exist for dynamic data:

**Stack:**
- Automatic memory management
- Fast allocation (just move stack pointer)
- Automatic deallocation (scope-based)
- Limited size (typically 1-8MB)
- Perfect for small, short-lived objects
- Local variables, function parameters, return addresses

**Heap:**
- Manual management (malloc/free, new/delete)
- Slower allocation (search for a free block, Section 2.5)
- Manual or garbage-collected deallocation
- Large size (limited by physical + virtual memory)
- Good for large or long-lived objects
- Dynamic data structures

The stack's speed comes from its simplicity: allocation is decrementing a pointer, deallocation is incrementing. However, the stack cannot grow indefinitely, and objects must have known lifetimes.

## 2.3 Pointers and References

Pointers are variables that store memory addresses. They are the fundamental mechanism for building dynamic, linked data structures.

### Pointer Basics

```c
int x = 42;
int *p = &x;     // p stores address of x
int y = *p;      // y = 42 (dereference p)
*p = 100;        // x = 100 (modify through pointer)
```

The pointer-to-pointer pattern allows modification of pointers themselves:

```c
void insert(Node **head, int value) {
    Node *new = malloc(sizeof(Node));
    new->data = value;
    new->next = *head;
    *head = new;
}
```

### Pointer Arithmetic

In C and C++, pointers can be incremented and decremented:

```c
int arr[5] = {10, 20, 30, 40, 50};
int *p = arr;        // Points to arr[0]
p++;                 // Points to arr[1]
int val = *(p + 2); // Value at arr[3] = 40
```

This arithmetic is scaled by the size of the pointed-to type. `p++` moves by sizeof(*p) bytes.

### Null Pointers

The null pointer represents "points to nothing." Its representation is implementation-defined but is typically address 0. Dereferencing null causes undefined behavior (usually a crash).

Modern C++ prefers nullptr over NULL (which is just 0, potentially ambiguous with integer 0). Java and Python use null or None for reference types.

### Reference Types

References (C++, and analogous concepts in other languages) are aliases to existing objects:

```cpp
int x = 42;
int &r = x;  // r is another name for x
r = 100;     // x = 100
```

Unlike pointers:
- References must be initialized
- References cannot be reseated
- References cannot be null
- Access syntax is cleaner (no dereference operator)

References provide the safety of not being null while maintaining the efficiency of pointer-based indirection.

## 2.4 Records and Structures

Records (called structs in C, classes in object-oriented languages) group related fields:

```c
struct Student {
    char name[50];
    int id;
    float gpa;
    struct Student *advisor;  // Pointer for linked structures
};
```

### Memory Layout

Structures are laid out sequentially in memory, with padding as needed for alignment. The programmer can control layout with pragmas or attributes:

```c
// Force tight packing (no padding)
struct PackedStudent {
    char name[50];
    int id;
    float gpa;
} __attribute__((packed));
```

### Bit Fields

C and C++ allow specifying field widths in bits:

```c
struct Flags {
    unsigned int is_signed : 1;
    unsigned int is_array  : 1;
    unsigned int size      : 6;  // 0-63
};
```

Bit fields pack multiple boolean or small-integer fields into single bytes. However, they have drawbacks:
- No addressable pointer to a bit field
- Layout is implementation-defined
- May be slower to access than full bytes

## 2.5 How malloc Works: Allocators as Data Structures

Section 2.2 described heap allocation as "search for a free block". That search is a data-structure problem in its own right. The allocator keeps a set of free address ranges and must answer two operations quickly: `malloc(n)`, "give me a range of at least n bytes", and `free(p)`, "the range starting at p is free again". Every linked structure in this book calls `malloc` once per node, so the allocator's costs show up inside all of them.

### The Problem

Three facts make this harder than it looks.

- **Sizes vary and frees arrive in any order.** A C or C++ allocator cannot move a live block, because the program holds raw pointers to it and the allocator cannot find them all to fix them up. (A compacting garbage collector can, which is why it doesn't have this problem.) So the free space breaks into holes between live blocks.
- **`free(p)` gets only a pointer.** The allocator must recover the block's size and find its neighbours from the address alone. Programs call `free` about as often as `malloc`, so this has to be O(1), not a search.
- **Memory is lost two ways.** *Internal fragmentation* is space inside an allocated block that the program didn't ask for: headers, alignment padding, rounding up to a size class. *External fragmentation* is free memory split into holes too small to use. Fill a 1 MiB heap with 1,024 blocks of 1 KiB and free every other one: 512 KiB is free, yet a 2 KiB request fails because no two free blocks are adjacent.

No placement policy avoids external fragmentation on every input. J. M. Robson showed in 1971 that for any allocator that never moves blocks, some sequence of requests forces the heap to exceed the live data by a factor that grows with the logarithm of the ratio between the largest and smallest block sizes. Allocators are therefore judged on real programs, not worst cases.

### Implicit Free Lists and Boundary Tags

The simplest design puts the bookkeeping in the heap itself. Each block starts with a one-word *header* holding the block's size. Sizes are multiples of the alignment (8 or 16 bytes on real systems), so the low bits of the size are always zero, and one of them stores an "allocated" flag. Starting from the first block and adding sizes walks every block in address order: the list is *implicit*, because the links are the sizes.

- `malloc(n)` walks the blocks until it finds a free one that is big enough. If the block is much bigger, it *splits* it: the front becomes the allocated block and the rest a new free block. It returns the address just past the header.
- `free(p)` reads the header one word before `p` to get the size. The next block's header is at the header plus the size, so checking whether the next block is free and merging with it (*coalescing*) is O(1).

The previous block is the hard part. Nothing in our header says where the previous block starts. Knuth's *boundary tag* fixes this: copy the tag into a *footer*, the last word of every block. The word just before our header is then the previous block's footer, which gives its size and state in O(1). With immediate coalescing on every `free`, the heap keeps one invariant: **no two free blocks are adjacent**.

The simulation below models the heap as a Python list of words. Sizes are in words and always even, so bit 0 of a tag is free to hold the allocated flag.

```python
class FreeListHeap:
    """Implicit free list with boundary tags, first fit and immediate coalescing.

    mem is the heap, one list entry per word. Every block is laid out as
    [header, payload..., footer], and header and footer both hold the tag
    size | used, where size counts the whole block in words and is always even.
    """
    MIN_BLOCK = 4                              # header + 2 payload words + footer

    def __init__(self, words):
        assert words % 2 == 0 and words >= self.MIN_BLOCK
        self.mem = [0] * words
        self._tag(0, words, 0)                 # one free block covers the heap

    def _tag(self, addr, size, used):
        self.mem[addr] = self.mem[addr + size - 1] = size | used

    def _size(self, i):                        # i is a header or footer word
        return self.mem[i] & ~1

    def _used(self, i):
        return self.mem[i] & 1

    def blocks(self):
        addr = 0
        while addr < len(self.mem):
            yield addr, self._size(addr), self._used(addr)
            addr += self._size(addr)

    def malloc(self, n):
        need = max(self.MIN_BLOCK, (n + 3) & ~1)   # n + header + footer, rounded up to even
        for addr, size, used in self.blocks():     # first fit: lowest address that fits
            if not used and size >= need:
                if size - need >= self.MIN_BLOCK:  # split; the tail stays free
                    self._tag(addr + need, size - need, 0)
                    size = need
                self._tag(addr, size, 1)
                return addr + 1                    # the pointer is the first payload word
        return None                                # no free block is big enough

    def free(self, p):
        addr = p - 1
        size = self._size(addr)
        nxt = addr + size
        if nxt < len(self.mem) and not self._used(nxt):   # next block's header
            size += self._size(nxt)
        if addr > 0 and not self._used(addr - 1):         # previous block's footer
            addr -= self._size(addr - 1)
            size += self._size(addr)
        self._tag(addr, size, 0)
```

A trace on a 24-word heap, writing blocks as `start:size` with U for used and F for free:

| Operation | Returns | Blocks afterwards | What happened |
|-----------|---------|-------------------|---------------|
| start | | 0:24 F | one free block |
| `p = malloc(3)` | 1 | 0:6 U, 6:18 F | 3 + 2 tags = 5, rounded up to 6; split |
| `q = malloc(5)` | 7 | 0:6 U, 6:8 U, 14:10 F | 5 + 2 = 7, rounded up to 8 |
| `r = malloc(2)` | 15 | 0:6 U, 6:8 U, 14:4 U, 18:6 F | exactly the minimum block |
| `free(p)` | | 0:6 F, 6:8 U, 14:4 U, 18:6 F | both neighbours used (there is no left one) |
| `free(r)` | | 0:6 F, 6:8 U, 14:10 F | header at 18 says free: merge right |
| `free(q)` | | 0:24 F | header at 14 and footer at 5 both say free: merge both ways |

After the three `malloc` calls the list `mem` begins `[7, 0, 0, 0, 0, 7, 9, ...]`: tag 7 is size 6 with the used bit set, and the same tag sits in word 0 (header) and word 5 (footer). Each block carries one word of internal fragmentation from rounding plus two words of tags.

**Cost.** `free` is O(1) worst case. `malloc` is O(B) worst case, where B is the number of blocks, allocated *and* free, because the walk steps over every allocated block too. The footer costs a word per block. Real allocators such as dlmalloc save it on allocated blocks: a free block keeps its footer, and each header carries a "previous block in use" bit, so the footer is only read when that bit says the previous block is free.

### Explicit Free Lists and Placement Policies

Walking allocated blocks is wasted work. An *explicit* free list threads a doubly linked list (Chapter 4) through the free blocks only, storing the `prev` and `next` pointers in the free block's payload, which nobody else is using. `malloc` now costs O(F) for F free blocks. `free` stays O(1): coalescing unlinks the free neighbours, which a doubly linked list does in O(1) given the node, and pushes the merged block. The price is a larger minimum block, header plus two pointers plus footer: 32 bytes on a 64-bit machine, so `malloc(1)` costs 32 bytes. Pushing freed blocks at the head (LIFO order) is O(1); keeping the list sorted by address costs O(F) per `free` but fragments less.

Which free block to choose is the *placement policy*:

- **First fit** takes the first block in the list that is big enough. With an address-ordered list, small leftover splinters collect at the low addresses and every search has to step over them.
- **Next fit** resumes the search where the previous one stopped. Searches are shorter, but allocations get scattered across the whole heap.
- **Best fit** takes the smallest block that is big enough, leaving the smallest leftover. On a plain list it scans all F blocks; with free blocks kept in a balanced tree or a trie keyed by size it costs O(log F).

Intuition says best fit should create many useless tiny leftovers. Measurements say otherwise: Johnstone and Wilson ("The Memory Fragmentation Problem: Solved?", 1998) replayed the allocation traces of real programs and found that best fit and address-ordered first fit both waste very little memory, while next fit does noticeably worse. Neither policy dominates on every input (Exercise 2.8 builds a case for each), and Knuth's *fifty-percent rule* says the search cost doesn't go away: in steady state under first fit there are about half as many free blocks as allocated ones.

### Segregated Free Lists and Size Classes

Every production allocator replaces the single list with an array of lists, one per *size class*. `malloc(n)` rounds n up to its class and pops the head of that list in O(1), falling back to a larger class or fresh memory only when the list is empty. Most programs allocate a small number of distinct sizes over and over, so the fast path hits almost every time.

The extreme form, *simple segregated storage*, gives each class its own pages carved into equal slots and never splits or coalesces. Objects then need no header at all: the allocator finds the size class from the page the address falls in. What it gives up is flexibility: memory parked in the free list of one class cannot serve a request for another.

- **dlmalloc** (Doug Lea, first released in 1987) is "in most ways a best-fit allocator", in its own documentation's words. Chunks under 256 bytes live in *small bins*, exact-size doubly linked lists 8 bytes apart, and larger free chunks live in bins covering ranges of sizes, kept as bitwise tries so the best fit is found quickly. Chunks carry Knuth's boundary tags. glibc's `malloc` (ptmalloc) is derived from it and added a per-thread cache, *tcache*, in glibc 2.26 (2017).
- **jemalloc** (Jason Evans, written for FreeBSD's libc) spaces its small size classes at four per doubling of size after the smallest ones: 16, 32, 48, ..., 128, then 160, 192, 224, 256, then 320, 384, 448, 512, and so on. Its manual states that this limits internal fragmentation to about 20% for all but the smallest classes: a 129-byte request gets a 160-byte slot and wastes 31 bytes, 19%. It runs several independent *arenas* (by default four per CPU) to cut lock contention, and gives each thread a cache of free objects so most requests need no synchronization at all.
- **tcmalloc** (Google, "thread-caching malloc") maps small requests to one of 60 to 80 size classes. Its front end is a cache per thread (the original design) or, in newer versions, per CPU. Behind it, each size class has a *transfer cache* and a *central free list* that carves objects out of *spans* of pages; requests above the largest class go straight to the page heap.

The thread or CPU cache matters as much as the size classes. A single free list behind one lock serializes every allocation in a multithreaded program. A thread-local list needs no lock and no atomic instruction; the cost is memory sitting idle in one thread's cache while another thread asks the operating system for more.

### The Buddy System

The buddy system trades internal fragmentation for very cheap coalescing. The managed space has 2^m units. Every block has a size 2^k (its *order* is k) and starts at a multiple of 2^k. There is one free list per order.

- **Allocate n units:** round up to the smallest order k with 2^k ≥ n. Take a free block of the smallest order j ≥ k that has one. While j > k, split it into two halves of order j − 1, keep the low half and put the high half on the free list. The two halves of a split are each other's *buddies*.
- **Free a block of order k at address a:** its buddy is at **a XOR 2^k**. Because a is a multiple of 2^k, bit k is the only bit that differs between the low and high halves of their parent, so flipping it gives the other half. If the buddy is free and still of order k, merge the two into the parent (which starts at `a` with bit k cleared) and repeat one order up.

No footers and no searching for neighbours: the address alone identifies the only block it can merge with.

```python
class BuddyAllocator:
    """Binary buddy system over addresses 0 .. 2**max_order - 1 (units, e.g. pages)."""

    def __init__(self, max_order):
        self.max_order = max_order
        self.free_lists = [set() for _ in range(max_order + 1)]  # order k -> free addresses
        self.free_lists[max_order].add(0)
        self.order_of = {}                     # allocated address -> order

    def alloc(self, n):
        k = max(0, (n - 1).bit_length())       # smallest k with 2**k >= n
        j = k
        while j <= self.max_order and not self.free_lists[j]:
            j += 1                             # smallest non-empty order that is big enough
        if j > self.max_order:
            return None
        addr = self.free_lists[j].pop()
        while j > k:                           # split, keep the low half, free the high half
            j -= 1
            self.free_lists[j].add(addr + (1 << j))
        self.order_of[addr] = k
        return addr

    def free(self, addr):
        k = self.order_of.pop(addr)
        while k < self.max_order:
            buddy = addr ^ (1 << k)            # flip bit k of the address
            if buddy not in self.free_lists[k]:
                break                          # buddy is allocated or split: stop merging
            self.free_lists[k].remove(buddy)
            addr &= ~(1 << k)                  # the merged block starts at the lower buddy
            k += 1
        self.free_lists[k].add(addr)
```

The free lists are sets here so that "is my buddy free?" and "remove my buddy" are O(1). The Linux kernel gets the same effect with doubly linked lists plus a flag and the order stored in each page's descriptor.

Trace on 64 units (`BuddyAllocator(6)`):

1. `A = alloc(5)` needs order 3 (8 units). Only order 6 is free, so 64 splits into 32 + 32, the low 32 into 16 + 16, the low 16 into 8 + 8. A = 0. Free: 8 at order 3, 16 at order 4, 32 at order 5.
2. `B = alloc(12)` needs order 4 and takes the free 16. B = 16.
3. `C = alloc(3)` needs order 2. Order 2 is empty, so the order-3 block at 8 splits into 4 + 4. C = 8, and 12 is free at order 2.
4. `free(A)`: the buddy of 0 at order 3 is 0 XOR 8 = 8. Block 8 is split (C lives in it), so there is no merge, and 0 goes on the order-3 list.
5. `free(C)`: buddy 8 XOR 4 = 12 is free, so merge into 8 at order 3. Buddy 8 XOR 8 = 0 is free at order 3, so merge into 0 at order 4. Buddy 0 XOR 16 = 16 is B, allocated, so stop. Free: 0 at order 4 and 32 at order 5.

<figure>
{{#include ../images/buddy-allocator.svg}}
<figcaption>The space after step 3, each block drawn above the addresses it covers: every split creates a pair of buddies, and the shaded part of each allocated block is what was asked for.</figcaption>
</figure>

**Cost.** Allocation and free are both O(m) worst case, one step per order, where m is log2 of the space size in units. The price is internal fragmentation: the three requests above total 20 units but occupy 28, 29% waste. Rounding up to a power of two wastes just under half the block in the worst case (a request of 2^k + 1 gets 2^(k+1)) and a quarter on average if request sizes are spread uniformly between consecutive powers of two. There is also external fragmentation the buddy rule cannot fix: two adjacent free blocks that are not buddies, such as free blocks at 12 and 16 in a 64-unit space, can never merge.

Kenneth Knowlton described the binary buddy system in "A Fast Storage Allocator" (CACM, 1965). The Linux kernel's page allocator is a buddy allocator over physical page frames: it keeps free lists per order in each memory zone (`/proc/buddyinfo` prints how many free blocks of each order there are), finds a buddy by XORing the page frame number with `1 << order`, and by default goes up to order 10, blocks of 1,024 pages, which is 4 MiB with 4 KiB pages.

### Slab Allocation

Jeff Bonwick's slab allocator ("The Slab Allocator: An Object-Caching Kernel Memory Allocator", USENIX 1994, written for the SunOS 5.4 kernel) starts from an observation about kernels: they allocate a few kinds of fixed-size objects (inodes, process descriptors, network buffers) over and over, and initializing an object often costs more than allocating it.

- There is a **cache** per object type. A cache owns **slabs**: one or more contiguous pages, obtained from the page allocator, cut into equal-size objects, with a free list of the objects in each slab.
- Allocation pops an object from a partially full slab, and free pushes it back. Both are O(1). Objects have no headers, and there is no external fragmentation inside a slab: the only waste is the leftover tail of the slab that is too small for another object.
- Freed objects keep their *constructed* state (initialized locks, list heads), so the constructor runs once when the slab is created, not on every allocation. When memory runs short, completely free slabs go back to the page allocator.
- *Slab colouring* starts the objects in different slabs at slightly different offsets, so the same field of different objects doesn't always land in the same CPU cache sets.

This is segregated storage with one class per type, layered on top of the buddy allocator. Linux had three implementations: SLAB (following Bonwick's design), SLOB (for very small systems) and SLUB (Christoph Lameter, merged in 2007), which is simpler and keeps its per-slab metadata in the page descriptor. SLOB was removed in Linux 6.4 and SLAB in 6.8 (2024), so SLUB is now the only one. `kmalloc` serves general requests from caches named by size (`kmalloc-32`, `kmalloc-64`, `kmalloc-96`, ...), which you can see in `/proc/slabinfo`. Memcached's slab classes (Chapter 29) apply the same idea in user space.

### Arenas and Bump Allocation

When many objects die at the same time, the allocator doesn't need to track them individually at all. An *arena* (or *region*) is a large chunk with a pointer `top` to its first unused byte. Allocation rounds `top` up to the required alignment (Section 2.2), returns it, and advances it. There is no per-object free. Instead, `reset` frees everything at once by setting `top` back to the start.

```python
class Arena:
    """Bump allocator over one chunk of `size` bytes; offsets stand in for addresses."""

    def __init__(self, size):
        self.size, self.top = size, 0

    def alloc(self, n, align=8):               # align must be a power of two
        start = (self.top + align - 1) & -align    # round up to a multiple of align
        if start + n > self.size:
            return None                        # a real arena would chain a new chunk
        self.top = start + n
        return start

    def reset(self):
        self.top = 0                           # frees every object at once
```

Both operations are O(1) worst case and take a handful of instructions; a real arena that chains chunks frees them all on reset. Objects allocated together sit next to each other, which helps the cache. The stack of Section 2.2 is a bump allocator whose frees must come in LIFO order.

Arenas fit any workload with phases. Compilers put the syntax tree and intermediate code for a compilation unit in arenas (LLVM's `BumpPtrAllocator`, GCC's obstacks). Servers give each request a pool that is discarded when the response is sent (Apache's APR pools, PostgreSQL's memory contexts, which are reset at the end of a query). Game engines allocate per-frame scratch data from an arena that is reset every frame. The cost is that memory is not reused until reset, and one long-lived object in an arena keeps the whole arena alive; a pointer kept past a reset points into memory that the next phase will overwrite.

### Testing the Simulations

An allocator bug usually shows up far from its cause, as one object silently overwriting another. The simulations above can be checked directly: after every operation of a long random sequence, assert that the blocks tile the space exactly, that no two live allocations overlap, that the allocator agrees with the test about which blocks are live, and that no two free blocks could still be merged. For the free list, a brute-force first fit also predicts every `malloc` result.

```python
import random


def assert_disjoint(intervals):
    intervals = sorted(intervals)
    for (s1, e1), (s2, e2) in zip(intervals, intervals[1:]):
        assert e1 <= s2, "two live allocations overlap"


def check_free_list(h, live):
    """live maps each pointer the test holds to the number of words it asked for."""
    end, prev_free, found = 0, False, {}
    for addr, size, used in h.blocks():
        assert h.mem[addr] == h.mem[addr + size - 1], "header and footer disagree"
        if used:
            found[addr + 1] = size - 2         # payload capacity
        else:
            assert not prev_free, "two adjacent free blocks"
        prev_free = not used
        end = addr + size
    assert end == len(h.mem), "blocks do not tile the heap"
    assert found.keys() == live.keys()
    assert all(found[p] >= n for p, n in live.items())
    assert_disjoint((p, p + n) for p, n in live.items())


def first_fit_reference(h, n):
    need = max(h.MIN_BLOCK, (n + 3) & ~1)
    return next((a + 1 for a, s, u in h.blocks() if not u and s >= need), None)


def check_buddy(b, live):
    blocks = sorted([(a, k) for k, s in enumerate(b.free_lists) for a in s]
                    + list(b.order_of.items()))
    pos = 0
    for addr, k in blocks:
        assert addr == pos and addr % (1 << k) == 0, "blocks do not tile the space"
        pos += 1 << k
    assert pos == 1 << b.max_order
    for k, s in enumerate(b.free_lists[:-1]):
        assert all(a ^ (1 << k) not in s for a in s), "free buddies not merged"
    assert b.order_of.keys() == live.keys()
    assert all(1 << b.order_of[a] >= n for a, n in live.items())
    assert_disjoint((a, a + n) for a, n in live.items())


random.seed(1)
for trial in range(200):
    h, b = FreeListHeap(256), BuddyAllocator(8)
    live_h, live_b = {}, {}
    for step in range(300):
        if live_h and random.random() < 0.45:
            p = random.choice(list(live_h))
            h.free(p)
            del live_h[p]
        else:
            n = random.randint(1, 40)
            expect = first_fit_reference(h, n)
            p = h.malloc(n)
            assert p == expect
            if p is not None:
                live_h[p] = n
        if live_b and random.random() < 0.45:
            a = random.choice(list(live_b))
            b.free(a)
            del live_b[a]
        else:
            n = random.randint(1, 70)
            a = b.alloc(n)
            if a is not None:
                live_b[a] = n
        check_free_list(h, live_h)
        check_buddy(b, live_b)
    for p in list(live_h):
        h.free(p)
    for a in list(live_b):
        b.free(a)
    assert list(h.blocks()) == [(0, 256, 0)]       # everything coalesced back
    assert b.free_lists[8] == {0}
print("all invariants held")
```

## 2.6 Type Systems and Generic Programming

Modern languages provide mechanisms for writing data structures that work with arbitrary types.

### Templates (C++)

```cpp
template<typename T>
class Stack {
    std::vector<T> data;
public:
    void push(const T& item) { data.push_back(item); }
    T pop() { T item = data.back(); data.pop_back(); return item; }
};
```

Templates are resolved at compile-time, producing zero runtime overhead for type checking.

### Generics (Java, C#)

```java
public class Stack<T> {
    private ArrayList<T> data = new ArrayList<>();
    public void push(T item) { data.add(item); }
    public T pop() { return data.remove(data.size() - 1); }
}
```

Java generics use type erasure, they exist only at compile time, with runtime types being just Object.

### Python Duck Typing

Python uses dynamic typing with duck typing ("if it walks like a duck..."):

```python
class Stack:
    def __init__(self):
        self.data = []
    def push(self, item):
        self.data.append(item)
    def pop(self):
        return self.data.pop()
```

Any object with append() and pop() works with this Stack. This flexibility comes at the cost of runtime type checking.

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**2.1 ★ Two's complement by hand.** Work in 8 bits.

(a) Write the bit patterns of −1, −5 and −128.

(b) A signed 8-bit variable holds 127 and you add 1. What value does it hold now, assuming the hardware simply wraps?

(c) An unsigned 8-bit variable holds 200 and you add 100. What does it hold?

(d) What is −(−128) in signed 8-bit arithmetic?

<details>
<summary>Solution</summary>

In two's complement, −x is formed by inverting the bits of x and adding 1. Equivalently, an 8-bit pattern with value v as an unsigned number means v − 256 as a signed number whenever the top bit is set.

**(a)**
- −1: invert 00000001 → 11111110, add 1 → **11111111** (255 unsigned).
- −5: invert 00000101 → 11111010, add 1 → **11111011** (251 unsigned).
- −128: **10000000** (128 unsigned). It is its own pattern; there is no +128 in 8 bits.

**(b)** 127 is 01111111. Adding 1 gives 10000000, which reads as **−128**. This is the wraparound from Section 2.1. (In C, signed overflow is formally undefined behavior, so the compiler is allowed to assume it never happens. Wrapping is what the hardware does, not a promise the language makes.)

**(c)** 200 + 100 = 300 = 256 + 44. Unsigned arithmetic is defined to wrap modulo 256, so the result is **44**.

**(d)** Invert 10000000 → 01111111, add 1 → 10000000, which is **−128** again. The range −128..127 is asymmetric, so negating the minimum value overflows. This is why `abs(INT_MIN)` is a classic bug.

</details>

**2.2 ★ Which byte comes first?** The 32-bit value 0xDEADBEEF is stored at address 0x100.

(a) List the bytes at addresses 0x100, 0x101, 0x102, 0x103 on a little-endian machine and on a big-endian machine.

(b) A program reads the single byte at 0x100 to "check the low byte" of the value. On which machine does it get 0xEF?

<details>
<summary>Solution</summary>

**(a)**

| Address | Little-endian | Big-endian |
|---------|---------------|------------|
| 0x100 | EF | DE |
| 0x101 | BE | AD |
| 0x102 | AD | BE |
| 0x103 | DE | EF |

Little-endian puts the least significant byte (0xEF) at the lowest address; big-endian puts the most significant byte (0xDE) there.

**(b)** Only on the little-endian machine. On big-endian the same read returns 0xDE, the high byte. Code that reads part of a value through a narrower pointer (type punning, Section 2.2) silently changes meaning between the two. You can confirm the layouts in Python with `struct.pack('<I', 0xDEADBEEF)` (bytes `ef be ad de`) and `struct.pack('>I', 0xDEADBEEF)` (bytes `de ad be ef`).

</details>

**2.3 ★★ Layout and reordering.** Assume a typical 64-bit platform: `char` is 1 byte, `int` is 4 bytes aligned to 4, `double` is 8 bytes aligned to 8.

```c
struct Record {
    char   a;
    double b;
    char   c;
    int    d;
};
```

(a) Give the offset of each field and `sizeof(struct Record)`.

(b) Reorder the fields to make the struct as small as possible. What is the new size?

(c) If you store 10 million records in an array, how much memory does the reordering save?

<details>
<summary>Hint</summary>

Each field goes at the next offset that is a multiple of its alignment, and the total size is rounded up to a multiple of the largest alignment in the struct, so that every element of an array of these structs is aligned too.

</details>

<details>
<summary>Solution</summary>

**(a)**

| Field | Size | Offset | Padding before it |
|-------|------|--------|-------------------|
| a | 1 | 0 | 0 |
| b | 8 | 8 | 7 |
| c | 1 | 16 | 0 |
| d | 4 | 20 | 3 |

The fields end at byte 24, which is already a multiple of 8, so `sizeof(struct Record)` = **24**. Only 14 of those bytes are data.

**(b)** Sort by decreasing alignment: `double b; int d; char a; char c;`. Offsets are 0, 8, 12, 13, the fields end at 14, and the size rounds up to the next multiple of 8: **16**.

**(c)** 10,000,000 × (24 − 16) = 80,000,000 bytes, about 80 MB, saved by moving lines of source code around. The data didn't change at all. (Checked with `gcc` on x86-64: 24 and 16. The same rule explains the `struct Example` in Section 2.2: `char`, `int`, `char` has size 12, because its largest alignment is 4.)

</details>

**2.4 ★★ Pointer arithmetic trace.** Assume `int` is 4 bytes and `arr` starts at address 0x2000.

```c
int arr[6] = {10, 20, 30, 40, 50, 60};
int *p = arr + 1;
int *q = p + 3;
printf("%d %d %ld\n", *p, *(q - 1), (long)(q - p));
p += 2;
*p = *q + 1;
```

(a) What does the `printf` print?

(b) What address does `q` hold?

(c) What is the contents of `arr` at the end?

<details>
<summary>Solution</summary>

Pointer arithmetic counts in elements, not bytes (Section 2.3): `p + k` moves k × sizeof(int) = 4k bytes.

- `p = arr + 1` points at `arr[1]` (20).
- `q = p + 3` points at `arr[4]` (50).

**(a)** `*p` is 20. `*(q - 1)` is `arr[3]`, which is 40. `q - p` is measured in elements: 4 − 1 = 3. Output: `20 40 3`.

**(b)** `q` is `arr + 4`, so 0x2000 + 4 × 4 = **0x2010**.

**(c)** `p += 2` moves `p` to `arr[3]`. Then `*p = *q + 1` stores `arr[4] + 1` = 51 into `arr[3]`. Final contents: `{10, 20, 30, 51, 50, 60}`.

</details>

**2.5 ★★ Floats as keys.** Run this in CPython:

```python
d = {}
d[0.1 + 0.2] = "a"
print(0.3 in d)

nan = float("nan")
s = {nan}
print(nan in s, float("nan") in s)

print(sorted([3.0, float("nan"), 1.0, 2.0]))
```

It prints:

```
False
True False
[3.0, nan, 1.0, 2.0]
```

Explain each line, and state what rule a data structure that stores floating-point keys should follow.

<details>
<summary>Hint</summary>

A hash table finds a key by hashing it and then testing equality; a sort assumes that `<` defines a consistent order. Check what each of those assumptions does with 0.1 + 0.2 and with NaN.

</details>

<details>
<summary>Solution</summary>

**Line 1: `False`.** 0.1 + 0.2 evaluates to 0.30000000000000004, a different double from 0.3. The dict compares keys exactly, so the lookup misses. This is the "0.1 + 0.2 ≠ 0.3" problem from Section 2.1 turning into a missing record.

**Line 2: `True False`.** NaN is not equal to anything, including itself (`nan == nan` is `False`). Python's containers check identity before equality (`x is e or x == e`), so the same NaN object is found. A different NaN object hashes and compares as a stranger, so it is never found. A set can even hold many "NaN" entries that all print the same.

**Line 3: unsorted output.** Every comparison against NaN (`<`, `>`, `==`) is `False`, so `<` is no longer a consistent total order and the sort's assumptions break. Here the sort ends up returning its input unchanged. The exact result depends on the algorithm and the input order, which is the real problem: the output is not sorted and nothing raises an error.

**Rule:** don't use raw floats as exact keys for hashing or ordering unless every key comes from the same exact computation. Round or quantize to a fixed precision (or store integers, such as cents instead of dollars), and reject or canonicalize NaN before it enters a hash table, a sorted array or a search tree.

</details>

**2.6 ★★★ Pack 100 million flags.** You need to store 100 million records of the `struct Flags` from Section 2.4 (`is_signed` 1 bit, `is_array` 1 bit, `size` 6 bits).

(a) Compare the memory used by three layouts: a struct of three `int` fields, the bit-field struct (assume its container is one 4-byte `unsigned int`), and one byte per record in a byte array.

(b) Implement the byte layout in Python: `pack(is_signed, is_array, size)` returns an int in 0..255 with `is_signed` in bit 0, `is_array` in bit 1 and `size` in bits 2 to 7; `unpack(b)` returns the three fields; `set_size(b, size)` returns `b` with only the `size` field changed.

(c) Why can't C give you a pointer to a bit field, and what must the compiler emit for `f.size = 9`?

<details>
<summary>Hint</summary>

For (b), a field of width w starting at bit k is `(b >> k) & ((1 << w) - 1)`. To overwrite it, clear those bits with an inverted mask first.

</details>

<details>
<summary>Solution</summary>

**(a)**

| Layout | Bytes per record | 100 million records |
|--------|------------------|---------------------|
| Three `int` fields | 12 | 1.2 GB |
| Bit-field struct | 4 | 400 MB |
| One byte each | 1 | 100 MB |

The three fields need only 8 bits, so the byte layout is optimal, and 12× smaller than the naive struct. The bit-field struct wastes 3 of its 4 bytes because its storage unit is the `unsigned int` the fields were declared with.

**(b)**

```python
SIZE_SHIFT = 2
SIZE_MASK = 0x3F            # 6 bits


def pack(is_signed, is_array, size):
    assert is_signed in (0, 1) and is_array in (0, 1) and 0 <= size <= SIZE_MASK
    return is_signed | (is_array << 1) | (size << SIZE_SHIFT)


def unpack(b):
    return b & 1, (b >> 1) & 1, (b >> SIZE_SHIFT) & SIZE_MASK


def set_size(b, size):
    assert 0 <= size <= SIZE_MASK
    cleared = b & ~(SIZE_MASK << SIZE_SHIFT) & 0xFF   # zero bits 2..7, keep bits 0..1
    return cleared | (size << SIZE_SHIFT)


records = bytearray(100)            # 100 million in the real thing: 100 MB
records[3] = pack(1, 0, 9)
assert records[3] == 0b00100101     # size 9 = 001001, then is_array 0, is_signed 1
assert unpack(records[3]) == (1, 0, 9)
records[3] = set_size(records[3], 42)
assert unpack(records[3]) == (1, 0, 42)
```

**(c)** Memory is byte-addressable (Section 2.2): an address names a byte, not a bit, so there is no address for "bits 2 to 7 of this byte". For the same reason the hardware cannot write 6 bits in place. `f.size = 9` becomes a read-modify-write: load the containing word, AND it with a mask that clears the field, OR in `9 << shift`, store the word back. That is exactly `set_size` above. It costs a few extra instructions per access, and in concurrent code the read-modify-write also rewrites the neighbouring fields, so two threads updating different bit fields of the same word can lose each other's writes.

</details>

**2.7 ★★ Buddy allocation by hand.** A buddy allocator manages 64 units, all free. It receives `P = alloc(7)`, `Q = alloc(20)`, `R = alloc(2)`, `S = alloc(9)`, in that order, and splits as in Section 2.5 (keep the low half, free the high half).

(a) Give the address and block size of P, Q, R and S, and list the free blocks afterwards.

(b) How many units are lost to internal fragmentation?

(c) Now `free(R)`. Compute each buddy address the allocator checks, say which merges happen, and give the free blocks afterwards.

<details>
<summary>Solution</summary>

**(a)** P needs order 3 (8 units). The only free block is 0..63, which splits into 32 + 32, then 16 + 16, then 8 + 8: **P = 0** (size 8), leaving free blocks 8 (order 3), 16 (order 4) and 32 (order 5). Q needs order 5 and takes **Q = 32** (size 32). R needs order 1 (2 units); orders 1 and 2 are empty, so the order-3 block at 8 splits into 4 + 4 and the low 4 into 2 + 2: **R = 8** (size 2), leaving 10 free at order 1 and 12 free at order 2. S needs order 4 and takes **S = 16** (size 16). Free afterwards: **10 (2 units) and 12 (4 units)**.

**(b)** The requests total 7 + 20 + 2 + 9 = 38 units and the blocks total 8 + 32 + 2 + 16 = 58, so **20 units** (34% of the allocated space) are internal fragmentation.

**(c)** R is at 8 with order 1. Buddy 8 XOR 2 = **10** is free at order 1: merge into 8 at order 2. Buddy 8 XOR 4 = **12** is free at order 2: merge into 8 at order 3. Buddy 8 XOR 8 = **0** is P, which is allocated: stop. Free afterwards: **one block of 8 units at 8**. Running the `BuddyAllocator` of Section 2.5 on the same calls gives the same addresses.

</details>

**2.8 ★★ No policy wins everywhere.** A heap has two free blocks: 20 words at address 0 and 15 words at address 100. Ignore headers and minimum sizes, so a request of n words takes exactly n words from the front of the chosen block.

(a) The requests are 15, then 20. Show that first fit fails and best fit succeeds.

(b) The requests are 10, 10, then 15. Show that best fit fails and first fit succeeds.

(c) What does this mean for choosing a policy?

<details>
<summary>Solution</summary>

**(a)** First fit gives the 15 to the first block that fits, the 20-word block at 0, leaving free blocks of 5 and 15. The request for 20 then fails. Best fit gives the 15 to the 15-word block, an exact fit, so the 20-word block is still whole and the second request succeeds.

**(b)** First fit: 10 from the 20-word block (free: 10 and 15), 10 more from it (free: 0 and 15), then 15 from the 15-word block. All succeed. Best fit: the first 10 goes to the smaller block that fits, the 15 (free: 20 and 5), the second 10 goes to the 20 (free: 10 and 5), and the 15 fails although 15 words are free in total.

**(c)** Each policy has inputs on which it fails while the other succeeds, so neither dominates, consistent with Robson's lower bound that some sequence defeats every non-moving allocator. Policies are compared on traces of real programs, where best fit and address-ordered first fit both do well.

</details>

**2.9 ★★ Arena alignment and reset.** Use the `Arena` class from Section 2.5 with a 64-byte chunk.

(a) Allocate, in order, (size, alignment) = (1, 1), (8, 8), (2, 2), (4, 4), (16, 16), (1, 1). Give each offset, the final `top`, and the bytes lost to padding.

(b) Find an order for the same six requests that wastes no padding.

(c) A request handler keeps the offset of the 16-byte object in a global variable, the arena is reset, and the next request allocates (16, 16) and writes to it. What does the stale offset now refer to?

<details>
<summary>Hint</summary>

`(top + align - 1) & -align` rounds `top` up to the next multiple of `align`. This is the same rule as struct padding in Exercise 2.3.

</details>

<details>
<summary>Solution</summary>

**(a)**

| Request | `top` before | Offset | Padding |
|---------|--------------|--------|---------|
| (1, 1) | 0 | 0 | 0 |
| (8, 8) | 1 | 8 | 7 |
| (2, 2) | 16 | 16 | 0 |
| (4, 4) | 18 | 20 | 2 |
| (16, 16) | 24 | 32 | 8 |
| (1, 1) | 48 | 48 | 0 |

Final `top` is **49**. The objects total 32 bytes and **17 bytes** are padding.

**(b)** Decreasing alignment: (16, 16), (8, 8), (4, 4), (2, 2), (1, 1), (1, 1) land at offsets 0, 16, 24, 28, 30, 31 and `top` ends at **32**, no padding. Each object ends on a multiple of the next object's alignment, the same reason sorting struct fields by decreasing alignment works.

**(c)** After `reset`, `top` is 0 and the next request lays out its objects from offset 0 again, so its (16, 16) object lands at offset 0. Offset 32 now belongs to whatever object of the new request covers byte 32, or to unallocated space if the request uses less. Reads through the stale offset see another request's data and writes corrupt it, and nothing detects it. This is the arena form of use-after-free, and the reason an arena-allocated object must not outlive the phase its arena belongs to.

</details>

---

## Where this connects

- [Chapter 3: Arrays—The Foundation of Contiguous Storage](ch03-arrays-the-foundation-of-contiguous-storage.md). The first structure built directly on this memory model
- [Chapter 16: External Memory and Cache-Oblivious Structures](../volume-3/ch16-external-memory-and-cache-oblivious-structures.md). What the memory hierarchy does to these assumptions
- [Chapter 29: System Design as Data Structure Composition](../volume-5/ch29-system-design-as-data-structure-composition.md). Memcached's slab classes, the size-class idea of Section 2.5 applied to a cache
