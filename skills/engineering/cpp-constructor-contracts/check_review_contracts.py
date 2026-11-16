#!/usr/bin/env python3
"""Independent review probes. Compile negatives only; run initialized cases only.
GCC-oriented diagnostics, standard-library Python, no downloaded code or installs.
"""
import json
import os
from pathlib import Path
import subprocess
import tempfile

CXX = os.environ.get('CXX', 'g++')
CASES = [
    ('late_member_initializer', '''
#include <type_traits>
struct Late { int n = 7; constexpr Late(); };
constexpr Late::Late() = default;
constexpr Late a; constexpr Late b{};
static_assert(a.n == 7 && b.n == 7);
static_assert(!std::is_trivially_default_constructible_v<Late>);
''', None),
    ('omission_uses_dmi', '''
struct Preserve { int n = 7; constexpr Preserve() {} };
struct Override { int n = 7; constexpr Override() : n() {} };
constexpr Preserve a{}; constexpr Override b{};
static_assert(a.n == 7 && b.n == 0);
''', None),
    ('pointer_value', '''
struct Handle { int *p; constexpr Handle() = default; };
constexpr Handle h{}; static_assert(h.p == nullptr);
''', None),
    ('ordinary_constructor_traits', '''
#include <type_traits>
struct First { int n; First() = default; };
struct Empty { int n; Empty() {} };
struct Late { int n; Late(); }; Late::Late() = default;
static_assert(std::is_trivially_default_constructible_v<First>);
static_assert(!std::is_trivially_default_constructible_v<Empty>);
static_assert(!std::is_trivially_default_constructible_v<Late>);
static_assert(!std::is_aggregate_v<First> && !std::is_aggregate_v<Empty> && !std::is_aggregate_v<Late>);
''', None),
    ('empty_array_rejected', '''
template<class T> struct Empty { T member; constexpr Empty() {} };
struct Ready { int n = 7; };
constexpr Empty<Ready> positive{};
static_assert(positive.member.n == 7);
template<class T> constexpr auto inspect() { Empty<T> x[2]{}; return x[1].member; }
static_assert(inspect<Ready>().n == 7);
static_assert(inspect<int>() == 0);
''', 'accessing uninitialized member'),
    ('member_initializer_trait_mutant', '''
#include <type_traits>
struct Member { int n = 7; Member() = default; };
static_assert(std::is_trivially_default_constructible_v<Member>, "DMI prevents trivial default construction");
''', 'static assertion failed: DMI prevents trivial default construction'),
]
RUNTIME = '''
struct Empty { int n; Empty() {} };
static Empty global;
thread_local Empty local_to_thread;
struct Late { int n = 7; Late(); }; Late::Late() = default;
int main() {
    static Empty function_static;
    Late late; Late late_array[2]{};
    if (global.n != 0 || local_to_thread.n != 0 || function_static.n != 0) return 1;
    if (late.n != 7 || late_array[0].n != 7 || late_array[1].n != 7) return 2;
    Empty initialized_later; initialized_later.n = 42;
    return initialized_later.n == 42 ? 0 : 3;
}
'''

def run(args):
    return subprocess.run(args, text=True, capture_output=True, timeout=30,
                          env={**os.environ, 'LC_ALL': 'C'})

def main():
    version = run([CXX, '--version'])
    if version.returncode:
        raise RuntimeError(version.stderr)
    records = []
    with tempfile.TemporaryDirectory(prefix='constructor-review-') as temp:
        root = Path(temp)
        for name, source, rejection in CASES:
            path = root / (name + '.cpp')
            path.write_text(source)
            result = run([CXX, '-std=c++20', '-Wall', '-Wextra', '-pedantic-errors', '-fsyntax-only', str(path)])
            if rejection is None:
                passed = result.returncode == 0
            else:
                passed = result.returncode != 0 and 'error:' in result.stderr and rejection in result.stderr
            records.append({'name': name, 'passed': passed, 'diagnostic': result.stderr})
            if not passed:
                raise RuntimeError(json.dumps(records[-1]))
        path = root / 'runtime.cpp'; path.write_text(RUNTIME)
        for name, flags in [('debug', ['-O0']), ('release', ['-O2', '-DNDEBUG']),
                            ('ubsan', ['-O1', '-fsanitize=undefined', '-fno-sanitize-recover=all'])]:
            executable = root / name
            build = run([CXX, '-std=c++20', '-Wall', '-Wextra', '-pedantic-errors', *flags, str(path), '-o', str(executable)])
            if build.returncode:
                raise RuntimeError(build.stderr)
            result = run([str(executable)])
            if result.returncode or result.stderr:
                raise RuntimeError(result.stderr or 'Runtime contract failed')
            records.append({'name': name, 'passed': True})
    print(json.dumps({'compiler': version.stdout.splitlines()[0], 'checks': records}, indent=2))

if __name__ == '__main__':
    main()
