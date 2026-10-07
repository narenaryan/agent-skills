#!/usr/bin/env python3
"""Local-only PostgreSQL locking-join experiment. Requires existing psql/server.

No third-party Python modules, installs, network listeners, or existing data use.
Prerequisites: an existing disposable database on a separately managed test
cluster, a test role allowed to create schemas, and a private Unix-socket
directory owned by the current OS user (mode 0700). This script does not start
servers, create databases, install software, or read connection passwords.
The host, port, database, and user must be supplied explicitly:
  python reproduce.py --host /tmp/private-pg-socket --port 5432 \
      --database locking_join_test \
      --user test_owner --confirm-disposable --repeats 5
This script creates and drops only its own random-named schema.
It fails closed if a lock wait is not observed or an expected result differs.
Expected outputs are source-derived; runtime validation was blocked at Unix
socket creation in the authoring environment. Inspect the emitted server
version and plans before treating results as evidence for another deployment.

Example setup (Bash, existing PostgreSQL programs on PATH; no downloads):
  set -euo pipefail
  for name in ${!PG@}; do unset "$name"; done
  export PGPASSFILE=/dev/null PGSERVICEFILE=/dev/null
  test_root=$(mktemp -d /tmp/postgres-locking.XXXXXX)
  mkdir "$test_root/socket"
  chmod 700 "$test_root" "$test_root/socket"
  trap 'pg_ctl -D "$test_root/data" -m fast -w stop >/dev/null 2>&1 || true' EXIT
  initdb -D "$test_root/data" -U locking_join_owner -A trust --no-locale
  pg_ctl -D "$test_root/data" -l "$test_root/server.log" \
    -o "-c listen_addresses='' -c unix_socket_directories='$test_root/socket' -c unix_socket_permissions=0700" -w start
  createdb -h "$test_root/socket" -p 5432 -U locking_join_owner -w locking_join_test
  python reproduce.py --host "$test_root/socket" --port 5432 \
    --database locking_join_test --user locking_join_owner --confirm-disposable
  pg_ctl -D "$test_root/data" -m fast -w stop
  trap - EXIT
  printf 'Stopped; retained disposable cluster and logs at %s\\n' "$test_root"
The setup leaves its unique temporary directory for inspection after shutdown.
"""
import argparse
import json
import os
from pathlib import Path
import queue
import re
import stat
import subprocess
import threading
import time
import uuid


