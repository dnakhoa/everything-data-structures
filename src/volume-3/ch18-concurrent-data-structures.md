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

Thread A executes (1) and is preempted. Thread B runs both lines and pushes its node. Thread A resumes and executes (2), overwriting `head` with a node whose `next` still points at the *old* head. Thread B's node is gone: silently, with no error, no crash, and no way to detect it later. That is a **lost update**, and it happens because the read and the write were not one indivisible step.

The two properties above address different questions:

**Safety. What results are legal.** *Linearizability* is the standard: every operation appears to take effect instantaneously at some point between its call and its return, and that ordering is consistent with real time. It matters because it composes. Linearizable components can be combined and the result stays reasonable, which is not true of weaker conditions like sequential consistency.

**Liveness: whether threads make progress.** These form a hierarchy:

| Guarantee | Promise | Cost |
|-----------|---------|------|
| Blocking | None, a stalled thread can block everyone | Cheapest, simplest |
| Obstruction-free | A thread running alone finishes | Weak in practice |
| Lock-free | *Some* thread always makes progress | System-wide throughput; individual threads may starve |
| Wait-free | *Every* thread finishes in bounded steps | Strongest; usually the slowest in the common case |

The distinction that matters in production: with locks, a thread that is descheduled, page-faults, or crashes while holding a lock stalls every other thread indefinitely. Lock-free structures cannot suffer that failure mode. This matters far more in a real-time or kernel context than in a typical server, which is worth remembering before reaching for lock-free code.

## 18.2 Lock-Free Techniques

**Compare-and-Swap (CAS)** is the primitive everything else is built from. Its semantics are: *atomically*, compare the value at an address to an expected value, and if they match, replace it with a new value. Report whether the swap happened.

The critical word is *atomically*. This is a single indivisible hardware instruction (`LOCK CMPXCHG` on x86, `LDREX`/`STREX` or `CAS` on ARM)not something you can write in plain C. The following is what CAS is **specified to do**, and is emphatically *not* a valid implementation, since the read and the write can be interleaved by another thread exactly as in the lost-update example above:

