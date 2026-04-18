---
name: go-error-handling
description: Use when designing Go error types, choosing error vs panic, or implementing recover — covers structured error types with Unwrap, errors.Is/As, the direct-call rule for recover, re-panic, and panic-as-internal-control-flow for complex parsers
---

# Go Error Handling

Errors are values. Design the type to carry structured context (op, path, cause); callers inspect with `errors.Is` / `errors.As`. Panic is for programmer bugs and unrecoverable init — not cross-package flow control.

## Structured error types

```go
type PathError struct {
    Op   string   // "open", "unlink"
    Path string
    Err  error    // wrapped cause
}

func (e *PathError) Error() string { return e.Op + " " + e.Path + ": " + e.Err.Error() }
func (e *PathError) Unwrap() error { return e.Err }
```

Error strings prefix the op/package: `"parse config.yaml: line 4: invalid key"`.

## Inspection: `errors.Is` / `errors.As`

```go
if errors.Is(err, fs.ErrNotExist) { ... }      // walks Unwrap chain
var pe *fs.PathError
if errors.As(err, &pe) { use(pe.Op, pe.Path) }
```

Prefer over `err == ErrX` (breaks with wrapping) or `err.(*PathError)` (single-level only).

## Recover: direct-call rule

```go
func safe() (err error) {
    defer func() {
        if r := recover(); r != nil {
            err = fmt.Errorf("panic: %v", r)
        }
    }()
    risky()
    return
}
```

`recover()` returns `nil` unless invoked **directly** inside a deferred function's body. Moving it into a helper silently breaks recovery. Use **named** returns so the deferred func can set `err`.

## Re-panic unknown values

```go
defer func() {
    r := recover()
    if r == nil { return }
    e, ok := r.(myLocalError)
    if !ok { panic(r) }   // propagate foreign panics
    err = e.err
}()
```

Only swallow panics of types you own.

## Panic as internal control flow

Parser/regexp packages legitimately `panic(localError{…})` deep in the stack and `recover` at the public API boundary. Rules:

- Panic value must be an **unexported** type.
- Recover at every exported entry point.
- Never let a control-flow panic escape the package.

## When to panic

| Situation | Panic? |
|-----------|-------|
| Impossible state / programmer bug | yes |
| Missing required env at `init` | yes |
| Bad user input | no — return error |
| Network / I/O failure | no — return error |
| Internal parser control flow | yes, bounded by recover at API edge |

## Pitfalls

- **`recover()` inside a helper:** `defer cleanup()` where `cleanup` calls `recover` returns nil; panic continues. Must live in the deferred func's own body.
- **`defer recover()`:** defers the `recover` call itself, which runs with no active panic. Wrap in a func literal.
- **Sentinel after wrapping:** `err == io.EOF` fails once wrapped. Use `errors.Is`.
- **Panic across package boundary:** forces every caller to wrap in `recover`. Convert at the exported boundary.
- **Mutating a returned error:** callers may retain it; never modify fields of `*myError` after return.
