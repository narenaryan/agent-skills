#!/usr/bin/env python3
"""Original offline TLS fixture; no network, installation, or host-store changes.

Requires already installed Python 3.10+ ssl and OpenSSL CLI 3.x. Generates short-
lived test-only keys in a TemporaryDirectory and deletes them on exit. Never use
these certificates/keys for accounts, services, signing, or persistent access.
Tests a root-anchor replacement, NOT CRL/OCSP/intermediate distrust or any real
advisory. TLS handshakes are real; deployment evidence classification is synthetic.
"""
from dataclasses import dataclass, replace
from pathlib import Path
import os
import shutil
import ssl
import subprocess
import tempfile
import unittest

HOST = "fixture.invalid"


def run_openssl(root, *args):
    env = os.environ.copy()
    # Fixture-only config; do not inherit a custom provider/config or key logger.
    env.pop("SSLKEYLOGFILE", None)
    env["OPENSSL_CONF"] = str(root / "empty.cnf")
    subprocess.run(["openssl", *args], cwd=root, env=env, check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)


def make_chain(root, name, serial):
    run_openssl(root, "req", "-x509", "-newkey", "rsa:2048", "-noenc",
                "-keyout", f"{name}-ca.key", "-out", f"{name}-ca.pem",
                "-days", "1", "-subj", f"/CN=Disposable Fixture {name}",
                "-addext", "basicConstraints=critical,CA:TRUE",
                "-addext", "keyUsage=critical,keyCertSign,cRLSign")
    run_openssl(root, "req", "-new", "-newkey", "rsa:2048", "-noenc",
                "-keyout", f"{name}.key", "-out", f"{name}.csr",
                "-subj", f"/CN={HOST}")
    (root / "leaf.ext").write_text(
        "basicConstraints=critical,CA:FALSE\n"
        "keyUsage=critical,digitalSignature,keyEncipherment\n"
        "extendedKeyUsage=serverAuth\n"
        f"subjectAltName=DNS:{HOST}\n", encoding="ascii")
    run_openssl(root, "x509", "-req", "-in", f"{name}.csr",
                "-CA", f"{name}-ca.pem", "-CAkey", f"{name}-ca.key",
                "-set_serial", str(serial), "-days", "1",
                "-extfile", "leaf.ext", "-out", f"{name}.pem")


def client(bundle):
    # Do not explicitly load default stores or enable SSLKEYLOGFILE.
    # A managed runtime may preload anchors; tests isolate fixture A/B decisions.
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.load_verify_locations(cafile=str(bundle))
    return ctx


def server(root, name):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(str(root / f"{name}.pem"), str(root / f"{name}.key"))
    return ctx


def handshake(ctx, peer, hostname=HOST):
    if not isinstance(hostname, str) or not hostname:
        raise ValueError("A nonempty intended hostname is mandatory")
    if ctx.verify_mode != ssl.CERT_REQUIRED or not ctx.check_hostname:
        raise ValueError("Fixture requires chain and hostname verification")
    ci, co, si, so = (ssl.MemoryBIO() for _ in range(4))
    c = ctx.wrap_bio(ci, co, server_hostname=hostname)
    s = peer.wrap_bio(si, so, server_side=True)
    done = [False, False]
    for _ in range(100):
        for index, obj in enumerate((c, s)):
            if not done[index]:
                try:
                    obj.do_handshake()
                    done[index] = True
                except ssl.SSLWantReadError:
                    pass
        if co.pending:
            si.write(co.read())
        if so.pending:
            ci.write(so.read())
        if all(done):
            if c.session_reused:
                raise RuntimeError("Fixture unexpectedly resumed a session")
            return c, s, co, si
    raise TimeoutError("Bounded fixture handshake did not finish")


@dataclass(frozen=True)
class Evidence:
    path_matches: bool = True
    generation_matches: bool = True
    fresh_handshake: bool = True
    allowed_peer_passes: bool = True
    wrong_hostname_rejected: bool = True
    disallowed_result: str = "expected_certificate_rejection"


def disposition(e):
    # Local evidence policy, not a PKI engine or production closure approval.
    controls = (e.path_matches, e.generation_matches, e.fresh_handshake,
                e.allowed_peer_passes, e.wrong_hostname_rejected)
    if not all(v is True for v in controls):
        return "verification-pending"
    if e.disallowed_result == "accepted":
        return "exposure-observed"
    if e.disallowed_result == "expected_certificate_rejection":
        return "path-verified"
    return "verification-pending"


class TrustTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not shutil.which("openssl"):
            raise RuntimeError("OpenSSL is not installed; fixture not executed")
        cls.temp = tempfile.TemporaryDirectory(prefix="tls-fixture-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        (cls.root / "empty.cnf").write_text("", encoding="ascii")
        make_chain(cls.root, "a", 1001)
        make_chain(cls.root, "b", 1002)
        cls.a = server(cls.root, "a")
        cls.b = server(cls.root, "b")

    def setUp(self):
        self.bundle = self.root / "active.pem"
        self.bundle.write_bytes((self.root / "a-ca.pem").read_bytes())

    def replace_bundle(self):
        self.bundle.write_bytes((self.root / "b-ca.pem").read_bytes())

    def rejected(self, context, peer, hostname=HOST, expected_code=20):
        # OpenSSL X509_V_ERR_UNABLE_TO_GET_ISSUER_CERT_LOCALLY = 20;
        # X509_V_ERR_HOSTNAME_MISMATCH = 62. Other failures are not this oracle.
        with self.assertRaises(ssl.SSLCertVerificationError) as caught:
            handshake(context, peer, hostname)
        self.assertEqual(caught.exception.verify_code, expected_code,
                         caught.exception.verify_message)

    def test_01_baseline_accepts_original_anchor(self):
        handshake(client(self.bundle), self.a)

    def test_02_baseline_rejects_untrusted_anchor(self):
        self.rejected(client(self.bundle), self.b)

    def test_03_replacing_file_leaves_loaded_context_accepting_a(self):
        old = client(self.bundle)
        self.replace_bundle()
        handshake(old, self.a)

    def test_04_recreated_context_rejects_removed_anchor(self):
        self.replace_bundle()
        self.rejected(client(self.bundle), self.a)

    def test_05_recreated_context_accepts_allowed_control(self):
        self.replace_bundle()
        handshake(client(self.bundle), self.b)

    def test_06_reloading_is_additive_not_removal(self):
        old = client(self.bundle)
        initial = old.cert_store_stats()["x509_ca"]
        self.replace_bundle()
        old.load_verify_locations(cafile=str(self.bundle))
        self.assertEqual(old.cert_store_stats()["x509_ca"], initial + 1)
        handshake(old, self.a)
        handshake(old, self.b)

    def test_07_diagnostic_client_does_not_update_application(self):
        application = client(self.bundle)
        self.replace_bundle()
        diagnostic = client(self.bundle)
        self.rejected(diagnostic, self.a)
        handshake(application, self.a)

    def test_08_allowed_chain_wrong_hostname_rejected(self):
        self.rejected(client(self.bundle), self.a, "wrong.invalid", expected_code=62)

    def test_09_missing_hostname_not_accepted(self):
        for name in (None, ""):
            with self.assertRaises(ValueError):
                handshake(client(self.bundle), self.a, name)

    def test_10_existing_connection_survives_bundle_change(self):
        c, s, co, si = handshake(client(self.bundle), self.a)
        self.replace_bundle()
        c.write(b"fixture")
        si.write(co.read())
        self.assertEqual(s.read(), b"fixture")

    def test_11_good_evidence_is_path_scoped(self):
        self.assertEqual(disposition(Evidence()), "path-verified")

    def test_12_missing_controls_are_unknown(self):
        for field in ("path_matches", "generation_matches", "fresh_handshake",
                      "allowed_peer_passes", "wrong_hostname_rejected"):
            for value in (False, None, "true"):
                with self.subTest(field=field, value=value):
                    self.assertEqual(disposition(replace(Evidence(), **{field: value})),
                                     "verification-pending")

    def test_13_expected_rejection_is_not_arbitrary_failure(self):
        for outcome in ("timeout", "dns_failure", "protocol_error", "unknown", None):
            self.assertEqual(disposition(replace(Evidence(), disallowed_result=outcome)),
                             "verification-pending")

    def test_14_current_acceptance_reopens_exposure(self):
        self.assertEqual(disposition(replace(Evidence(), disallowed_result="accepted")),
                         "exposure-observed")


if __name__ == "__main__":
    print("Python SSL:", ssl.OPENSSL_VERSION)
    unittest.main(verbosity=2)
