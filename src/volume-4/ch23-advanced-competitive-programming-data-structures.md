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

Link-cut trees, invented by Sleator and Tarjan in 1983, support dynamic forest operations: linking trees, cutting edges, and querying aggregates on paths, all in O(log n) amortized time.

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

    def _is_root(self, x):
        """True if x is the root of its splay tree (its parent pointer,
        if any, is a path-parent pointer, not a splay-tree edge)."""
        return x.parent is None or (x.parent.left is not x and
                                    x.parent.right is not x)

    def _push(self, x):
        if x and x.rev:
            x.left, x.right = x.right, x.left
            if x.left: x.left.rev ^= True
            if x.right: x.right.rev ^= True
            x.rev = False

    def _update(self, x):
        x.sum = x.val
        if x.left: x.sum += x.left.sum
        if x.right: x.sum += x.right.sum

    def _rotate(self, x):
        p = x.parent
        g = p.parent
        if not self._is_root(p):
            if g.left is p:
                g.left = x
            else:
                g.right = x
        x.parent = g
        if x is p.left:
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
        stack = [x]
        y = x
        while not self._is_root(y):
            y = y.parent
            stack.append(y)
        while stack:
            self._push(stack.pop())
        while not self._is_root(x):
            p = x.parent
            if not self._is_root(p):
                g = p.parent
                if (g.left is p) == (p.left is x):
                    self._rotate(p)   # zig-zig
                else:
                    self._rotate(x)   # zig-zag
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
        self._push(x)
        if y.left is x and x.right is None:
            x.parent = None
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

**Mo's with Rollback:** For answers that are cheap to extend but hard to shrink (maximum, DSU connectivity): each query rebuilds from its block boundary and rolls the left-side additions back.

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
        """k-th smallest (1-indexed) among positions l..r (0-indexed, inclusive)"""
        if l > r:
            return None
        if self.lo == self.hi:
            return self.lo

        left_before = self.b[l - 1] if l > 0 else 0   # left-goers before l
        in_left = self.b[r] - left_before              # left-goers in [l, r]

        if k <= in_left:
            return self.left.kth(left_before, left_before + in_left - 1, k)
        else:
            right_before = l - left_before
            in_right = (r - l + 1) - in_left
            return self.right.kth(right_before, right_before + in_right - 1,
                                  k - in_left)
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
        self.op = op
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
        return self.op(self.st[j][l], self.st[j][r - (1 << j) + 1])
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

## Exercises

Difficulty: ★ check your understanding · ★★ apply it · ★★★ stretch.

**23.1 ★ Which cells does a Fenwick tree touch?** For the `FenwickTree` of Section 23.3 with `n = 8`, list the indices of `bit[]` that are read or written by each call: (a) `add(5, x)`, (b) `add(3, x)`, (c) `prefix_sum(7)`, (d) `prefix_sum(6)`. Then say which range of the original array `bit[6]` covers.

<details>
<summary>Solution</summary>

`idx & (-idx)` isolates the lowest set bit. `add` climbs by adding it; `prefix_sum` descends by subtracting it.

| Call | Steps | Indices touched |
|------|-------|-----------------|
| `add(5, x)` | 5 (101) → 6 (110) → 8 (1000) → 16 stops | 5, 6, 8 |
| `add(3, x)` | 3 (011) → 4 (100) → 8 → 16 stops | 3, 4, 8 |
| `prefix_sum(7)` | 7 (111) → 6 (110) → 4 (100) → 0 stops | 7, 6, 4 |
| `prefix_sum(6)` | 6 (110) → 4 (100) → 0 stops | 6, 4 |

`bit[i]` covers the `lowbit(i)` positions ending at `i`. `lowbit(6) = 2`, so `bit[6]` holds `a[5] + a[6]` (1-indexed). That is why `prefix_sum(7)` is `bit[7] + bit[6] + bit[4]` = `a[7]` + `a[5..6]` + `a[1..4]`: three disjoint power-of-two blocks, one per set bit of 7.

</details>

**23.2 ★ Build and query a sparse table.** Build the `SparseTable` of Section 23.11 for `arr = [5, 2, 4, 7, 1, 3]` with `op=min`. Write out the meaningful entries of `st[0]`, `st[1]` and `st[2]`, then evaluate `query(1, 5)` and `query(0, 3)`. Finally, show with these numbers why the same query trick gives a wrong answer if you build the table with addition instead.

<details>
<summary>Hint</summary>

`st[k][i]` is the minimum of the `2^k` elements starting at `i`. A query covers `[l, r]` with two windows of length `2^j` that may overlap.

</details>

<details>
<summary>Solution</summary>

```
st[0] = [5, 2, 4, 7, 1, 3]        windows of length 1
st[1] = [2, 2, 4, 1, 1]           min(a[i], a[i+1]),  i = 0..4
st[2] = [2, 1, 1]                 min(st[1][i], st[1][i+2]),  i = 0..2
```

