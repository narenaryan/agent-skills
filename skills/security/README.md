# security skills

Security workflows for container image patching and controlled DNSSEC trust-anchor diagnostics.

## Skills

- **[container-image-patching](container-image-patching/SKILL.md)** - scan Dockerfiles or images with Trivy, upgrade only fixed vulnerable packages, enforce a 20% image-size gate, and publish `-cve-patched` images.

- **[dnssec-sentinel-diagnostics](dnssec-sentinel-diagnostics/SKILL.md)** - distinguish trusted-key sentinel patterns from unsupported queries, failed controls, and mixed resolver paths.

## Install

```bash
./install.sh security                 # install all
./install.sh container-image-patching # install one
```
