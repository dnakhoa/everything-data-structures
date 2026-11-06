# Chapter 5: Stacks and Queues—Ordered Access Patterns

## 5.1 Stacks: The LIFO Principle

A stack is an ADT supporting two primary operations: push (add to top) and pop (remove from top). The last element pushed is the first to be popped, Last In, First Out.

**Mental Model**: A stack of plates in a cafeteria. You add plates to the top, and you take plates from the top. You never reach into the middle of the stack.

```
    ┌─────────┐
    │   TOP   │  ← Push(4), Pop() returns 4
    ├─────────┤
    │    3    │
    ├─────────┤
    │    2    │
    ├─────────┤
    │    1    │
    └─────────┘
        BOTTOM
```

## 5.2 Stack Implementation

### Array-Based Stack

```c
#define MAX_SIZE 1000

typedef struct {
    int top;
    element_type data[MAX_SIZE];
} Stack;

void init(Stack *s) { s->top = -1; }

int is_empty(Stack *s) { return s->top == -1; }
int is_full(Stack *s) { return s->top == MAX_SIZE - 1; }

void push(Stack *s, element_type x) {
    if (is_full(s)) { /* handle overflow */ }
    s->data[++s->top] = x;
}

element_type pop(Stack *s) {
    if (is_empty(s)) { /* handle underflow */ }
    return s->data[s->top--];
}

element_type peek(Stack *s) {
    if (is_empty(s)) { /* handle empty */ }
    return s->data[s->top];
}
```

### Linked List-Based Stack

```c
typedef struct StackNode {
    element_type data;
    struct StackNode *next;
} StackNode;

StackNode *top = NULL;

void push(element_type x) {
    StackNode *node = malloc(sizeof(StackNode));
    node->data = x;
    node->next = top;
    top = node;
}

element_type pop() {
    if (top == NULL) { /* handle underflow */ }
    StackNode *tmp = top;
    element_type val = tmp->data;
    top = top->next;
    free(tmp);
    return val;
}
```

## 5.3 Stack Applications

### Function Call Stack

The most important use of stacks: managing function calls. Each function call pushes a stack frame containing:
- Return address
- Parameters
- Local variables
- Saved registers

```c
int fact(int n) {
    if (n <= 1) return 1;
    return n * fact(n - 1);
}

fact(4):
fact(4) calls fact(3)
    fact(3) calls fact(2)
        fact(2) calls fact(1)
            fact(1) returns 1
        fact(2) returns 2 * 1 = 2
    fact(3) returns 3 * 2 = 6
fact(4) returns 4 * 6 = 24

Stack growth:
┌──────────┐
│ fact(1)  │ ← Returns, stack shrinks
├──────────┤
│ fact(2)  │
├──────────┤
│ fact(3)  │
├──────────┤
│ fact(4)  │ ← Called first
└──────────┘
```

Stack overflow occurs when the call stack exceeds its allocated size, often due to infinite recursion.

### Expression Evaluation

Stacks enable evaluation of expressions in postfix (Reverse Polish) notation:

```
Infix:     3 + 4 * 2 / (1 - 5)
Postfix:   3 4 2 * 1 5 - / +

Evaluation:
Push 3
Push 4
Push 2
Multiply: pop 2, pop 4, push 8      Stack: [3, 8]
Push 1
Push 5
Subtract: pop 5, pop 1, push -4    Stack: [3, 8, -4]
Divide: pop -4, pop 8, push -2     Stack: [3, -2]
Add: pop -2, pop 3, push 1        Stack: [1]
Result: 1
```

**Infix to Postfix Conversion** (Shunting-yard algorithm):
- Numbers: output immediately
- Operators: pop operators with higher precedence (or equal precedence, for left-associative operators such as `-` and `/`), then push
- Left parenthesis: push
- Right parenthesis: pop until left parenthesis
- End of input: pop all remaining operators

### Parentheses Matching

```c
int is_balanced(char *expr) {
    Stack s;
    init(&s);

    while (*expr) {
        if (*expr == '(' || *expr == '[' || *expr == '{') {
            push(&s, *expr);
        } else if (*expr == ')' || *expr == ']' || *expr == '}') {
            if (is_empty(&s)) return 0;
            char top = pop(&s);
            if ((top == '(' && *expr != ')') ||
                (top == '[' && *expr != ']') ||
                (top == '{' && *expr != '}')) {
                return 0;
            }
        }
        expr++;
    }
    return is_empty(&s);
}
```

