# Sources and validation limits

Reviewed October 25, 2026. Inspired by user-supplied Linux Magazine reading notes;
no issue number or article URL was supplied, so those notes are leads, not cited
technical authority. This is original synthesis from the primary material below.
Source review date is not a publication date. No new-publication claim is made.

## Primary sources

- [sysstat iostat manual](https://man7.org/linux/man-pages/man1/iostat.1.html):
  first report versus interval reports, `-y`, `-x`, `-t`, `await` (queue plus
  service), and the explicit `%util` warning for devices serving requests in
  parallel. Current upstream manual; not a pinned installed sysstat version.
- [procps-ng vmstat manual](https://man7.org/linux/man-pages/man8/vmstat.8.html):
  first rate report since boot versus subsequent intervals; process/memory
  fields remain instantaneous; runnable/blocked, swap, timestamp and wide fields.
- BCC tool source snapshot
  [`c398a9a7a41cba623b520cda27457b92d7fcad2b`](https://github.com/iovisor/bcc/tree/c398a9a7a41cba623b520cda27457b92d7fcad2b),
  read October 25, 2026:
  [biosnoop.py](https://github.com/iovisor/bcc/blob/c398a9a7a41cba623b520cda27457b92d7fcad2b/tools/biosnoop.py),
  [biolatency.py](https://github.com/iovisor/bcc/blob/c398a9a7a41cba623b520cda27457b92d7fcad2b/tools/biolatency.py),
  [biosnoop examples](https://github.com/iovisor/bcc/blob/c398a9a7a41cba623b520cda27457b92d7fcad2b/tools/biosnoop_example.txt).
  These establish flags, default microseconds versus `-m` milliseconds, per-disk
  `-D`, histogram interval/count, and biosnoop's separate QUE/LAT columns.
  Samples are emitted on completion and missing start timestamps are skipped:
  outstanding/unmatched requests do not become slow completed samples.
  Attribution is cached execution context, not proof of original buffered writer.
  Biosnoop initializes queue duration to zero when cached attribution/queue-start
  metadata is absent; COMM `?` plus QUE=0 does not establish zero queueing.
  Biolatency `-m` integer-divides nanoseconds before bucketing, losing sub-ms detail;
  the skill therefore preserves default microseconds in its NVMe-facing example.
  Queue-start and completion attachment fallbacks vary across kernels; these
  intervals must not be called pure physical-media service time or application
  latency. Source was read, not fetched and executed.
- [BCC installation prerequisites](https://github.com/iovisor/bcc/blob/c398a9a7a41cba623b520cda27457b92d7fcad2b/INSTALL.md):
  kernel/build dependencies and distribution-dependent tool packaging. No install
  commands are incorporated or executed. BCC is BPF Compiler Collection.
- [Linux libbpf overview](https://docs.kernel.org/bpf/libbpf/libbpf_overview.html):
  load/attach lifecycle, BTF-based CO-RE relocations. CO-RE portability does not
  supply missing kernel helpers/hooks or permissions. BCC and libbpf command
  interfaces must not be interchanged without checking local documentation.
- [GNU timeout manual](https://www.gnu.org/software/coreutils/manual/html_node/timeout-invocation.html):
  reference URL; web fetch timed out. Installed GNU coreutils 9.7 `timeout --help`
  independently verifies the selected INT signal and exit statuses. Reaching the timeout returns
  124; INT is a soft deadline, not guaranteed termination or successful
  probe/coverage certification.

## Worked decision contrasts

| Case | Tempting but unsupported conclusion | Defensible next step |
|---|---|---|
| NVMe busy near 100%, acceptable latency | Device saturated | Compare throughput/latency at the same load; busy time is not capacity |
| Long QUE, short LAT for matched requests | SSD failing | Investigate pre-issue queueing and workload; do not change scheduler from this alone |
| Long LAT | Bad media | Inspect storage-path/error evidence; cloud/network/driver/controller delays remain possible |
| Empty completion histogram during a stall | No slow I/O | Check attachment, device/window, event loss, and outstanding requests |
| High CPU or swap activity | Disk is root cause | Discriminate CPU or memory pressure before narrowing block tracing |
| Kernel worker is issuing writes | Worker owns application workload | Correlate filesystem/application evidence before attribution |

These are decision scenarios, not measured kernel results. No universal latency,
queue length, or utilization threshold is supplied. Histograms from separate runs
cannot be subtracted to derive queue percentiles; workloads and request cohorts
may differ, and percentiles are not additive even for one cohort.

## Reproduction

From the repository root:

```bash
python3 skills/engineering/linux-io-latency-triage/reproduce.py
python3 -O skills/engineering/linux-io-latency-triage/reproduce.py
```

The original standard-library fixture uses normalized synthetic timestamps and
explicit capture-quality flags. Nineteen tests cover same-request boundary math,
unknown queue timestamps and missing-metadata zero, in-flight censoring, empty versus failed capture,
wrong device/window, loss, unknown coverage, origin attribution, invalid clock
orders, hidden tails, and refusing a hardware-failure verdict. Deliberately naive
baselines mislabel incomplete empty captures as healthy and any completed I/O as
hardware failure. The remedy describes evidence rather than claiming a diagnosis.

Three deliberate in-memory mutations were caught by the suite: ignoring failed
attachment, inventing zero for missing queue time, and trusting process names
without origin evidence. These test guard sensitivity, not kernel fidelity.

The fixture is not a BCC parser, tracer, or executable policy engine. Its
`outstanding_known` flag requires evidence supplied by the caller; biosnoop alone
does not provide a complete in-flight inventory. Tests do not validate kernel
hooks, lost-event accounting, host permissions, syscall/device attribution,
CO-RE portability, timing accuracy, observer overhead, SSD health or remediation.

In the build environment Python 3.12.14 was available; iostat, BCC tools and
bpftool were not on PATH. No tools were installed; no privileged probes or live
I/O load ran. Actual tracing requires a separately authorized Linux environment
with suitable installed tooling. Successful scenario tests must not be reported
as real-kernel validation. Repository README mentions `test.sh`, but it is absent
at the inspected base; no full repository suite is claimed.
