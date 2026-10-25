"""Original offline byte-splice contract, not an HTTP client or durable writer.

Python 3.10+ stdlib. No network, subprocess, or files. Header fields below are
already parsed, unique, and normalized by a hypothetical trusted HTTP adapter;
an absent Content-Encoding maps to the internal coding value "identity".
Only a known-size identity-coded single range with a strong ASCII ETag is
supported. Persistent storage, request selection, TLS, framing, and credential
handling belong to the unimplemented adapter. The immutable result models a
staged commit; it does not establish filesystem crash consistency.
"""

from dataclasses import dataclass, replace
import hashlib
import re
import unittest


class InvalidEvidence(ValueError):
    pass


class RestartRequired(InvalidEvidence):
    pass


@dataclass(frozen=True)
class Checkpoint:
    resource: str
    selection: str  # Nonsecret representation-context identifier, not auth data.
    etag: str
    total: int
    prefix: bytes
    generation: int = 0


@dataclass(frozen=True)
class Response:
    resource: str
    selection: str
    status: int = 206
    etag: str = '"v1"'
    content_range: str = "bytes 4-7/8"
    coding: str = "identity"
    media_type: str = "application/octet-stream"
    content_length: int | None = 4


def strong_ascii_tag(value):
    # Deliberately narrower than RFC's obs-text grammar; rejects rather than
    # rewriting unsupported validators. A strong ETag is not a trusted digest.
    return isinstance(value, str) and re.fullmatch(r'"[\x21\x23-\x7e]*"', value) is not None


def request_headers(checkpoint):
    if not strong_ascii_tag(checkpoint.etag):
        raise RestartRequired("No supported strong validator")
    return {"Range": f"bytes={len(checkpoint.prefix)}-",
            "If-Range": checkpoint.etag, "Accept-Encoding": "identity"}


def stage_suffix(checkpoint, response, chunks, *, max_total=1024, max_chunk=128):
    """Return a new immutable checkpoint only after all supplied bytes succeed.

    An iterator exception models an interrupted body. The caller must supply
    raw identity-domain bytes only after transport/header validation and must
    not turn an interrupted transfer into successful iterator exhaustion.
    """
    request_headers(checkpoint)
    n = len(checkpoint.prefix)
    if (type(checkpoint.total) is not int or not 0 < n < checkpoint.total
            or checkpoint.total > max_total or max_chunk <= 0):
        raise InvalidEvidence("Invalid or unsupported checkpoint/budget")
    if (response.resource, response.selection) != (checkpoint.resource, checkpoint.selection):
        raise RestartRequired("Resource or representation selection changed")
    if response.status == 200:
        raise RestartRequired("Full response must replace, never append")
    if response.status != 206:
        raise InvalidEvidence("No supported partial response; 416 is not completion proof")
    if not strong_ascii_tag(response.etag) or response.etag != checkpoint.etag:
        raise RestartRequired("Representation validator changed")
    if response.coding.lower() != "identity":
        raise RestartRequired("Unsupported byte domain")
    if response.media_type.lower().split(";", 1)[0].strip() == "multipart/byteranges":
        raise InvalidEvidence("Multipart not supported")
    match = re.fullmatch(r"bytes ([0-9]+)-([0-9]+)/([0-9]+)", response.content_range)
    if not match:
        raise InvalidEvidence("Unsupported or malformed Content-Range")
    try:
        first, last, total = map(int, match.groups())
    except ValueError as exc:
        raise InvalidEvidence("Range numeral exceeds parser limits") from exc
    if first != n or not first <= last < total or total != checkpoint.total:
        raise InvalidEvidence("Noncontiguous range or changed total")
    expected = last - first + 1
    if response.content_length is not None and (
            type(response.content_length) is not int or response.content_length != expected):
        raise InvalidEvidence("Content-Length differs from range length")
    staged = bytearray()
    for chunk in chunks:
        if not isinstance(chunk, bytes) or len(chunk) > max_chunk:
            raise InvalidEvidence("Adapter yielded invalid or oversized chunk")
        if len(staged) + len(chunk) > expected:
            raise InvalidEvidence("Body exceeds declared range")
        staged.extend(chunk)
    if len(staged) != expected:
        raise InvalidEvidence("Body is incomplete")
    return replace(checkpoint, prefix=checkpoint.prefix + bytes(staged),
                   generation=checkpoint.generation + 1)


def commit_candidate(current, original, candidate):
    """Model compare-and-swap; production requires an actual atomic operation.

    Precondition: candidate is exactly a successful stage_suffix(original, ...)
    result. This helper is not an authenticity gate for arbitrary candidate data.
    """
    if current != original or candidate.generation != original.generation + 1:
        raise InvalidEvidence("Checkpoint advanced while suffix was staged")
    return candidate


def verified_artifact(checkpoint, expected_sha256):
    """The expected digest must come from separately trusted artifact metadata."""
    if len(checkpoint.prefix) != checkpoint.total:
        raise InvalidEvidence("Incomplete artifact")
    if hashlib.sha256(checkpoint.prefix).hexdigest() != expected_sha256:
        raise InvalidEvidence("Artifact digest mismatch")
    return checkpoint.prefix


