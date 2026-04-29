---
name: rust-runtime-bug-classes
description: Use when writing or reviewing Rust code that touches the filesystem, processes untrusted input, reimplements a Unix CLI, crosses a trust boundary like chroot, or handles bytes that may not be UTF-8 — covers TOCTOU on paths, permission races, OsStr vs String, panic-on-input, silently-discarded errors, NSS/dlopen after chroot, and bug-for-bug compatibility with GNU tools
---

# Bugs Rust's Type System Won't Catch

Rust prevents memory unsafety and data races, **not** logic bugs that live in syscalls, encoding, error propagation, or trust boundaries. These are the recurring classes.

## Filesystem race & identity bugs

| Bug | Wrong | Right |
|---|---|---|
| TOCTOU between `remove_file` + `create` | `fs::remove_file(p)?; File::create(p)?` | `OpenOptions::new().create_new(true).open(p)` — atomic, refuses dangling symlinks |
| Default perms then chmod | `create_dir(p)?; set_permissions(p, 0o700)?` | `DirBuilderExt::mode(0o700)` / `OpenOptions::mode()` at creation; set `umask` explicitly |
| Path equality via string | `file == Path::new("/")` | `fs::canonicalize(file)?`; for identity, compare `(dev, inode)` from `MetadataExt` |
| Path operations on tainted input | resolving paths repeatedly | Anchor on a file descriptor (e.g. `openat`, `cap-std` crate) instead of re-resolving paths |

## OsStr / bytes vs String

Filesystem paths and process args are **not** guaranteed UTF-8 on Unix.

- `String::from_utf8_lossy` corrupts binary streams by replacing bytes with `U+FFFD`.
- `print!("{}", ...)` panics on broken pipe and forces UTF-8.
- Stay in bytes: `OsStr`, `OsString`, `Path`, `PathBuf`, `Vec<u8>`, `&[u8]`. Use `io::stdout().write_all(&bytes)` for raw output.

## Panic-on-input is a DoS

`unwrap()`, `expect()`, `slice[i]`, `a + b`, `a - b` all panic on attacker-controlled input. For services and CLIs taking untrusted data, enable in `Cargo.toml` or `clippy.toml`:

```toml
# clippy lints to deny/warn in untrusted-input crates
unwrap_used = "warn"
expect_used = "warn"
panic = "warn"
indexing_slicing = "warn"
arithmetic_side_effects = "warn"
```

Use `?`, `.get(i)`, `checked_add`, `try_from`.

## Silently discarded errors

```rust
file.set_len(size).ok();          // hides ENOSPC
let _ = writeln!(out, "...");     // hides broken pipe
fs::remove_file(p).unwrap_or_default();
```

Propagate. If ignoring is intentional, leave a comment naming the exact errno that's safe. In tools that iterate (e.g. `rm -r`), track the worst exit code and return it at the end rather than aborting on first failure or losing failures silently.

## Trust boundaries: chroot, setuid, sandboxing

NSS (`getpwnam`, `getgrnam`, DNS) and other glibc paths `dlopen` shared libs **at call time**. After `chroot`, those loads come from the new root.

```rust
let uid = users::get_user_by_name(name);  // resolve BEFORE
chroot(new_root)?;                         // ...then cross the boundary
```

Static linking the Rust binary does **not** prevent glibc from `dlopen`'ing NSS modules. Resolve users, groups, hostnames, and load any plugins before `chroot`/`setuid`/seccomp.

## Reimplementing GNU/BSD tools

When rewriting `coreutils`, `find`, `grep`, etc., scripts depend on **bug-for-bug** behavior: exit codes, stderr wording, signal-name parsing (`kill -1` vs `kill -SIGHUP`), locale-sensitive sort, glob edge cases. Run the upstream test suite in CI; treat behavioral divergence as a bug, not a feature.

## Pitfalls

- `create_new(true)` returns `AlreadyExists` on dangling symlinks — handle it; don't fall back to `create()` which re-introduces the race.
- `canonicalize` requires the path to exist; for not-yet-created files, canonicalize the parent and join the basename.
- `OsStr` has no `len_chars` or `contains(&str)` — converting to `&str` to search reintroduces the UTF-8 assumption you were avoiding.
- Clippy `arithmetic_side_effects` flags every `+` including loop counters; scope it to crates handling untrusted input, not workspace-wide.
- `chroot` alone is not a sandbox; combine with `setuid` to a non-root user and ideally seccomp/landlock.