(The code allocates `n` slots per row; the trailing slots stay 0 and are never read.)

- `query(1, 5)`: length 5, `j = log[5] = 2`. Windows `[1..4]` and `[2..5]`: `min(st[2][1], st[2][2]) = min(1, 1) = 1`.
- `query(0, 3)`: length 4, `j = 2`. Both windows are `[0..3]`: `min(st[2][0], st[2][0]) = 2`.

With addition, `query(1, 5)` would return `sum(a[1..4]) + sum(a[2..5]) = 14 + 15 = 29`, but the true sum is `2 + 4 + 7 + 1 + 3 = 17`. Positions 2, 3 and 4 are counted twice. The overlap is harmless for min, max and gcd because `op(x, x) = x` (idempotence); it is fatal for sum. A sum query on a sparse table must instead use disjoint power-of-two blocks, which costs O(log n), at which point a Fenwick tree is simpler.

</details>

**23.3 ★★ Trace lazy propagation.** Build the `SegmentTree` of Section 23.2 on `[1, 2, 3, 4]`. Node 1 is the root covering `[0, 3]`, nodes 2 and 3 cover `[0, 1]` and `[2, 3]`, and nodes 4 to 7 are the leaves. Give `tree[1..7]` and `lazy[1..7]` (a) after the build, (b) after `range_update(1, 0, 3, 1, 3, 2)` (add 2 to positions 1 to 3), and (c) after `range_query(1, 0, 3, 2, 2)`. What does the query return? Which values in `tree[]` were stale between (b) and (c), and why is that safe?

<details>
<summary>Hint</summary>

An update stops descending at any node whose segment is fully inside `[ql, qr]`. Children are only brought up to date when a later operation needs to pass through that node.

</details>

<details>
<summary>Solution</summary>

| Node | Segment | (a) tree | (b) tree | (b) lazy | (c) tree | (c) lazy |
|------|---------|----------|----------|----------|----------|----------|
| 1 | [0,3] | 10 | 16 | 0 | 16 | 0 |
| 2 | [0,1] | 3 | 5 | 0 | 5 | 0 |
| 3 | [2,3] | 7 | 11 | 2 | 11 | 0 |
| 4 | [0,0] | 1 | 1 | 0 | 1 | 0 |
| 5 | [1,1] | 2 | 4 | 2 | 4 | 2 |
| 6 | [2,2] | 3 | 3 | 0 | 5 | 2 |
| 7 | [3,3] | 4 | 4 | 0 | 6 | 2 |

All lazy values are 0 after the build.

Update trace: node 1 is partly covered, so it pushes (nothing pending) and recurses. Node 2 is partly covered: node 4 is disjoint, node 5 is fully covered and gets `tree += 2·1`, `lazy += 2`. Node 2 recomputes to `1 + 4 = 5`. Node 3 is fully covered: `tree += 2·2 = 4` gives 11, `lazy[3] = 2`, and the recursion stops there. Node 1 recomputes to `5 + 11 = 16`.

Query trace: node 1 is partial, pushes nothing. Node 3 is partial for `[2, 2]`, so `_push(3)` adds `2·1` to each child and sets `lazy[3] = 0`. Node 6 is fully covered and returns **5**, which is `3 + 2`.

Between (b) and (c), `tree[6]` and `tree[7]` were stale (3 and 4 instead of 5 and 6). That is safe because every path to them goes through node 3, and any operation that passes through node 3 calls `_push` first. Node 3's own value was correct the whole time. The leftover `lazy` values on leaves 5, 6 and 7 are never read, since `_push` is only called on nodes that recurse.

</details>

**23.4 ★★ Trace a suffix automaton with a clone.** Run `SuffixAutomaton.extend` on `"a"`, `"b"`, `"b"` in that order. Give the final `next`, `link` and `len` arrays, explain why the third call creates a clone, and use the formula from Section 23.7 to count distinct substrings of `"abb"`.

<details>
<summary>Hint</summary>

The clone happens when walking suffix links finds a transition on `c` to a state `q` with `len[q] > len[p] + 1`: `q` represents strings that are too long to all be suffixes of the new prefix.

</details>

<details>
<summary>Solution</summary>

After `"a"`: state 1 (`len 1`), `next[0] = {a: 1}`, `link[1] = 0`.

After `"ab"`: state 2 (`len 2`). Walking from `last = 1`: `next[1][b] = 2`, then `p = 0`: `next[0][b] = 2`, then `p = -1`, so `link[2] = 0`.

