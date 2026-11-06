"""Ephemeral SSH-stdin CPU reader. Writes nothing on server; returns small JSON.

No generator import, model forward, new teacher, training, GPU or deployment.
The launcher supplies an exact asset packet bound to existing accepted captures.
"""
import gc
import hashlib
import json
import math
import os
import pathlib
import time


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main(spec):
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    import torch
    torch.set_num_threads(2)
    assert not torch.cuda.is_initialized()
    def forbidden(*a, **kw):
        raise RuntimeError("E0 prohibits CUDA/download/model execution")
    torch.cuda._lazy_init = forbidden
    torch.hub.download_url_to_file = forbidden
    started = time.perf_counter()
    root = pathlib.Path(spec["root"]).resolve()
    ledger = root / "reports/budget.json"
    before = sha(ledger)
    balance = json.loads(ledger.read_text())
    result = {"status": "RUNNING", "observed_unix": time.time(), "root": str(root),
              "budget_before_sha256": before, "ledger_before": balance,
              "remote_writes": 0, "GPU_submissions": 0, "model_forwards": 0,
              "new_teacher_calls": 0, "groups": [], "errors": []}
    def tree_digest(value):
        h = hashlib.sha256()
        def walk(x):
            if isinstance(x, torch.Tensor):
                if not bool(torch.isfinite(x).all()):
                    raise ValueError("Nonfinite raw tensor")
                h.update(str((str(x.dtype), list(x.shape))).encode())
                h.update(memoryview(x.detach().contiguous().reshape(-1).view(torch.uint8).cpu().numpy()))
            elif isinstance(x, dict):
                for key in sorted(x):
                    h.update(str(key).encode()); walk(x[key])
            elif isinstance(x, (tuple, list)):
                h.update(type(x).__name__.encode())
                for item in x:
                    walk(item)
            elif x is None or isinstance(x, (str, int, float, bool)):
                h.update(repr(x).encode())
            else:
                raise TypeError("Unsupported tensor-tree value")
        walk(value)
        return h.hexdigest()
    try:
        for group in spec["groups"]:
            stage = pathlib.Path(group["stage"]).resolve()
            if not stage.is_relative_to(root):
                raise ValueError("Stage outside project")
            reg = json.loads((stage / "registration.json").read_text())
            if reg["source_revision"] != group["source_revision"]:
                raise ValueError("Archived source identity changed")
            for rel, digest in reg["payload_sha256"].items():
                path = (stage / rel).resolve()
                if not path.is_relative_to(stage) or sha(path) != digest:
                    raise ValueError("Archived payload identity changed: " + rel)
            output = pathlib.Path(group["output"]).resolve()
            if not output.is_relative_to(root):
                raise ValueError("Output outside project")
            if sha(output / "runner.json") != group["runner_sha256"] or sha(stage / "CPU-final-results.json") != group["final_sha256"]:
                raise ValueError("Original runner/final receipt changed")
            rows = []
            for item in group["points"]:
                bound = item["raw_artifact"]
                path = pathlib.Path(bound["path"]).resolve()
                if not path.is_relative_to(output) or path.stat().st_size != bound["bytes"] or sha(path) != bound["sha256"]:
                    raise ValueError("Raw file byte identity changed: " + str(path))
                payload = torch.load(path, weights_only=True, map_location="cpu")
                if tree_digest(payload) != bound["tensor_sha256"]:
                    raise ValueError("Raw tensor identity changed")
                teacher = payload["DENSE_SAME_STATE"]
                if not isinstance(teacher, tuple) or len(teacher) != 2:
                    raise ValueError("c/u teacher tuple required")
                flat = [t for v in payload.values() for t in (v if isinstance(v, tuple) else (v,))]
                if len(flat) != 12 or any(not isinstance(t, torch.Tensor) or t.device.type != "cpu" for t in flat):
                    raise ValueError("Exact 12 CPU tensors required")
                pairs = {name: {"shape_c": list(pair[0].shape), "shape_u": list(pair[1].shape),
                                "dtype_c": str(pair[0].dtype), "dtype_u": str(pair[1].dtype)}
                         for name, pair in payload.items() if isinstance(pair, tuple)}
                row = {"selection": item["selection"], "sigma": item["sigma"], "sigma_index": item["sigma_index"],
                       "raw_artifact": bound, "schema": list(payload), "pairs": pairs,
                       "tensor_count": len(flat), "identity_verified": True,
                       "trajectory": "PI0_NOT_H1", "not_restorable_runtime_snapshot": True}
                if group["kind"] == "SOURCE_PHASE16":
                    if set(payload) != {"DENSE_SAME_STATE", "C", "D_REFERENCE_A", "FUSION_A", "NEW_P", "actual_latent", "timestep"}:
                        raise ValueError("Source-phase candidate schema differs")
                    row["moments"] = {}
                    for name in ("C", "D_REFERENCE_A", "FUSION_A", "NEW_P"):
                        pair = payload[name]
                        if any(t.dtype != torch.float32 or t.shape != teacher[b].shape for b, t in enumerate(pair)):
                            raise ValueError("Branch shape/dtype differs")
                        ec = pair[0].double() - teacher[0].double()
                        eu = pair[1].double() - teacher[1].double()
                        mc = ec.square().mean().item(); mu = eu.square().mean().item(); cross = (ec * eu).mean().item()
                        q = (8 * ec - 7 * eu).square().mean().item()
                        old = item["losses"][name]
                        for got, expected in zip((mc, mu, cross), old["CFG_gram_absolute"]):
                            if not math.isclose(got, expected, rel_tol=2e-8, abs_tol=1e-10):
                                raise ValueError("Raw branch Gram differs from accepted receipt")
                        if not math.isclose(q, old["absolute_guided_MSE"], rel_tol=2e-8, abs_tol=1e-10):
                            raise ValueError("Raw guided MSE differs")
                        row["moments"][name] = {"mc": mc, "mu": mu, "cross": cross, "q_guided_direct": q}
                        del ec, eu
                    if item["selection"]["source"] == "D" and not all(torch.equal(x, y) for x, y in zip(payload["D_REFERENCE_A"], payload["FUSION_A"])):
                        raise ValueError("Accepted D-source A identity differs")
                rows.append(row)
                del payload, flat, teacher
                gc.collect()
            result["groups"].append({"kind": group["kind"], "source_revision": group["source_revision"],
                                     "payload_files_verified": len(reg["payload_sha256"]), "points": rows})
        if sha(ledger) != before:
            raise ValueError("Read-only audit ledger changed")
        assert not torch.cuda.is_initialized()
        result.update(status="E0_ALL28_RAW_FILES_CPU_READ_IDENTITY_VERIFIED", budget_after_sha256=sha(ledger),
                      CUDA_initialized=False, CPU_wall_seconds=time.perf_counter() - started)
    except BaseException as exc:
        result.update(status="E0_READONLY_AUDIT_FAILED_PARTIAL_RETAINED", error_type=type(exc).__name__, error=str(exc),
                      budget_after_sha256=sha(ledger), CPU_wall_seconds=time.perf_counter() - started)
        result["errors"].append({"error_type": type(exc).__name__, "message": str(exc)})
    print(json.dumps(result, allow_nan=False))
    return 0 if result["status"] == "E0_ALL28_RAW_FILES_CPU_READ_IDENTITY_VERIFIED" else 1
