"""Compile original fixtures with an existing compiler; never download tools."""
import pathlib
import os
import shutil
import subprocess
import tempfile

source = pathlib.Path(__file__).with_name('lookup.cpp')
compiler = shutil.which('g++')
if not compiler:
    raise SystemExit('BLOCKED: existing g++ required; no compiler installed')

with tempfile.TemporaryDirectory(prefix='lookup-contract-') as directory:
    out = pathlib.Path(directory)
    def build(name, flags):
        binary = out / name
        subprocess.run([compiler, '-std=c++17', '-Wall', '-Wextra', *flags,
                        str(source), '-o', str(binary)], check=True)
        return binary
    def run(binary, *args):
        # Leak checking is outside this bounds test and unavailable under ptrace.
        env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0')
        return subprocess.run([str(binary), *args], capture_output=True, text=True, env=env)
    print(subprocess.check_output([compiler, '--version'], text=True).splitlines()[0])
    for flags, name in [(['-O0'], 'debug'), (['-O2', '-DNDEBUG'], 'release'),
                        (['-O1', '-g', '-fsanitize=address', '-fno-omit-frame-pointer', '-no-pie'], 'asan')]:
        binary = build(name, flags)
        result = run(binary)
        if result.returncode:
            raise SystemExit(name + ' failed: ' + result.stderr)
        print(name, result.stdout.strip())
        if name == 'asan':
            bad = run(binary, 'invalid')
            if bad.returncode == 77:
                raise SystemExit('INCONCLUSIVE: allocation did not meet page-control premise')
            if not bad.returncode or 'heap-buffer-overflow' not in bad.stderr:
                raise SystemExit('INCONCLUSIVE: expected ASan heap-buffer-overflow absent: ' + bad.stderr)
            print('ASan caught intentional same-page 16-byte read from 3-byte allocation')
    for macro in ['MUTANT_SLOT_ONLY', 'MUTANT_PREFIX']:
        result = run(build(macro, ['-O2', '-D' + macro]))
        if result.returncode != 1 or 'oracle mismatch' not in result.stderr:
            raise SystemExit('mutation not caught: ' + macro)
        print('caught', macro)
