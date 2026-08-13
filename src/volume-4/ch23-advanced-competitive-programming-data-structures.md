# Chapter 23: Advanced Competitive Programming Data Structures

## 23.1 Introduction to Competitive Programming Data Structures

Competitive programming demands data structures that excel under specific constraints: fast operations, minimal memory, and elegant implementation. While the foundational structures covered earlier serve as building blocks, competitive programming has developed specialized structures optimized for algorithmic challenges.

This chapter covers structures essential for International Olympiad in Informatics (IOI), International Collegiate Programming Contest (ICPC), and Codeforces/Topcoder competitions. These structures often sacrifice generality or worst-case guarantees for practical performance and competitive implementation.

## 23.2 Segment Trees with Lazy Propagation

### Conceptual Foundation

A segment tree is a binary tree that represents an array segment, enabling efficient range queries and updates. Lazy propagation defers updates until necessary, dramatically improving performance for range modifications.

**Core Properties:**
- Represents array in binary tree form
- Each node stores aggregate of its segment (sum, min, max, etc.)
- Height: O(log n)
- Space: O(n) with 4n safe upper bound

### Mechanism: Range Query with Lazy Propagation

```python
class SegmentTree:
    def __init__(self, arr):
        self.n = len(arr)
        self.tree = [0] * (4 * self.n)
        self.lazy = [0] * (4 * self.n)
        self._build(1, 0, self.n - 1, arr)

    def _build(self, node, l, r, arr):
        if l == r:
            self.tree[node] = arr[l]
        else:
            mid = (l + r) // 2
            self._build(node * 2, l, mid, arr)
            self._build(node * 2 + 1, mid + 1, r, arr)
            self.tree[node] = self.tree[node * 2] + self.tree[node * 2 + 1]

    def _push(self, node, l, r):
        """Push lazy values to children"""
        if self.lazy[node] != 0:
            mid = (l + r) // 2
            # Apply to left child
            self.tree[node * 2] += self.lazy[node] * (mid - l + 1)
            self.lazy[node * 2] += self.lazy[node]
            # Apply to right child
            self.tree[node * 2 + 1] += self.lazy[node] * (r - mid)
            self.lazy[node * 2 + 1] += self.lazy[node]
            self.lazy[node] = 0

    def range_update(self, node, l, r, ql, qr, val):
        if ql <= l and r <= qr:
            self.tree[node] += val * (r - l + 1)
            self.lazy[node] += val
            return

        if r < ql or l > qr:
            return

        self._push(node, l, r)
        mid = (l + r) // 2
        self.range_update(node * 2, l, mid, ql, qr, val)
        self.range_update(node * 2 + 1, mid + 1, r, ql, qr, val)
        self.tree[node] = self.tree[node * 2] + self.tree[node * 2 + 1]

    def range_query(self, node, l, r, ql, qr):
        if ql <= l and r <= qr:
            return self.tree[node]

        if r < ql or l > qr:
            return 0

        self._push(node, l, r)
        mid = (l + r) // 2
        return (self.range_query(node * 2, l, mid, ql, qr) +
                self.range_query(node * 2 + 1, mid + 1, r, ql, qr))
```

### Complexity Analysis

| Operation | Time Complexity | Space |
|-----------|----------------|-------|
| Build | O(n) | O(n) |
| Range Query | O(log n) | - |
| Range Update | O(log n) | - |
| Point Query | O(log n) | - |
| Point Update | O(log n) | - |

### Advanced Variants

**Merge Sort Tree**: For k-th smallest queries, store sorted vectors at each node.

**Segment Tree Beats**: For range min/max updates with constraints.

**Dynamic Segment Tree**: For values outside initial range, create nodes on demand.

## 23.3 Fenwick Trees (Binary Indexed Trees)

### Conceptual Foundation

A Fenwick tree, invented by Boris Ryabko in 1989 and popularized by Peter Fenwick, provides O(log n) prefix operations with minimal memory. It's simpler than segment trees for prefix-sum based queries.

