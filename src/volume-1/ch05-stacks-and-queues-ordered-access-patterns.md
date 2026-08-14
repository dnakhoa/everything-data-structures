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
- Operators: pop operators with higher precedence, then push
- Left parenthesis: push
- Right parenthesis: pop until left parenthesis

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
Enqueue 4, 5, 6, then dequeue twice, then enqueue 7:
         front
            │
            ▼
┌────┬────┬────┬────┬────┬────┐
│ 6  │ 7  │ -- │ -- │ 4  │ 5  │
└────┴────┴────┴────┴────┴────┘
                        │
                       rear
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
- Decrease/increase key: O(log n) or O(1) with index

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

queue = Queue()
threading.Thread(target=producer, args=(queue,)).start()
threading.Thread(target=consumer, args=(queue,)).start()
```

## 5.9 Historical Context

The stack and queue concepts emerged in the 1950s as programmers recognized common access patterns. Alan Turing's 1949 work on subroutine linkage predated formal stack concepts, the call stack was an informal but essential mechanism.

The term "stack" became standard in the 1960s, replacing earlier terms like "pushdown list." The queue concept was formalized alongside it.

Edsger Dijkstra's 1968 paper on " cooperating sequential processes" introduced semaphores and discussed bounded buffers (producer-consumer) as fundamental synchronization problems.

---

## Where this connects

- [Chapter 9: Heaps and Priority Queues](ch09-heaps-and-priority-queues.md). The priority queue, when FIFO and LIFO are both the wrong order
- [Chapter 21: Algorithm Design Using Data Structures](../volume-3/ch21-algorithm-design-using-data-structures.md). The stack as the implicit structure behind all recursion
