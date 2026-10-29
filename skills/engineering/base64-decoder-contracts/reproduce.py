"""Original stdlib-only contract fixtures; not a third-party speed benchmark."""
import base64
import binascii
import unittest


def decode_canonical(data):
    if not isinstance(data, bytes):
        raise TypeError("bytes required")
    decoded = base64.b64decode(data, validate=True)
    if base64.b64encode(decoded) != data:
        raise binascii.Error("noncanonical Base64")
    return decoded


def decode_crlf_profile(data):
    """Local standard-alphabet profile permitting CR/LF only, not MIME parsing."""
    if not isinstance(data, bytes):
        raise TypeError("bytes required")
    return decode_canonical(data.replace(b"\r", b"").replace(b"\n", b""))


class Contracts(unittest.TestCase):
    def test_clean_bytes(self):
        for raw in (b"", b"f", b"fo", b"foo", bytes(range(256))):
            with self.subTest(raw=raw):
                self.assertEqual(decode_canonical(base64.b64encode(raw)), raw)

    def test_default_accepts_punctuation(self):
        self.assertEqual(base64.b64decode(b"Z!g=="), b"f")
        with self.assertRaises(binascii.Error):
            decode_canonical(b"Z!g==")

    def test_strict_is_not_canonical_on_tested_python(self):
        self.assertEqual(base64.b64decode(b"Zh==", validate=True), b"f")
        with self.assertRaises(binascii.Error):
            decode_canonical(b"Zh==")

    def test_second_pad_bit_case(self):
        self.assertEqual(base64.b64decode(b"Zm9=", validate=True), b"fo")
        with self.assertRaises(binascii.Error):
            decode_canonical(b"Zm9=")

    def test_padding_and_trailing_data(self):
        for data in (b"Zg", b"Zg===", b"=Zg==", b"Zg==junk", b"===="):
            with self.subTest(data=data), self.assertRaises(binascii.Error):
                decode_canonical(data)

    def test_url_alphabet_is_distinct(self):
        self.assertEqual(base64.urlsafe_b64decode(b"-_8="), b"\xfb\xff")
        with self.assertRaises(binascii.Error):
            decode_canonical(b"-_8=")
        self.assertEqual(decode_canonical(b"+/8="), b"\xfb\xff")

    def test_whitespace_profiles_differ(self):
        with self.assertRaises(binascii.Error):
            decode_canonical(b"Zg==\r\n")
        self.assertEqual(decode_crlf_profile(b"Zg==\r\n"), b"f")

    def test_crlf_does_not_imply_all_whitespace(self):
        for data in (b"Z g==", b"Z\tg==", b"Z\vg==", b"Z\fg=="):
            with self.subTest(data=data), self.assertRaises(binascii.Error):
                decode_crlf_profile(data)

    def test_bytes_only_profile(self):
        for data in ("Zg==", bytearray(b"Zg=="), None):
            with self.subTest(data=data), self.assertRaises(TypeError):
                decode_canonical(data)

    def test_equal_lengths_are_not_equal_outputs(self):
        left, right = decode_canonical(b"Zg=="), decode_canonical(b"Zw==")
        self.assertEqual(len(left), len(right))
        self.assertNotEqual(left, right)

    def test_profile_normalization_is_per_call_work(self):
        calls = []
        def normalize(data):
            calls.append(data)
            return data.replace(b"\n", b"")
        for _ in range(3):
            self.assertEqual(decode_canonical(normalize(b"Zg==\n")), b"f")
        self.assertEqual(len(calls), 3)

    def test_throughput_denominator(self):
        decoded = b"foo" * 100
        encoded = base64.b64encode(decoded)
        self.assertEqual(len(encoded), 400)
        self.assertEqual(len(decoded), 300)
        self.assertEqual(len(encoded) / len(decoded), 4 / 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