```c
/* SPECIFICATION ONLY. This is what the hardware does atomically.
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

**The ABA problem** is the classic trap. CAS checks whether a value is unchanged, but what you actually care about is whether the *state* is unchanged, and those differ. Thread A reads head = X. Thread B pops X, pops Y, then pushes X back. Thread A's CAS on X succeeds (the pointer matches)but the list beneath it is now completely different, and A may splice in a node pointing at freed memory.

The standard defenses:

- **Tagged pointers**: pack a counter alongside the pointer and CAS both together (a double-width CAS, `LOCK CMPXCHG16B`). The counter increments on every update, so a recycled pointer no longer compares equal.
- **Hazard pointers**: each thread publishes the pointers it is currently dereferencing; memory is not reclaimed while any hazard pointer references it.
- **Epoch-based reclamation / RCU**: defer reclamation until every thread has passed through a quiescent state.
- **Garbage collection**: in a GC'd language, ABA via memory reuse largely disappears, which is why lock-free code is considerably easier to write correctly in Java than in C.

**Memory reclamation is the hard part** of lock-free programming in a non-GC language, and it is where most bugs live. Removing a node from a lock-free structure is easy; knowing when no other thread can still be reading it is not. This is the single strongest argument for using a well-tested library rather than writing your own.

**Memory ordering** is the other subtlety. Modern CPUs and compilers reorder memory operations aggressively. Correct lock-free code requires explicit ordering constraints. `memory_order_acquire` on loads that must see prior writes, `memory_order_release` on stores that must be visible to subsequent readers. Defaulting to `memory_order_seq_cst` is correct and slower; anything weaker demands genuine care. x86 has a strong memory model that hides many mistakes; the same code on ARM or POWER then fails in production, which is a well-known way to ship a bug.

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
            /* Someone else is mid-enqueue, so help them finish. */
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

That final CAS is allowed to fail, because if it does, some other thread has already performed the fix-up. This **helping** pattern (threads completing each other's partial operations rather than waiting)is the general technique for building lock-free structures with multi-step updates.

**Concurrent hash maps** are where most real applications actually meet this material, and the design has evolved:

- **One global lock**: correct, trivially, and a bottleneck at any real concurrency.
- **Lock striping**: N independent locks, bucket *i* guarded by lock `i mod N`. Java's `ConcurrentHashMap` used 16 segments by default through Java 7. Simple and effective.
- **Per-bucket locking with lock-free reads**: Java 8 onward CASes into empty buckets and locks only the first node of a non-empty one, while reads are entirely lock-free over `volatile` fields. Reads scale perfectly; writes contend only on the exact bucket.
- **Split-ordered lists** (Shalev and Shavit, 2006): a genuinely lock-free hash table that supports resizing without ever blocking. Resizing being the operation that makes concurrent hash tables hard, since it touches everything at once.

**Concurrent skip lists** are worth knowing because they are why `ConcurrentSkipListMap` exists while a concurrent balanced BST does not. Insertion is local (CAS a few forward pointers)whereas a red-black tree rebalance rotates nodes far from the insertion point, which is very hard to do lock-free. Randomized structure buys concurrency. This is the same trade that makes skip lists attractive in MemSQL, LevelDB's memtable, and Redis sorted sets.

**Read-Copy-Update (RCU)** deserves separate mention because it is the dominant technique inside the Linux kernel. Readers pay *nothing at all*: no atomics, no barriers on most architectures, literally just a dereference. Writers copy the structure, modify the copy, and atomically swap the pointer, then wait for a grace period before freeing the old version. It is the right answer for the extremely common read-mostly case, and the wrong one for write-heavy workloads.

## 18.4 When Not to Go Lock-Free

Lock-free programming is one of the easiest ways to write code that is subtly, intermittently, unreproducibly wrong. Before choosing it, work down this list:

1. **Don't share.** Thread-local state, sharding, or message passing eliminates the problem instead of solving it. This is by far the best option when it applies.
2. **Use immutable data.** Persistent structures ([Chapter 17](ch17-persistent-data-structures.md)) need no synchronization for readers at all.
3. **Use a plain lock.** An uncontended mutex costs ~20ns. Correct, readable, and fast enough for the overwhelming majority of code.
4. **Use a well-tested concurrent library.** `ConcurrentHashMap`, `folly::ConcurrentHashMap`, `crossbeam`, `java.util.concurrent`. These were written by specialists and tested for years.
5. **Only then write lock-free code yourself**, and only with model checking or stress testing under a race detector (TSan, `loom` in Rust, JCStress in Java). Reasoning alone is not sufficient; neither is testing on x86 alone.

The honest summary: lock-free structures win on tail latency and on immunity to a stalled thread, not usually on average throughput. A striped lock frequently beats a hand-rolled lock-free structure on both performance and correctness.

## 18.5 Historical Context

Leslie Lamport defined sequential consistency in 1979 and produced the first lock-free queue (for one reader and one writer) in 1977. Maurice Herlihy and Jeannette Wing introduced linearizability in 1990, giving the field its correctness criterion.

Herlihy's 1991 paper "Wait-Free Synchronization" is the theoretical foundation: it established the **consensus hierarchy**, proving that primitives have a consensus number (the maximum number of threads for which they can solve consensus)and that atomic read/write registers have consensus number 1, while compare-and-swap has consensus number ∞. That result is why CAS is *the* universal primitive and why hardware designers ship it: with CAS you can build a wait-free implementation of any object, and without something like it you provably cannot.

Maged Michael and Michael Scott published their queue in 1996; it went into `java.util.concurrent` and has been the reference lock-free FIFO ever since. Michael followed with hazard pointers in 2004, addressing the reclamation problem. Paul McKenney's RCU work brought the read-mostly approach into the Linux kernel from 2002 onward, where it is now used in tens of thousands of places.

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**18.1 ★ Classify the progress guarantee.** For each, say whether it is blocking, lock-free (but not wait-free), or wait-free, using the table in 18.1.

1. A counter protected by a mutex.
2. `lock_free_push` from 18.2.
3. A spinlock built from CAS: `int zero = 0; while (!atomic_compare_exchange_weak(&lock, &zero, 1)) { zero = 0; }`, followed by a critical section and `atomic_store(&lock, 0)`.
4. An RCU reader that loads the current pointer and reads through it.

<details>
<summary>Solution</summary>

1. **Blocking.** If the holder is descheduled inside the critical section, every other thread waits.
2. **Lock-free, not wait-free.** A failed CAS means another thread's push succeeded, so the system as a whole progresses. But a single thread can lose the race on every attempt, so its own step count is unbounded.
3. **Blocking.** Using CAS does not make an algorithm lock-free. A thread that acquires the spinlock and is then preempted stalls every other thread, which spins forever. The progress guarantee is a property of the algorithm, not of the instructions it uses.
4. **Wait-free.** The reader performs a fixed number of its own steps (a load and a dereference) and never retries or waits, regardless of what writers do. Writers are a different story: they wait for a grace period.

</details>

**18.2 ★ Lost update, then fixed.** The stack is `head → X → Y`. Thread A calls `push(P)` and thread B calls `push(Q)` using the unsynchronized `push` from 18.1. They interleave as A(1), B(1), B(2), A(2). Draw the final list. Then replay the same scheduling idea with `lock_free_push` from 18.2: A loads `old_head` and sets `P->next`, B runs its whole push, then A attempts its CAS. What happens, and what is the final list?

<details>
<summary>Solution</summary>

Unsynchronized:

| Step | Effect | State |
|------|--------|-------|
| A(1) | `P->next = head` (X) | P → X |
| B(1) | `Q->next = head` (X) | Q → X |
| B(2) | `head = Q` | head → Q → X → Y |
| A(2) | `head = P` | head → P → X → Y |

Final list: **P → X → Y**. Q still points at X but nothing points at Q, so B's push is lost.

With `lock_free_push`: A loads `old_head = X` and sets `P->next = X`. B completes its push, so `head = Q`. A's CAS compares `head` (Q) with `old_head` (X), fails, and writes Q into `old_head`. A loops: `P->next = Q`, and the CAS now succeeds. Final list: **P → Q → X → Y**. Both pushes survive, and A paid one extra loop iteration.

</details>

**18.3 ★★ ABA, step by step.** Here is the matching lock-free pop (C11, ignoring memory reclamation):

```c
Node *pop(_Atomic(Node*) *head) {
    Node *old = atomic_load(head);
    while (old && !atomic_compare_exchange_weak(head, &old, old->next))
        ;
    return old;
}
```

The stack is `A → B → C`. Thread 1 calls `pop`, loads `old = A`, evaluates `old->next` (B) as the CAS argument, and is preempted just before the CAS executes. Thread 2 then pops A, pops B and frees B, and pushes A back (reusing the node). (a) What does the stack look like after thread 2? (b) What happens when thread 1's CAS runs? (c) Show how a tagged pointer, where the tag increments on every successful CAS, changes the outcome. (d) Is there a problem tagging does *not* fix?

<details>
<summary>Hint</summary>

The CAS compares only the pointer value. After thread 2 finishes, is `head` equal to A?

</details>

<details>
<summary>Solution</summary>

(a) After thread 2: popping A leaves `B → C`, popping B leaves `C`, pushing A sets `A->next = C`. The stack is **A → C**, and B's memory has been freed.

(b) Thread 1's CAS compares `head` (A) with `old` (A). They match, so it installs its stale argument B: **head now points at freed memory**, and C has dropped out of the stack. The next pop dereferences a dangling pointer.

(c) With tags, `head` is a (pointer, tag) pair swapped by a double-width CAS:

| Event | head |
|-------|------|
| Initial | (A, 0) |
| Thread 1 reads | (A, 0) |
| Thread 2 pops A | (B, 1) |
| Thread 2 pops B | (C, 2) |
| Thread 2 pushes A | (A, 3) |
| Thread 1 CAS expects (A, 0) | fails, reloads (A, 3) |
| Thread 1 retries with next = C | (C, 4), returns A |

The final stack is **C**, which is correct: A was popped twice and pushed once, B was popped once.

(d) Tagging prevents the wrong CAS, but thread 1 still read `old->next` from a node that another thread could have freed. If A itself had been freed and returned to the operating system, that read is a use-after-free even though the CAS would later fail. Preventing that requires a reclamation scheme (hazard pointers, epochs, or a garbage collector), which is why 18.2 calls reclamation the hard part.

</details>

**18.4 ★★ Helping in the Michael–Scott queue.** The queue holds only its dummy node D: `D->next == NULL` and `head == tail == D`. Thread A calls `enqueue(X)`. Its CAS on `D->next` succeeds, and A is preempted before its final CAS on `q->tail`. Thread B now calls `enqueue(Y)` and runs to completion. Trace each iteration of B's loop, then say what happens when A resumes. What is the final state? Why must B help rather than wait for A?

<details>
<summary>Solution</summary>

State when A stops: `D → X`, `tail == D` (lagging by one).

**B, iteration 1:** `tail = D`, `next = D->next = X`. The tail re-check passes. Since `next != NULL`, B performs A's unfinished step: `CAS(&q->tail, D, X)` succeeds, `tail == X`. `continue`.

**B, iteration 2:** `tail = X`, `next = NULL`. B's `CAS(&X->next, NULL, Y)` succeeds, linking Y. B's `CAS(&q->tail, X, Y)` succeeds. B returns.

**A resumes:** it executes `CAS(&q->tail, D, X)`. `q->tail` is Y, not D, so the CAS fails, and A returns. That failure is harmless because the work it would have done was already done by B.

Final state: `D → X → Y`, `head == D`, `tail == Y`. The FIFO order is X then Y, matching the order in which the linking CASes succeeded.

If B waited for A to advance the tail, then a preempted, page-faulting, or crashed A would stall B indefinitely, and the queue would be blocking: exactly the failure mode lock-freedom exists to rule out. Helping means any thread can finish any other thread's half-done operation, so no thread ever depends on another being scheduled. (`compare_exchange_weak` may also fail spuriously; in every branch a failure just leads to a retry or leaves the tail lagging for the next operation to repair, so the algorithm stays correct.)

</details>

**18.5 ★★ Lock striping by the numbers.** A hash map has 256 buckets guarded by 16 locks, with bucket i under lock `i mod 16`, as in 18.3.

1. Which buckets share a lock with bucket 37?
2. Two threads each write one key at the same moment, with keys hashing uniformly. What is the probability they contend for a lock, under a global lock, under 16-way striping, and under per-bucket locking?
3. With 8 threads writing simultaneously, what is the probability that at least two of them contend under 16-way striping?
4. Why must a resize from 256 to 512 buckets acquire all 16 locks?

<details>
<summary>Solution</summary>

1. 37 mod 16 = 5, so lock 5 guards buckets 5, 21, 37, 53, ..., 245: the 16 buckets congruent to 5 mod 16.
2. Global lock: 1 (they always contend). Striping: 1/16 ≈ 6%. Per-bucket: 1/256 ≈ 0.4%.
3. This is the birthday problem. The chance all 8 land on distinct stripes is (16 × 15 × 14 × 13 × 12 × 11 × 10 × 9) / 16⁸ ≈ 0.121, so the chance of at least one collision is about **0.88**. Sixteen stripes sounds like a lot until eight writers are active. In practice contention also depends on how long the lock is held, which is why short critical sections matter as much as stripe count.
4. A resize reads every bucket and moves entries to buckets that are guarded by different stripes. If it held only some locks, a writer holding another stripe could insert into a bucket the resize has already copied, and that write would be lost when the old table is discarded. Holding all 16 stops the world for the duration of the resize, which is exactly the problem split-ordered lists were invented to avoid.

</details>

**18.6 ★★ Design: a read-mostly configuration map.** A service has 32 worker threads that look up configuration values about a million times per second in total. One background thread reloads the whole configuration once a minute. Choose among a single mutex around a hash map, `ConcurrentHashMap`, and an immutable map published through an atomic pointer (the RCU style from 18.3, using the persistent structures from Chapter 17). Justify the choice and state when it would be wrong.

<details>
<summary>Solution</summary>

Use the **immutable map behind an atomic pointer**. Readers do one acquire load of the pointer and then read an ordinary immutable map with no locks, no CAS, and no shared writes, so the 32 threads never touch a common cache line except the pointer itself, which is read-only between reloads. The writer builds a complete new map off to the side and publishes it with one release store. Old maps are reclaimed by the garbage collector or after an RCU grace period.

It also gives a property the other two lack: a reader that loads the pointer once sees a **consistent snapshot** of every key. With `ConcurrentHashMap`, a reader looking up two related keys during a reload can see one old value and one new.

The cost is on the write side: each update copies the map (O(n), or O(log n) per changed key with a HAMT). Once a minute, that is negligible.

- A **single mutex** serializes every lookup across 32 threads. Correct, and the worst option here.
- **`ConcurrentHashMap`** works and has lock-free reads, but buys fine-grained write concurrency this workload never uses, and loses snapshot consistency.

The choice flips if writes become frequent, for example a per-request counter in the same map. Copying the whole map on every write would then dominate, and `ConcurrentHashMap` (or sharding the counters per thread) is the right answer.

</details>

**18.7 ★★★ A tiny model checker.** 18.4 says reasoning alone is not enough; model checking explores every interleaving. Write `outcomes(n_threads, increments)` that returns every possible final value of a shared counter when each thread performs `increments` non-atomic increments, each made of two steps: `r = counter` (load) then `counter = r + 1` (store). Report the results for (2, 1), (2, 2), and (2, 3). Explain why 1 is impossible with two increments per thread. Then change the increment to a CAS retry loop (load r, then `CAS(counter, r, r + 1)`, retry on failure) and confirm only the correct total is reachable.

<details>
<summary>Hint</summary>

Recursively try every runnable thread as the next one to take a step. The state is the counter, each thread's program counter, and each thread's register.

</details>

<details>
<summary>Solution</summary>

```python
def outcomes(n_threads, increments):
    """Every final counter value reachable when each thread runs
    `increments` copies of: r = counter (load), counter = r + 1 (store)."""
    results = set()

    def explore(counter, pcs, regs):
        # pcs[t] counts thread t's steps: even = about to load, odd = about to store
        if all(pc == 2 * increments for pc in pcs):
            results.add(counter)
            return
        for t in range(n_threads):
            pc = pcs[t]
            if pc == 2 * increments:
                continue                                   # thread t is done
            new_pcs = pcs[:t] + (pc + 1,) + pcs[t + 1:]
            if pc % 2 == 0:                                # load
                explore(counter, new_pcs, regs[:t] + (counter,) + regs[t + 1:])
            else:                                          # store
                explore(regs[t] + 1, new_pcs, regs)

    explore(0, (0,) * n_threads, (0,) * n_threads)
    return sorted(results)

