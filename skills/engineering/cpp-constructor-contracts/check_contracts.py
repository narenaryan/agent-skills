#!/usr/bin/env python3
"""Original isolated GCC-oriented C++20 probes, not a portable conformance suite.
Run from this directory: python3 check_contracts.py
No generated program reads an indeterminate value. Negative programs are compiled only.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile

CC = os.environ.get('CXX', 'g++')
HEADER = '''#include <type_traits>
struct First { int n; constexpr First() = default; };
// Template permits a valid constexpr specialization; avoid C++20 IFNDR.
template<class T> struct EmptyT { T n; constexpr EmptyT() {} };
struct Ready { int n = 7; };
constexpr EmptyT<Ready> valid_empty{};
static_assert(valid_empty.n.n == 7);
using Empty = EmptyT<int>;
struct Late { int n; constexpr Late(); }; constexpr Late::Late() = default;
struct Member { int n = 7; constexpr Member() = default; };
struct Fixed { int n = 7; constexpr Fixed() {} };
'''
# name, mode, body, expected compiler success, expected rejection evidence
CASES = [
 ('first_value', 'c++20', 'constexpr First x{}; static_assert(x.n == 0);', True, ''),
 ('first_default', 'c++20', 'constexpr First x;', False, 'uninitialized'),
 ('empty_value', 'c++20', 'constexpr Empty x{};', False, 'incompletely initialized'),
 ('late_value', 'c++20', 'constexpr Late x{};', False, 'incompletely initialized'),
 ('first_traits', 'c++20', 'static_assert(std::is_trivially_default_constructible_v<First>); static_assert(!std::is_aggregate_v<First>);', True, ''),
 ('empty_traits', 'c++20', 'static_assert(!std::is_trivially_default_constructible_v<Empty>); static_assert(!std::is_aggregate_v<Empty>);', True, ''),
 ('late_traits', 'c++20', 'static_assert(!std::is_trivially_default_constructible_v<Late>);', True, ''),
 ('member_initializer', 'c++20', 'constexpr Member x; constexpr Fixed y; static_assert(x.n == 7 && y.n == 7); static_assert(!std::is_trivially_default_constructible_v<Member>);', True, ''),
 ('wrapper_explicit_value', 'c++20', 'struct Outer { First f; constexpr Outer() : f() {} }; constexpr Outer x; static_assert(x.f.n == 0);', True, ''),
 ('wrapper_omitted', 'c++20', 'template<class T> struct Outer { T f; constexpr Outer() {} }; constexpr Outer<Ready> good{}; static_assert(good.f.n == 7); constexpr Outer<First> x{};', False, 'incompletely initialized'),
 ('wrapper_implicit_value', 'c++20', 'struct Outer { First f; Outer() = default; }; constexpr Outer x{}; static_assert(x.f.n == 0);', True, ''),
 ('array_value', 'c++20', 'constexpr First x[3]{}; static_assert(x[0].n == 0 && x[2].n == 0);', True, ''),
 ('mutant_zero_guarantee', 'c++20', 'static_assert(std::is_trivially_default_constructible_v<Empty>, "contract_changed");', False, 'static assertion failed: contract_changed'),
 ('mutant_late_trivial', 'c++20', 'static_assert(std::is_trivially_default_constructible_v<Late>, "contract_changed");', False, 'static assertion failed: contract_changed'),
]
# Separate header avoids C++20 constexpr rules contaminating C++17 aggregate probe.
AGGREGATE = '#include <type_traits>\nstruct A { int n; A() = default; };\n'
EXTRA = [
 ('aggregate17', 'c++17', AGGREGATE + 'static_assert(std::is_aggregate_v<A>); constexpr A x{9}; static_assert(x.n == 9);', True, ''),
 ('aggregate20', 'c++20', AGGREGATE + 'static_assert(!std::is_aggregate_v<A>); constexpr A x{}; static_assert(x.n == 0);', True, ''),
 ('aggregate20_old_call', 'c++20', AGGREGATE + 'A x{9};', False, 'no matching function'),
]
RUNTIME = HEADER + '''
Empty hidden; // Static zero-initialization precedes the empty constructor.
int main() {
    First a{}; Member b; Fixed c{}; First array[3]{};
    if (a.n != 0 || b.n != 7 || c.n != 7 || array[2].n != 0 || hidden.n != 0) return 1;
    Empty assigned; assigned.n = 19; // Write before any read.
    return assigned.n == 19 ? 0 : 2;
}
'''

def invoke(args):
    return subprocess.run(args, text=True, capture_output=True, timeout=30,
                          env={**os.environ, 'LC_ALL': 'C'})

def main():
    version = invoke([CC, '--version'])
    if version.returncode: raise RuntimeError(version.stderr)
    records = []
    with tempfile.TemporaryDirectory(prefix='constructor-contracts-') as tmp:
        root = Path(tmp)
        for name, mode, body, good, diagnostic in CASES + EXTRA:
            source = (HEADER + body if (name, mode, body, good, diagnostic) in CASES else body) + '\nint main() { return 0; }\n'
            path = root / (name + '.cpp'); path.write_text(source)
            result = invoke([CC, '-std=' + mode, '-Wall', '-Wextra', '-pedantic-errors', '-fsyntax-only', str(path)])
            ok = result.returncode == 0 if good else result.returncode != 0 and diagnostic in result.stderr
            records.append({'name': name, 'expected': 'accept' if good else 'reject', 'passed': ok,
                            'diagnostic': result.stderr if not good or not ok else ''})
            if not ok: raise RuntimeError(json.dumps(records[-1], indent=2))
        path = root / 'runtime.cpp'; path.write_text(RUNTIME)
        for name, flags in [('debug', ['-O0']), ('release', ['-O2', '-DNDEBUG']),
                            ('ubsan', ['-O1', '-fsanitize=undefined', '-fno-sanitize-recover=all'])]:
            exe = root / name
            result = invoke([CC, '-std=c++20', '-Wall', '-Wextra', '-pedantic-errors', *flags, str(path), '-o', str(exe)])
            if result.returncode: raise RuntimeError(result.stderr)
            run = invoke([str(exe)])
            if run.returncode or run.stderr: raise RuntimeError(run.stderr or 'Runtime contract failed')
            records.append({'name': name, 'passed': True})
    print(json.dumps({'compiler': version.stdout.splitlines()[0], 'checks': records,
                      'limits': 'GCC-oriented diagnostics; no uninitialized runtime reads, performance, ABI, or general conformance claim.'}, indent=2))

if __name__ == '__main__': main()
