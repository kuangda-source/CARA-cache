"""Assemble a separate runtime; never modify either pinned source checkout.

The completion is a technical candidate, not validated official reproduction.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

root = Path(__file__).resolve().parents[1]
lock = json.loads((root / "manifests/runtime_completion.json").read_text())
wc = root / "vendor/WorldCache"
base = root / "vendor/CosmosPredict25"
for path, expected in ((wc, lock["worldcache_commit"]), (base, lock["completion_commit"])):
    actual = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True, timeout=20).strip()
    if actual != expected:
        raise SystemExit(f"Unexpected source revision: {path}")
dest = root / "cache/runtime"
if dest.exists():
    raise SystemExit("Destination exists; preserve and inspect it before reassembly")
shutil.copytree(wc / "Models/Cosmos-Predict2.5", dest, symlinks=True,
                ignore=shutil.ignore_patterns("__pycache__", ".git"))
for relative in lock["directories"]:
    if (dest / relative).exists():
        raise SystemExit(f"Refusing overwrite: {relative}")
    shutil.copytree(base / relative, dest / relative, symlinks=True,
                    ignore=shutil.ignore_patterns("__pycache__"))
for relative, expected in lock["files"].items():
    if hashlib.sha256((dest / relative).read_bytes()).hexdigest() != expected:
        raise SystemExit(f"Completion hash mismatch: {relative}")
print(dest)