**Key Insight:** Use binary representation to represent ranges as sums of power-of-two sized blocks.

### Mechanism

```python
class FenwickTree:
    def __init__(self, n):
        self.n = n
        self.bit = [0] * (n + 1)

    def add(self, idx, delta):
        """Add delta at position idx (1-indexed)"""
        while idx <= self.n:
            self.bit[idx] += delta
            idx += idx & (-idx)

    def prefix_sum(self, idx):
        """Sum of [1, idx]"""
        result = 0
        while idx > 0:
            result += self.bit[idx]
            idx -= idx & (-idx)
        return result

    def range_sum(self, l, r):
        """Sum of [l, r]"""
        return self.prefix_sum(r) - self.prefix_sum(l - 1)

    def find_kth(self, k):
        """Find smallest idx with prefix_sum >= k"""
        idx = 0
        bit_mask = 1 << (self.n.bit_length() - 1)
        while bit_mask:
            t_idx = idx + bit_mask
            if t_idx <= self.n and self.bit[t_idx] < k:
                idx = t_idx
                k -= self.bit[t_idx]
            bit_mask >>= 1
        return idx + 1
```

### 2D Fenwick Tree

```python
class BIT2D:
    def __init__(self, n, m):
        self.n, self.m = n, m
        self.bit = [[0] * (m + 1) for _ in range(n + 1)]

    def add(self, x, y, delta):
        i = x
        while i <= self.n:
            j = y
            while j <= self.m:
                self.bit[i][j] += delta
                j += j & (-j)
            i += i & (-i)

    def prefix_sum(self, x, y):
        result = 0
        i = x
        while i > 0:
            j = y
            while j > 0:
                result += self.bit[i][j]
                j -= j & (-j)
            i -= i & (-i)
        return result
```

## 23.4 Heavy-Light Decomposition

### Conceptual Foundation

Heavy-Light Decomposition (HLD), introduced by Sleator and Tarjan, enables O(log n) path queries on trees by decomposing the tree into chains where heavy edges form continuous segments.

**Key Concepts:**
- Heavy edge: Edge to child with largest subtree
- Light edge: All other edges
- Heavy path: Path following heavy edges
- Decomposition ensures O(log n) chains per path

### Mechanism

```python
class HeavyLightDecomposition:
    def __init__(self, n, edges):
        self.n = n
        self.adj = [[] for _ in range(n)]
        for u, v in edges:
            self.adj[u].append(v)
            self.adj[v].append(u)

        self.parent = [-1] * n
        self.depth = [0] * n
        self.size = [0] * n
        self.heavy = [-1] * n
        self.head = [0] * n
        self.pos = [0] * n
        self.cur_pos = 0

        self._dfs(0)
        self._decompose(0, 0)

    def _dfs(self, v):
        self.size[v] = 1
        max_size = 0
        for u in self.adj[v]:
            if u != self.parent[v]:
                self.parent[u] = v
                self.depth[u] = self.depth[v] + 1
                self._dfs(u)
                self.size[v] += self.size[u]
                if self.size[u] > max_size:
                    max_size = self.size[u]
                    self.heavy[v] = u

    def _decompose(self, v, h):
        self.head[v] = h
        self.pos[v] = self.cur_pos
        self.cur_pos += 1
        if self.heavy[v] != -1:
            self._decompose(self.heavy[v], h)
        for u in self.adj[v]:
            if u != self.parent[v] and u != self.heavy[v]:
                self._decompose(u, u)

    def query_path(self, u, v, segtree):
        """Query on path u-v using segment tree"""
        result = 0
        while self.head[u] != self.head[v]:
            if self.depth[self.head[u]] < self.depth[self.head[v]]:
                u, v = v, u
            head_u = self.head[u]
            result += segtree.range_query(self.pos[head_u], self.pos[u])
            u = self.parent[head_u]
        # Same head
        if self.depth[u] > self.depth[v]:
            u, v = v, u
        result += segtree.range_query(self.pos[u], self.pos[v])
        return result
```

