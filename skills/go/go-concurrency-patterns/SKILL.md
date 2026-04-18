---
name: go-concurrency-patterns
description: Use when designing Go concurrent code — goroutine lifetimes, channel sizing, worker pools, parallelization, or diagnosing goroutine leaks and data races; covers semaphore via buffered channel, leaky buffer, fan-out, channel-of-channels for RPC
---

# Go Concurrency Patterns

Ownership transfers on send: one goroutine owns a value at a time. Unbuffered = sync point; buffered = bounded decoupling.

## Channel blocking

| Op | Unbuffered | Buffered (N) |
|----|-----------|--------------|
| send | blocks until recv ready | blocks when full |
| recv | blocks until sender ready | blocks when empty |
| send on closed | panics | panics |
| recv on closed | zero, ok=false | drain, zero, ok=false |

## Semaphore via buffered channel

```go
var sem = make(chan struct{}, MaxOutstanding)
func handle(r *Request) {
    sem <- struct{}{}
    defer func() { <-sem }()
    process(r)
}
```

Replaces mutex+counter. `struct{}` is zero-byte.

## Non-blocking select (leaky buffer)

```go
select {
case b = <-freeList:   // try pool
default:
    b = new(Buffer)    // allocate fallback
}
...
select {
case freeList <- b:    // try return
default:               // drop; GC reclaims
}
```

`default:` makes `select` non-blocking.

## Channel-of-channels for replies

```go
type Request struct {
    args  []int
    reply chan int
}
queue <- &Request{args, make(chan int)}
ans := <-req.reply
```

Each request carries its own reply channel — no correlation IDs.

## Fan-out across cores

```go
n := runtime.GOMAXPROCS(0)
c := make(chan int, n)         // buffered for drain
for i := 0; i < n; i++ { go worker(i, c) }
for i := 0; i < n; i++ { <-c } // join
```

Buffer size = worker count so the last worker never blocks.

## Pitfalls

- **Loop-variable capture (Go <1.22):** `for req := range q { go f(req) }` — all goroutines see the final `req`. Pass as arg: `go func(r *Req){ f(r) }(req)`, or upgrade to 1.22+.
- **Goroutine leak:** `go func(){ c <- 1 }()` with no receiver blocks forever; the goroutine outlives its caller. Size buffers correctly or guarantee a receiver before sending.
- **Closing from the receiver side:** sending on a closed channel panics. Only the sole sender may close; with multiple senders use a separate `done` channel or `sync.Once`.
- **Unbuffered self-deadlock:** sending and receiving on the same unbuffered channel in one goroutine deadlocks instantly.
- **Select starvation:** `select` chooses randomly among ready cases. A `default:` branch disables blocking entirely — don't include one when you actually want to wait.
