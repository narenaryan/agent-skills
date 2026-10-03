---
name: container-image-patching
description: Use when asked to patch Docker or OCI container image vulnerabilities from a Dockerfile or existing image - scans with Trivy, upgrades only fixed vulnerable OS packages, enforces image-size limits, and retags patched images with cve-patched
---

# Container Image Patching

Patch container CVEs surgically. Upgrade only packages that Trivy reports as HIGH/CRITICAL with available fixes; avoid broad distro upgrades or unnecessary base-image changes.

## When to Use

Use for Dockerfile or image inputs when reducing Trivy-reported HIGH/CRITICAL vulnerabilities while preserving runtime behavior and image size. The examples assume Debian/Ubuntu `apt-get`; adapt only the package-manager command for non-apt images.

## Workflow

1. Identify the input:
   - Dockerfile: build a local source image first, for example `docker build -t app:scan-source -f Dockerfile .`.
   - Existing image: pull or inspect it directly, for example `docker pull python:3.12`.
2. Ensure Trivy is installed: macOS `brew install trivy`; Linux use the official Trivy package instructions; Windows `winget install aquasecurity.trivy` or `choco install trivy`.
3. Capture baseline image size: `docker image inspect IMAGE --format '{{.Size}}'`.
4. Scan only actionable severities: `trivy image IMAGE --severity HIGH,CRITICAL`.
5. Record each vulnerable package with a fixed version. Separate findings without fixes.
6. Patch only the specific packages that have fixes. Add a late Dockerfile layer, or create a temporary patch Dockerfile for image-only input:

```Dockerfile
FROM python:3.12
RUN apt-get update && \
    apt-get install --only-upgrade -y libssl3t64 && \
    rm -rf /var/lib/apt/lists/*
```

7. Build the patched image with `-cve-patched` appended to the original tag, for example `python:3.12-cve-patched` or `app:scan-source-cve-patched`.
8. Compare size. The patched image must be no more than 20% larger than the baseline:
   `patched_size <= baseline_size * 1.20`.
9. Re-run Trivy on the patched image: `trivy image python:3.12-cve-patched --severity HIGH,CRITICAL`.
10. Verify every originally fixable HIGH/CRITICAL finding is gone. If new vulnerabilities appear, repeat only targeted upgrades.

## Patch Rules

- Use `apt-get install --only-upgrade -y <pkg>` for each package; do not use `upgrade`, `dist-upgrade`, or unconstrained installs.
- Keep package names exact from Trivy/OS metadata, such as `libssl3t64`.
- Combine related package upgrades into one cleanup layer.
- Remove `/var/lib/apt/lists/*` in the same `RUN` instruction.
- Preserve the application Dockerfile and entrypoint unless a vulnerability fix requires changing them.
- For non-apt images, upgrade named installed packages only.

## Report Template

Return:

- source image or Dockerfile build tag
- patched image tag ending in `-cve-patched`
- packages upgraded and fixed CVEs
- baseline size, patched size, and percentage increase
- before/after Trivy summary for HIGH and CRITICAL
- any remaining HIGH/CRITICAL findings and why they remain

## Pitfalls

- Rebuilding from a newer base image without proving the required package fixes.
- Running broad upgrades that silently alter many packages and inflate the image.
- Treating unfixed CVEs as patch failures; separate them from fixable findings.
- Forgetting the size gate after successful vulnerability cleanup.
