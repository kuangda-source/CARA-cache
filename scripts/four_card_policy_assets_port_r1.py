"""Reversible host port of the complete 1624-cell card; no scientific edits.

The supervisor and runner share one --pid=host container, so the original
UUID flock is passed within that container, never recreated across namespaces.
The original CPU numerical/production and terminal audits remain mandatory.
"""
import ast
import copy
import hashlib
import json
import math
import os
from pathlib import Path

from four_card_bank24_execution_adapter_r1 import exact_patch, require, read, digest

ROOT = '/data20t/gaokuangda/worldcache_workspace'
RUN = 'wc-policy-interval-assets-cal4-full1624-ada-r1'
STAGE = 'wc-policy-assets-fourcard-full1624-r1-20261022'
CONFIG = 'configs/wc_policy_interval_assets_full1624_r1_20261020.json'
IMAGE = 'sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d'
SCIENCE_SOURCE = '832ee685b823540fde5584c917c0f7c05253f0fd'
CONTRACT = 'policy_assets_fourcard_contract'


def sha(path):
    return digest(Path(path).read_bytes())


def generated_sources(root):
    """Make only enumerated, invertible runtime/identity substitutions."""
    root = Path(root)
    generated, evidence = {}, {}
    specs = {
        'scripts/run_wc_policy_interval_assets_r1.py': [
            ('from wcomr.policy_interval_assets_r1 import', 'from '+CONTRACT+' import', 1),
            ('from wcomr.policy_interval_assets_production_r1 import validate', 'from '+CONTRACT+' import validate', 1),
            ("HF_HUB_CACHE=str(a.project/'hfhub')", "HF_HUB_CACHE=str(a.project/'cache/huggingface/hub')", 1),
            ("read(a.project/'configs/f1_setup.json')", "read(a.stage/'configs/f1_setup.json')", 1),
            ('torch.cuda.get_device_capability()==(8,6)', 'torch.cuda.get_device_capability()==(8,9)', 1),
        ],
        'scripts/check_wc_policy_interval_assets_cpu_r1.py': [
            ('from wcomr.policy_interval_assets_production_r1 import validate', 'from '+CONTRACT+' import validate', 1),
            ("read(a.project/'configs/f1_setup.json')", "read(a.stage/'configs/f1_setup.json')", 1),
            ("    assert not a.output.exists();atomic_json(a.output,value)",
             "    if a.mode=='production':\n        from four_card_policy_assets_port_r1 import cpu_transport_probe\n        value['host_transport_CPU']=cpu_transport_probe(a.stage)\n    assert not a.output.exists();atomic_json(a.output,value)", 1),
        ],
        'scripts/postprocess_wc_policy_interval_assets_r1.py': [
            ('from wcomr.policy_interval_assets_r1 import', 'from '+CONTRACT+' import', 1),
        ],
        'scripts/wc_policy_interval_assets_lifecycle_r1.py': [
            ('from wcomr import policy_interval_assets_r1 as A', 'import '+CONTRACT+' as A', 2),
            ('from wcomr.policy_interval_assets_production_r1 import validate', 'from '+CONTRACT+' import validate', 1),
            ('from wcomr.policy_interval_assets_lifecycle_r1 import validate_authority', 'from '+CONTRACT+' import validate_authority', 2),
            ('from wcomr.policy_interval_assets_r1 import CONFIG,RUN,CPU_BUNDLE,CPU_PROOF,read,sha',
             'from '+CONTRACT+' import CONFIG,RUN,CPU_BUNDLE,CPU_PROOF,read,sha', 1),
            ("process_identity(j['supervisor_pid']) for k,j in v['pool']['jobs'].items() if j['status']=='RESERVED_OR_RUNNING'",
             "process_identity(j['supervisor_pid']) for k,j in v['pool']['jobs'].items() if j['status']=='RESERVED_OR_RUNNING' and isinstance(j.get('supervisor_pid'),int)", 1),
            ("    a=p.parse_args()\n    if hasattr(a,'output')",
             "    a=p.parse_args()\n    if a.command not in ('cpu-worker','supervise'):raise ValueError('Use the four-card controller; legacy transport is disabled')\n    if hasattr(a,'output')", 1),
        ],
        'src/wcomr/gpu_budget_pool_v2.py': [
            ("'A6000' not in gpu['name']", "'RTX 6000 Ada' not in gpu['name']", 1),
            ("gpu['compute_cap'] != '8.6'", "gpu['compute_cap'] != '8.9'", 1),
        ],
        'src/wcomr/gpu_budget_approved_card_v2.py': [
            ("'A6000' not in gpu['name']", "'RTX 6000 Ada' not in gpu['name']", 1),
            ("gpu['compute_cap'] != '8.6'", "gpu['compute_cap'] != '8.9'", 1),
        ],
    }
    for name, substitutions in specs.items():
        original = (root/name).read_text()
        result = exact_patch(original, substitutions)
        generated[name] = result
        evidence[name] = dict(original_sha256=digest(original.encode()),
            generated_sha256=digest(result.encode()), substitutions=substitutions)
    generated['scripts/'+CONTRACT+'.py'] = CONTRACT_SOURCE
    compile(CONTRACT_SOURCE, CONTRACT, 'exec')
    return generated, evidence


