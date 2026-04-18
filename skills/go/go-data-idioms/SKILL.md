---
name: go-data-idioms
description: Use when working with Go slices, maps, defer, or named returns — covers new vs make, slice capacity and backing-array aliasing, append reallocation, defer LIFO and argument-capture timing, named returns mutated by defer, and zero-value-useful design
---

# Go Data Idioms

Slices are `(ptr, len, cap)` headers over a shared backing array; aliasing is the default. `defer` evaluates args at the defer site, not at return. Design types so the zero value is usable.

## `new` vs `make`

| Call | Returns | For |
|------|---------|-----|
| `new(T)` | `*T`, zeroed | structs, ints, arrays |
| `make(T, …)` | `T`, initialized | slices, maps, channels |

`new([]int)` yields `*[]int` pointing to a nil slice — rarely useful. Use `make([]int, n)`.

## Slices: aliasing and `append`

```go
s := []int{1, 2, 3, 4}
t := s[1:3]            // shares backing; t[0]=9 mutates s[1]
u := append(s, 5)      // may or may not reallocate

s = append(s, x)       // MUST reassign
append(s, x)           // lost — returned header discarded
```

Reallocation when `len + added > cap`. Before realloc, original and returned share memory; after, they don't. Treat the return as authoritative.

## Maps: comma-ok for absence

```go
v, ok := m[k]    // ok=false means absent
_, ok := m[k]    // presence-only
```

Missing key silently returns zero value; without `ok` you cannot tell "absent" from "present and zero".

## Defer: LIFO and argument capture

```go
for i := 0; i < 3; i++ {
    defer fmt.Println(i)    // args evaluated NOW → 2, 1, 0
}

x := 1
defer func() { fmt.Println(x) }()
x = 2                       // prints 2 — closure reads at call time
```

Direct-call defer captures args at the defer statement. A `func(){}` literal reads variables when it runs.

## Named returns + defer = post-return mutation

```go
func parse() (out T, err error) {
    defer func() {
        if err != nil { err = fmt.Errorf("parse: %w", err) }
    }()
    ...
    return   // defer sees and rewrites err
}
```

Works only with **named** returns. Defer runs after return operands evaluate, before control leaves the frame.

## Zero-value-useful

```go
type Buf struct {
    mu  sync.Mutex       // zero: unlocked
    buf bytes.Buffer     // zero: empty, usable
}
var b Buf                // no constructor needed
```

## Pitfalls

- **Forgetting to reassign `append`:** silent element loss when cap is exceeded.
- **Slice retention:** `big[0:1]` keeps the whole backing array alive. `copy` into a fresh slice when keeping a small prefix.
- **`defer` in a loop:** all defers run at function exit, not per iteration — handles accumulate. Wrap iteration in a helper.
- **Closure vs argument capture:** `defer f(x)` captures x now; `defer func(){ f(x) }()` captures x at execution.
- **Nil map write panics:** `var m map[string]int; m["k"] = 1` panics. Always `make` before writing.
- **Two-dim slice allocation:** one contiguous `make([]T, x*y)` sliced into rows beats per-row `make` when rows have fixed size.