### Applications

| Query Type | Complexity | Example |
|------------|------------|---------|
| Path sum | O(log² n) | Sum of node values on path |
| Path max | O(log² n) | Maximum on path |
| Path update | O(log² n) | Add value to all nodes on path |
| Subtree query | O(log n) | Query entire subtree |

## 23.5 Link-Cut Trees

### Conceptual Foundation

Link-cut trees, invented by Sleator and Tarjan in 1983, support dynamic forest operations: linking trees, cutting edges, and querying aggregates on paths—all in O(log n) amortized time.

**Operations:**
- **link(u, v)**: Connect u as child of v
- **cut(u)**: Remove edge between u and parent
- **evert(u)**: Make u the root
- **path_query(u, v)**: Aggregate on u-v path

### Mechanism

```python
class LinkCutTree:
    class Node:
        def __init__(self, val):
            self.val = val
            self.left = None
            self.right = None
            self.parent = None
            self.rev = False
            self.sum = val

    def _push(self, x):
        if x and x.rev:
            x.left, x.right = x.right, x.left
            if x.left: x.left.rev ^= True
            if x.right: x.right.rev ^= True
            x.rev = False

    def _update(self, x):
        x.sum = x.val
        if x.left: x.sum ^= x.left.sum
        if x.right: x.sum ^= x.right.sum

    def _rotate(self, x):
        p = x.parent
        g = p.parent
        if p == p.parent.left:
            p.parent.left = x
        else:
            p.parent.right = x
        x.parent = g.parent
        if x == p.left:
            p.left = x.right
            if x.right: x.right.parent = p
            x.right = p
        else:
            p.right = x.left
            if x.left: x.left.parent = p
            x.left = p
        p.parent = x
        self._update(p)
        self._update(x)

    def _splay(self, x):
        stack = []
        y = x
        stack.append(y)
        while y.parent:
            stack.append(y.parent)
            y = y.parent
        while stack:
            self._push(stack.pop())
        while x.parent:
            self._push(x.parent)
            if x == x.parent.left:
                if x.parent.parent and x.parent == x.parent.parent.left:
                    self._rotate(x.parent)
                self._rotate(x)
            else:
                if x.parent.parent and x.parent == x.parent.parent.right:
                    self._rotate(x.parent)
                self._rotate(x)

    def access(self, x):
        last = None
        while x:
            self._splay(x)
            x.right = last
            self._update(x)
            last = x
            x = x.parent
        return last

    def make_root(self, x):
        self.access(x)
        self._splay(x)
        x.rev ^= True

    def link(self, x, y):
        self.make_root(x)
        x.parent = y

    def cut(self, x, y):
        self.make_root(x)
        self.access(y)
        self._splay(y)
        if y.left == x:
            y.left.parent = None
            y.left = None
            self._update(y)

    def query_path(self, x, y):
        self.make_root(x)
        self.access(y)
        self._splay(y)
        return y.sum
```

## 23.6 Mo's Algorithm

### Conceptual Foundation

Mo's algorithm answers offline range queries in O((n + q)√n) by reordering queries to minimize pointer movement. It's particularly effective for queries with additive functions.

**Key Insight:** Sort queries by block of L, then by R for optimal pointer movement.

### Mechanism

