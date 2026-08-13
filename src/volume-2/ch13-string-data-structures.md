# Chapter 13: String Data Structures

## 13.1 Tries (Prefix Trees)

A trie stores strings by their prefixes:

```
Trie for {"cat", "car", "card", "do", "dog", "done"}:

root
 │
 ├── c
 │   └── a
 │       ├── t (end)
 │       └── r
 │           ├── d (end)
 │           └── (nothing)
 │
 └── d
     └── o
         ├── g (end)
         └── n
             └── e (end)
```

**Operations:**
- Insert: O(L) where L is string length
- Search: O(L)
- Prefix search: O(P) where P is prefix length

## 13.2 Radix Trees (Compressed Tries)

Compress paths with single-child nodes:

```
Radix Tree (same words):

root
 │
 ├── ca
 │   ├── t (end)
 │   └── rd (end)
 │
 └── do
     ├── g (end)
     └── ne (end)

Space reduced: ca replaces c-a, rd replaces r-d
```

## 13.3 Suffix Trees

A suffix tree contains all suffixes of a string:

```
For "banana$":

Suffixes:
- banana$
- anana$
- nana$
- ana$
- na$
- a$
- $

Suffix tree stores these as paths:
root
 └── b
     └── a
         └── n
             ├── a (→ "ana$")
             │   └── n
             │       └── a
             │           └── $
             └── a
                 └── n
                     └── a
                         └── $
```

**Applications:**
- Substring search: O(m)
- Longest common substring: O(n)
- Longest repeated substring: O(n)

## 13.4 Suffix Arrays

A suffix array is the sorted list of suffix starting positions:

```
String: "banana$"
Suffixes: 0:"banana$", 1:"anana$", 2:"nana$", 3:"ana$", 4:"na$", 5:"a$", 6:"$"

Sorted suffixes:
"$"          → index 6
"a$"         → index 5
"ana$"       → index 3
"anana$"     → index 1
"banana$"    → index 0
"na$"        → index 4
"nana$"      → index 2

Suffix Array: [6, 5, 3, 1, 0, 4, 2]
```

**LCP Array** (Longest Common Prefix):
```
LCP between consecutive suffixes:
[0, 1, 0, 2, 0, 1, 2]
```

## 13.5 Applications

**Autocomplete**: Trie prefix matching
**Spell checking**: Dictionary lookup
**IP routing**: Longest prefix match
**DNA sequencing**: Pattern matching
**Search engines**: Inverted indexes
