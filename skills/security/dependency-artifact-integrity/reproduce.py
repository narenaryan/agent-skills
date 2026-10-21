"""Offline pip-download contract test. Creates inert wheels; installs/runs no package.
Requires an already available pip. No fetched code, index, or network is used.
"""
import base64
import csv
import hashlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile


def wheel(directory, name, payload, dependency=None):
    metadata = f"Metadata-Version: 2.1\nName: {name}\nVersion: 1.0\n"
    if dependency:
        metadata += f"Requires-Dist: {dependency}==1.0\n"
    prefix = f"{name}-1.0.dist-info"
    files = {
        f"{name}/data.txt": payload.encode(),
        f"{prefix}/METADATA": (metadata + "\n").encode(),
        f"{prefix}/WHEEL": b"Wheel-Version: 1.0\nGenerator: local-fixture\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
    }
    record = io.StringIO(newline="")
    writer = csv.writer(record)
    for path, data in files.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
        writer.writerow([path, "sha256=" + digest, len(data)])
    writer.writerow([f"{prefix}/RECORD", "", ""])
    files[f"{prefix}/RECORD"] = record.getvalue().encode()
    target = directory / f"{name}-1.0-py3-none-any.whl"
    with zipfile.ZipFile(target, "w") as archive:
        for path, data in files.items():
            archive.writestr(zipfile.ZipInfo(path, (2020, 1, 1, 0, 0, 0)), data)
    return hashlib.sha256(target.read_bytes()).hexdigest()


def main():
    with tempfile.TemporaryDirectory(prefix="integrity-fixture-") as temp:
        root = Path(temp)
        packages = root / "packages"
        packages.mkdir()
        clean = wheel(packages, "fixture_leaf", "approved inert data")
        top = wheel(packages, "fixture_top", "parent inert data", "fixture_leaf")
        env = {k: v for k, v in os.environ.items() if not k.startswith("PIP_")}
        env["PIP_CONFIG_FILE"] = os.devnull
        env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
        env["PYTHONNOUSERSITE"] = "1"
        print(subprocess.check_output([sys.executable, "-m", "pip", "--version"], env=env, text=True).strip())

        def case(label, requirements, enforced, success, diagnostic=""):
            requirement_file = root / f"{label}.txt"
            requirement_file.write_text(requirements, encoding="utf-8")
            before = requirement_file.read_bytes()
            output = root / label
            command = [sys.executable, "-m", "pip", "download", "--no-index", "--no-cache-dir",
                       "--only-binary=:all:", "--find-links", str(packages), "--dest", str(output),
                       "-r", str(requirement_file)]
            if enforced:
                command.append("--require-hashes")
            result = subprocess.run(command, cwd=root, env=env, text=True, capture_output=True, timeout=30)
            if (result.returncode == 0) != success or diagnostic not in result.stdout + result.stderr:
                raise RuntimeError(f"{label}: unexpected result\n{result.stdout}\n{result.stderr}")
            if requirement_file.read_bytes() != before:
                raise RuntimeError(f"{label}: requirements changed")
            if success:
                saved = output / "fixture_leaf-1.0-py3-none-any.whl"
                if not saved.exists() or saved.read_bytes() != (packages / saved.name).read_bytes():
                    raise RuntimeError(f"{label}: expected exact artifact not saved")
            elif list(output.glob("*.whl")):
                raise RuntimeError(f"{label}: artifact unexpectedly saved")
            print(f"PASS {label}: {'accepted' if success else 'rejected'}; requirements unchanged")

        case("clean-enforced", f"fixture_leaf==1.0 --hash=sha256:{clean}\n", True, True)
        case("transitive-complete", f"fixture_top==1.0 --hash=sha256:{top}\nfixture_leaf==1.0 --hash=sha256:{clean}\n", True, True)
        case("transitive-unhashed", f"fixture_top==1.0 --hash=sha256:{top}\nfixture_leaf==1.0\n", True, False, "Hashes are required")
        case("missing-hash", "fixture_leaf==1.0\n", True, False, "Hashes are required")
        changed = wheel(packages, "fixture_leaf", "different inert data")
        if changed == clean:
            raise RuntimeError("mutation did not change bytes")
        case("tampered-unhashed-baseline", "fixture_leaf==1.0\n", False, True)
        case("tampered-enforced", f"fixture_leaf==1.0 --hash=sha256:{clean}\n", True, False, "DO NOT MATCH THE HASHES")
    print("All six offline cases passed. No package was installed or executed.")


if __name__ == "__main__":
    main()
