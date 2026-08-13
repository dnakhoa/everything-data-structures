# Chapter 18: Concurrent Data Structures

## 18.1 Thread Safety

Concurrent access requires synchronization.

**Correctness criteria:**
- **Linearizability**: Each operation appears atomic
- **Sequential consistency**: Operations match program order
- **Lock-freedom**: At least one thread progresses
- **Wait-freedom**: All threads progress in bounded steps

To see why these criteria are needed, look at what breaks without them. Consider two threads pushing onto the singly linked stack from [Chapter 5](../volume-1/ch05-stacks-and-queues-ordered-access-patterns.md):

```c
void push(Stack *s, Node *n) {
    n->next = s->head;    // (1) read head
    s->head = n;          // (2) write head
}
```

Thread A executes (1) and is preempted. Thread B runs both lines and pushes its node. Thread A resumes and executes (2), overwriting `head` with a node whose `next` still points at the *old* head. Thread B's node is gone — silently, with no error, no crash, and no way to detect it later. That is a **lost update**, and it happens because the read and the write were not one indivisible step.

The two properties above address different questions:

**Safety — what results are legal.** *Linearizability* is the standard: every operation appears to take effect instantaneously at some point between its call and its return, and that ordering is consistent with real time. It matters because it composes — linearizable components can be combined and the result stays reasonable, which is not true of weaker conditions like sequential consistency.

**Liveness — whether threads make progress.** These form a hierarchy:

| Guarantee | Promise | Cost |
|-----------|---------|------|
| Blocking | None — a stalled thread can block everyone | Cheapest, simplest |
| Obstruction-free | A thread running alone finishes | Weak in practice |
| Lock-free | *Some* thread always makes progress | System-wide throughput; individual threads may starve |
| Wait-free | *Every* thread finishes in bounded steps | Strongest; usually the slowest in the common case |

The distinction that matters in production: with locks, a thread that is descheduled, page-faults, or crashes while holding a lock stalls every other thread indefinitely. Lock-free structures cannot suffer that failure mode. This matters far more in a real-time or kernel context than in a typical server, which is worth remembering before reaching for lock-free code.

## 18.2 Lock-Free Techniques

**Compare-and-Swap (CAS)** is the primitive everything else is built from. Its semantics are: *atomically*, compare the value at an address to an expected value, and if they match, replace it with a new value. Report whether the swap happened.

The critical word is *atomically*. This is a single indivisible hardware instruction — `LOCK CMPXCHG` on x86, `LDREX`/`STREX` or `CAS` on ARM — not something you can write in plain C. The following is what CAS is **specified to do**, and is emphatically *not* a valid implementation, since the read and the write can be interleaved by another thread exactly as in the lost-update example above:

```c
/* SPECIFICATION ONLY — this is what the hardware does atomically.
   Written like this in plain C it is a race, not a CAS. */
bool cas_semantics(int *addr, int expected, int new_value) {
    if (*addr == expected) {   // ← another thread can run between
        *addr = new_value;     //   these two lines
        return true;
    }
    return false;
}
```

The real thing comes from the compiler or the standard library:

```c
#include <stdatomic.h>

/* C11: compiles to a single LOCK CMPXCHG on x86.
   On failure, `expected` is updated with the actual value. */
bool ok = atomic_compare_exchange_weak(&head, &expected, new_value);
```

The standard usage pattern is a **retry loop**: read the current value, compute the new one, attempt to swap, and start over if someone beat you to it.

```c
void lock_free_push(_Atomic(Node*) *head, Node *n) {
    Node *old_head = atomic_load(head);
    do {
        n->next = old_head;
    } while (!atomic_compare_exchange_weak(head, &old_head, n));
    /* If the CAS fails, old_head now holds the current value; retry. */
}
```

No thread ever waits for another. A failed CAS means someone else succeeded, which is why this is lock-free rather than wait-free: the system always progresses, but one unlucky thread could in principle retry forever.

**The ABA problem** is the classic trap. CAS checks whether a value is unchanged, but what you actually care about is whether the *state* is unchanged, and those differ. Thread A reads head = X. Thread B pops X, pops Y, then pushes X back. Thread A's CAS on X succeeds — the pointer matches — but the list beneath it is now completely different, and A may splice in a node pointing at freed memory.

The standard defenses:

- **Tagged pointers**: pack a counter alongside the pointer and CAS both together (a double-width CAS, `LOCK CMPXCHG16B`). The counter increments on every update, so a recycled pointer no longer compares equal.
- **Hazard pointers**: each thread publishes the pointers it is currently dereferencing; memory is not reclaimed while any hazard pointer references it.
- **Epoch-based reclamation / RCU**: defer reclamation until every thread has passed through a quiescent state.
- **Garbage collection**: in a GC'd language, ABA via memory reuse largely disappears, which is why lock-free code is considerably easier to write correctly in Java than in C.

**Memory reclamation is the hard part** of lock-free programming in a non-GC language, and it is where most bugs live. Removing a node from a lock-free structure is easy; knowing when no other thread can still be reading it is not. This is the single strongest argument for using a well-tested library rather than writing your own.

**Memory ordering** is the other subtlety. Modern CPUs and compilers reorder memory operations aggressively. Correct lock-free code requires explicit ordering constraints — `memory_order_acquire` on loads that must see prior writes, `memory_order_release` on stores that must be visible to subsequent readers. Defaulting to `memory_order_seq_cst` is correct and slower; anything weaker demands genuine care. x86 has a strong memory model that hides many mistakes; the same code on ARM or POWER then fails in production, which is a well-known way to ship a bug.

