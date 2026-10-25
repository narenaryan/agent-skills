---
name: http-resume-integrity
description: Use when interrupted or parallel HTTP downloads resume with corrupt bytes, a server ignores Range, or decompression and file offsets disagree.
---

# HTTP Resume Integrity

A checkpoint identifies a representation, not merely a URL and file length. Treat resumption as a conditional splice, not an append operation. Scope this recipe to sequential, single-range, identity-coded downloads.

## Response gate

Send `Range: bytes=N-` with `If-Range` containing the saved strong ETag. A weak ETag is unsuitable. Byte offsets address the encoded representation; transparent decompression changes the coordinate system.

| Response | Local action before publishing bytes |
|---|---|
| `206` | Validate single-part byte range, start `N`, inclusive end, unchanged total, matching strong ETag, coding, and actual body length. A shorter valid interval needs another request. |
| `200` | Never append. Stage a new full transfer with new metadata; replace only after validation. |
| `416` | Reconcile metadata; `bytes */L` alone does not prove the local file is complete or correct. |
| Error, malformed range, changed identity | Preserve the last verified checkpoint; stop or restart under the download policy. |

These conservative gates intentionally reject some legal responses, including unknown totals and multipart ranges. Broader clients need separate handling, not relaxed checks.

## Checkpoint recipe

1. Persist effective resource identity, representation-selecting request context, ETag, total length, byte domain, and committed prefix together. Isolate destinations by job; do not store secrets in logs. Changes in redirect target or selection context invalidate this checkpoint unless equivalence is independently established.
2. Request `Accept-Encoding: identity`, then inspect the response. [Requests](https://requests.readthedocs.io/en/latest/user/quickstart/#raw-response-content) automatically decompresses through `iter_content`; a file length measured after decoding is not a safe resume offset. Verify the adapter exposes the intended bytes.
3. Stage each bounded response separately. Validate headers, count bytes, and require successful transfer completion before advancing the checkpoint. A timeout, short body, or exhausted retry budget leaves the prior prefix intact. Limit total bytes, response size, elapsed time, and attempts independently.
4. Serialize checkpoint commits or compare generations before committing; two successful concurrent retries must not append the same suffix twice. File length alone does not establish contiguous coverage for parallel downloads.
5. Before promoting the assembled artifact, check its expected total and independently trusted digest/signature when available. An ETag is not an authenticity guarantee. Follow [dependency-artifact-integrity](../../security/dependency-artifact-integrity/SKILL.md) before executing downloaded packages.

Example: old bytes `AAAA1111`, new bytes `BBBB2222`; resuming after four bytes without identity checks produces `AAAA2222`. Its length is correct, but it belongs to neither version.

Run the original offline byte-splice fixture:

```bash
python3 skills/engineering/http-resume-integrity/reproduce.py
```

See [primary sources and validation limits](SOURCES.md). No HTTP-client integration or production downloader is supplied.

## Pitfalls

- `Accept-Ranges` advertises support, not a future response guarantee.
- `curl -C -` derives an offset from local files; that does not establish their provenance.
- A matching length or clean transport exit cannot authenticate artifact bytes.
- Never disable TLS verification to make a resume succeed.
