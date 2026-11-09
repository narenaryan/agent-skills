"""Original static/path-model checks; no installation or external URL requests."""
from pathlib import Path
import posixpath
import re
import unittest

HERE = Path(__file__).resolve().parent
REPO_DIR = '/repo/skills/engineering/patch-reproducer-validity'
FLAT_DIR = '/copy/skills/patch-reproducer-validity'
NAMES = ('rbvm-applicability', 'rbvm-guarded-remediation', 'rbvm-verified-closure')
URLS = {
    'https://github.com/narenaryan/agent-skills/blob/main/skills/security/'
    + name + '/SKILL.md' for name in NAMES
}


def targets(markdown):
    """Extract this package's simple inline links, not arbitrary Markdown."""
    return re.findall(r'\[[^\]]*\]\(([^)]+)\)', markdown)


def resolve(directory, target):
    return posixpath.normpath(posixpath.join(directory, target))


def local_missing(markdown, directory, files):
    return [target for target in targets(markdown)
            if not target.startswith(('https://', 'http://', '#'))
            and resolve(directory, target) not in files]


class ContentPaths(unittest.TestCase):
    def setUp(self):
        self.docs = {name: (HERE / name).read_text(encoding='utf-8')
                     for name in ('SKILL.md', 'BACKPORT-COVERAGE.md', 'SOURCES.md')}
        self.names = {p.name for p in HERE.iterdir() if p.is_file()}

    def test_old_cross_category_paths_fail_flat_copy(self):
        old = '\n'.join(f'[gate](../../security/{name}/SKILL.md)' for name in NAMES)
        repo_files = {f'/repo/skills/security/{name}/SKILL.md' for name in NAMES}
        flat_files = {f'/copy/skills/{name}/SKILL.md' for name in NAMES}
        self.assertEqual(local_missing(old, REPO_DIR, repo_files), [])
        self.assertEqual(len(local_missing(old, FLAT_DIR, flat_files)), 3)
        # Even corrected sibling paths need absent dependencies in a single copy.
        sibling = '[gate](../rbvm-applicability/SKILL.md)'
        self.assertEqual(local_missing(sibling, FLAT_DIR, set()),
                         ['../rbvm-applicability/SKILL.md'])

    def test_current_local_links_resolve_in_both_layouts(self):
        for directory in (REPO_DIR, FLAT_DIR):
            files = {directory + '/' + name for name in self.names}
            for name, content in self.docs.items():
                with self.subTest(directory=directory, document=name):
                    self.assertEqual(local_missing(content, directory, files), [])

    def test_cross_skill_targets_are_exact_source_urls(self):
        found = {t for t in targets(self.docs['BACKPORT-COVERAGE.md'])
                 if '/skills/security/' in t}
        self.assertEqual(found, URLS)
        self.assertFalse(any(t.startswith('../') for text in self.docs.values()
                             for t in targets(text)))

    def test_missing_companion_is_detected(self):
        files = {FLAT_DIR + '/' + name for name in self.names
                 if name != 'BACKPORT-COVERAGE.md'}
        self.assertIn('BACKPORT-COVERAGE.md',
                      local_missing(self.docs['SKILL.md'], FLAT_DIR, files))

    def test_reintroduced_relative_links_are_detected_individually(self):
        files = {FLAT_DIR + '/' + name for name in self.names}
        for name in NAMES:
            url = ('https://github.com/narenaryan/agent-skills/blob/main/'
                   'skills/security/' + name + '/SKILL.md')
            old = '../../security/' + name + '/SKILL.md'
            mutated = self.docs['BACKPORT-COVERAGE.md'].replace(url, old)
            with self.subTest(skill=name):
                self.assertEqual(local_missing(mutated, FLAT_DIR, files), [old])

    def test_local_links_survive_relocation_and_spaces(self):
        directory = '/alternate checkout/nested path/copied skill'
        files = {directory + '/' + name for name in self.names}
        for name, content in self.docs.items():
            with self.subTest(document=name):
                self.assertEqual(local_missing(content, directory, files), [])

    def test_fixture_invocations_declare_working_directory(self):
        self.assertTrue({'reproduce.py', 'check_backport.py',
                         'check_content_paths.py'} <= self.names)
        self.assertIn('From the repository root, run:', self.docs['SKILL.md'])
        self.assertIn('python3 skills/engineering/patch-reproducer-validity/reproduce.py',
                      self.docs['SKILL.md'])
        self.assertIn('From the directory containing this document',
                      self.docs['BACKPORT-COVERAGE.md'])
        self.assertIn('python3 check_backport.py', self.docs['BACKPORT-COVERAGE.md'])
        self.assertIn('From this skill\'s directory', self.docs['SOURCES.md'])
        self.assertIn('python3 check_content_paths.py', self.docs['SOURCES.md'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