Third character `b`: new state 3 with `len 3`. From `p = 2`: no `b` transition, so `next[2][b] = 3`, `p = link[2] = 0`. State 0 already has `b → 2`, so `q = 2`. Now `len[0] + 1 = 1` but `len[2] = 2`. Before this step, state 2 represented `{"b", "ab"}`, both ending only at position 2 of `"ab"`. In `"abb"`, `"b"` now also ends at position 3, while `"ab"` does not. The two strings no longer share an end-position set, so the state must split. The clone (state 4) gets `len 1`, `link[4] = link[2] = 0`, and a copy of state 2's transitions `{b: 3}`. The redirect loop changes `next[0][b]` from 2 to 4 and stops at `p = -1`. Finally `link[2] = link[3] = 4`.

| State | len | link | next |
|-------|-----|------|------|
| 0 | 0 | -1 | {a: 1, b: 4} |
| 1 | 1 | 0 | {b: 2} |
| 2 | 2 | 4 | {b: 3} |
| 3 | 3 | 4 | {} |
| 4 | 1 | 0 | {b: 3} |

Distinct substrings = Σ over states v ≠ 0 of `len[v] - len[link[v]]` = (1 − 0) + (2 − 1) + (3 − 1) + (1 − 0) = **5**, matching `{a, b, ab, bb, abb}`. Five states for n = 3 is within the 2n − 1 bound.

</details>

**23.5 ★★ Find the bug: rollback with path compression.** A contestant wants faster finds and changes the `DSU` of Section 23.14 to:

```python
def find(self, x):
    if self.parent[x] != x:
        self.parent[x] = self.find(self.parent[x])
    return self.parent[x]
```

Everything else is unchanged. Starting from `DSU(4)`, run `union(0, 1)`, `union(2, 3)`, `s = snapshot()`, `union(1, 3)`, `find(3)`, `rollback(s)`. What are `parent` and `size` at the end, and which connectivity answer is now wrong?

<details>
<summary>Solution</summary>

| Step | parent | size | change logged |
|------|--------|------|---------------|
| start | [0, 1, 2, 3] | [1, 1, 1, 1] | |
| union(0, 1) | [0, 0, 2, 3] | [2, 1, 1, 1] | (1, 1, 1) |
| union(2, 3) | [0, 0, 2, 2] | [2, 1, 2, 1] | (3, 3, 1) |
| union(1, 3) | [0, 0, 0, 2] | [4, 1, 2, 1] | (2, 2, 2) |
| find(3) | [0, 0, 0, **0**] | unchanged | none |
| rollback(s) | [0, 0, 2, 0] | [2, 1, 2, 1] | |

Rollback restored `parent[2] = 2`, the one pointer it logged. It knows nothing about `parent[3] = 0`, which path compression wrote without recording it. Now `find(3) = 0` and `find(2) = 2`: the structure says 3 is connected to 0 and not to 2, the exact opposite of the truth at snapshot `s`. `size[2] = 2` also describes a set that now contains only 2.

The fix is the one the chapter uses: no path compression, so every pointer change is a logged union. Union by size alone keeps trees at depth O(log n), which is why rollback DSU costs O(log n) per operation instead of O(α(n)).

</details>

**23.6 ★★ Why HLD paths cross few chains.** In `HeavyLightDecomposition`, `heavy[v]` is the child with the largest subtree. (a) Prove that if `(v, c)` is a light edge then `size[c] < size[v] / 2`. (b) Conclude that any path from a node to the root crosses at most ⌊log₂ n⌋ light edges. (c) Use this to justify the O(log² n) bound for `query_path`. (d) Why must `_decompose` recurse into `heavy[v]` before the light children?

<details>
<summary>Hint</summary>

For (a), compare `size[c]` with `size[heavy[v]]` and remember both subtrees fit inside `v`'s. For (b), follow subtree sizes upward from the start node.

</details>

<details>
<summary>Solution</summary>

(a) Let `h = heavy[v]`. Since `c` is light, `size[c] ≤ size[h]`. Both subtrees are disjoint parts of `v`'s subtree, which also contains `v`, so `size[c] + size[h] ≤ size[v] − 1`. Then `2·size[c] ≤ size[c] + size[h] ≤ size[v] − 1 < size[v]`.

(b) Walk from a node `u` up to the root. Subtree sizes never decrease along the way, and each light edge crossed (from `c` up to `v`) more than doubles the size: `size[v] > 2·size[c]`. Starting from `size[u] ≥ 1` and never exceeding `n`, at most ⌊log₂ n⌋ doublings fit.

(c) Each iteration of the `while` loop in `query_path` handles one chain and then jumps from `head[u]` to its parent, which crosses a light edge. A u-v path is two node-to-LCA paths, so there are O(log n) iterations, and each issues one segment tree query over a contiguous `pos` range costing O(log n). Total O(log² n).