assert outcomes(2, 1) == [1, 2]
assert outcomes(2, 2) == [2, 3, 4]
assert outcomes(2, 3) == [2, 3, 4, 5, 6]
```

For two threads with 2 or 3 increments each, every value from 2 up to the correct total is reachable. The low end is the surprising part: six increments can produce 2.

**Why not 1 with two increments each?** The final value is whatever the last store wrote, which is one more than some value loaded by the thread that made it. Suppose thread T makes the last store. That is T's second store, and T's second load happened after T's first store had written a value of at least 1. Every store writes at least 1, so the counter is never 0 again after that point, and T's second load returns at least 1. The last store therefore writes at least 2.

The CAS version: the store step only succeeds if the counter still holds the loaded value, and a failure sends the thread back to load.

```python
def outcomes_cas(n_threads, increments):
    results = set()

    def explore(counter, pcs, regs, done):
        if all(d == increments for d in done):
            results.add(counter)
            return
        for t in range(n_threads):
            if done[t] == increments:
                continue
            if pcs[t] == 0:                                # load
                explore(counter, pcs[:t] + (1,) + pcs[t + 1:],
                        regs[:t] + (counter,) + regs[t + 1:], done)
            elif counter == regs[t]:                       # CAS succeeds
                explore(counter + 1, pcs[:t] + (0,) + pcs[t + 1:], regs,
                        done[:t] + (done[t] + 1,) + done[t + 1:])
            else:                                          # CAS fails: retry
                explore(counter, pcs[:t] + (0,) + pcs[t + 1:], regs, done)

    explore(0, (0,) * n_threads, (0,) * n_threads, (0,) * n_threads)
    return sorted(results)

assert outcomes_cas(2, 2) == [4]
assert outcomes_cas(3, 1) == [3]
```

Every interleaving now ends at n × k. The search also terminates, even though a CAS loop can retry: a CAS fails only when some other thread's CAS succeeded since the load, and the total number of successes is bounded. That is lock-freedom in miniature: retries happen, but only because the system made progress.

Real model checkers such as `loom` and JCStress do this same exhaustive (or systematically sampled) exploration, plus the reorderings that weak memory models allow, which this sketch ignores.

</details>

---

## Where this connects

- [Chapter 17: Persistent Data Structures](ch17-persistent-data-structures.md). Immutability as the alternative to synchronisation
- [Chapter 12: Hash Tables](../volume-2/ch12-hash-tables.md). The hash table these techniques are usually applied to