class Session:
    def __init__(self, args, label):
        self.label = label
        env = {k: v for k, v in os.environ.items() if not k.startswith('PG')}
        env['PGAPPNAME'] = 'locking_join_' + label
        env['PGCONNECT_TIMEOUT'] = '5'
        env['PGPASSFILE'] = '/dev/null'
        env['PGSERVICEFILE'] = '/dev/null'
        self.proc = subprocess.Popen(
            [args.psql, '-X', '-w', '-qAt', '-h', args.host, '-p', str(args.port),
             '-U', args.user, '-d', args.database,
             '-v', 'ON_ERROR_STOP=0', '-v', 'VERBOSITY=verbose',
             '-P', 'null=<NULL>'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, env=env)
        self.lines = queue.Queue()
        def reader():
            for line in self.proc.stdout:
                self.lines.put(line.rstrip('\n'))
            self.lines.put(None)
        threading.Thread(target=reader, daemon=True).start()
        self.query("SET statement_timeout = '20s';\nSET lock_timeout = '15s';")
        self.pid = int(self.query('SELECT pg_backend_pid();')[0])

    def send(self, sql):
        marker = 'done_' + uuid.uuid4().hex
        self.proc.stdin.write(sql + '\n\\echo ' + marker + '\n')
        self.proc.stdin.flush()
        return marker

    def receive(self, marker, allow_error=False):
        end = time.monotonic() + 30
        result = []
        while True:
            line = self.lines.get(timeout=max(0.01, end - time.monotonic()))
            if line == marker:
                break
            if line is None:
                raise RuntimeError(f'{self.label}: psql exited: {result}')
            result.append(line)
        if not allow_error and any('ERROR:' in x or 'FATAL:' in x for x in result):
            raise RuntimeError(f'{self.label}: {result}')
        return result

    def query(self, sql):
        return self.receive(self.send(sql))

    def close(self):
        if self.proc.poll() is None:
            try:
                self.proc.stdin.write('ROLLBACK;\n\\q\n')
                self.proc.stdin.flush()
                self.proc.wait(timeout=5)
            except (BrokenPipeError, subprocess.TimeoutExpired):
                self.proc.terminate()
                self.proc.wait(timeout=5)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--psql', default='psql')
    p.add_argument('--host', required=True)
    p.add_argument('--port', type=int, required=True)
    p.add_argument('--database', required=True, help='Explicit disposable test database name')
    p.add_argument('--user', required=True, help='Explicit test database role')
    p.add_argument('--confirm-disposable', action='store_true',
                   help='Confirm this database is disposable and authorized for test writes')
    p.add_argument('--repeats', type=int, default=5)
    args = p.parse_args()
    if ',' in args.host:
        p.error('--host must identify one Unix-socket directory, not a libpq host list')
    if not Path(args.host).is_absolute() or not Path(args.host).is_dir():
        p.error('--host must be an existing absolute Unix-socket directory')
    host_stat = Path(args.host).stat()
    if host_stat.st_uid != os.getuid() or stat.S_IMODE(host_stat.st_mode) & 0o077:
        p.error('--host must be owned by this user and inaccessible to group/others')
    if not args.confirm_disposable:
        p.error('--confirm-disposable is required; never target production')
    if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]{0,62}', args.database):
        p.error('--database must be a plain database name, not a connection string or URI')
    if not re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]{0,62}', args.user):
        p.error('--user must be a plain role name')
    if not 1 <= args.port <= 65535:
        p.error('--port must be between 1 and 65535')
    if args.repeats < 1:
        p.error('--repeats must be positive')
    schema = 'locking_join_' + uuid.uuid4().hex
    sessions = []
    setup_complete = False
    try:
        observer = Session(args, 'observer'); sessions.append(observer)
        a = Session(args, 'a'); sessions.append(a)
        b = Session(args, 'b'); sessions.append(b)
        print(json.dumps({'server': observer.query('SELECT version();')[0],
                          'server_version_num': observer.query('SHOW server_version_num;')[0]}))
        observer.query(f'CREATE SCHEMA {schema};')
        setup_complete = True
        for s in sessions:
            s.query(f'SET search_path = {schema};')
        observer.query('CREATE TABLE queue (id integer PRIMARY KEY);\n'
                       'CREATE TABLE work_item (id integer PRIMARY KEY, '
                       'queue_id integer NOT NULL REFERENCES queue(id));')
        joined = ('SELECT w.id,w.queue_id,q.id FROM work_item w '
                  'JOIN queue q ON q.id=w.queue_id WHERE w.id=42 '
                  'FOR NO KEY UPDATE OF w;')
        cte = ('WITH locked AS (SELECT * FROM work_item WHERE id=42 '
               'FOR NO KEY UPDATE) SELECT w.id,w.queue_id,q.id '
               'FROM locked w JOIN queue q ON q.id=w.queue_id;')
        cases = [
            ('inner_existing', joined, False, False, []),
            ('left_existing', joined.replace('JOIN queue', 'LEFT JOIN queue'), False, False, ['42|2|<NULL>']),
            ('both_existing', joined.replace('OF w;', 'OF w,q;'), False, False, []),
            ('split_existing', 'SELECT queue_id FROM work_item WHERE id=42 FOR NO KEY UPDATE;', False, False, ['2']),
            ('cte_existing', cte, False, False, ['42|2|2']),
            ('cte_new_parent', cte, True, False, []),
            ('split_new_parent', 'SELECT queue_id FROM work_item WHERE id=42 FOR NO KEY UPDATE;', True, False, ['3']),
            ('split_deleted', 'SELECT queue_id FROM work_item WHERE id=42 FOR NO KEY UPDATE;', False, False, []),
            ('repeatable_read', joined, False, 'REPEATABLE READ', None),
            ('serializable', joined, False, 'SERIALIZABLE', None),
        ]
        for repeat in range(1, args.repeats + 1):
            for name, sql, new_parent, strict, expected in cases:
                observer.query('TRUNCATE work_item,queue;\nINSERT INTO queue VALUES (1),(2);\n'
                               'INSERT INTO work_item VALUES (42,1);')
                if repeat == 1:
                    print(json.dumps({'plan': name, 'lines': observer.query('EXPLAIN ' + sql)}))
                a.query('BEGIN ISOLATION LEVEL READ COMMITTED;')
                if new_parent:
                    a.query('INSERT INTO queue VALUES (3);')
                if name == 'split_deleted':
                    a.query('DELETE FROM work_item WHERE id=42;')
                else:
                    a.query(f'UPDATE work_item SET queue_id={3 if new_parent else 2} WHERE id=42;')
                b.query('BEGIN ISOLATION LEVEL ' + (strict or 'READ COMMITTED') + ';')
                token = b.send(sql)
                deadline = time.monotonic() + 10
                while observer.query(f'SELECT {a.pid}=ANY(pg_blocking_pids({b.pid}));') != ['t']:
                    if time.monotonic() > deadline:
                        raise RuntimeError(f'{name}: waiter never observed blocked by A')
                    time.sleep(0.02)  # Polling only; database wait state is the barrier.
                a.query('COMMIT;')
                actual = b.receive(token, allow_error=strict)
                if strict:
                    if not any(re.match(r'ERROR:\s+40001:', line) for line in actual):
                        raise RuntimeError(f'{name}: expected ERROR SQLSTATE 40001, got {actual}')
                else:
                    if actual != expected:
                        raise RuntimeError(f'{name}: expected {expected}, got {actual}')
                    if name.startswith('split_') and actual:
                        key = int(actual[0])
                        related = b.query(f'SELECT id FROM queue WHERE id={key};')
                        if related != [str(key)]:
                            raise RuntimeError(f'{name}: expected related row {key}, got {related}')
                b.query('ROLLBACK;')
                print(json.dumps({'repeat': repeat, 'case': name, 'blocked_by_a': True,
                                  'result': actual, 'assertion': 'pass'}), flush=True)
        print(json.dumps({'summary': 'pass', 'cases': len(cases), 'repeats': args.repeats}))
    finally:
        for s in reversed(sessions[1:]):
            s.close()
        if sessions:
            try:
                if setup_complete:
                    # RESTRICT is the default: fail instead of dropping external dependencies.
                    sessions[0].query(f'DROP TABLE IF EXISTS {schema}.work_item;\n'
                                      f'DROP TABLE IF EXISTS {schema}.queue;\n'
                                      f'DROP SCHEMA {schema};')
            finally:
                sessions[0].close()


if __name__ == '__main__':
    main()