(d) Recursing into the heavy child first gives it `pos[v] + 1`, then its heavy child `pos[v] + 2`, and so on. Every heavy chain therefore occupies a contiguous block of `pos`, which is what lets `range_query(pos[head_u], pos[u])` answer a whole chain segment in one call. Visiting a light child first would interleave its subtree into the middle of the chain.

</details>

**23.7 ★★★ Choosing Mo's block size.** `MoSolver` uses block size `B = √n`. (a) Show that with sorting by `(l // B, r)`, the total pointer movement is O(qB + n²/B). (b) Find the `B` that minimises this, and the resulting bound. (c) For `n = 10^5` and `q = 10^3`, estimate the pointer moves for `B = √n` and for your optimal `B`.

<details>
<summary>Hint</summary>

Bound the right pointer per block of left endpoints, and the left pointer per query.

</details>

<details>
<summary>Solution</summary>

(a) There are at most `n/B` distinct blocks for `l`. Within one block the queries are sorted by `r`, so the right pointer moves monotonically and travels at most `n` per block (plus up to `n` to reset when the block changes): O(n · n/B) = O(n²/B). The left pointer stays inside one block between consecutive queries of that block, so it moves at most `B` per query, and at most `2B` when crossing into the next block: O(qB + n). Total O(qB + n²/B) add/remove calls. The alternating `r` order in the chapter's sort key removes the reset sweep of the right pointer, which roughly halves the constant but does not change the bound.

(b) `qB` grows with `B`, `n²/B` shrinks; they balance when `qB = n²/B`, i.e. `B = n/√q`. Then each term is `n√q`, so the total is **O(n√q)**. With `q ≈ n` this is `B = √n` and O(n√n), the chapter's O((n + q)√n). When `q` is much smaller than `n`, `B = √n` is too small.

(c)
- `B = √n ≈ 316`: `qB + n²/B ≈ 3.2·10^5 + 3.2·10^7 ≈ 3.2·10^7`.
- `B = n/√q ≈ 3162`: `qB + n²/B ≈ 3.2·10^6 + 3.2·10^6 ≈ 6.3·10^6`.

The tuned block size does about five times less work. Changing one line of `__init__` to `max(1, int(len(arr) / max(1, len(queries)) ** 0.5))` captures it.

</details>

**23.8 ★★★ Implement distinct-count with Mo's algorithm.** Subclass `MoSolver` from Section 23.6 so that `answers[i]` is the number of distinct values in `arr[l..r]` (inclusive) for query `i`. Queries are objects with fields `l`, `r`, `idx`. Then explain why `_process` performs both expanding loops before both shrinking loops, and what would go wrong with your subclass if it shrank first.

<details>
<summary>Hint</summary>

Keep a count per value and a running number of values whose count is positive. Each `_add` and `_remove` must be O(1).

</details>

<details>
<summary>Solution</summary>

```python
from collections import namedtuple

Query = namedtuple("Query", "l r idx")

class DistinctMo(MoSolver):
    def __init__(self, arr, queries):
        self.cnt = {}
        self.distinct = 0
        super().__init__(arr, queries)   # runs _process, so set state first

    def _add(self, idx):
        x = self.arr[idx]
        self.cnt[x] = self.cnt.get(x, 0) + 1
        if self.cnt[x] == 1:
            self.distinct += 1

    def _remove(self, idx):
        x = self.arr[idx]
        self.cnt[x] -= 1
        if self.cnt[x] == 0:
            self.distinct -= 1

    def _get_answer(self):
        return self.distinct

arr = [1, 2, 1, 3, 2, 2, 4]
qs = [Query(0, 2, 0), Query(1, 4, 1), Query(3, 6, 2), Query(0, 6, 3)]
assert DistinctMo(arr, qs).answers == [2, 3, 3, 4]
```

The state must exist before `super().__init__` because the base constructor immediately calls `_process`, which calls `_add`.

Expanding first keeps `cur_l ≤ cur_r + 1` at every step, so the window never has negative length. If the code shrank first, moving from window `[0, 1]` to query `[5, 6]` would advance `cur_l` past `cur_r` and call `_remove` on positions 2, 3, 4 that were never added. `cnt[x]` would go to −1 (or raise `KeyError` for an unseen value), `distinct` would drift, and the later `_add` calls that bring those positions back would bump the counts from −1 to 0 without incrementing `distinct`. Every subsequent answer would be off. Expanding first means every `_remove` undoes a previous `_add`.

Each query costs O(1) per pointer step, so the whole run is O((n + q)√n) with the chapter's block size.

</details>

---

## Where this connects

- [Chapter 21: Algorithm Design Using Data Structures](../volume-3/ch21-algorithm-design-using-data-structures.md). The paradigms these structures accelerate
- [Chapter 25: Complete Selection Guide and Complexity Reference](ch25-complete-selection-guide-and-complexity-reference.md). The selection matrix for picking among them
