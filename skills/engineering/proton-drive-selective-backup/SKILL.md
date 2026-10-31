---
name: proton-drive-selective-backup
description: Use when backing up selected macOS Documents or Downloads to Proton Drive while excluding installers and dependencies, reviewing Git-based exclusions, or checking whether a filtered upload is actually recoverable.
---

# Proton Drive selective backup

A cleanup candidate is not a backup exclusion. A Git remote is not proof that local work is recoverable. Separate inventory, selection, transfer and restore evidence; never delete originals to make a backup smaller.

## Selection contract

| Input | Default decision |
|---|---|
| Regular `.dmg` files; `node_modules` directories | Exclude with an explicit reason; review locally patched dependencies |
| PDFs, photos, Office files, archives, dotfiles | Keep as candidates, not automatically authorized uploads |
| `build`, `dist`, `vendor`, caches | Exclude only exact reviewed paths; names alone do not establish reproducibility |
| Git projects | Keep working files; require separate repository-recovery review |
| Symlinks, special files, unreadable/changing entries | Report blockers, never silently follow or call complete |

The planner requires explicit roots, emits JSON, hashes files, and never invokes Git, Mole or Proton. Its `.git` omission blocks completeness. Check local-only/unpushed branches, dirty/untracked work, ignored assets, LFS objects and submodules before approving project exclusions. `.gitignore` is not a backup policy.

## Recipe

1. Obtain permission for the exact local roots. After checking installed-version help, optional `mo analyze --json "$HOME/Documents"` provides sizing insights; partial sizes are lower bounds. Never run Mole cleanup, purge, installer or optimize in this workflow.
2. From this skill directory, run:

   ```bash
   python3 scripts/plan_backup.py --root "Documents=$HOME/Documents" --root "Downloads=$HOME/Downloads"
   ```

   Resolve exclusions, Git warnings, collisions, limits and errors. Keep the manifest private: filenames and hashes reveal information. See [planner contract](PLANNER.md).
3. Show selected data categories, destination account/folder, estimated bytes and omissions. Obtain upload approval, explicitly covering sensitive documents or secrets; encryption does not substitute for consent. Installation, persistent authentication and recurring runs require their own authorization. Browser login is `proton-drive auth login`; putting the binary on PATH is separate from its saved session.
4. Prepare an approved, private staging copy outside every source root; use regular files, not symlinks or hard links to changing originals. Rehash staging against the approved manifest and stop on drift. See [transfer and restore gates](WORKFLOW.md). The planner does not implement staging or transfer.
5. Confirm installed CLI options, upload only staging, reconcile every planned item, then restore into a fresh directory and compare paths, sizes and SHA-256. Report sampled versus complete verification accurately. Never propagate local deletion or run remote replacement by default.

## Pitfalls

- Proton `skip` can omit changed files; current-source `replace` trashes remote content. JSON mode does not make a command a dry run.
- Case-only or Unicode-equivalent names may collide on restoration. Resolve without overwriting originals.
- A clean scan is not an atomic snapshot; later changes invalidate approval and hashes. File bytes alone do not preserve macOS ACLs, resource forks or extended attributes.
- Upload success, cached remote digests and configured Git remotes are not restore evidence. [Sources and version limits](SOURCES.md).
