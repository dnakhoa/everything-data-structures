# Chapter 17: Persistent Data Structures

## 17.1 Persistence Defined

A persistent data structure preserves previous versions when modified.

**Types:**
- **Partial persistence**: Query old versions, update current
- **Full persistence**: Query and update any version
- **Confluent persistence**: Merge versions

## 17.2 Persistent BSTs

Share unchanged nodes on modification:

```
Before update (insert 25):
         A(50)
        /   \
     B(30)  C(70)

After update:
         A'(50)           ← New root
        /    \
     B(30)  C(70)         ← Shared (unchanged)
      │
      └──── D(25)         ← New node
```

## 17.3 Functional Data Structures

Functional languages favor immutable structures:
- Thread-safe by default
- Undo/redo trivial
- Predictable performance

**Examples:**
- Clojure's persistent vectors
- Haskell's persistent maps
- Scala's immutable collections
