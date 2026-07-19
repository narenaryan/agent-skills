---
name: npm-publish-ci-pitfalls
description: Use when setting up or debugging npm publishing from CI (GitHub Actions tag-release workflows) — covers EOTP token failures, npm ≥11.6 silently stripping ./-prefixed bin entries, provenance/OIDC rejections on private repos, ERR_UNSUPPORTED_NODE_MODULES_TYPE_STRIPPING from shipping raw .ts, and registry 404s right after a successful publish
---

# npm Publish from CI: Non-Obvious Pitfalls

Field-tested failure modes of `npm publish` in GitHub Actions (tag-triggered release workflows). Each was hit live; the diagnostic signature is the log line quoted.

## 1. `npm error code EOTP` — token cannot bypass 2FA

CI publish reaches the registry, then dies with `This operation requires a one-time password`. The `NPM_TOKEN` is valid but the account's 2FA-for-writes policy demands an interactive OTP.

**Fix (operator, npmjs.com):** granular access token with **"Bypass two-factor authentication"** explicitly enabled. Note npm is deprecating bypass-2FA tokens for publishing (`gh.io/npm-gat-bypass2fa-deprecation`) — prefer trusted publishing (§3) once the package exists.

## 2. npm ≥11.6 silently strips `bin` entries with `./` prefix

Log signature: `npm warn publish "bin[cmd]" script name src/cli.js was invalid and removed`. It's a **warning, not an error** — the publish proceeds and ships a package with **no CLI command at all**.

**Fix:** `"bin": { "cmd": "src/cli.js" }` — no `./` prefix. Verify before tagging:

```bash
npm pkg fix                # normalizes; diff should be empty on a clean manifest
npm pack && tar -xOf *.tgz package/package.json | node -p "JSON.parse(require('fs').readFileSync(0,'utf8')).bin"
```

`npm pack --dry-run` does NOT surface this warning; only the publish path (or `npm pkg fix`) does.

## 3. Provenance and OIDC on private repos

- `npm publish --provenance` from a **private** repo fails at the registry: `E422 … Unsupported GitHub Actions source repository visibility: "private"`. Provenance requires a public source repo, full stop.
- **Trusted publishing (OIDC) itself works from private repos** — but it turns provenance ON by default, so a private repo must set `provenance=false` (env `npm_config_provenance: false` on the publish step) or it hits the same E422.
- Trusted publisher config lives in package settings on npmjs.com → the package must already exist. Bootstrap the first publish with a token, then switch.
- OIDC needs npm ≥ 11.5.1, GitHub-hosted runners, job permission `id-token: write`, and setup-node's `registry-url`. Reusable `workflow_call` workflows are unreliable (validation checks the calling workflow's filename).

## 4. Raw `.ts` in a package breaks every install (Node type stripping)

A Node ≥22.6/24 project can run `.ts` files directly in its own checkout, so a package that ships raw TypeScript passes every repo-side check — then the installed CLI dies instantly with `ERR_UNSUPPORTED_NODE_MODULES_TYPE_STRIPPING`: **Node deliberately disables type stripping for files under `node_modules`.**

**Fix:** compile at pack time. TS ≥5.7's `rewriteRelativeImportExtensions: true` permits `allowImportingTsExtensions` imports *with* emit and rewrites `./x.ts` → `./x.js` in the output — dev keeps running raw `.ts`, the tarball gets `lib/*.js` (`outDir: lib`, `allowJs` to carry plain-JS entry files, `bin` → `lib/cli.js`, build in `prepack`).

**Prevention (the real lesson):** tarball-content inspection is not enough — `npm pack --dry-run` looked perfect here. CI must smoke-test the *packed artifact the way a user gets it*:

```bash
npm pack
TMP=$(mktemp -d)
npm install -g --prefix "$TMP" ./<name>-*.tgz
"$TMP/bin/<cmd>"   # bare invocation: exercises the full import chain, must exit 0
```

## 5. Registry 404 immediately after a successful publish

`+ pkg@version` in the CI log is authoritative — the publish landed. Yet `npm view`/`npm install` can 404 for minutes on a brand-new package: the top-level packument lags and CDNs negative-cache the 404.

**Diagnose instead of panicking:** the versioned manifest (`registry.npmjs.org/<pkg>/<version>`) and tarball URL go 200 before the packument does. If those are 200, wait (~1–5 min); repeated polling of the packument can keep re-priming the cached 404, so use a cache-buster query param.

## 6. Tag-release hygiene

- Guard step: fail if `${GITHUB_REF_NAME#v}` ≠ `node -p "require('./package.json').version"`.
- After a failed release run is fixed by new commits, do **not** re-run the failed workflow run — it rebuilds the old tag commit. Re-point the tag: `git tag -f vX.Y.Z origin/main && git push -f origin vX.Y.Z`.
- Nothing is consumed on the registry until a publish fully succeeds — a failed version number remains usable.
- Scoped packages: `publishConfig: { "access": "public" }` (default is restricted), and `repository` field must match the repo when provenance is on.