### Undo/Redo Systems

Applications maintain two stacks: one for undo, one for redo:

```c
typedef struct {
    Stack undo;
    Stack redo;
    Document doc;
} Editor;

void do_action(Editor *ed, Action action) {
    push(&ed->undo, save_state(&ed->doc));
    apply(action, &ed->doc);
    clear_stack(&ed->redo);
}

void undo(Editor *ed) {
    if (is_empty(&ed->undo)) return;
    State *s = pop(&ed->undo);
    push(&ed->redo, save_state(&ed->doc));
    restore(s, &ed->doc);
}

void redo(Editor *ed) {
    if (is_empty(&ed->redo)) return;
    State *s = pop(&ed->redo);
    push(&ed->undo, save_state(&ed->doc));
    restore(s, &ed->doc);
}
```

### Backtracking Algorithms

Depth-first search, maze solving, and many recursive algorithms naturally use stacks:

```c
void solve_maze(int maze[][], int start_x, int start_y) {
    Stack path;
    init(&path);
    push(&path, (Point){start_x, start_y});

    while (!is_empty(&path)) {
        Point p = peek(&path);

        if (is_goal(p)) {
            print_solution(&path);
            return;
        }

        if (!has_unvisited_neighbors(maze, p)) {
            pop(&path);  // Backtrack
        } else {
            Point next = get_unvisited_neighbor(maze, p);
            mark_visited(maze, next);
            push(&path, next);
        }
    }
}
```

## 5.4 Queues: The FIFO Principle

A queue is an ADT where elements are added at the rear and removed from the front. First In, First Out.

**Mental Model**: A line of people waiting for a bus. New arrivals join at the back; those at the front board first.

```
FRONT                                                   REAR
 │                                                       │
 ▼                                                       ▼
┌────────┬────────┬────────┬────────┬────────┐
│   A    │   B    │   C    │   D    │   E    │
└────────┴────────┴────────┴────────┴────────┘
   ↑                                                 ↑
Dequeue()                                      Enqueue(F)
returns A
```

## 5.5 Queue Implementation

### Simple Array Queue (Inefficient)

```c
typedef struct {
    int data[MAX_SIZE];
    int front;
    int rear;
    int size;
} Queue;

// Problem: Array fills up even though elements leave from front
// Solution: Circular queue
```

### Circular Queue

```c
typedef struct {
    int data[MAX_SIZE];
    int front;
    int rear;
} CircularQueue;

int is_empty(CircularQueue *q) {
    return q->front == q->rear;
}

int is_full(CircularQueue *q) {
    return (q->rear + 1) % MAX_SIZE == q->front;
}

void enqueue(CircularQueue *q, int x) {
    if (is_full(q)) { /* handle overflow */ }
    q->data[q->rear] = x;
    q->rear = (q->rear + 1) % MAX_SIZE;
}

int dequeue(CircularQueue *q) {
    if (is_empty(q)) { /* handle underflow */ }
    int x = q->data[q->front];
    q->front = (q->front + 1) % MAX_SIZE;
    return x;
}
```

```
MAX_SIZE = 6, starting from front = rear = 4.
Enqueue 4, 5, 6, then dequeue twice, then enqueue 7:
front
  │
  ▼
┌────┬────┬────┬────┬────┬────┐
│ 6  │ 7  │ -- │ -- │ 4  │ 5  │
└────┴────┴────┴────┴────┴────┘
            ▲
           rear
4 and 5 have been dequeued; their slots still hold the old
values but are free and will be overwritten.
```

### Linked List Queue

```c
typedef struct QNode {
    int data;
    struct QNode *next;
} QNode;

typedef struct {
    QNode *front;
    QNode *rear;
} LinkedQueue;

void enqueue(LinkedQueue *q, int x) {
    QNode *node = malloc(sizeof(QNode));
    node->data = x;
    node->next = NULL;
    if (q->rear) q->rear->next = node;
    q->rear = node;
    if (!q->front) q->front = node;
}

int dequeue(LinkedQueue *q) {
    if (!q->front) { /* handle underflow */ }
    QNode *tmp = q->front;
    int x = tmp->data;
    q->front = tmp->next;
    if (!q->front) q->rear = NULL;
    free(tmp);
    return x;
}
```

## 5.6 Double-Ended Queue (Deque)

