#!/usr/bin/env python3
"""Original conservative classifier demonstration; no network requests or DNS implementation.

Run: python3 reproduce.py
Uses synthetic Cloudflare-style JSON envelopes. Live observations are in SOURCES.md.
Only exact-owner A/AAAA test names are accepted; CNAME chains are intentionally
inconclusive. The caller must supply samples from the same endpoint/time window.
"""
import ipaddress
import itertools
import unittest


def outcome(response, name, qtype=1):
    """Return Y/F only for well-formed expected-query samples; otherwise ?."""
    if not isinstance(response, dict) or type(qtype) is not int or qtype not in (1, 28):
        return '?'
    if response.get('CD') is not False or response.get('TC') is not False:
        return '?'
    questions = response.get('Question')
    if not isinstance(questions, list) or len(questions) != 1:
        return '?'
    q = questions[0]
    if not isinstance(q, dict) or type(q.get('type')) is not int or q.get('type') != qtype or str(q.get('name', '')).rstrip('.').lower() != name.rstrip('.').lower():
        return '?'
    status = response.get('Status')
    answers = response.get('Answer', [])
    if type(status) is not int or not isinstance(answers, list):
        return '?'
    if status == 2:
        return 'F' if not answers else '?'
    if status != 0:
        return '?'
    for answer in answers:
        if not isinstance(answer, dict):
            return '?'
        if type(answer.get('type')) is int and answer.get('type') == qtype and str(answer.get('name', '')).rstrip('.').lower() == name.rstrip('.').lower():
            if not isinstance(answer.get('data'), str):
                return '?'
            try:
                address = ipaddress.ip_address(answer.get('data', ''))
            except (ValueError, TypeError):
                return '?'
            if address.version == (4 if qtype == 1 else 6):
                return 'Y'
    return '?'


def classify(control, is_ta, not_ta, bogus, tag=38696):
    """Inference, not proof of implementation, individual backend, or future health."""
    if type(tag) is not int or not 0 <= tag <= 65535:
        raise ValueError('key tag must be an unsigned 16-bit integer')
    ordinary = outcome(control, 'cloudflare.com')
    if ordinary != 'Y':
        return 'inconclusive'
    names = (f'root-key-sentinel-is-ta-{tag:05d}.dnstest.dev',
             f'root-key-sentinel-not-ta-{tag:05d}.dnstest.dev', 'dnssec-failed.org')
    pattern = tuple(outcome(r, n) for r, n in zip((is_ta, not_ta, bogus), names))
    # Nonvalidating paths may not set AD on the ordinary control either.
    if pattern == ('Y', 'Y', 'Y'):
        return 'validation-not-demonstrated'
    if control.get('AD') is not True:
        return 'inconclusive'
    result = {('Y', 'F', 'F'): 'consistent-with-trusted',
              ('F', 'Y', 'F'): 'consistent-with-untrusted',
              ('Y', 'Y', 'F'): 'sentinel-indeterminate'}.get(pattern, 'inconclusive')
    # A positive sentinel must itself be authenticated before inferring trust.
    if result in ('consistent-with-trusted', 'consistent-with-untrusted'):
        positive = is_ta if pattern[0] == 'Y' else not_ta
        if positive.get('AD') is not True:
            return 'inconclusive'
    return result


def sample(name, value, ad=True):
    data = {'Status': 0 if value == 'Y' else 2, 'CD': False, 'TC': False,
            'AD': ad if value == 'Y' else False,
            'Question': [{'name': name, 'type': 1}]}
    if value == 'Y':
        data['Answer'] = [{'name': name, 'type': 1, 'data': '192.0.2.1'}]
    return data


def case(pattern, tag=38696):
    return [sample('cloudflare.com', 'Y')] + [sample(n, x) for n, x in zip(
        (f'root-key-sentinel-is-ta-{tag:05d}.dnstest.dev',
         f'root-key-sentinel-not-ta-{tag:05d}.dnstest.dev', 'dnssec-failed.org'), pattern)]