```python
class MoSolver:
    def __init__(self, arr, queries):
        self.arr = arr
        self.queries = queries
        self.block_size = int(len(arr) ** 0.5)
        self.answers = [0] * len(queries)
        self._process()

    def _process(self):
        # Sort queries: block by L, then by R (alternating for optimization)
        self.queries.sort(key=lambda x: (
            x.l // self.block_size,
            x.r if (x.l // self.block_size) % 2 == 0 else -x.r
        ))

        cur_l, cur_r = 0, -1
        for q in self.queries:
            while cur_l > q.l:
                cur_l -= 1
                self._add(cur_l)
            while cur_r < q.r:
                cur_r += 1
                self._add(cur_r)
            while cur_l < q.l:
                self._remove(cur_l)
                cur_l += 1
            while cur_r > q.r:
                self._remove(cur_r)
                cur_r -= 1
            self.answers[q.idx] = self._get_answer()

    def _add(self, idx):
        # Update frequency and current answer
        pass

    def _remove(self, idx):
        # Update frequency and current answer
        pass

    def _get_answer(self):
        return 0
```

### Variants

**Mo's on Trees:** Use Euler tour to flatten tree into array.

**3D Mo's:** Add time dimension for updates.

**Mo's with Rollback:** For parallel binary search.

## 23.7 Suffix Automaton

### Conceptual Foundation

A suffix automaton (SAM) recognizes all substrings of a string in O(n) construction time, with at most 2n-1 states. It's a deterministic acyclic finite automaton.

**Properties:**
- Minimum DFA for all substrings
- Size ≤ 2n - 1
- Links form suffix links (longest proper suffix)

### Mechanism

```python
class SuffixAutomaton:
    def __init__(self):
        self.next = [dict()]  # state 0: initial
        self.link = [-1]
        self.len = [0]
        self.last = 0

    def extend(self, c):
        p = self.last
        cur = len(self.next)
        self.next.append(dict())
        self.len.append(self.len[p] + 1)
        self.link.append(0)

        while p >= 0 and c not in self.next[p]:
            self.next[p][c] = cur
            p = self.link[p]

        if p == -1:
            self.link[cur] = 0
        else:
            q = self.next[p][c]
            if self.len[p] + 1 == self.len[q]:
                self.link[cur] = q
            else:
                clone = len(self.next)
                self.next.append(self.next[q].copy())
                self.len.append(self.len[p] + 1)
                self.link.append(self.link[q])

                while p >= 0 and self.next[p].get(c) == q:
                    self.next[p][c] = clone
                    p = self.link[p]

                self.link[q] = self.link[cur] = clone

        self.last = cur
        return cur
```

### Applications

| Query | Complexity | Description |
|-------|------------|-------------|
| Substring check | O(m) | Follow transitions |
| Distinct substrings | O(n) | Sum(len[v] - len[link[v]]) |
| Longest common substring | O(n log n) | With two SAMs |
| Occurrences | O(m) | Follow + subtree sum |

## 23.8 Palindromic Tree (Eertree)

### Conceptual Foundation

The Palindromic Tree, invented by Mikhail Rubinchik and later popularized, stores all distinct palindromic substrings. It uses two root nodes: odd length (-1) and even length (0).

**Properties:**
- O(n) construction
- O(n) distinct palindromes maximum
- Each node represents a palindrome

### Mechanism

```python
class PalindromicTree:
    class Node:
        def __init__(self, length, pos):
            self.length = length
            self.pos = pos  # ending position
            self.next = {}
            self.link = 0

    def __init__(self, s):
        self.s = s
        self.nodes = [self.Node(-1, -1), self.Node(0, -1)]
        self.nodes[0].link = 0
        self.nodes[1].link = 0
        self.last = 1
        self.size = 2
        self.num_pal = 0

        for i, c in enumerate(s):
            self._add_char(i, c)

    def _add_char(self, pos, c):
        cur = self.last
        while True:
            cur_len = self.nodes[cur].length
            if pos - cur_len - 1 >= 0 and self.s[pos - cur_len - 1] == c:
                break
            cur = self.nodes[cur].link

        if c in self.nodes[cur].next:
            self.last = self.nodes[cur].next[c]
            return

        new_node = self.Node(self.nodes[cur].length + 2, pos)
        self.nodes.append(new_node)
        self.nodes[cur].next[c] = self.size
        self.size += 1

        if new_node.length == 1:
            new_node.link = 1
        else:
            tmp = self.nodes[cur].link
            while True:
                if pos - self.nodes[tmp].length - 1 >= 0 and \
                   self.s[pos - self.nodes[tmp].length - 1] == c:
                    break
                tmp = self.nodes[tmp].link
            new_node.link = self.nodes[tmp].next[c]

        self.last = self.size - 1
        self.num_pal += 1
```