A deque allows insertion and deletion at both ends:

```c
typedef struct {
    int data[MAX_SIZE];
    int front;
    int rear;
    int size;
} Deque;

void push_front(Deque *d, int x);
void push_back(Deque *d, int x);
int pop_front(Deque *d);
int pop_back(Deque *d);
```

**Applications:**
- Implementing both stacks and queues
- Palindrome checking
- A-Steal algorithm (parallel task scheduling)
- Text editor undo/redo (two deques)

## 5.7 Priority Queues

A priority queue extracts elements based on priority, not arrival order:

```c
// Higher number = higher priority (max-heap)
// Lower number = higher priority (min-heap)

typedef struct {
    element_type *data;
    int size;
    int capacity;
    int (*compare)(element_type, element_type);
} PriorityQueue;
```

**Operations:**
- Insert: O(log n)
- Extract min/max: O(log n)
- Peek: O(1)
- Decrease/increase key: O(log n) in a binary heap, given an index that locates the element in O(1)

**Implementations:**
- Binary heap: Most common, O(log n) worst case
- Fibonacci heap: O(1) amortized insert, used in Dijkstra's algorithm
- Binomial heap: O(log n) all operations, useful for meldable priority queues
- Array (sorted): O(1) extract-min, O(n) insert
- Array (unsorted): O(n) extract-min, O(1) insert

## 5.8 Queue Applications

### Breadth-First Search

BFS naturally uses a queue to explore graphs level by level:

```python
def bfs(graph, start):
    visited = {start}
    queue = deque([start])

    while queue:
        vertex = queue.popleft()
        process(vertex)

        for neighbor in graph[vertex]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
```

### Task Scheduling

Operating systems use queues to manage processes:
- Ready queue: Processes waiting for CPU
- I/O queues: Processes waiting for devices
- Priority queues: Real-time scheduling

### Print Spooling

Multiple print jobs go into a queue; printers process them in order (or by priority).

### Producer-Consumer Problem

Queues mediate between threads or processes with different speeds:

```python
from queue import Queue
import threading

def producer(queue):
    for i in range(10):
        queue.put(i)  # Blocks if queue full

def consumer(queue):
    while True:
        item = queue.get()  # Blocks if queue empty
        process(item)
        queue.task_done()

queue = Queue(maxsize=4)  # bounded, so put() can block
threading.Thread(target=producer, args=(queue,)).start()
threading.Thread(target=consumer, args=(queue,)).start()
```

## 5.9 Historical Context

The stack and queue concepts emerged in the 1950s as programmers recognized common access patterns. Alan Turing's 1949 work on subroutine linkage predated formal stack concepts, the call stack was an informal but essential mechanism.

The term "stack" became standard in the 1960s, replacing earlier terms like "pushdown list." The queue concept was formalized alongside it.

Edsger Dijkstra's 1968 paper on " cooperating sequential processes" introduced semaphores and discussed bounded buffers (producer-consumer) as fundamental synchronization problems.

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**5.1 ★ Evaluate a postfix expression.** Evaluate `5 1 2 + 4 * + 3 -` with a stack, as in Section 5.3. Show the stack after every token, and give the infix expression it came from.

<details>
<summary>Solution</summary>

Operands are pushed; an operator pops the right operand first, then the left, and pushes the result.

| Token | Action | Stack (bottom → top) |
|-------|--------|----------------------|
| 5 | push | [5] |
| 1 | push | [5, 1] |
| 2 | push | [5, 1, 2] |
| + | pop 2, pop 1, push 1 + 2 | [5, 3] |
| 4 | push | [5, 3, 4] |
| * | pop 4, pop 3, push 3 × 4 | [5, 12] |
| + | pop 12, pop 5, push 5 + 12 | [17] |
| 3 | push | [17, 3] |
| - | pop 3, pop 17, push 17 − 3 | [14] |

Result: **14**. The infix form is `5 + (1 + 2) * 4 - 3`. Note the pop order for `-`: the first value popped (3) is the right operand. Getting that backwards gives −14.

</details>

**5.2 ★ Circular queue trace.** Use the `CircularQueue` code from Section 5.5 with `MAX_SIZE` = 5, starting from `front = rear = 0`. Apply: enqueue 10, 20, 30, 40; check `is_full`; dequeue twice; enqueue 50, 60. Give `front` and `rear` after each step and the final contents of `data`. How many elements can this queue hold, and why?

