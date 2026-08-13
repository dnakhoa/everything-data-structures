# Chapter 15: Spatial and Geometric Data Structures

## 15.1 K-Dimensional Trees (KD-Trees)

KD-trees partition k-dimensional space:

```
2D KD-Tree:
Level 0: Split on x-axis
Level 1: Split on y-axis
Level 2: Split on x-axis
...

        Split on x: x < 7
               │
         ┌─────┴─────┐
         │           │
    [2,3] │       [8,1]
          │
    Split on y: y < 5
         │
    ┌────┴────┐
    │         │
[1,8]     [5,4]
```

## 15.2 Quad Trees

Divide 2D space into four quadrants recursively:

```
Level 0:        ┌─────────┐
               │         │
               │         │
               └─────────┘
Level 1:    ┌───┬───┐
           │ NW │ NE │
           ├───┼───┤
           │ SW │ SE │
           └───┴───┘
```

## 15.3 R-Trees

R-trees index rectangles/hyper-rectangles:

```
R-Tree:
        ┌──────────────────┐
        │   [MBR of all]    │
        │  ┌──┐      ┌──┐   │
        │  │  │      │  │   │
        │  └──┘      └──┘   │
        │    ┌──────┐      │
        │    │      │      │
        │    └──────┘      │
        └──────────────────┘
```

## 15.4 Applications

**KD-Trees:**
- Nearest neighbor search
- Point clouds
- Ray tracing

**Quad Trees:**
- Image compression
- Collision detection
- Sparse data

**R-Trees:**
- Geographic Information Systems
- Database spatial indexes
- Map applications