## 23.9 Wavelet Trees

### Conceptual Foundation

Wavelet trees answer range quantile queries (k-th smallest) in O(log σ) where σ is alphabet size, using only O(n log σ) space. They recursively partition based on the most significant bit.

**Key Operation:** K-th smallest in subarray [l, r]

### Mechanism

```python
class WaveletTree:
    def __init__(self, arr, lo, hi):
        self.lo = lo
        self.hi = hi
        self.b = []

        if lo >= hi or not arr:
            return

        mid = (lo + hi + 1) // 2
        self.c = lo

        left_arr = []
        right_arr = []

        for x in arr:
            if x < mid:
                left_arr.append(x)
            else:
                right_arr.append(x)
            self.b.append(len(left_arr))

        self.left = WaveletTree(left_arr, lo, mid - 1)
        self.right = WaveletTree(right_arr, mid, hi)

    def kth(self, l, r, k):
        if l > r:
            return None
        if self.lo == self.hi:
            return self.lo

        in_left = self.b[r] - (self.b[l - 1] if l > 0 else 0)
        left_l = 1 if l == 0 else self.b[l - 1] + 1
        left_r = left_l + in_left - 1

        if k <= in_left:
            return self.left.kth(left_l, left_r, k)
        else:
            right_l = r - (self.b[r] - self.b[r - 1] if r > 0 else 0) - in_left + 1
            right_r = r - in_left
            return self.right.kth(right_l, right_r, k - in_left)
```

## 23.10 Li Chao Trees

### Conceptual Foundation

Li Chao trees maintain dynamic line sets for point queries in O(log C) where C is coordinate range. They're ideal for online convex hull trick scenarios.

**Operations:**
- Add line (insert)
- Query minimum at point

### Mechanism

```python
class LiChaoNode:
    def __init__(self, line=None):
        self.line = line  # (m, b) for y = mx + b
        self.left = None
        self.right = None

class LiChaoTree:
    def __init__(self, x_left, x_right):
        self.x_left = x_left
        self.x_right = x_right
        self.root = None

    def f(self, line, x):
        return line[0] * x + line[1]

    def add_line(self, line):
        self.root = self._add_line(self.root, self.x_left, self.x_right, line)

    def _add_line(self, node, l, r, new_line):
        if not node:
            return LiChaoNode(new_line)

        mid = (l + r) // 2
        left_is_better = self.f(new_line, l) < self.f(node.line, l)
        mid_is_better = self.f(new_line, mid) < self.f(node.line, mid)

        if mid_is_better:
            node.line, new_line = new_line, node.line

        if r == l:
            return node

        if left_is_better != mid_is_better:
            node.left = self._add_line(node.left, l, mid, new_line)
        else:
            node.right = self._add_line(node.right, mid + 1, r, new_line)

        return node

    def query(self, x):
        return self._query(self.root, self.x_left, self.x_right, x)

    def _query(self, node, l, r, x):
        if not node:
            return float('inf')
        if l == r:
            return self.f(node.line, x)
        mid = (l + r) // 2
        if x <= mid:
            return min(self.f(node.line, x),
                      self._query(node.left, l, mid, x))
        else:
            return min(self.f(node.line, x),
                      self._query(node.right, mid + 1, r, x))
```

## 23.11 Sparse Tables

### Conceptual Foundation

Sparse tables answer static range queries in O(1) after O(n log n) preprocessing, but only for idempotent operations (min, max, gcd).