class ResumeCases(unittest.TestCase):
    def setUp(self):
        self.old = b"AAAA1111"
        self.new = b"BBBB2222"
        self.cp = Checkpoint("https://example.invalid/archive", "identity-v1", '"v1"', 8, b"AAAA")
        self.response = Response(self.cp.resource, self.cp.selection)

    def test_baseline_silently_mixes_equal_length_versions(self):
        naive = self.cp.prefix + self.new[4:]
        self.assertEqual(len(naive), len(self.new))
        self.assertNotIn(naive, (self.old, self.new))
        with self.assertRaises(RestartRequired):
            stage_suffix(self.cp, replace(self.response, etag='"v2"'), [self.new[4:]])

    def test_correct_resume_and_trusted_digest(self):
        next_cp = stage_suffix(self.cp, self.response, [b"11", b"11"])
        current = commit_candidate(self.cp, self.cp, next_cp)
        self.assertEqual(verified_artifact(current, hashlib.sha256(self.old).hexdigest()), self.old)
        self.assertEqual(self.cp.prefix, b"AAAA")

    def test_headers_pin_validator_and_byte_domain(self):
        self.assertEqual(request_headers(self.cp), {
            "Range": "bytes=4-", "If-Range": '"v1"', "Accept-Encoding": "identity"})

    def test_weak_missing_or_malformed_validator_cannot_resume(self):
        for tag in ('W/"v1"', '', 'v1', '"bad\nvalue"', '"a" "b"'):
            with self.subTest(tag=tag), self.assertRaises(RestartRequired):
                request_headers(replace(self.cp, etag=tag))

    def test_200_is_never_appended_even_with_same_etag(self):
        with self.assertRaises(RestartRequired):
            stage_suffix(self.cp, replace(self.response, status=200), [self.old])
        self.assertEqual(self.cp.prefix, b"AAAA")

    def test_416_is_not_success_even_when_length_matches(self):
        with self.assertRaises(InvalidEvidence):
            stage_suffix(self.cp, replace(self.response, status=416, content_range="bytes */8"), [])

    def test_errors_are_not_data(self):
        for status in (301, 304, 403, 500):
            with self.subTest(status=status), self.assertRaises(InvalidEvidence):
                stage_suffix(self.cp, replace(self.response, status=status), [b"oops"])

    def test_wrong_start_gap_overlap_or_inverted_range(self):
        for header in ("bytes 3-6/8", "bytes 5-7/8", "bytes 4-3/8", "bytes 4-8/8"):
            with self.subTest(header=header), self.assertRaises(InvalidEvidence):
                stage_suffix(self.cp, replace(self.response, content_range=header), [b"1111"])

    def test_unknown_changed_or_malformed_total(self):
        for header in ("bytes 4-7/*", "bytes 4-7/9", "items 4-7/8", "bytes 4-7/-1", "bytes ٤-٧/٨"):
            with self.subTest(header=header), self.assertRaises(InvalidEvidence):
                stage_suffix(self.cp, replace(self.response, content_range=header), [b"1111"])

    def test_short_valid_interval_needs_another_request(self):
        mid = stage_suffix(self.cp, replace(self.response, content_range="bytes 4-5/8", content_length=2), [b"11"])
        self.assertEqual(request_headers(mid)["Range"], "bytes=6-")
        with self.assertRaises(InvalidEvidence):
            verified_artifact(mid, hashlib.sha256(self.old).hexdigest())
        end = stage_suffix(mid, replace(self.response, content_range="bytes 6-7/8", content_length=2), [b"11"])
        self.assertEqual(end.prefix, self.old)

    def test_coding_or_selection_or_target_change(self):
        variants = (replace(self.response, coding="gzip"),
                    replace(self.response, selection="different-language"),
                    replace(self.response, resource="https://other.invalid/archive"))
        for response in variants:
            with self.subTest(response=response), self.assertRaises(RestartRequired):
                stage_suffix(self.cp, response, [b"1111"])

    def test_multipart_rejected(self):
        with self.assertRaises(InvalidEvidence):
            stage_suffix(self.cp, replace(self.response, media_type="multipart/byteranges; boundary=x"), [b"1111"])

    def test_short_overlong_and_length_mismatch_bodies(self):
        for body in (b"111", b"11111"):
            with self.subTest(body=body), self.assertRaises(InvalidEvidence):
                stage_suffix(self.cp, self.response, [body])
        with self.assertRaises(InvalidEvidence):
            stage_suffix(self.cp, replace(self.response, content_length=5), [b"1111"])

    def test_absent_content_length_uses_range_and_actual_count(self):
        candidate = stage_suffix(self.cp, replace(self.response, content_length=None), [b"1111"])
        self.assertEqual(candidate.prefix, self.old)

    def test_interrupted_iterator_never_commits_prefix_or_suffix(self):
        def interrupted():
            yield b"11"
            raise TimeoutError("synthetic interruption")
        with self.assertRaises(TimeoutError):
            stage_suffix(self.cp, self.response, interrupted())
        self.assertEqual(self.cp.prefix, b"AAAA")
        self.assertEqual(self.cp.generation, 0)

    def test_byte_budgets_reject_before_commit(self):
        with self.assertRaises(InvalidEvidence):
            stage_suffix(self.cp, self.response, [b"1111"], max_total=7)
        with self.assertRaises(InvalidEvidence):
            stage_suffix(self.cp, self.response, [b"1111"], max_chunk=3)

    def test_concurrent_retry_cannot_commit_twice(self):
        a = stage_suffix(self.cp, self.response, [b"1111"])
        b = stage_suffix(self.cp, self.response, [b"1111"])
        current = commit_candidate(self.cp, self.cp, a)
        with self.assertRaises(InvalidEvidence):
            commit_candidate(current, self.cp, b)

    def test_same_validator_does_not_authenticate_bytes(self):
        corrupt = stage_suffix(self.cp, self.response, [b"2222"])
        with self.assertRaises(InvalidEvidence):
            verified_artifact(corrupt, hashlib.sha256(self.old).hexdigest())


if __name__ == "__main__":
    unittest.main(verbosity=2)
