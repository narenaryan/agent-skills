---
name: go-pprof-profiling
description: Use when profiling Go programs with pprof — CPU hotspots, allocation rates, GC pressure, lock contention, or goroutine leaks; covers profile types (cpu/heap/block/mutex/goroutine), go tool pprof interactive commands, flat vs cum, differential profiles with -base, and sample_index for inuse vs alloc
---

# Go pprof Profiling

Sampling profiler. **Flat** = samples in the function itself; **cum** = samples in the function plus everything it called. Heap is approximate (1 sample per ~512 KB by default) — small hot allocations vanish.

## Profile types

| Profile | Endpoint | Measures |
|---------|----------|----------|
| cpu | `/debug/pprof/profile?seconds=30` | wall-clock samples at 100 Hz |
| heap | `/debug/pprof/heap` | live + cumulative allocations |
| goroutine | `/debug/pprof/goroutine` | all goroutine stacks (leak hunt) |
| block | `/debug/pprof/block` | time blocked on sync primitives |
| mutex | `/debug/pprof/mutex` | contention on Lock/Unlock |
| trace | `/debug/pprof/trace?seconds=5` | full execution trace (`go tool trace`) |

Block/mutex are off by default — enable at startup:

```go
runtime.SetBlockProfileRate(1)       // every blocking event
runtime.SetMutexProfileFraction(1)   // every contention event
```

Install endpoints: `import _ "net/http/pprof"` then serve on `localhost:6060`.

## Heap sample index

| `-sample_index=` | Units | Use for |
|------------------|-------|---------|
| `alloc_space` | bytes allocated (lifetime) | GC pressure, hotspots |
| `alloc_objects` | allocations (lifetime) | churn count |
| `inuse_space` | live bytes (default) | heap footprint |
| `inuse_objects` | live objects | leak candidates |

Allocation hotspots are **invisible** in the default `inuse_space` view — switch to `alloc_objects`.

## Interactive commands

| Command | What |
|---------|------|
| `top` / `top -cum` | rank by flat / cumulative |
| `list FuncRE` | source lines with sample counts |
| `weblist FuncRE` | source + disasm in browser |
| `peek FuncRE` | callers and callees |
| `focus=RE` / `ignore=RE` / `hide=RE` | regex filter on stack |
| `tagfocus=k=v` | filter on profile labels |
| `nodefraction=0.05` | hide nodes <5% cumulative |

## Differential profiling

```bash
go tool pprof -base v1.pb.gz v2.pb.gz         # subtract; negatives = improvements
go tool pprof -diff_base v1.pb.gz v2.pb.gz    # subtract then normalize to zero total
go tool pprof -http=localhost:8080 -base v1 v2
```

Use `-diff_base` when run durations differ — it compares rates, not absolutes.

## Pitfalls

- **Heap sampling misses small hot allocations:** default rate 512 KB. Set `runtime.MemProfileRate = 1` in tests only.
- **Inlining hides callees:** inlined functions vanish; samples attribute to the caller. Use `list` for per-line, or `//go:noinline` while profiling.
- **`-http` binds all interfaces:** pass `-http=localhost:8080` or the UI is exposed externally.
- **CPU frequency scaling skews timing:** pin governor to performance for reproducible CPU profiles.
- **Unoptimized binary:** `-gcflags=all=-N -l` produces misleading hotspots — profile optimized builds only.
- **`-base` with different sample rates:** heap profiles must share `MemProfileRate`, or the diff is meaningless.
- **`goroutine` profile is stop-the-world:** expensive on busy servers.
