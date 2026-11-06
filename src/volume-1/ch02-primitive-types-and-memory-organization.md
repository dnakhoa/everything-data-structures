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

This gives the familiar scientific notation: (-1)^sign × 1.mantissa × 2^exponent

Key considerations for data structures:
- Floating-point equality is problematic (0.1 + 0.2 ≠ 0.3)
- NaN (Not a Number) propagates through operations
- Infinity arithmetic has special rules
- Denormalized numbers provide gradual underflow

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
- Slower allocation (search for free block)
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

## 2.5 Type Systems and Generic Programming

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

---

## Where this connects

- [Chapter 3: Arrays—The Foundation of Contiguous Storage](ch03-arrays-the-foundation-of-contiguous-storage.md). The first structure built directly on this memory model
- [Chapter 16: External Memory and Cache-Oblivious Structures](../volume-3/ch16-external-memory-and-cache-oblivious-structures.md). What the memory hierarchy does to these assumptions
