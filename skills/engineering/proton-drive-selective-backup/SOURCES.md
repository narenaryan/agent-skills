# Provenance and validation boundaries

Reviewed 2026-10-31. Original synthesis and planner; no upstream implementation copied. This is a selective file-byte backup workflow, not a full-system backup utility or a Mole/Proton integration test.

## Primary references

- [Official CLI downloads](https://proton.me/download/drive/cli/index.html): lists 0.9.0, release date 2026-10-05, architecture-specific builds and SHA-512. Review date is separate from release date.
- [Proton CLI support](https://proton.me/support/drive-cli): browser authentication, local source/remote parent argument ordering, upload/download and JSON. Public documentation, not proof of local installation or account authorization.
- [Proton CLI README](https://github.com/ProtonDriveApps/sdk/blob/main/cli/README.md), observed blob `f646acfb2e71c21538f6660749f22c1c313ea1cf`: OS secret store, version/help commands and PATH setup. Do not use its plaintext testing credential option.
- [Upload command](https://github.com/ProtonDriveApps/sdk/blob/main/cli/src/commands/fileSystem/commandFileSystemUpload.ts), blob `5db04ed8293452aa47dd5258668995ff98e09be4`, and [conflict resolver](https://github.com/ProtonDriveApps/sdk/blob/main/cli/src/commands/fileSystem/transferConflictResolver.ts), blob `ec696e0967ed07dfa5647500f81be06fc3a4bb87`: inspected main exposes file/folder conflict options, not include/exclude/dry-run; same-content comparison uses claimed SHA-1. File revision creation differs from remote trash-and-replace. JSON suppresses conflict prompts. These observations are version-sensitive and not asserted as exact 0.9.0 source parity; inspect the installed release's help before executing.
- [Mole macOS reference](https://github.com/tw93/Mole/blob/main/skills/mole/references/macos.md), blob `71cea51bfd864ef39f77835ef5fb291b114eccd5`, written against 1.62.0: scoped read-only analysis, completeness labels, JSON flag ordering and destructive cleanup distinctions. Mole insights are optional, not a backup manifest or permission to delete.
- [Python OS interfaces](https://docs.python.org/3/library/os.html): descriptor-relative operations, no-follow flags, stat and platform feature detection. The planner checks available interfaces and fails closed outside supported macOS/Linux environments.
- [Git ignore semantics](https://git-scm.com/docs/gitignore): ignores concern untracked paths; they do not establish remote recoverability. The conservative planner does not invoke Git or exclude working-tree content based on ignore rules.
- [Proton symlink issue #75](https://github.com/ProtonDriveApps/sdk/issues/75) and [case-collision issue #76](https://github.com/ProtonDriveApps/sdk/issues/76): user-reported failure examples, not independently reproduced defects. Defensive no-symlink staging and restore-name review do not rely on those reports being universal.

## Executable scope

Run the original fixtures from the skill directory:

```sh
python3 scripts/test_plan_backup.py
python3 -O scripts/test_plan_backup.py
```

Tests create only synthetic temporary trees. They exercise selection, bounded reads, descriptor/path checks, explicit exclusions, Git review boundaries, filenames, collisions and injected filesystem failures/races. They do not install or execute Mole, Proton, a Git repository or fetched third-party code. Actual Mac/APFS behavior, provider authentication, upload/download, keychain persistence, remote revisions, quota/rate limits, staging copying and restore verification are untested. No performance, secure-erasure or production-readiness claim.

The planner emits a review artifact, not an atomic snapshot or transfer capability. It uses filesystem metadata and descriptor checks to detect common replacement/change races; an adversarial same-user process or bind mount is outside its guarantees. Byte hashing may update access times and may hydrate cloud placeholders. No complete macOS metadata preservation is provided. Approval and a tested staging/restore implementation remain mandatory before actual data movement. Keep report paths/hashes private.