<details>
<summary>Solution</summary>

| Step | front | rear | Notes |
|------|-------|------|-------|
| start | 0 | 0 | empty: front == rear |
| enqueue 10 | 0 | 1 | data[0] = 10 |
| enqueue 20 | 0 | 2 | data[1] = 20 |
| enqueue 30 | 0 | 3 | data[2] = 30 |
| enqueue 40 | 0 | 4 | data[3] = 40 |
| is_full | 0 | 4 | (4 + 1) % 5 == 0, so **full** |
| dequeue → 10 | 1 | 4 | |
| dequeue → 20 | 2 | 4 | |
| enqueue 50 | 2 | 0 | data[4] = 50, rear wraps to 0 |
| enqueue 60 | 2 | 1 | data[0] = 60; now full again |

Final `data` = [60, 20, 30, 40, 50], with the live queue being 30, 40, 50, 60 (from `front` = 2, wrapping). The 20 in `data[1]` is a stale value in a free slot.

The queue holds at most **4** elements, one fewer than `MAX_SIZE`. With `front == rear` meaning "empty", a completely full array would also have `front == rear`, and the two states could not be told apart. Keeping one slot empty makes "full" a different condition, `(rear + 1) % MAX_SIZE == front`. The alternative is to store a `size` field (as the `Deque` struct in Section 5.6 does) and use all `MAX_SIZE` slots.

</details>

**5.3 ★★ Which outputs can a stack produce?** The numbers 1, 2, 3, 4 are pushed in that order, and you may pop at any time (each number is popped exactly once). Which of these output sequences are possible? For each possible one, give the push/pop sequence; for each impossible one, say where it gets stuck. Then give a simple algorithm that decides any case.

(a) 3 1 2 4   (b) 2 4 3 1   (c) 1 3 2 4   (d) 4 1 2 3

<details>
<summary>Hint</summary>

To output x, every number below x must already be pushed. Once x has been popped, whatever is on top of the stack is the only thing that can come out next, apart from numbers not pushed yet.

</details>

<details>
<summary>Solution</summary>

**(a) 3 1 2 4: impossible.** To output 3, push 1, 2, 3 and pop 3. The stack is now [1, 2] with 2 on top. The next output must be 1, but 1 is under 2.

**(b) 2 4 3 1: possible.** push 1, push 2, pop (2), push 3, push 4, pop (4), pop (3), pop (1).

**(c) 1 3 2 4: possible.** push 1, pop (1), push 2, push 3, pop (3), pop (2), push 4, pop (4).

**(d) 4 1 2 3: impossible.** Outputting 4 first leaves [1, 2, 3] with 3 on top, so the next output must be 3, not 1.

**Algorithm (simulate greedily):** for each wanted output x, push the next unpushed numbers until x has been pushed; then the top of the stack must be x, so pop it, otherwise the sequence is impossible.

```python
def stack_can_produce(out):
    stack, next_in = [], 1
    for x in out:
        while next_in <= x:          # push everything up to x
            stack.append(next_in)
            next_in += 1
        if not stack or stack[-1] != x:
            return False             # x is buried under something else
        stack.pop()
    return True


assert not stack_can_produce([3, 1, 2, 4])
assert stack_can_produce([2, 4, 3, 1])
assert stack_can_produce([1, 3, 2, 4])
assert not stack_can_produce([4, 1, 2, 3])
```

Greedy is safe because pushing is the only way to reach x, and popping anything other than x would output the wrong number. It runs in O(n). The forbidden pattern is "a higher number, then a low one, then a middle one" (like 3, 1, 2): out of 24 orderings of 1..4, exactly 14 are producible (in general, the Catalan number C(n)).

</details>

**5.4 ★★ Shunting-yard and associativity.** Convert `8 - 3 - 2 * ( 1 + 4 )` to postfix with the shunting-yard rules in Section 5.3, using precedence `*` `/` above `+` `-`. Show the operator stack and output after each token. Then show what goes wrong if an operator only pops operators of *strictly* higher precedence.

<details>
<summary>Hint</summary>

The interesting moment is the second `-`, which arrives while the first `-` is on the stack.

</details>

<details>
<summary>Solution</summary>

All four operators are left-associative, so an incoming operator pops everything of higher **or equal** precedence (stopping at a `(`), then pushes itself.

