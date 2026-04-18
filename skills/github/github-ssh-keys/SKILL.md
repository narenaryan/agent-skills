---
name: github-ssh-keys
description: 'Use when setting up, troubleshooting, or hardening SSH keys for GitHub — FIDO2/U2F hardware keys (ed25519-sk/ecdsa-sk), macOS Keychain integration (UseKeychain, --apple-use-keychain), Windows MSYS2-vs-native-OpenSSH agent confusion, "Bad configuration option: usekeychain" errors, or choosing between ed25519 and rsa-4096'
---

# GitHub SSH Keys

Prefer Ed25519. GitHub dropped DSA on 2022-03-15; RSA keys created after 2021-11-02 must sign with SHA-2 (`rsa-sha2-256` / `rsa-sha2-512`). Fall back to RSA-4096 only when the target genuinely cannot handle Ed25519.

## Algorithm choice

| Key type | When |
|----------|------|
| `ed25519` | default; all modern systems |
| `rsa -b 4096` | legacy servers without Ed25519 |
| `ed25519-sk` | FIDO2/U2F hardware key |
| `ecdsa-sk` | hardware key whose firmware lacks Ed25519 |

The `_sk` file on disk is a **handle**, not the key. Physical device lost = key lost.

## Generate

```bash
ssh-keygen -t ed25519 -C "you@example.com"
ssh-keygen -t ed25519-sk -C "you@example.com"        # hardware
ssh-keygen -t ed25519-sk -O resident                 # store handle on device
ssh-keygen -t ed25519-sk -O verify-required          # require PIN/biometric per use
ssh-keygen -t ed25519-sk -O no-touch-required        # skip touch (not recommended)
```

Import resident keys onto a new host: `ssh-add -K` (lowercase K on OpenSSH 8.2+; not the macOS `-K`).

## macOS Keychain

`~/.ssh/config`:
```
Host github.com
  AddKeysToAgent yes
  UseKeychain yes
  IdentityFile ~/.ssh/id_ed25519
```

```bash
ssh-add --apple-use-keychain ~/.ssh/id_ed25519    # Monterey+
ssh-add -K ~/.ssh/id_ed25519                      # pre-Monterey
```

Omit `UseKeychain` when the key has no passphrase. If a Homebrew/MacPorts `ssh-add` is first on `PATH`, `--apple-use-keychain` breaks — call `/usr/bin/ssh-add` explicitly, and add `IgnoreUnknown UseKeychain` to `~/.ssh/config` so non-Apple clients don't error on the directive.

## Windows

```powershell
Get-Service ssh-agent | Set-Service -StartupType Manual   # elevated, once
Start-Service ssh-agent                                    # elevated
ssh-add C:\Users\you\.ssh\id_ed25519                       # unelevated
```

Git for Windows bundles its own MSYS2 OpenSSH with a **separate agent**. If `ssh-add` saved the key but `git push` still prompts, pin git to the system client:

```bash
git config --global core.sshCommand "C:/Windows/System32/OpenSSH/ssh.exe"
```

## Pitfalls

- **Passphrase-less private keys** are plaintext credentials — always set one, let agent/Keychain cache it.
- **Agent forwarding (`ForwardAgent yes`)** exposes every loaded key to the remote host; root there can use them. Prefer `ProxyJump` or a per-host key.
- **Loaded keys leak by probing:** without `IdentitiesOnly yes` the agent tries every key against every server, disclosing public-key fingerprints.
- **Resident `-sk` keys are device-bound:** reprovision the hardware token and the public key is irrecoverable — back it up first.
- **Windows dual OpenSSH:** a key added to one agent is invisible to the other. `ssh -vT git@github.com` prints which binary runs.
- **Homebrew `openssh` on macOS PATH:** `ssh-add --apple-use-keychain` errors with "unknown option" — use `/usr/bin/ssh-add`.
- **DSA / SHA-1:** rejected by GitHub. A pre-2021 `ssh-rsa` client negotiating SHA-1 signatures will fail authentication.