def reconstruct(stage):
    """Load only the same accepted calibration metadata, no old videos."""
    from wcomr.policy_interval_assets_r1 import validate_contract
    from wcomr.current_birth_real_inputs_r1 import load
    from wcomr.p_acr_profile528_contract_r1 import validate_local_bindings
    stage = Path(stage)
    config = read(stage/CONFIG)
    validate_contract(config)
    original = read(stage/'configs/wc_scout_cal12_production_entry_r1_20261018.json')
    require(config['requests'] == original['requests'], 'Original four CAL requests changed')
    for binding in config['references'].values():
        require(sha(stage/binding['ref']) == binding['sha256'], 'Frozen collection reference changed')
    calibration, specs, references, parent, evidence = load(stage)
    values = validate_local_bindings(stage, read(stage/'configs/wc_p_acr_local12_profile528_production_r1_20261015.json'))
    return config, parent, (calibration, specs, references, evidence), {'SOURCE_PHASE': values['H1']}, values['previous']


def validate(stage, project):
    stage, project = Path(stage), Path(project)
    registration = read(stage/'registration.json')
    require(registration['namespace'] == 'FULL1624_FOUR_CARD_PORT_R1', 'Wrong new-card registration')
    for name, expected in registration['payload_sha256'].items():
        p = stage/name
        require(not p.is_symlink() and p.resolve().is_relative_to(stage.resolve()) and sha(p) == expected,
                'Registered payload changed: '+name)
    for name, expected in registration['runtime_source_sha256'].items():
        require(sha(project/'runtime'/name) == expected, 'Pinned runtime changed')
    config, parent, inputs, tables, prior = reconstruct(stage)
    # The scientific config stays byte-identical. Execution pricing is separate.
    quote = read(stage/'fourcard-whole-quote.json')
    if quote.get('forecast_complete_GPUh') is not None:
        require(quote['scope_counts'] == config['scope_counts'] and quote['billed_limit_GPUh'] == 12
                and 0 < quote['forecast_complete_GPUh'] <= 12, 'Full quote exceeds approved whole card')
        config = dict(config, forecast_complete_GPUh=quote['forecast_complete_GPUh'])
    return config, registration, parent, inputs, tables, prior


def quote_from_bank24(capture, accepted, original):
    """Price the entire collection; do not treat observer work as ordinary video."""
    require(accepted.get('full_protocol_accepted') is True, 'Accepted full BANK24 required for quote')
    rows = capture['runner']['runs']
    require(len(rows) == 24 and all(r['status'] in ('COMPLETE','VIDEO_REJECTED','TEXT_REJECTED') for r in rows),
            'All BANK24 positions required')
    durations = [r['ended_unix']-r['started_unix'] for r in rows if r['status'] in ('COMPLETE','VIDEO_REJECTED')]
    require(durations and all(math.isfinite(x) and x > 0 for x in durations), 'Observed whole request times required')
    load = capture['runner'].get('load_seconds')
    require(isinstance(load,(int,float)) and math.isfinite(load) and load > 0, 'Actual model load required')
    terms = copy.deepcopy(original['terms_seconds'])
    terms['load'] = load
    terms['full14_requests'] = 14 * max(durations)
    ratio = max(1., max(durations)/original['observed_planning_inputs']['max_whole_request_seconds'])
    terms['all_readout_trials'] *= ratio
    terms['fourcard_container_setup_and_exit'] = 300.
    forecast = math.ceil(sum(terms.values())*original['planning_margin'])/3600
    return dict(status='FULL1624_ADA_WHOLE_CARD_PLANNING_WITH_ACCEPTED_BANK24_TIMES',
        scope_counts=original['scope_counts'], terms_seconds=terms,
        forecast_complete_GPUh=forecast, billed_limit_GPUh=12., within_approved_limit=forecast <= 12,
        measured_terms=['load','full14_requests'], extra_readout_scaling=ratio,
        remaining_terms_are_conservative_historical_allowances=True,
        independent_Ada_action_prices_measured=False,
        minimum_free_disk_bytes=original['minimum_free_disk_bytes'],
        minimum_MemAvailable_bytes=math.ceil(original['peak_CPU_anchor_bank_planning_bytes']*1.3+4*2**30))


