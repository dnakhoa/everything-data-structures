# Chapter 20: Data Structure Design Patterns

## 20.1 Wrapper/Decorator Pattern

Add functionality to existing structures:
```python
class SynchronizedDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lock = threading.Lock()

    def __getitem__(self, key):
        with self.lock:
            return super().__getitem__(key)
```

## 20.2 Composite Pattern

Tree-like hierarchical structures:
```python
class Component:
    def operation(self): pass

class Composite(Component):
    def __init__(self):
        self.children = []

    def add(self, c):
        self.children.append(c)

    def operation(self):
        for c in self.children:
            c.operation()
```

## 20.3 Iterator Pattern

Abstract traversal:
```python
class TreeIterator:
    def __init__(self, root):
        self.stack = [root] if root else []

    def __iter__(self):
        return self

    def __next__(self):
        if not self.stack:
            raise StopIteration
        node = self.stack.pop()
        if node.right:
            self.stack.append(node.right)
        if node.left:
            self.stack.append(node.left)
        return node.val
```

## 20.4 Builder Pattern

Complex construction:
```python
class BSTBuilder:
    def __init__(self):
        self.values = []

    def add(self, value):
        self.values.append(value)
        return self

    def build(self):
        self.values.sort()
        return self._build_range(0, len(self.values))

    def _build_range(self, lo, hi):
        if lo >= hi:
            return None
        mid = (lo + hi) // 2
        node = TreeNode(self.values[mid])
        node.left = self._build_range(lo, mid)
        node.right = self._build_range(mid + 1, hi)
        return node
```
