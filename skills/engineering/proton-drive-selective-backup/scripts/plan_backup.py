#!/usr/bin/env python3
"""Private, read-only dry-run inventory. Python 3.11+, macOS/Linux only."""
import argparse
import hashlib
import json
import os
import re
import stat
import sys
import unicodedata


class Blocked(Exception):
    pass


def identity(s):
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)


def key(name):
    return unicodedata.normalize('NFC', name).casefold()


def arguments(argv):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', action='append', required=True, metavar='LABEL=/absolute/path')
    p.add_argument('--exclude-dir', action='append', default=[], metavar='LABEL/relative/path')
    p.add_argument('--max-entries', type=int, default=100000)
    p.add_argument('--max-depth', type=int, default=128)
    p.add_argument('--max-bytes', type=int, default=100 * 1024**3,
                   help='Maximum total bytes read for hashing (default 100 GiB)')
    a = p.parse_args(argv)
    roots = []
    labels = set()
    for spec in a.root:
        label, sep, path = spec.partition('=')
        if not sep or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', label):
            p.error('Each root requires a safe ASCII label and an absolute path')
        if label.casefold() in labels:
            p.error('Root labels must be distinct, ignoring case')
        if not os.path.isabs(path) or '\x00' in path or '..' in path.split('/'):
            p.error('Root paths must be absolute, without parent traversal')
        labels.add(label.casefold())
        roots.append((label, os.path.normpath(path)))
    for i, (_, path) in enumerate(roots):
        for _, other in roots[:i]:
            if os.path.commonpath((path, other)) in (path, other):
                p.error('Selected root paths overlap')
    exclusions = set()
    for spec in a.exclude_dir:
        label, sep, rel = spec.partition('/')
        if (not sep or label not in dict(roots) or not rel or
                any(x in ('', '.', '..') for x in rel.split('/')) or '\x00' in rel):
            p.error('Directory exclusions must be exact LABEL/root-relative/path values')
        exclusions.add((label, rel))
    if a.max_entries < 1 or not 0 <= a.max_depth <= 256 or a.max_bytes < 0:
        p.error('Limits must be nonnegative; max-entries positive; max-depth at most 256')
    a.roots = sorted(roots)
    a.exclusions = exclusions
    return a