def container_command(project, stage, mode, manifest, environment, uid, gid, gpu_uuid=None):
    require(mode in ('cpu-worker','supervise'), 'Unsupported container task')
    project, stage = Path(project), Path(stage)
    require(stage.parent == project/'.sync', 'Independent stage must be under project .sync')
    gpu = mode == 'supervise'
    require(gpu == bool(gpu_uuid), 'GPU exposure must match the task')
    name = stage.name+('-gpu' if gpu else '-cpu')
    args = ['docker','run','--read-only','--network','none','--pid','host','--name',name,
        '--label','wcomr.manifest='+manifest,'--user',str(uid)+':'+str(gid),
        '--cpus','2','--memory','48g' if gpu else '16g','--pids-limit','512',
        '--tmpfs','/tmp:rw,size=2g','-v',str(project)+':'+str(project)+':ro',
        '-v',str(stage)+':'+str(stage)+':rw','-w',str(project/'runtime')]
    if gpu:
        args += ['--gpus','device='+gpu_uuid]
        for directory in ['outputs','reports','.sync']:
            path = project/directory
            args += ['-v',str(path)+':'+str(path)+':rw']
    env = dict(environment, WC_SCOUT_KIND='CAL12', CUDA_VISIBLE_DEVICES='',
               NVIDIA_VISIBLE_DEVICES=gpu_uuid if gpu else 'void')
    env['PYTHONPATH'] = str(stage/'scripts')+':'+str(stage/'src')
    for key, value in sorted(env.items()):
        args += ['-e',key+'='+str(value)]
    args += ['--entrypoint',str(project/'envs/wc-cosmos-py310-cu128-r3/bin/python'), IMAGE,
        str(stage/'scripts/wc_policy_interval_assets_lifecycle_r1.py'), mode,
        '--project',str(project),'--stage',str(stage)]
    if gpu:
        args += ['--authorization',str(stage/'policy-assets-GPU-authorization.json')]
    return args


def cpu_transport_probe(stage):
    """Real inherited-FD/parent/namespace check inside the GPU-hidden CPU container."""
    import fcntl
    import subprocess
    import sys
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='' and os.environ.get('NVIDIA_VISIBLE_DEVICES')=='void',
            'Actual CPU transport probe must hide GPUs')
    directory=Path(stage)/'CPU-transport-only';directory.mkdir()
    lock=directory/'fixture.lock'
    code='''import fcntl,json,os,sys
from pathlib import Path
fd=int(sys.argv[1]);path=Path(sys.argv[2]);expected=json.loads(sys.argv[3]);stat=os.fstat(fd)
assert [stat.st_dev,stat.st_ino]==expected['inode']
assert os.getppid()==expected['parent'] and os.readlink('/proc/self/ns/pid')==expected['namespace']
assert Path('/proc/self/fd/'+str(fd)).resolve()==path.resolve()
assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
with path.open('rb') as other:
 try:fcntl.flock(other,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:pass
 else:raise AssertionError('Independent open stole inherited lease')
print(json.dumps(dict(parent_and_namespace_match=True,original_fd_inode_match=True,independent_open_refused=True,GPU_hidden=True)))
'''
    with lock.open('xb') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);stat=os.fstat(handle.fileno())
        expected=dict(inode=[stat.st_dev,stat.st_ino],parent=os.getpid(),namespace=os.readlink('/proc/self/ns/pid'))
        result=subprocess.run([sys.executable,'-c',code,str(handle.fileno()),str(lock),json.dumps(expected)],
            pass_fds=(handle.fileno(),),capture_output=True,text=True,timeout=15,check=True)
        proof=json.loads(result.stdout)
    with lock.open('rb') as handle:
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
    return dict(proof,child_exited=True,fixture_lock_released=True,authority_ledger_opened=False)


CONTRACT_SOURCE = '''"""Separate physical identity; unchanged original scientific validator."""
import inspect,os,sys
from pathlib import Path
from wcomr.policy_interval_assets_r1 import *
from four_card_policy_assets_port_r1 import RUN,validate as _validate,require
def validate(project,stage):
 return _validate(stage,project)
def validate_authority(auth,c,regsha,proofsha,acceptedsha):
 from wcomr import policy_interval_assets_lifecycle_r1 as original
 namespace=original.__dict__.copy();namespace['RUN']=RUN
 exec(compile(inspect.getsource(original.validate_authority),'<physical-full1624-authority>','exec'),namespace)
 namespace['validate_authority'](auth,c,regsha,proofsha,acceptedsha)
 stage=Path(auth['entry_stage'])
 require(auth['execution_quote_sha256']==sha(stage/'fourcard-whole-quote.json'),'Execution quote binding changed')
 require(auth['upstream_full_protocol_accepted'] is True and auth['new_host_complete_CPU_accepted'] is True,'Complete upstream and CPU required')
 require(auth['billed_limit_GPUh']==12,'Preserve specific complete12 approval')
'''
