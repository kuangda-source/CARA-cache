"""Reversible host-only substitutions around the unchanged BANK24 science.

This module does not launch GPUs or initialize a budget. The remaining container,
supervisor, terminal audit and authority handoff are explicit prerequisites.
"""
import ast
import copy
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys

LIFECYCLE_SOURCE = '2bd41dc8fa19f42353e03a7c78b7264b4b2695c6'
ENTRY_SOURCE = 'c1c95ce0c598fb7839b0b89f4a69bd45c8aef7c9'
RUNNER_SHA = '3a4aa59bc8559a82e43717bc7d04592a8a346e2812f209bd8f98243045a63b4c'
CONFIG = 'configs/wc_scout_bank24_production_entry_r1_20261018.json'
WORKSPACE = '/data20t/gaokuangda/worldcache_workspace'
TARGET_CAPABILITY = (8, 9)
ADAPTER_STATUS = 'BANK24_SM89_EXECUTION_ADAPTER_CPU_PASS_NOT_FULL_GPU_LIFECYCLE'
REMAINING = ['containerized_GPU_supervisor_and_PID_FD_lock_contract',
             'portable_post_and_terminal_collector_full24_acceptance',
             'new_host_whole_card_quote', 'actual_CUDA_compatibility',
             'single_authoritative_v2_history_and_writer_handoff']


def digest(value):
    return hashlib.sha256(value).hexdigest()


def read(path):
    raw=Path(path).read_bytes()
    return json.loads(gzip.decompress(raw) if raw[:2]==b'\x1f\x8b' else raw)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def exact_patch(source, replacements):
    value = source
    for before, after, count in replacements:
        require(before != after and value.count(before) == count,
                'Exact registered host substitution differs: ' + before[:70])
        value = value.replace(before, after)
    restored = value
    for before, after, count in reversed(replacements):
        require(restored.count(after) == count, 'Ambiguous host substitution reversal')
        restored = restored.replace(after, before)
    require(restored == source, 'Original science is not reversibly recoverable')
    ast.parse(value)
    return value


def adapt_runner(original):
    require(digest(original.encode()) == RUNNER_SHA, 'Original runner bytes changed')
    from wcomr.scout_production_entry_adapter_r1 import adapt
    scout = adapt(original)
    replacements = [
        ('from wcomr.scout_production_entry_r1 import',
         'from bank24_sm89_entry_contract import', 4),
        ("HF_HUB_CACHE=str(a.project/'hfhub')",
         "HF_HOME=str(a.project/'cache/huggingface'),HF_HUB_CACHE=str(a.project/'cache/huggingface/hub')", 1),
        ("[str(a.stage/'src'),str(a.project/'runtime')",
         "[str(a.stage),str(a.stage/'inputs/src'),str(a.project/'runtime')", 1),
        ("(a.project/'configs/f1_setup.json')", "(a.stage/'inputs/configs/f1_setup.json')", 1),
        ("'source_revision':a.source_revision,", "'source_revision':a.source_revision,'scientific_entry_source_revision':" + repr(ENTRY_SOURCE) + ',', 1),
        ('torch.cuda.get_device_capability()==(8,6)',
         'torch.cuda.get_device_capability()==(8,9)', 1)]
    value = exact_patch(scout, replacements)
    require('torch.cuda.get_device_capability()==(8,9)' in value,
            'An explicit SM89 guard must remain')
    return value, dict(original_runner_sha256=RUNNER_SHA,
        unchanged_scout_adapter_sha256=digest(scout.encode()),
        host_runner_sha256=digest(value.encode()),reversible_host_replacements=len(replacements),
        target_compute_capability=list(TARGET_CAPABILITY),
        original_scientific_entry_source=ENTRY_SOURCE,
        sampling_or_guardrails_or_readout_changed=False)


def adapt_budget_pool(original):
    """Change only the hardware predicate; preserve accounting and transactions."""
    replacements = [("'A6000' not in gpu['name']", "'RTX 6000 Ada' not in gpu['name']", 1),
                    ("gpu['compute_cap'] != '8.6'", "gpu['compute_cap'] != '8.9'", 1)]
    return exact_patch(original, replacements)


def device_gate(gpu):
    return (isinstance(gpu, dict) and str(gpu.get('uuid', '')).startswith('GPU-')
        and 'RTX 6000 Ada' in gpu.get('name', '') and str(gpu.get('compute_cap')) == '8.9'
        and type(gpu.get('memory_used_mib')) in (int, float)
        and math.isfinite(gpu['memory_used_mib']) and 0 <= gpu['memory_used_mib'] <= 1024
        and gpu.get('pids') == [])


def require_gpu_prerequisites(proof):
    """Even a valid frontend/adapter CPU receipt cannot grant GPU admission."""
    required = ['full_new_host_scope_production_CPU_accepted',
        'container_supervisor_and_terminal_lifecycle_accepted',
        'whole_card_new_host_quote_accepted', 'single_authoritative_v2_handoff_accepted']
    require(isinstance(proof, dict) and all(proof.get(k) is True for k in required),
            'Full new-host lifecycle CPU, quote and authoritative handoff are still required')
    require(proof.get('cap_GPUh') == 226
        and proof.get('origin_used_GPUh') == 79.99637737158223
        and proof.get('reset_history') is False, 'Historical budget identity changed')
    require(type(proof.get('forecast_GPUh')) in (int, float)
        and type(proof.get('billed_limit_GPUh')) in (int, float)
        and math.isfinite(proof['forecast_GPUh']) and math.isfinite(proof['billed_limit_GPUh'])
        and 0 < proof['forecast_GPUh'] <= proof['billed_limit_GPUh'] < 12,
        'Complete BANK24 planning quote outside authorized strict bound')


