"""Offline Linux import preflight, CPU-only by default. Run from the isolated Cosmos runtime directory.

Supply its package paths via PYTHONPATH. Never disables guardrails or imports
local modified model code as a replacement. Prints a small JSON receipt.
"""
import argparse
import importlib
import json
import os
import platform
import sys
import time
import traceback
from pathlib import Path

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
parser = argparse.ArgumentParser()
parser.add_argument("--receipt", type=Path)
parser.add_argument("--cuda-device", default="", help="GPU UUID after live admission; empty is CPU-only")
args = parser.parse_args()
os.environ["CUDA_VISIBLE_DEVICES"] = args.cuda_device
started = time.time()
receipt = {"stage": "F0_RUNTIME_IMPORT" if args.cuda_device else "F0_CPU_IMPORT", "platform": platform.platform(),
           "python": sys.version, "started_unix": started,
           "cuda_visible_device": args.cuda_device, "video_generation_started": False, "modules": {}}
try:
    for name in ("torch", "cosmos_oss", "cosmos_predict2.config", "cosmos_predict2.inference"):
        module = importlib.import_module(name)
        receipt["modules"][name] = {"path": getattr(module, "__file__", None),
                                     "version": getattr(module, "__version__", None)}
    receipt["status"] = "PASS"
except Exception as exc:
    receipt["status"] = "TECH_BLOCKED"
    receipt["error_type"] = type(exc).__name__
    receipt["error"] = str(exc)
    traceback.print_exc(file=sys.stderr)
finally:
    receipt["elapsed_seconds"] = time.time() - started
    rendered = json.dumps(receipt, indent=2) + "\n"
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.receipt.with_suffix(".tmp")
        temporary.write_text(rendered)
        temporary.replace(args.receipt)
    print(rendered)
sys.exit(0 if receipt["status"] == "PASS" else 1)
