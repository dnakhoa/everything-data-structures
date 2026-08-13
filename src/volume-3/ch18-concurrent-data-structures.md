# Chapter 18: Concurrent Data Structures

## 18.1 Thread Safety

Concurrent access requires synchronization.

**Correctness criteria:**
- **Linearizability**: Each operation appears atomic
- **Sequential consistency**: Operations match program order
- **Lock-freedom**: At least one thread progresses
- **Wait-freedom**: All threads progress in bounded steps

## 18.2 Lock-Free Techniques

**Compare-and-Swap (CAS):**
```c
bool cas(int *addr, int expected, int new) {
    if (*addr == expected) {
        *addr = new;
        return true;
    }
    return false;
}
```

## 18.3 Concurrent Data Structures

| Structure | Implementation | Technique |
|-----------|----------------|----------|
| Counter | Atomic operations | CAS |
| Stack | Lock-free | CAS on head |
| Queue | Michael-Scott | Head/tail pointers with CAS |
| Hash map | Segmented locks | Lock per bucket |
| Skip list | Lock-free | CAS on pointers |
