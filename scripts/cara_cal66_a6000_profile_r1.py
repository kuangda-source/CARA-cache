"""Enumerated SM86 execution adaptation; original CAL66 science stays identical."""
import ast
import hashlib
from pathlib import Path

RUN = 'cara-shared-cal66-a6000-r1'
VERSION = 'CARA_SHARED66_A6000_R1'
STAGE = 'cara-shared66-full-a6000-r2-20261025'
QUOTE = 'manifests/cara_CAL66_A6000_whole_quote_r1_20261025.json'
QUOTE_SHA = '190dd6d5eb105bde2d4be3af248e0d60d904acd9049706fd35d9fc746233ca8c'


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Unexpected adapter source: ' + old[:80])
    return text.replace(old, new)


def adapt(name, text):
    original = text
    if name.endswith('/shared66_card.py'):
        text = replace_once(text, "RUN='cara-shared-cal66-ada-r2'", 'RUN=' + repr(RUN))
        text = replace_once(text, "VERSION='CARA_SHARED66_RECOVERY_R2'", 'VERSION=' + repr(VERSION))
        text = replace_once(text, "RECOVERY_QUOTE='manifests/cara_CAL66_full_recovery_quote_r2_20261025.json'", 'RECOVERY_QUOTE=' + repr(QUOTE))
        text = replace_once(text, "RECOVERY_QUOTE_SHA='ea6f015803d15385e9903077617a3d3f52618551df771443e00f7c19260c7018'", 'RECOVERY_QUOTE_SHA=' + repr(QUOTE_SHA))
        text = replace_once(text, "q['arm_seconds']==card['quote']['arm_seconds']", "set(q['arm_seconds'])==set(card['roles']) and all(math.isfinite(t) and t>0 for t in q['arm_seconds'].values()) and abs(sum(q['arm_seconds'][s['role']] for s in card['matrix'])/3600-q['components']['all66_generation_GPUh'])<1e-12")
        text = replace_once(text, "basis='Original full66 arm prices plus accepted failed-run startup allowance'", "basis='A6000 historical complete-request forecast; same frozen66 matrix',arm_seconds=q['arm_seconds']")
    elif name == 'scripts/run_cara_shared66_r1.py':
        text = replace_once(text, 'torch.cuda.get_device_capability()==(8,9)', 'torch.cuda.get_device_capability()==(8,6)')
    elif name == 'src/wcomr/gpu_budget_pool_v2.py':
        # No liability is released: financial uncertainty holds still count in
        # reserved hours, but are not live device owners after fresh host audit.
        text = text.replace("'RTX 6000 Ada' not in gpu['name']", "'A6000' not in gpu['name']")
        text = text.replace("gpu['compute_cap'] != '8.9'", "gpu['compute_cap'] != '8.6'")
        text = replace_once(text, "reserved += job['billed_limit_GPUh']; devices.append(job['gpu_uuid'])", "reserved += job['billed_limit_GPUh']\n                if job.get('confirmed_GPU_submission') is not False: devices.append(job['gpu_uuid'])")
        text = replace_once(text, "j['status'] == 'RESERVED_OR_RUNNING' and j['gpu_uuid'] == job['gpu_uuid']", "j['status'] == 'RESERVED_OR_RUNNING' and j.get('confirmed_GPU_submission') is not False and j['gpu_uuid'] == job['gpu_uuid']")
        # Only this explicitly reserved external-host envelope may be spent.
        anchor = '    def reserve(self, job, gpu):\n'
        text = replace_once(text, anchor, anchor + "        envelope = json.loads((self.project / 'reports/cal66-migration-envelope.json').read_text())\n        if job['job_id'] != " + repr(RUN) + " or envelope['run_id'] != job['job_id'] or envelope['limit_GPUh'] != job['billed_limit_GPUh'] or envelope['gpu_uuid'] != job['gpu_uuid'] or envelope.get('central_reservation_verified') is not True:\n            raise ValueError('One registered external-host budget envelope required')\n")
    elif name == 'tests/check_cara_shared66_lifecycle_cpu_r1.py':
        anchor = "pool.update(BudgetPool.accounting(pool));atomic_json(root/'reports/gpu-budget-v2.json',pool)"
        text = replace_once(text, anchor, anchor + ";atomic_json(root/'reports/cal66-migration-envelope.json',dict(run_id=contract.RUN,limit_GPUh=config['billed_limit_GPUh'],gpu_uuid='GPU-CPU-fixture',central_reservation_verified=True,declared_CPU_fixture=True))")
        text = replace_once(text, 'GPU-CPU-fixture, NVIDIA RTX 6000 Ada Generation, 0, 8.9', 'GPU-CPU-fixture, NVIDIA RTX A6000, 0, 8.6')
    elif name == 'tests/check_shared66_storage_cpu_r1.py':
        anchor = "normal_atomic(root/'reports/gpu-budget-v2.json',v)"
        text = replace_once(text, anchor, anchor + ";normal_atomic(root/'reports/cal66-migration-envelope.json',dict(run_id=contract.RUN,limit_GPUh=config['billed_limit_GPUh'],gpu_uuid='GPU-CPU-fixture',central_reservation_verified=True,declared_CPU_fixture=True))")
    else:
        raise ValueError('Unregistered host adaptation: ' + name)
    ast.parse(text)
    return text, dict(path=name, original_sha256=hashlib.sha256(original.encode()).hexdigest(),
                      generated_sha256=hashlib.sha256(text.encode()).hexdigest())
