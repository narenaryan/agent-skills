---
name: go-interfaces-embedding
description: Use when designing Go type hierarchies with interfaces, type switches, or struct/interface embedding — covers implicit satisfaction, comma-ok assertions, compile-time interface checks via var _, method promotion rules, and name-collision resolution
---

# Go Interfaces & Embedding

Interface satisfaction is implicit and structural. Embedding promotes the inner type's method set; the receiver stays the inner type. Composition, not inheritance — no virtual dispatch.

## Type switch vs assertion

```go
switch t := v.(type) {
case int:   use(t)      // t is int
case *Foo:  use(t)      // t is *Foo
default:                // t keeps interface type
}

s, ok := v.(string)     // comma-ok avoids panic
```

Bare `v.(string)` panics on mismatch.

## Compile-time interface compliance

```go
var _ json.Marshaler = (*RawMessage)(nil)
```

Breaks the build if `*RawMessage` stops implementing `Marshaler`. Use when no other static conversion in the package already proves it.

## Embedding: method promotion

```go
type ReadWriter struct {
    *Reader
    *Writer
}
rw.Read(p)    // dispatches to (*Reader).Read; receiver is rw.Reader
```

The promoted method's receiver is the **embedded** value. An inner method calling `m.Other()` sees the **inner** `Other`, not any outer shadow — you cannot override polymorphically, only shadow at the outer level.

## Name collisions

| Situation | Behavior |
|-----------|----------|
| Outer same name as embedded | Outer shadows; reach inner via type name `j.Logger.Println` |
| Same name, same depth | Compile error **only if referenced** |
| Different depths | Shallower wins |

Access embedded fields by type name (minus package): `j.Logger`.

## Interface embedding

```go
type ReadWriter interface {
    Reader
    Writer
}
```

Union of method sets. Only between interfaces — cannot embed an interface in a struct to declare required methods.

## Receivers and interfaces

| Holder | Method set |
|--------|------------|
| `T` value | `T` receivers only |
| `*T` value | `T` and `*T` receivers |

A `T` value does not satisfy an interface whose method uses a pointer receiver.

## Pitfalls

- **Recursive `String()`:** `fmt.Sprintf("%s", x)` inside `(x T) String()` recurses. Convert: `fmt.Sprint([]int(x))`.
- **Discarding errors with `_`:** `fi, _ := os.Stat(p); fi.IsDir()` nil-panics on failure.
- **Assuming polymorphism:** an inner method calling `m.Other()` calls the inner `Other`, not an outer shadow.
- **Nil interface vs nil concrete:** `var p *T; var i Iface = p; i == nil` is **false** — interface holds (type, value) and type is non-nil.
- **Empty interface:** prefer `any` (Go 1.18+) over `interface{}`; identical.