| Token | Operator stack | Output |
|-------|----------------|--------|
| 8 | | 8 |
| - | - | 8 |
| 3 | - | 8 3 |
| - | - | 8 3 - |
| 2 | - | 8 3 - 2 |
| * | - * | 8 3 - 2 |
| ( | - * ( | 8 3 - 2 |
| 1 | - * ( | 8 3 - 2 1 |
| + | - * ( + | 8 3 - 2 1 |
| 4 | - * ( + | 8 3 - 2 1 4 |
| ) | - * | 8 3 - 2 1 4 + |
| end | | 8 3 - 2 1 4 + * - |

Postfix: `8 3 - 2 1 4 + * -`, which evaluates to (8 − 3) − 2 × 5 = **−5**, the correct value.

With "strictly higher" only, the second `-` does not pop the first, and the result is `8 3 2 1 4 + * - -`, which means 8 − (3 − 2 × 5) = **15**. The parser has made `-` right-associative. For `+` and `*` the mistake is invisible (they are associative), which is why it survives testing.

A Python version with the corrected rule:

```python
PREC = {"+": 1, "-": 1, "*": 2, "/": 2}


def to_postfix(tokens):
    out, ops = [], []
    for t in tokens:
        if t in PREC:
            # all four operators are left-associative: pop >= precedence
            while ops and ops[-1] in PREC and PREC[ops[-1]] >= PREC[t]:
                out.append(ops.pop())
            ops.append(t)
        elif t == "(":
            ops.append(t)
        elif t == ")":
            while ops[-1] != "(":
                out.append(ops.pop())
            ops.pop()                  # discard the "("
        else:
            out.append(t)              # operand
    while ops:                         # end of input: flush the stack
        out.append(ops.pop())
    return out


assert to_postfix("8 - 3 - 2 * ( 1 + 4 )".split()) == "8 3 - 2 1 4 + * -".split()
assert to_postfix("3 + 4 * 2 / ( 1 - 5 )".split()) == "3 4 2 * 1 5 - / +".split()
```

A right-associative operator such as exponentiation (`2 ^ 3 ^ 2` = 2^9) is the case where "strictly higher" is the correct rule.

</details>

**5.5 ★★ A queue from two stacks.** Implement a FIFO queue using only two stacks (Python lists used only with `append` and `pop()`), and show that any sequence of n operations takes O(n) total time, so each operation is amortized O(1), even though a single dequeue can take O(n).

<details>
<summary>Hint</summary>

Pushing a stack's contents onto another stack reverses their order. Only do that when the second stack is empty.

</details>

<details>
<summary>Solution</summary>

```python
class TwoStackQueue:
    def __init__(self):
        self.inbox = []    # receives enqueues, newest on top
        self.outbox = []   # serves dequeues, oldest on top

    def enqueue(self, x):
        self.inbox.append(x)

    def dequeue(self):
        if not self.outbox:
            while self.inbox:                     # reverse inbox into outbox
                self.outbox.append(self.inbox.pop())
        if not self.outbox:
            raise IndexError("dequeue from empty queue")
        return self.outbox.pop()


q = TwoStackQueue()
for x in (1, 2, 3):
    q.enqueue(x)
assert q.dequeue() == 1          # moves 3, 2, 1 into outbox; pops 1
q.enqueue(4)                     # goes to inbox; outbox still has 2, 3
assert [q.dequeue(), q.dequeue(), q.dequeue()] == [2, 3, 4]
```

**Correctness.** Every element in `outbox` is older than every element in `inbox`, and `outbox` has the oldest element on top. Refilling only when `outbox` is empty preserves both facts: the transfer reverses `inbox`, so its oldest element ends on top.

**Amortized cost.** Follow a single element: it is pushed onto `inbox` once, popped from `inbox` once, pushed onto `outbox` once and popped from `outbox` once. That is at most 4 stack operations per element over its whole life, so n operations cost O(n) in total, amortized O(1) each (aggregate analysis, Chapter 1). A single dequeue that triggers a transfer of k elements costs O(k), so the worst case per operation is O(n). If you need a hard O(1) bound per operation, use the circular queue from Section 5.5 instead. The two-stack queue earns its keep where only stacks are cheap, for example in purely functional languages where an immutable list is a stack.

</details>

**5.6 ★★ Bounded undo history.** The editor in Section 5.3 saves a full state on every action and never forgets any. You must cap it at the last 100 states: when a 101st is saved, the oldest is discarded. Undo still restores the newest state. Which structure should hold the undo history, and why not the array-based `Stack` from Section 5.2?

<details>
<summary>Solution</summary>

The history now needs two operations at **different** ends: push and pop at the newest end (save and undo), and remove at the oldest end (discard when over the limit). That is a deque, not a stack.

- **Array-based `Stack`:** discarding the bottom element means shifting all 99 others down, O(n) per action. It works for 100 entries but scales badly and is the wrong shape.
- **Linked list stack:** the bottom node is at the far end of a singly linked chain, so removing it needs a walk (Exercise 4.2). A doubly linked list with head and tail pointers works, at the cost of a node allocation per action.
- **Circular buffer of capacity 100** (Section 5.5): save writes at `rear` and, if the buffer is full, advances `front` to drop the oldest; undo steps `rear` back by one. Every operation is O(1), there is no allocation after setup, and memory is fixed at 100 slots. This is the right choice.

Python's `collections.deque(maxlen=100)` is exactly this:

```python
from collections import deque

undo = deque(maxlen=3)        # 3 instead of 100 to keep the example short
for state in ["a", "b", "c", "d", "e"]:
    undo.append(state)         # appending to a full deque drops the oldest
assert list(undo) == ["c", "d", "e"]
assert undo.pop() == "e"      # undo restores the newest state
```

The redo stack needs no cap: it can never hold more than the undo history did, and it is cleared on every new action.

</details>

**5.7 ★★★ Sliding window maximum.** Given an array `a` of n numbers and a window size k, output the maximum of every window `a[i : i + k]`. The obvious approach is O(nk). Use a deque to do it in O(n) total.

For example, `a = [1, 3, -1, -3, 5, 3, 6, 7]` and k = 3 gives `[3, 3, 5, 5, 6, 7]`.

<details>
<summary>Hint</summary>

Store indices in the deque. If a newer element is at least as large as an older one, the older one can never be the maximum of any future window, so it can be thrown away.

</details>

<details>
<summary>Solution</summary>

Keep a deque of indices whose values are strictly decreasing from front to back. The front is always the maximum of the current window.

For each new index i:

1. Pop from the back every index whose value is ≤ `a[i]`: those elements are older and no larger, so they can never be a window maximum again.
2. Push i at the back.
3. If the front index has slid out of the window (≤ i − k), pop it from the front.
4. Once the first full window is reached (i ≥ k − 1), output `a[front]`.

```python
from collections import deque


def window_max(a, k):
    dq = deque()      # indices; their values are strictly decreasing
    out = []
    for i, x in enumerate(a):
        while dq and a[dq[-1]] <= x:   # x dominates these: drop them
            dq.pop()
        dq.append(i)
        if dq[0] <= i - k:             # front index has left the window
            dq.popleft()
        if i >= k - 1:
            out.append(a[dq[0]])
    return out


assert window_max([1, 3, -1, -3, 5, 3, 6, 7], 3) == [3, 3, 5, 5, 6, 7]
assert window_max([5, 4, 3, 2, 1], 2) == [5, 4, 3, 2]
assert window_max([2, 2, 2], 1) == [2, 2, 2]
```

Trace of the example (deque shown as values):

| i | a[i] | Deque after step | Output |
|---|------|------------------|--------|
| 0 | 1 | [1] | |
| 1 | 3 | [3] | |
| 2 | −1 | [3, −1] | 3 |
| 3 | −3 | [3, −1, −3] | 3 |
| 4 | 5 | [5] | 5 |
| 5 | 3 | [5, 3] | 5 |
| 6 | 6 | [6] | 6 |
| 7 | 7 | [7] | 7 |

**Why O(n):** each index is pushed onto the deque once and popped at most once (from one end or the other), so all the `while` loops together do at most n pops. Each deque operation is O(1) at either end, which is what a deque (Section 5.6) is for. At most one front pop is needed per step, because the window advances by one index at a time. This is one of the standard uses of a deque that is neither a stack nor a queue: elements leave from both ends.

</details>

---

## Where this connects

- [Chapter 9: Heaps and Priority Queues](ch09-heaps-and-priority-queues.md). The priority queue, when FIFO and LIFO are both the wrong order
- [Chapter 21: Algorithm Design Using Data Structures](../volume-3/ch21-algorithm-design-using-data-structures.md). The stack as the implicit structure behind all recursion