def verify_inputs(inputs, original_sha256, extra_sha256):
    root = Path(inputs).resolve()
    require(len(original_sha256) == 1789, 'Full original1789 denominator required')
    require(not set(original_sha256).intersection(extra_sha256), 'Extra metadata cannot override science')
    for name, expected in {**original_sha256, **extra_sha256}.items():
        rel = Path(name)
        require(not rel.is_absolute() and '..' not in rel.parts, 'Unsafe registered input')
        path = root / rel
        require(not path.is_symlink() and path.resolve().is_relative_to(root), 'Escaping or symlink input')
        require(digest(path.read_bytes()) == expected, 'Frozen input changed: ' + name)
    return dict(original_files=1789,extra_metadata_files=len(extra_sha256),
                original_closure_unchanged=True,metadata_not_new_GPU_evidence=True)


def reconstruct(inputs):
    """Use the original pure metadata/calibration routines, with no old videos.

    The old four Native slots remain provenance. BANK24 still generates its own
    six Native paths. This is not acceptance of old absolute paths or artifacts.
    """
    import os
    os.environ['WC_SCOUT_KIND'] = 'BANK24'
    root = Path(inputs).resolve()
    sys.path.insert(0, str(root/'src'))
    from wcomr.current_birth_real_inputs_r1 import load
    from wcomr.p_acr_profile528_contract_r1 import validate_local_bindings
    from wcomr import scout_production_entry_r1 as entry
    calibration, specs, references, parent, evidence = load(root)
    values = validate_local_bindings(root, read(root/'configs/wc_p_acr_local12_profile528_production_r1_20261015.json'))
    c = read(root/CONFIG)
    entry.validate_contract(c)
    for binding in c['references'].values():
        require(digest((root/binding['ref']).read_bytes()) == binding['sha256'],
                'Original BANK24 reference changed')
    require(c['requests'] == read(root/c['references']['DEV6_inputs']['ref'])['requests'],
            'Original complete six DEV requests changed')
    for plan in entry.plans().values():
        anchor = None
        for step, action in enumerate(plan, 1):
            if action == 'D':
                anchor = step
            else:
                require((anchor, step) in calibration.rho_at and step in calibration.gains,
                        'Original real calibration support missing')
    rows = entry.matrix([r['name'] for r in c['requests']])
    require(len(rows) == 24 and sum(r['section'] == 'TIMED' for r in rows) == 18,
            'Original whole24 denominator changed')
    report = dict(status='BANK24_ORIGINAL_REAL_EXECUTION_INPUTS_RECONSTRUCTED_CPU_ONLY',
        scope_counts=copy.deepcopy(c['scope_counts']), matrix=rows,
        calibration_fingerprint=calibration.fingerprint,
        H1_fingerprint=values['H1']['fingerprint'],previous_fingerprint=values['previous']['fingerprint'],
        gamma=values['H1']['gamma'],ranking_fingerprint=evidence['ranking_fingerprint'],
        input_evidence_fingerprint=evidence['binding_fingerprint'],
        metadata_Native_provenance_slots=len(references),new_Native_paths_required=6,
        old_physical_Native_artifacts_read=False,DEV_refitted=False,
        numerical_paths_reexecuted=0,Cosmos_weights_loaded=0,CUDA_initialized=False,
        GPU_submissions=0,ledger_written=False)
    # Preserve the exact original four-element execution input tuple.
    return (c, parent, (calibration, specs, references, evidence),
            {'SOURCE_PHASE':values['H1']}, values['previous']), report


def entry_contract_source():
    # A separate module, never an edit to captured registration or original code.
    # Runtime validation is deliberately closed until the remaining lifecycle is
    # accepted. A generated runner is preparation and cannot launch on its own.
    return '''from pathlib import Path
import json
from wcomr.scout_production_entry_r1 import *
from four_card_bank24_execution_adapter_r1 import reconstruct,require_gpu_prerequisites
CONFIG='inputs/'+CONFIG
MODE_REF='inputs/'+MODE_REF
def validate(project,stage):
 stage=Path(stage)
 authorization=json.loads((stage/'new-host-GPU-authorization.json').read_text())
 require_gpu_prerequisites(authorization)
 reg=json.loads((stage/'host-registration.json').read_text())
 data,report=reconstruct(stage/'inputs')
 c,old,inputs,tables,prior=data
 return c,reg,old,inputs,tables,prior
'''


def generated_bundle(inputs):
    root = Path(inputs)
    sys.path.insert(0,str(root/'src'))
    runner, report = adapt_runner((root/'scripts/run_wc_drop1_full18_r1.py').read_text())
    budget = adapt_budget_pool((root/'src/wcomr/gpu_budget_pool_v2.py').read_text())
    entry = entry_contract_source()
    for name, code in [('bank24-sm89-runner.py',runner),
                       ('bank24_sm89_entry_contract.py',entry),
                       ('bank24_sm89_budget_pool.py',budget)]:
        compile(code, name, 'exec')
    return {'bank24-sm89-runner.py':runner,
            'bank24_sm89_entry_contract.py':entry,
            'bank24_sm89_budget_pool.py':budget}, report
