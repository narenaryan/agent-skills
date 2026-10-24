---
name: rust-tokio-cancellation-safety
description: Use when a Tokio loop races I/O, shutdown, timers, or receives with `select!` and may restart an operation after cancellation; prevent lost input, duplicated output.
---

# Tokio Cancellation Safety

`select!` drops losing futures; recreation starts over. Cancellation-safe means drop/recreate is a no-op, not rollback.

## Audit branch operations

| Operation in a `select!` loop | Progress if another branch wins | Safer pattern |
|---|---|---|
| `read` / `read_buf` | Cancellation-safe for one read attempt | Append returned bytes to loop-owned storage. |
| `read_exact` | May consume part of the stream; the helper may not return how much | Read incrementally into persistent framing state. |
| `write` / `write_buf` | Cancellation-safe for one attempt; completion reports a byte count | Keep the frame and offset outside the branch; advance only by the returned count. |
| `write_all` | May have written a prefix; a retry restarts at byte zero | Resume from a saved offset or keep one operation future alive. |
| `write_all_buf` | May write a prefix; the supplied `Buf` advances by the bytes written | Retain and resume that same buffer; do not rebuild it from the original payload. |
| `flush` | Cancellation-safe; buffered data may be partially flushed and the writer's buffer advances | Re-poll `flush` on the same writer; this does not prove peer receipt. |

## Preserve protocol state

1. Inspect every method and wrapper; an async helper may add non-safe awaits.
2. For framed reads, append completed `read`/`read_buf` results to loop-owned storage, parse complete frames, and retain the incomplete suffix. Bound the buffer; treat EOF with an unfinished frame as truncation.
3. Keep frame and offset in the owner. Resume only with the same frame and offset. Write its unsent suffix, reject zero as `WriteZero`, then advance by `n`. Never retry canceled `write_all` from zero on a stream.
4. For must-finish work, pin one future and poll `&mut future` across selects, or use one owner task. Dropping the owner still drops its state.

```rust
async fn write_frame_until_shutdown<W: tokio::io::AsyncWrite + Unpin>(
    writer: &mut W,
    shutdown_rx: &mut tokio::sync::oneshot::Receiver<()>,
    frame: &[u8],
    offset: &mut usize,
) -> std::io::Result<bool> {
    use tokio::io::AsyncWriteExt;
    if *offset > frame.len() {
        return Err(std::io::ErrorKind::InvalidInput.into());
    }
    while *offset < frame.len() {
        let n = tokio::select! {
            _ = &mut *shutdown_rx => return Ok(false), // sender drop stops too
            result = writer.write(&frame[*offset..]) => result?,
        };
        if n == 0 { return Err(std::io::ErrorKind::WriteZero.into()); }
        *offset += n;
    }
    Ok(true) // all bytes accepted by this AsyncWrite, not necessarily flushed
}
```

Offset is not atomic delivery. Choose whether shutdown may abandon partial frames. Default polling is randomized; `biased;` makes fairness yours.

## Pitfalls

- A timeout or shutdown branch is not rollback: prior writes accepted by a writer, dequeues, or external side effects may already have happened.
- Do not infer safety from a trait or method name; check the specific contract and [SOURCES.md](SOURCES.md).
- A cancel-safe `write` does not make a sequence atomic.