class Planner:
    def __init__(self, args):
        self.a = args
        self.entries = []
        self.blockers = []
        self.repositories = []
        self.count = 0
        self.bytes = 0
        self.used_exclusions = set()
        self.root_ids = set()

    def block(self, label, path, reason):
        self.blockers.append({'root': label, 'path': path, 'reason': reason})

    def repo(self, label, path, location):
        item = {'root': label, 'path': path, 'location': location,
                'status': 'review_required', 'checks': {
                    k: 'unverified' for k in ('working_tree_status', 'unpushed_commits',
                                             'remotes', 'lfs', 'submodules')},
                'metadata': 'omitted; whole-backup completeness blocked'}
        if item not in self.repositories:
            self.repositories.append(item)
            self.block(label, path, 'git_metadata_omitted_repository_review_required')

    def open_root(self, label, path):
        """Resolve every component by descriptor, never following a symlink."""
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        fd = os.open('/', flags)
        try:
            parts = [x for x in path.split('/') if x]
            for component in parts:
                try:
                    os.stat('.git', dir_fd=fd, follow_symlinks=False)
                except FileNotFoundError:
                    pass
                else:
                    self.repo(label, '', 'ancestor')
                new = os.open(component, flags, dir_fd=fd)
                os.close(fd)
                fd = new
            return fd
        except BaseException:
            os.close(fd)
            raise

    def hash_file(self, parent, name, initial):
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        try:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode) or identity(before) != identity(initial):
                raise Blocked('file_changed_before_read')
            if self.bytes + before.st_size > self.a.max_bytes:
                raise Blocked('hash_byte_limit')
            h = hashlib.sha256()
            read = 0
            while True:
                # Read one extra byte only when budget permits; size changes fail closed.
                remaining = self.a.max_bytes - self.bytes
                if remaining == 0:
                    if read != before.st_size:
                        raise Blocked('hash_byte_limit')
                    break
                data = os.read(fd, min(1024 * 1024, remaining))
                if not data:
                    break
                read += len(data)
                self.bytes += len(data)
                h.update(data)
                if read > before.st_size:
                    raise Blocked('file_changed_during_read')
            after = os.fstat(fd)
            entry = os.stat(name, dir_fd=parent, follow_symlinks=False)
            if read != before.st_size or identity(before) != identity(after) or identity(after) != identity(entry):
                raise Blocked('file_changed_during_read')
            return h.hexdigest()
        finally:
            os.close(fd)

    def walk(self, label, fd, rel, depth, device):
        before = os.fstat(fd)
        names = []
        # Bounded enumeration rather than unbounded listdir materialization.
        with os.scandir(fd) as it:
            for entry in it:
                self.count += 1
                if self.count > self.a.max_entries:
                    raise Blocked('entry_limit')
                names.append(entry.name)
        seen = set()
        for name in sorted(names):
            path = rel + '/' + name if rel else name
            if key(name) in seen:
                self.block(label, path, 'casefold_or_unicode_normalization_collision')
            seen.add(key(name))
            row = {'root': label, 'path': path}
            self.entries.append(row)
            try:
                s = os.stat(name, dir_fd=fd, follow_symlinks=False)
                if name.casefold() == '.git':
                    row.update(kind='git_metadata', action='omit', reason='repository_metadata_requires_separate_review')
                    self.repo(label, path, 'selected_tree')
                elif stat.S_ISLNK(s.st_mode):
                    row.update(kind='symlink', action='omit', reason='symlinks_not_followed')
                    self.block(label, path, 'symlink_omitted')
                elif stat.S_ISDIR(s.st_mode):
                    row['kind'] = 'directory'
                    explicit = (label, path) in self.a.exclusions
                    if explicit or name.casefold() == 'node_modules':
                        if explicit:
                            self.used_exclusions.add((label, path))
                        row.update(action='exclude_subtree', reason='explicit_user_policy' if explicit else 'default_node_modules',
                                   omitted_descendant_count='not_enumerated')
                    elif s.st_dev != device:
                        raise Blocked('cross_device_directory')
                    elif depth >= self.a.max_depth:
                        raise Blocked('depth_limit')
                    else:
                        child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                        try:
                            if identity(os.fstat(child)) != identity(s):
                                raise Blocked('directory_changed_before_walk')
                            row['action'] = 'include'
                            self.walk(label, child, path, depth + 1, device)
                            if identity(os.fstat(child)) != identity(os.stat(name, dir_fd=fd, follow_symlinks=False)):
                                raise Blocked('directory_entry_changed')
                        finally:
                            os.close(child)
                elif stat.S_ISREG(s.st_mode):
                    row.update(kind='file', size=s.st_size)
                    if name.casefold().endswith('.dmg'):
                        row.update(action='exclude', reason='default_dmg')
                    else:
                        row.update(action='include', sha256=self.hash_file(fd, name, s))
                else:
                    raise Blocked('special_file_unsupported')
            except (OSError, Blocked) as e:
                reason = str(e) if isinstance(e, Blocked) else 'filesystem_access_error'
                row.update(action='blocked', reason=reason)
                self.block(label, path, reason)
                if reason == 'entry_limit':
                    raise
        if identity(before) != identity(os.fstat(fd)):
            raise Blocked('directory_changed_during_walk')

    def run(self):
        supported = (sys.platform.startswith('linux') or sys.platform == 'darwin') and all(
            hasattr(os, x) for x in ('O_NOFOLLOW', 'O_DIRECTORY', 'O_NONBLOCK'))
        supported = supported and os.open in os.supports_dir_fd and os.stat in os.supports_dir_fd and os.scandir in os.supports_fd
        if not supported:
            self.block('', '', 'platform_missing_required_nofollow_descriptor_support')
        else:
            for label, path in self.a.roots:
                fd = None
                try:
                    fd = self.open_root(label, path)
                    s = os.fstat(fd)
                    ident = (s.st_dev, s.st_ino)
                    if ident in self.root_ids:
                        raise Blocked('duplicate_root_identity')
                    self.root_ids.add(ident)
                    self.walk(label, fd, '', 0, s.st_dev)
                    # Re-resolve every absolute component to catch detached/replaced roots.
                    check = self.open_root(label, path)
                    try:
                        if identity(os.fstat(fd)) != identity(os.fstat(check)):
                            raise Blocked('root_changed')
                    finally:
                        os.close(check)
                except (OSError, Blocked) as e:
                    self.block(label, '', str(e) if isinstance(e, Blocked) else 'root_or_walk_access_error')
                finally:
                    if fd is not None:
                        os.close(fd)
        for label, path in sorted(self.a.exclusions - self.used_exclusions):
            self.block(label, path, 'explicit_exclusion_not_matched_to_directory')
        summary = {
            'included_files': sum(e.get('kind') == 'file' and e.get('action') == 'include' for e in self.entries),
            'included_directories': sum(e.get('kind') == 'directory' and e.get('action') == 'include' for e in self.entries),
            'included_bytes': sum(e.get('size', 0) for e in self.entries if e.get('action') == 'include'),
            'excluded_files': sum(e.get('action') == 'exclude' for e in self.entries),
            'excluded_file_bytes': sum(e.get('size', 0) for e in self.entries if e.get('action') == 'exclude'),
            'excluded_subtrees': sum(e.get('action') == 'exclude_subtree' for e in self.entries),
            'blocked_entries': sum(e.get('action') == 'blocked' for e in self.entries),
            'omitted_entries': sum(e.get('action') == 'omit' for e in self.entries),
            'excluded_subtree_descendants': 'unknown; not enumerated',
        }
        return {'schema_version': 1, 'summary': summary, 'mode': 'read_only_dry_run', 'complete': not self.blockers,
                'roots': [{'label': l, 'path': p} for l, p in self.a.roots],
                'entries': sorted(self.entries, key=lambda x: (x['root'], x['path'])),
                'blockers': sorted(self.blockers, key=lambda x: (x['root'], x['path'], x['reason'])),
                'repositories': sorted(self.repositories, key=lambda x: (x['root'], x['path'], x['location'])),
                'hashed_bytes': self.bytes,
                'limits': {'entries': self.a.max_entries, 'depth': self.a.max_depth, 'hashed_bytes': self.a.max_bytes},
                'notices': ['Private manifest: contains user-selected paths and file hashes.',
                            'Not a snapshot, staging operation, upload, or destination readback verification.',
                            'Not authorization to upload, install, log in, delete, or modify anything.',
                            'Completeness applies only to this selective plan, not excluded subtrees.',
                            'Excluded subtrees are not enumerated or recursively counted.',
                            'No wall-time guarantee: filesystem operations can block, including network-backed regular reads.',
                            'Hostile same-user races and bind mounts are not fully preventable; no snapshot guarantee.',
                            'File contents are hashed, not printed. Source reads may update filesystem access times.']}


def main(argv=None):
    result = Planner(arguments(argv)).run()
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2))
    return 0 if result['complete'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
