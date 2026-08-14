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
- Xbox 360 "red ring of death": Integer overflow in timer
- Knights of the Round Table bug: Division by zero from overflow

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
    // 7 bytes padding (typically)
};
// sizeof(Example) = 16 (on 64-bit system)
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

---

## Where this connects

- [Chapter 3: Arrays—The Foundation of Contiguous Storage](ch03-arrays-the-foundation-of-contiguous-storage.md). The first structure built directly on this memory model
- [Chapter 16: External Memory and Cache-Oblivious Structures](../volume-3/ch16-external-memory-and-cache-oblivious-structures.md). What the memory hierarchy does to these assumptions
