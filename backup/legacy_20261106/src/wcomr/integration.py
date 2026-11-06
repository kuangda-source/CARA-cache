"""Version-checked, in-memory injection into the unmodified official WC forward.

No patch is installed for Native/official F1 runs. W1 uses the same scheduling
and warp implementation; only the pre-warp residual approximation is replaced.
GPU execution and real-model shadow parity are still separate acceptance gates.
"""
import ast
import hashlib
import inspect
import json
from pathlib import Path
from .calibration import ResidualCalibrator


def _begin(net):
    if net.cnt == 0 or not hasattr(net, "_w1_calibrators"):
        net._w1_generation = getattr(net, "_w1_generation", 0) + 1
        net._w1_calibrators = [ResidualCalibrator(), ResidualCalibrator()]


def _context(net, branch):
    return (net._w1_generation, id(net), branch,
            getattr(net, "_w1_request_key", None), getattr(net, "_w1_expert_key", None))


def _predict(net, branch, probe, official):
    prediction, reason = net._w1_calibrators[branch].predict(
        context=_context(net, branch), step=net.cnt, probe=probe,
        official=official, mode=net._w1_mode)
    net._w1_last_reason = reason
    return prediction


def _observe(net, branch, probe, residual):
    net._w1_calibrators[branch].observe_full(
        context=_context(net, branch), step=net.cnt,
        probe=probe, residual=residual)


def inject_source(source):
    """Narrow substitutions fail closed if upstream shape changes."""
    edits = [
        ("    current_idx = self.cnt % 2", "    _w1_begin(self)\n    current_idx = self.cnt % 2"),
        ("        self.previous_internal_states[current_idx] = test_x\n",
         "        x_B_T_H_W_D = ori_x + _w1_predict(self, current_idx, test_x - ori_x, x_B_T_H_W_D - ori_x)\n"
         "        self.previous_internal_states[current_idx] = test_x\n"),
        ("    # --- Final Layer & Unpatchify ---",
         "    if not skip_forward:\n"
         "        _w1_observe(self, current_idx, self.probe_residual_cache[current_idx], residual_x)\n\n"
         "    # --- Final Layer & Unpatchify ---"),
    ]
    for old, new in edits:
        if source.count(old) != 1:
            raise RuntimeError("Unsupported upstream forward; injection anchor mismatch")
        source = source.replace(old, new)
    ast.parse(source)
    return source


def build_forward(original, mode):
    if mode == "official":
        return original
    if mode not in ("scalar", "shrink"):
        raise ValueError(mode)
    namespace = dict(original.__globals__)
    namespace.update(_w1_begin=_begin, _w1_predict=_predict, _w1_observe=_observe)
    source = inject_source(inspect.getsource(original))
    exec(compile(source, "<w1-pinned-forward>", "exec"), namespace)
    result = namespace[original.__name__]

    def forward(net, *args, **kwargs):
        net._w1_mode = mode
        return result(net, *args, **kwargs)
    return forward


def install(mode, root):
    if mode == "official":
        return
    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc
    lock = json.loads((Path(root) / "manifests/upstream.json").read_text())
    module = Path(inspect.getfile(wc))
    if hashlib.sha256(module.read_bytes()).hexdigest() != lock["cache_module_sha256"]:
        raise RuntimeError("Cache module hash differs from pinned source")
    wc.worldcache_mini_train_dit_forward = build_forward(wc.worldcache_mini_train_dit_forward, mode)
