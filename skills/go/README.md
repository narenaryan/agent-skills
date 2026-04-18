# go skills

Practical Go engineering skills focused on production behavior: concurrency, profiling, interfaces, data semantics, and error design.

## Skills

- **[go-concurrency-patterns](go-concurrency-patterns/SKILL.md)** - designing concurrent Go code: goroutine lifetimes, channel sizing, worker pools, semaphore via buffered channels, fan-out, and leak/race pitfalls.
- **[go-data-idioms](go-data-idioms/SKILL.md)** - working with slices, maps, `defer`, and named returns. Covers `new` vs `make`, backing-array aliasing, append reallocation, and zero-value-useful design.
- **[go-error-handling](go-error-handling/SKILL.md)** - designing Go error types, choosing error vs panic, and implementing recover correctly with `errors.Is` / `errors.As`, `Unwrap`, and boundary-safe panic control flow.
- **[go-interfaces-embedding](go-interfaces-embedding/SKILL.md)** - struct/interface embedding, implicit interface satisfaction, type assertions/switches, method promotion, and name-collision behavior.
- **[go-pprof-profiling](go-pprof-profiling/SKILL.md)** - profiling with pprof for CPU, heap, mutex, block, and goroutine analysis. Covers flat vs cum, sample indexes, differential profiles, and common profiling traps.

## Install

```bash
./install.sh go                      # install all
./install.sh go-concurrency-patterns # install one
```
