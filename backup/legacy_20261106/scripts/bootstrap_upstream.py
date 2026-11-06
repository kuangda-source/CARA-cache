"""Fetch the recorded upstream commit without changing existing checkouts."""
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
lock = json.loads((root / "manifests/upstream.json").read_text())
dest = root / lock["path"]
if not dest.exists():
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "clone", lock["url"], str(dest)], check=True)
    subprocess.run(["git", "-C", str(dest), "checkout", "--detach", lock["commit"]], check=True)
head = subprocess.check_output(["git", "-C", str(dest), "rev-parse", "HEAD"], text=True).strip()
if head != lock["commit"]:
    raise SystemExit("Existing upstream differs; preserve and inspect it, do not overwrite")
if subprocess.check_output(["git", "-C", str(dest), "status", "--porcelain"], text=True).strip():
    raise SystemExit("Upstream contains local changes; preserve them")
print(head)
