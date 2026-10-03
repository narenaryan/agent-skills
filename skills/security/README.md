# security skills

Security workflows for container image vulnerability scanning, patching, and verification.

## Skills

- **[container-image-patching](container-image-patching/SKILL.md)** - scan Dockerfiles or images with Trivy, upgrade only fixed vulnerable packages, enforce a 20% image-size gate, and publish `-cve-patched` images.

## Install

```bash
./install.sh security                 # install all
./install.sh container-image-patching # install one
```
