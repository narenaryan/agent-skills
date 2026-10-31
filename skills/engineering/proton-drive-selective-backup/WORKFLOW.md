# Transfer and restore gates

This is an operator recipe, not an executable uploader. `plan_backup.py` only inventories and hashes explicitly selected roots. It never stages files, authenticates, uploads, modifies Git, installs software, or deletes data.

## One-time setup

Use the [official release page](https://proton.me/download/drive/cli/index.html), select the actual CPU architecture and verify its published SHA-512 before executing. On 2026-10-31 the page lists version 0.9.0 dated 2026-10-05 for macOS arm64/x64. Installation must be authorized separately. A trusted executable can be placed in `/usr/local/bin` if that directory is on PATH and writable under the user's approved setup; do not overwrite another executable or escalate privileges silently. No `curl | sh`.

Once installed, inspect:

```sh
proton-drive version
proton-drive filesystem upload --help
proton-drive filesystem download --help
```

With explicit authentication/session-storage permission, the user completes browser sign-in:

```sh
proton-drive auth login
```

The official README describes macOS Keychain storage. PATH availability does not guarantee a valid session. Do not copy credentials into the manifest, command line, repository or logs; never choose the testing-only plaintext credential store. Logging can disclose paths, so keep logs private and redact before sharing.

## Freeze a reviewed plan

- Pause writers or use an explicitly approved snapshot mechanism. The planner does not create snapshots or promise consistency across files.
- Resolve every blocker. Decide whether omitted repository history is recoverable elsewhere or needs a separate authorized backup. Verify remote commits and LFS/submodule availability separately; do not run arbitrary repository hooks or trust a configured URL. Keep working files by default.
- Review sensitive files, including `.env`, keys, health/financial documents and archives. They remain visible candidates to prevent silent loss; they are not preapproved for upload. Arrange a separate approved secure backup or explicit exclusion where needed.
- Choose a staging destination outside all scanned roots and cloud-sync folders, on suitable local storage. Estimate free space; an ordinary plaintext staging copy remains sensitive. Restrict access using an approved location without silently changing security settings.
- Copy the manifest's regular-file bytes using no-follow descriptor checks, not `cp -R` of live roots and not hard links. Check source identity/size/timestamps and hashes during copying; reject changed or replaced entries. If no trusted bounded copier is available, stop rather than claim the planner produced staging.
- Preserve labels and relative paths. Re-enumerate staging; reject extra/missing entries or symlinks, compare each size/SHA-256. Stage a manifest with relative paths, excluding unnecessary local absolute paths. Any selection/content change needs a new plan/review.
- This byte-oriented workflow does not preserve all macOS metadata, app bundles, sparse layout or filesystem semantics. Use a separately designed archive/full-system backup when that matters. Archives require their own safe extraction and metadata tests, not blanket exclusion or acceptance.

## Upload without destructive mirroring

The official CLI accepts local sources followed by a remote **parent** path. Do not use shell wildcards such as `Documents/*`: they miss dotfiles and bypass the approved manifest. Pass the verified staging directory as one quoted argument. Verify the remote parent/account exists before transfer.

Main-source inspection shows separate file/folder conflict options, no native include/exclude/dry-run. This is not proof that every release has identical flags. After confirming the installed help and testing disposable data under approval, prefer file revisions with folder merge where supported, or a fresh uniquely named snapshot folder. Never assume `skip` means unchanged: it may skip a changed conflict. `replace` trashes the remote object first. Do not use it as a backup default. JSON output disables interactive conflict resolution; it is not a simulation.

Record plan digest, tool version, destination, per-item transfer result and any remote revision identifiers actually returned. Reconcile an uncertain transfer by inspection, not blind replay or deletion. Do not repeatedly reupload unchanged data. Rate limits, quota exhaustion and partial uploads leave the snapshot incomplete. No automatic scheduling, retention pruning or remote cleanup is authorized by creating this skill.

## Restore evidence

Download to a fresh approved directory, never over originals. Before downloading, compare planned names under Unicode normalization/case folding and the target filesystem's additional restrictions. Current issue reports describe symlink upload omissions and case-insensitive restore collisions; treat them as warnings, not reproduced facts or proof that other paths are safe.

Compare restored relative-path set, byte sizes and SHA-256 with the staged manifest, including dotfiles, empty files and nested directories. A sample proves only that sample. Mark complete byte verification only when every selected file matches and all errors/exclusions are accounted for. Do not infer secure erasure, metadata preservation or long-term recoverability from this test. Keep the original data and a separate backup until the recovery plan is proven. Any cleanup is a separate decision.