## 18.3 Concurrent Data Structures

| Structure | Implementation | Technique |
|-----------|----------------|----------|
| Counter | Atomic operations | CAS |
| Stack | Lock-free | CAS on head |
| Queue | Michael-Scott | Head/tail pointers with CAS |
| Hash map | Segmented locks | Lock per bucket |
| Skip list | Lock-free | CAS on pointers |

**The Michael–Scott queue** (1996) is the standard lock-free FIFO and repays study. It keeps separate head and tail pointers with a permanent dummy node so that the empty case needs no special handling, and enqueue proceeds in two CAS steps: first link the new node to the current last node, then advance the tail pointer.

Between those two steps the queue is in an intermediate state where tail lags one node behind reality. The trick that makes this work is that **any thread which observes the lagging tail helps fix it** before proceeding:

```c
void enqueue(Queue *q, Node *n) {
    n->next = NULL;
    while (1) {
        Node *tail = atomic_load(&q->tail);
        Node *next = atomic_load(&tail->next);
        if (tail != atomic_load(&q->tail)) continue;      // stale, re-read
        if (next != NULL) {
            /* Someone else is mid-enqueue — help them finish. */
            atomic_compare_exchange_weak(&q->tail, &tail, next);
            continue;
        }
        if (atomic_compare_exchange_weak(&tail->next, &next, n)) {
            atomic_compare_exchange_weak(&q->tail, &tail, n);  // may fail; fine
            return;
        }
    }
}
```

That final CAS is allowed to fail, because if it does, some other thread has already performed the fix-up. This **helping** pattern — threads completing each other's partial operations rather than waiting — is the general technique for building lock-free structures with multi-step updates.

**Concurrent hash maps** are where most real applications actually meet this material, and the design has evolved:

- **One global lock**: correct, trivially, and a bottleneck at any real concurrency.
- **Lock striping**: N independent locks, bucket *i* guarded by lock `i mod N`. Java's `ConcurrentHashMap` used 16 segments by default through Java 7. Simple and effective.
- **Per-bucket locking with lock-free reads**: Java 8 onward CASes into empty buckets and locks only the first node of a non-empty one, while reads are entirely lock-free over `volatile` fields. Reads scale perfectly; writes contend only on the exact bucket.
- **Split-ordered lists** (Shalev and Shavit, 2006): a genuinely lock-free hash table that supports resizing without ever blocking — resizing being the operation that makes concurrent hash tables hard, since it touches everything at once.

**Concurrent skip lists** are worth knowing because they are why `ConcurrentSkipListMap` exists while a concurrent balanced BST does not. Insertion is local — CAS a few forward pointers — whereas a red-black tree rebalance rotates nodes far from the insertion point, which is very hard to do lock-free. Randomized structure buys concurrency. This is the same trade that makes skip lists attractive in MemSQL, LevelDB's memtable, and Redis sorted sets.

**Read-Copy-Update (RCU)** deserves separate mention because it is the dominant technique inside the Linux kernel. Readers pay *nothing at all* — no atomics, no barriers on most architectures, literally just a dereference. Writers copy the structure, modify the copy, and atomically swap the pointer, then wait for a grace period before freeing the old version. It is the right answer for the extremely common read-mostly case, and the wrong one for write-heavy workloads.

## 18.4 When Not to Go Lock-Free

Lock-free programming is one of the easiest ways to write code that is subtly, intermittently, unreproducibly wrong. Before choosing it, work down this list:

1. **Don't share.** Thread-local state, sharding, or message passing eliminates the problem instead of solving it. This is by far the best option when it applies.
2. **Use immutable data.** Persistent structures ([Chapter 17](ch17-persistent-data-structures.md)) need no synchronization for readers at all.
3. **Use a plain lock.** An uncontended mutex costs ~20ns. Correct, readable, and fast enough for the overwhelming majority of code.
4. **Use a well-tested concurrent library.** `ConcurrentHashMap`, `folly::ConcurrentHashMap`, `crossbeam`, `java.util.concurrent`. These were written by specialists and tested for years.
5. **Only then write lock-free code yourself** — and only with model checking or stress testing under a race detector (TSan, `loom` in Rust, JCStress in Java). Reasoning alone is not sufficient; neither is testing on x86 alone.

The honest summary: lock-free structures win on tail latency and on immunity to a stalled thread, not usually on average throughput. A striped lock frequently beats a hand-rolled lock-free structure on both performance and correctness.

## 18.5 Historical Context

Leslie Lamport defined sequential consistency in 1979 and produced the first lock-free queue (for one reader and one writer) in 1977. Maurice Herlihy and Jeannette Wing introduced linearizability in 1990, giving the field its correctness criterion.

Herlihy's 1991 paper "Wait-Free Synchronization" is the theoretical foundation: it established the **consensus hierarchy**, proving that primitives have a consensus number — the maximum number of threads for which they can solve consensus — and that atomic read/write registers have consensus number 1, while compare-and-swap has consensus number ∞. That result is why CAS is *the* universal primitive and why hardware designers ship it: with CAS you can build a wait-free implementation of any object, and without something like it you provably cannot.

Maged Michael and Michael Scott published their queue in 1996; it went into `java.util.concurrent` and has been the reference lock-free FIFO ever since. Michael followed with hazard pointers in 2004, addressing the reclamation problem. Paul McKenney's RCU work brought the read-mostly approach into the Linux kernel from 2002 onward, where it is now used in tens of thousands of places.