**Limitation:** Not for sum (not idempotent).

### Mechanism

```python
class SparseTable:
    def __init__(self, arr, op=min):
        self.n = len(arr)
        self.log = [0] * (self.n + 1)
        for i in range(2, self.n + 1):
            self.log[i] = self.log[i // 2] + 1

        self.k = self.log[self.n] + 1
        self.st = [[0] * self.n for _ in range(self.k)]
        self.st[0] = arr[:]

        for k in range(1, self.k):
            for i in range(self.n - (1 << k) + 1):
                self.st[k][i] = op(self.st[k-1][i],
                                   self.st[k-1][i + (1 << (k-1))])

    def query(self, l, r):
        j = self.log[r - l + 1]
        return min(self.st[j][l], self.st[j][r - (1 << j) + 1])
```

## 23.12 Cartesian Trees

### Conceptual Foundation

A Cartesian tree maintains array order via inorder traversal while enforcing heap property. O(n) construction using monotonic stack.

**Properties:**
- Inorder traversal gives original array
- Heap property on values
- Unique for given array

### Mechanism

```python
def build_cartesian(arr):
    n = len(arr)
    parent = [-1] * n
    left = [-1] * n
    right = [-1] * n

    stack = []
    for i in range(n):
        last = -1
        while stack and arr[stack[-1]] > arr[i]:
            last = stack.pop()

        if stack:
            right[stack[-1]] = i
            parent[i] = stack[-1]

        if last != -1:
            parent[last] = i
            left[i] = last

        stack.append(i)

    root = stack[0] if stack else -1
    return root, parent, left, right
```

## 23.13 Sqrt Decomposition

### Conceptual Foundation

Sqrt decomposition divides array into blocks of size √n, enabling O(√n) range queries. Simpler than segment trees but slower.

### Mechanism

```python
class SqrtDecomposition:
    def __init__(self, arr):
        self.arr = arr
        self.n = len(arr)
        self.block_size = int(self.n ** 0.5)
        self.n_blocks = (self.n + self.block_size - 1) // self.block_size
        self.block_sum = [0] * self.n_blocks
        self.block_min = [float('inf')] * self.n_blocks

        for i in range(self.n):
            b = i // self.block_size
            self.block_sum[b] += arr[i]
            self.block_min[b] = min(self.block_min[b], arr[i])

    def range_query(self, l, r):
        result = 0
        while l <= r:
            if l % self.block_size == 0 and l + self.block_size - 1 <= r:
                result += self.block_sum[l // self.block_size]
                l += self.block_size
            else:
                result += self.arr[l]
                l += 1
        return result
```

## 23.14 DSU with Rollback

### Conceptual Foundation

DSU with rollback supports undoing union operations, essential for offline queries and divide-and-conquer approaches.

### Mechanism

```python
class DSU:
    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n
        self.changes = []

    def find(self, x):
        while self.parent[x] != x:
            x = self.parent[x]
        return x

    def union(self, x, y):
        x = self.find(x)
        y = self.find(y)
        if x == y:
            self.changes.append((-1, -1, -1))
            return

        if self.size[x] < self.size[y]:
            x, y = y, x

        self.changes.append((y, self.parent[y], self.size[x]))
        self.parent[y] = x
        self.size[x] += self.size[y]

    def snapshot(self):
        return len(self.changes)

    def rollback(self, state):
        while len(self.changes) > state:
            y, parent_y, size_x = self.changes.pop()
            if y == -1:
                continue
            x = self.parent[y]
            self.size[x] = size_x
            self.parent[y] = parent_y
```

---

## Where this connects

- [Chapter 21: Algorithm Design Using Data Structures](../volume-3/ch21-algorithm-design-using-data-structures.md) — the paradigms these structures accelerate
- [Chapter 25: Complete Selection Guide and Complexity Reference](ch25-complete-selection-guide-and-complexity-reference.md) — the selection matrix for picking among them
