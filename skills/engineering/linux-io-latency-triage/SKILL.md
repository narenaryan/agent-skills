---
name: linux-io-latency-triage
description: Use when Linux applications stall, blocked tasks or I/O wait rise, NVMe latency spikes, or block tracing shows unexpectedly slow requests or no events
---

# Linux I/O Latency Triage

Measure the boundary before naming the bottleneck: application latency, OS queueing, and issued-request latency are different clocks. Block completion samples omit requests still outstanding; an empty histogram cannot exonerate a stalled device.

## Establish comparable evidence

Record window, device mapping, workload, versions, and units. Use `top` to orient CPU/process pressure, then interval measurements:

```bash
vmstat -w -t 1 11
iostat -x -y -t 1 10
```

Collect during the same incident window; sequential runs are not synchronized. Discard vmstat's first CPU/I/O rate row: it averages since boot; its process/memory fields are instantaneous. iostat `-y` skips its since-boot report. Check local flags.

| Signal | Next discriminating observation; not a verdict |
|---|---|
| Runnable tasks/high CPU | Check CPU pressure before blaming storage |
| Swap-in/out plus stalls | Investigate memory pressure driving I/O |
| Rising `await`/queue length | Inspect latency distribution and device layer |
| High SSD/NVMe `%util` | Correlate latency and throughput; parallel devices can remain busy without exhausting capacity |

## Preflight, then narrow tracing

Identify the installed implementation: BCC Python tools and libbpf CO-RE binaries can share names but differ in flags. BCC needs compatible compilation dependencies/headers; CO-RE needs suitable target BTF and supported helpers/hooks, not merely a recent kernel. Record kernel, hooks, device scope, and authorization. Never install tools, widen privileges, or disable security controls just to get a trace.

After approval for bounded tracing, examples for distributions shipping BCC's `-bpfcc` names:

```bash
biolatency-bpfcc -h
biosnoop-bpfcc -h
# Only in an already authorized tracing context:
biolatency-bpfcc -D -T 1 10
timeout --signal=INT 10s biosnoop-bpfcc -Q
```

Prefer histograms first; per-request output can be costly. Default microseconds preserve sub-ms detail; `-m` truncates to milliseconds. Use supported device filters once mapping is verified. Preserve stderr, attachment failures, lost-event warnings and stop status; INT is a soft stop, not guaranteed termination or complete capture.

For this BCC implementation, biolatency defaults to issue-to-completion; `-Q` includes OS queueing. Biosnoop `-Q` reports separate `QUE(ms)` and `LAT(ms)` for the same request. Long QUE with short LAT points toward pre-issue delay; long LAT localizes delay after issue, not necessarily failing media. Never subtract percentiles from separate histogram runs to estimate queueing.

## Evidence contract

Report measured boundary, time/device scope, observed tails, coverage gaps, and the next test. Correlate application/filesystem evidence before attributing writes; require independent device/error evidence before alleging SSD failure. See [sources and scenario tests](SOURCES.md).

## Pitfalls

- Issuing PID/comm can identify writeback workers, not the application that dirtied pages; unknown attribution stays unknown.
- Missing biosnoop attribution can print QUE=0 without queue metadata; treat it as unknown, not measured zero.
- Failed attachment, wrong device, dropped events, or outstanding requests invalidate “no slow I/O” claims.
- Block timing excludes earlier application/filesystem work; device-mapper/RAID layers must not be summed blindly.