class Tests(unittest.TestCase):
    def test_all_eight_rfc_patterns(self):
        expected = {('Y', 'F', 'F'): 'consistent-with-trusted',
                    ('F', 'Y', 'F'): 'consistent-with-untrusted',
                    ('Y', 'Y', 'F'): 'sentinel-indeterminate',
                    ('Y', 'Y', 'Y'): 'validation-not-demonstrated'}
        for pattern in itertools.product('YF', repeat=3):
            with self.subTest(pattern=pattern):
                self.assertEqual(classify(*case(pattern)), expected.get(pattern, 'inconclusive'))

    def test_naive_positive_only_false_readiness(self):
        unsupported = case('YYF')
        self.assertEqual(outcome(unsupported[1], unsupported[1]['Question'][0]['name']), 'Y')
        self.assertEqual(classify(*unsupported), 'sentinel-indeterminate')

    def test_transport_missing_malformed_and_dns_failures(self):
        for position in range(4):
            for invalid in (None, {}, {'error': 'HTTP 503'}, 'timeout'):
                data = case('YFF'); data[position] = invalid
                self.assertEqual(classify(*data), 'inconclusive')
            for status in (3, 5, '0', True):
                data = case('YFF'); data[position]['Status'] = status
                self.assertEqual(classify(*data), 'inconclusive')

    def test_cd_and_truncation(self):
        for position in range(4):
            for field in ('CD', 'TC'):
                data = case('YFF'); data[position][field] = True
                self.assertEqual(classify(*data), 'inconclusive')

    def test_empty_noerror_and_wrong_addresses(self):
        for bad in ([], [{'name': 'other.example', 'type': 1, 'data': '192.0.2.1'}],
                    [{'name': 'cloudflare.com', 'type': 1, 'data': 'garbage'}]):
            data = case('YFF'); data[0]['Answer'] = bad
            self.assertEqual(classify(*data), 'inconclusive')

    def test_wrong_question_type_or_name(self):
        for position in range(4):
            for key, val in [('type', 16), ('name', 'elsewhere.example')]:
                data = case('YFF'); data[position]['Question'][0][key] = val
                self.assertEqual(classify(*data), 'inconclusive')

    def test_unsigned_positive_control_or_sentinel(self):
        for position in (0, 1):
            data = case('YFF'); data[position]['AD'] = False
            self.assertEqual(classify(*data), 'inconclusive')

    def test_servfail_with_answer_rejected(self):
        data = case('YFF'); data[2]['Answer'] = [{'type': 1, 'data': '192.0.2.1'}]
        self.assertEqual(classify(*data), 'inconclusive')

    def test_tag_format(self):
        self.assertEqual(classify(*case('FYF', 42), tag=42), 'consistent-with-untrusted')
        for invalid in (-1, 65536, '38696', True):
            with self.assertRaises(ValueError): classify(*case('YFF'), tag=invalid)

    def test_aaaa_outcome(self):
        r = sample('example.test', 'Y');r['Question'][0]['type'] = 28
        r['Answer'][0].update(type=28, data='2001:db8::1')
        self.assertEqual(outcome(r, 'example.test', 28), 'Y')
        self.assertEqual(outcome(r, 'example.test', 1), '?')

    def test_json_type_confusion(self):
        for field in ('Question', 'Answer'):
            data = case('YFF'); data[1][field][0]['type'] = True
            self.assertEqual(classify(*data), 'inconclusive')
        for invalid in (1, True, None, [], {}):
            data = case('YFF'); data[1]['Answer'][0]['data'] = invalid
            self.assertEqual(classify(*data), 'inconclusive')
        self.assertEqual(outcome(sample('example.test', 'Y'), 'example.test', True), '?')

    def test_case_and_terminal_dot(self):
        r = sample('EXAMPLE.TEST.', 'Y')
        self.assertEqual(outcome(r, 'example.test'), 'Y')


if __name__ == '__main__':
    unittest.main(verbosity=2)
