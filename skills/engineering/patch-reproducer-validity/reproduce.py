#!/usr/bin/env python3
"""Synthetic off-by-one example for patch-reproducer-validity."""


def buggy_page(ids, after, limit):
    start = after
    return ids[start : start + limit - 1]


def fixed_page(ids, after, limit):
    start = after
    return ids[start : start + limit]


def assert_page_contract(page):
    assert page(list(range(1, 30)), after=10, limit=2) == [11, 12]


try:
    assert_page_contract(buggy_page)
except AssertionError:
    print("BASELINE RED: expected [11, 12], got [11]")
else:
    raise AssertionError("buggy baseline unexpectedly satisfied the contract")

assert_page_contract(fixed_page)
print("CANDIDATE GREEN: expected [11, 12], got [11, 12]")

buggy_result = buggy_page(list(range(1, 30)), after=10, limit=2)
fixed_result = fixed_page(list(range(1, 30)), after=10, limit=2)
assert bool(buggy_result) and bool(fixed_result)
print("WEAK ORACLE FALSE CONFIDENCE: nonempty check passes for both")
