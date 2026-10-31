# Read-only planner contract

Requires Python 3.11+ on macOS or Linux with descriptor-relative OS interfaces. No dependencies, shell commands, Git hooks, Mole calls or network calls. It reads file bytes for SHA-256 but never prints their contents. Reads may update access times or hydrate cloud placeholders; this is not a zero-side-effect filesystem snapshot.

Run from this skill directory after permission to inspect the selected roots:

```sh
python3 scripts/plan_backup.py --root "Documents=$HOME/Documents" --root "Downloads=$HOME/Downloads"
```

Roots are explicit absolute paths with unique ASCII labels. No implicit HOME, current-directory or full-disk scan. Overlapping roots, case-insensitive duplicate labels and parent traversal are rejected. Every root component must be a real directory, not a symlink. On macOS paths such as `/tmp` can themselves be symlinks: choose and approve the actual directory path instead of weakening this rule.

An exact additional directory exclusion, after reviewing reproducibility:

```sh
python3 scripts/plan_backup.py --root "Documents=$HOME/Documents" --exclude-dir Documents/project-a/dist
```

This is not a glob. An exclusion that fails to match an actual directory is a blocker, preventing a typo from looking applied. Default exclusions are regular `.dmg` files and directories named `node_modules`, case-insensitive. Excluded directories are not enumerated: their descendant counts and bytes are unknown, not zero. Review patched dependencies before accepting that policy. Generic `build`, `dist`, `vendor`, archives and binary formats remain candidates unless explicitly excluded.

## Output and exit status

JSON goes to stdout with stable ordering and escaped control characters. Do not redirect it into a selected source tree: the output would become a changing input. Store it in an approved private location outside the roots, or inspect stdout. Never post a real manifest in a public PR.

- Exit 0: no detected blockers in the selective inventory. This does **not** authorize upload or certify whole-disk completeness.
- Exit 2: argument errors or a manifest with blockers. Argument errors go to stderr; scan blockers appear in JSON. Do not suppress them to automate transfer.
- `entries`: root label, relative path, kind, decision, reason; included files also have byte size and SHA-256.
- `summary`: included/excluded file counts and byte totals, directories, excluded subtrees, blocked/omitted entries. Recursive excluded counts remain unknown.
- `repositories`: review requirements, not Git status results. `.git` metadata is omitted without opening it; ancestor markers are checked by metadata only. All remote, unpushed, status, LFS and submodule checks remain unverified. Working files, including ignored/untracked candidates, remain included by default. The omission blocks whole-backup completeness; this utility has no automatic Git exemption switch.
- `complete`: limited to detected selective-plan blockers. It says nothing about transfer, independent restore, excluded subtrees or a consistent instant across files.

Default limits: 100,000 discovered entries, depth 128, 100 GiB total bytes hashed. Override explicitly with `--max-entries`, `--max-depth`, `--max-bytes` after assessing time/storage costs. Exceeding limits is incomplete coverage, not an empty directory. There is no wall-time guarantee for a slow filesystem; stop the process if necessary and treat output as incomplete.

## Safety and limits

The walker opens directories and regular files relative to held descriptors with no-follow flags. It rejects symlinks, special files and cross-device traversal, checks file identity/size/times around reads and rechecks directory/root identity. Names are checked under NFC plus case folding; this is conservative, not an exhaustive model of every destination filesystem. Empty directories are recorded.

The planner does not lock writers or implement staging. A file can change after its hash is computed; an approved staging copier must revalidate identity and bytes. Hostile same-user manipulation, bind mounts and coherent database/application snapshots require stronger separately authorized mechanisms. Root filesystem ancestors are metadata-inspected for `.git`; their contents are not recursively read. Do not scan roots containing credentials merely because they are convenient. File-level approval and privacy review remain separate from inclusion.
