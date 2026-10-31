"""Synthetic standard-library tests; all fixtures are temporary."""
import contextlib
import hashlib
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import plan_backup as p


class PlannerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(os.path.realpath(self.temp.name))
        self.root = self.base / 'source'
        self.root.mkdir()
        # Host may itself have /.git. Isolate only external ancestor metadata;
        # all fixture ancestors and selected-tree filesystem calls stay real.
        original_stat = os.stat
        external_ids = set()
        ancestor = self.base.parent
        while True:
            st = original_stat(ancestor)
            external_ids.add((st.st_dev, st.st_ino))
            if ancestor == ancestor.parent:
                break
            ancestor = ancestor.parent
        def isolated_stat(name, *args, **kwargs):
            if name == '.git' and kwargs.get('dir_fd') is not None:
                st = os.fstat(kwargs['dir_fd'])
                if (st.st_dev, st.st_ino) in external_ids:
                    raise FileNotFoundError()
            return original_stat(name, *args, **kwargs)
        stat_patch = patch.object(os, 'stat', side_effect=isolated_stat)
        mocked = stat_patch.start()
        self.addCleanup(stat_patch.stop)
        support_patch = patch.object(os, 'supports_dir_fd', os.supports_dir_fd | {mocked})
        support_patch.start()
        self.addCleanup(support_patch.stop)

    def file(self, name, data=b'contents'):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def run_plan(self, *extra, root=None):
        return p.Planner(p.arguments(['--root', 'r=' + str(root or self.root), *extra])).run()

    def reasons(self, result):
        return {b['reason'] for b in result['blockers']}

    def test_defaults_preserve_binary_dotfiles_archives_and_build(self):
        included = ['a.bin', '.env', '.gitignore', 'x.zip', 'dist/a', 'build/b', 'vendor/c', 'd oc', 'é', 'line\nfile']
        for name in included + ['install.DMG', 'NODE_MODULES/secret']:
            self.file(name)
        result = self.run_plan()
        self.assertTrue(result['complete'])
        entries = {x['path']: x for x in result['entries']}
        for name in included:
            self.assertEqual(entries[name]['sha256'], hashlib.sha256(b'contents').hexdigest())
        self.assertEqual(entries['install.DMG']['action'], 'exclude')
        self.assertEqual(entries['NODE_MODULES']['omitted_descendant_count'], 'not_enumerated')
        self.assertNotIn('NODE_MODULES/secret', entries)
        self.assertEqual(result['summary']['included_files'], len(included))
        self.assertEqual(result['summary']['included_bytes'], len(included) * 8)
        self.assertEqual(result['summary']['excluded_files'], 1)
        self.assertEqual(result['summary']['excluded_file_bytes'], 8)
        self.assertEqual(result['summary']['excluded_subtrees'], 1)
        self.assertEqual(result, self.run_plan())

    def test_explicit_exclusion_is_exact(self):
        self.file('dist/a')
        self.file('other/dist/b')
        result = self.run_plan('--exclude-dir', 'r/dist')
        self.assertTrue(result['complete'])
        entries = {x['path']: x for x in result['entries']}
        self.assertEqual(entries['dist']['reason'], 'explicit_user_policy')
        self.assertEqual(entries['other/dist/b']['action'], 'include')
        self.assertIn('explicit_exclusion_not_matched_to_directory', self.reasons(self.run_plan('--exclude-dir', 'r/missing')))

    def test_git_directory_pointer_and_nested_root(self):
        self.file('.git/secret')
        self.file('nested/work')
        result = self.run_plan()
        self.assertFalse(result['complete'])
        self.assertNotIn('.git/secret', [x['path'] for x in result['entries']])
        self.assertEqual(set(result['repositories'][0]['checks'].values()), {'unverified'})
        nested = self.run_plan(root=self.root / 'nested')
        self.assertEqual(nested['repositories'][0]['location'], 'ancestor')
        (self.root / '.git/secret').unlink()
        (self.root / '.git').rmdir()
        self.file('.git', b'gitdir: /secret/location')
        self.assertFalse(self.run_plan()['complete'])

    def test_case_variant_git_metadata_is_not_hashed(self):
        self.file('.GIT/objects/private')
        result = self.run_plan()
        self.assertFalse(result['complete'])
        self.assertEqual(result['summary']['included_bytes'], 0)
        self.assertNotIn('.GIT/objects/private', [x['path'] for x in result['entries']])
        self.assertTrue(result['repositories'])

    def test_symlinks_never_followed(self):
        self.file('real/a')
        (self.root / 'filelink').symlink_to(self.root / 'real/a')
        (self.root / 'dirlink').symlink_to(self.root / 'real', target_is_directory=True)
        result = self.run_plan()
        self.assertEqual(sum(x['reason'] == 'symlink_omitted' for x in result['blockers']), 2)
        alias = self.base / 'alias'
        alias.symlink_to(self.root, target_is_directory=True)
        self.assertFalse(self.run_plan(root=alias)['complete'])
        self.assertFalse(self.run_plan(root=alias / 'real')['complete'])

    def test_case_and_unicode_collisions(self):
        for name in ['A', 'a', 'é', 'e\u0301']:
            self.file(name)
        self.assertIn('casefold_or_unicode_normalization_collision', self.reasons(self.run_plan()))

    def test_invalid_and_missing_arguments(self):
        cases = [[], ['--root', 'bad/name=/tmp'], ['--root', 'r=relative'],
                 ['--root', 'r=' + str(self.root), '--root', 'R=/other'],
                 ['--root', 'r=' + str(self.root), '--root', 'x=' + str(self.root / 'child')],
                 ['--root', 'r=/tmp/../tmp'], ['--root', 'r=/tmp', '--exclude-dir', 'r/../a']]
        for argv in cases:
            with self.subTest(argv=argv), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as c:
                p.arguments(argv)
            self.assertEqual(c.exception.code, 2)

    def test_limits(self):
        self.file('a', b'12345')
        self.file('dir/b')
        self.assertIn('hash_byte_limit', self.reasons(self.run_plan('--max-bytes', '4')))
        self.assertIn('depth_limit', self.reasons(self.run_plan('--max-depth', '0')))
        self.assertIn('entry_limit', self.reasons(self.run_plan('--max-entries', '1')))
        result = self.run_plan('--max-bytes', '5')
        self.assertLessEqual(result['hashed_bytes'], 5)

    def test_unreadable_error_redacted(self):
        self.file('a')
        with patch.object(p.Planner, 'hash_file', side_effect=PermissionError('secret-token')):
            result = self.run_plan()
        self.assertIn('filesystem_access_error', self.reasons(result))
        self.assertNotIn('secret-token', str(result))

    def test_content_race(self):
        path = self.file('a')
        original = os.read
        changed = False
        def race(fd, size):
            nonlocal changed
            data = original(fd, size)
            if not changed:
                changed = True
                path.write_bytes(b'changed size')
            return data
        with patch.object(os, 'read', side_effect=race):
            result = self.run_plan()
        self.assertIn('file_changed_during_read', self.reasons(result))

    def test_entry_replacement_race(self):
        path = self.file('a')
        original = os.read
        changed = False
        def race(fd, size):
            nonlocal changed
            data = original(fd, size)
            if not changed:
                changed = True
                path.unlink()
                path.write_bytes(b'contents')
            return data
        with patch.object(os, 'read', side_effect=race):
            result = self.run_plan()
        self.assertIn('file_changed_during_read', self.reasons(result))

    def test_directory_race(self):
        self.file('a')
        original = p.Planner.hash_file
        def race(planner, *args):
            value = original(planner, *args)
            self.file('newfile')
            return value
        with patch.object(p.Planner, 'hash_file', race):
            result = self.run_plan()
        self.assertIn('directory_changed_during_walk', self.reasons(result))

    def test_no_source_mutation_or_write_opens(self):
        path = self.file('a')
        before = path.stat()
        real_open = os.open
        def guarded_open(name, flags, *args, **kwargs):
            self.assertFalse(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
            return real_open(name, flags, *args, **kwargs)
        # Capability probe must still recognize the mocked function.
        with patch.object(os, 'open', side_effect=guarded_open) as mocked:
            with patch.object(os, 'supports_dir_fd', os.supports_dir_fd | {mocked}):
                self.assertTrue(self.run_plan()['complete'])
        after = path.stat()
        self.assertEqual(p.identity(before), p.identity(after))
        self.assertEqual(path.read_bytes(), b'contents')
        self.assertEqual(list(self.root.iterdir()), [path])

    def test_special_file(self):
        if not hasattr(os, 'mkfifo'):
            self.skipTest('Requires POSIX FIFO')
        os.mkfifo(self.root / 'pipe')
        self.assertIn('special_file_unsupported', self.reasons(self.run_plan()))

    def test_unsupported_platform_fails_closed(self):
        self.file('a')
        with patch.object(p.sys, 'platform', 'win32'):
            result = self.run_plan()
        self.assertEqual(result['entries'], [])
        self.assertIn('platform_missing_required_nofollow_descriptor_support', self.reasons(result))

    def test_cross_device_directory_blocked(self):
        self.file('dir/a')
        original = os.stat
        def different_device(name, *args, **kwargs):
            value = original(name, *args, **kwargs)
            if name == 'dir':
                class Stat:
                    pass
                fake = Stat()
                for attr in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns', 'st_mode'):
                    setattr(fake, attr, getattr(value, attr))
                fake.st_dev += 1
                return fake
            return value
        with patch.object(os, 'stat', side_effect=different_device) as mocked:
            with patch.object(os, 'supports_dir_fd', os.supports_dir_fd | {mocked}):
                result = self.run_plan()
        self.assertIn('cross_device_directory', self.reasons(result))
        self.assertNotIn('dir/a', [e['path'] for e in result['entries']])

    def test_main_exit_and_json(self):
        import json
        self.file('a')
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(p.main(['--root', 'r=' + str(self.root)]), 0)
        self.assertTrue(json.loads(output.getvalue())['complete'])
        (self.root / 'link').symlink_to('a')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(p.main(['--root', 'r=' + str(self.root)]), 2)


if __name__ == '__main__':
    unittest.main()
