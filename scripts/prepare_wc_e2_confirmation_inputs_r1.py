#!/usr/bin/env python3
"""Freeze the full E2 input matrix after a read-only identity exposure audit."""
import hashlib
import json
from pathlib import Path
import subprocess
import time


REMOTE_AUDIT = r'''import hashlib,json,pathlib,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr')
sha=lambda raw:hashlib.sha256(raw).hexdigest()
by_prompt={r['prompt_sha256']:r['name'] for r in INPUT['records']}
names=sorted([r['name'] for r in INPUT['records']],key=lambda n:(-len(n),n))
prefixes={}
for name in names:prefixes.setdefault(name.split('_')[0],[]).append(name)
def identity(value):
 if not isinstance(value,str):return None
 if sha(value.encode()) in by_prompt:return by_prompt[sha(value.encode())]
 for name in prefixes.get(value.split('_')[0],[]):
  if value==name or value.startswith(name+'_'):return name
 return None
hits={};receipts=[];errors=[]
def remember(name,path,location):
 if name:hits.setdefault(name,[]).append({'path':str(path),'location':location})
def walk(value,path,at='$'):
 if isinstance(value,dict):
  for key,child in value.items():walk(child,path,at+'.'+key)
 elif isinstance(value,list):
  for index,child in enumerate(value):walk(child,path,at+'['+str(index)+']')
 else:remember(identity(value),path,at)
for path in sorted((root/'outputs').rglob('receipt.json')):
 try:
  raw=path.read_bytes();value=json.loads(raw)
  receipts.append({'path':str(path),'bytes':len(raw),'sha256':sha(raw)})
  walk(value,path)
 except Exception as error:errors.append({'path':str(path),'error':str(error)})
paths=[]
for path in sorted((root/'outputs').rglob('*')):
 name=identity(path.name)
 if name:
  paths.append(str(path));remember(name,path,'OUTPUT_PATH_NAME')
budget=(root/'reports/budget.json').read_bytes()
print(json.dumps({'observed_unix':time.time(),'receipts':receipts,'identity_hits':hits,
 'matching_output_paths':paths,'read_errors':errors,'budget_sha256':sha(budget),
 'budget_used_gpu_hours':json.loads(budget)['used_gpu_hours'],
 'GPU_jobs_launched':json.loads(budget)['gpu_jobs_launched'],'GPU_submissions':0,
 'scope':'Current WorldCache outputs and recursive request identity; not unrecorded or external runs',
 'no_endpoint_or_timing_values_extracted':True}))
'''


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    root = Path(__file__).resolve().parents[1]
    protocol_path = root/'manifests/wc_e2_input_selection_protocol_r1_20261011.json'
    protocol = json.loads(protocol_path.read_text())
    report = root/'reports/wc_e2_confirmation_input_exposure_r1_20261011.json'
    manifest = root/'manifests/wc_e2_confirmation_full72_inputs_r1_20261011.json'
    requests_path = root/'configs/wc_e2_confirmation_requests_r1_20261011.jsonl'
    assert not any(p.exists() for p in (report, manifest, requests_path))
    for name, expected in protocol['frozen_sources'].items():
        assert sha((root/name).read_bytes()) == expected, name
    audit = json.loads((root/'reports/dataset_source_group_audit_20260930.json').read_text())
    records = audit['records']
    assert audit['counts']['joined'] == 1044 and len(records) == 1044
    lookup = {r['name']: r for r in records}
    by_prompt = {r['prompt_sha256']: r['name'] for r in records}
    assert len(lookup) == len(by_prompt) == 1044
    prefixes = {}
    for name in sorted(lookup, key=lambda n: (-len(n), n)):
        prefixes.setdefault(name.split('_')[0], []).append(name)

    def identity(value):
        if not isinstance(value, str):
            return None
        if sha(value.encode()) in by_prompt:
            return by_prompt[sha(value.encode())]
        for name in prefixes.get(value.split('_')[0], []):
            if value == name or value.startswith(name+'_'):
                return name
        return None

    local_files, local_hits = [], {}

    def walk(value, source, at='$'):
        if isinstance(value, dict):
            for key, child in value.items():
                walk(child, source, at+'.'+key)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, source, at+'['+str(index)+']')
        else:
            name = identity(value)
            if name:
                local_hits.setdefault(name, []).append({'source': source, 'location': at})

    for directory in ('configs', 'manifests'):
        for path in sorted((root/directory).iterdir()):
            if path.suffix not in ('.json', '.jsonl'):
                continue
            raw = path.read_bytes()
            value = ([json.loads(line) for line in raw.decode().splitlines() if line.strip()]
                     if path.suffix == '.jsonl' else json.loads(raw))
            name = str(path.relative_to(root))
            local_files.append({'path': name, 'sha256': sha(raw), 'bytes': len(raw)})
            walk(value, name)
    source = 'INPUT='+repr({'records': records})+'\n'+REMOTE_AUDIT
    process = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
                              'gkd_minchen', 'python3 -'], input=source, text=True,
                             capture_output=True, timeout=55)
    if process.returncode:
        raise RuntimeError(process.stderr[-3000:])
    remote = json.loads(process.stdout)
    # Save the actual observation even if incomplete. Never select through a
    # failed receipt read or treat an observation timeout as a run failure.
    observation = {'identity': 'WC_E2_PRESELECTION_IDENTITY_EXPOSURE_AUDIT_R1',
                   'protocol_sha256': sha(protocol_path.read_bytes()),
                   'script_sha256': sha(Path(__file__).read_bytes()),
                   'local_files': local_files, 'local_identity_hits': local_hits,
                   'remote': remote, 'GPU_submissions': 0}
    report.write_text(json.dumps(observation, indent=2)+'\n')
    assert not remote['read_errors'], 'Incomplete exposure audit, identities not frozen'
    cal = json.loads((root/'manifests/cal_v1.json').read_text())
    excluded = set(audit['engineering_excluded_groups'])
    excluded.update(r['name'] for r in cal['cases'])
    excluded.update(local_hits)
    excluded.update(remote['identity_hits'])
    excluded_groups = set(excluded)
    for name in excluded:
        excluded_groups.update(lookup[name]['group_members'])
    groups, eligible = set(), []
    for row in records:
        group = tuple(row['group_members'])
        if group in groups or excluded_groups.intersection(group):
            continue
        groups.add(group)
        eligible.append(lookup[min(group)])
    selected, pools = [], {}
    for category in protocol['categories_in_order']:
        pool = sorted((r for r in eligible if r['category'] == category),
                      key=lambda r: sha((protocol['salt']+'|'+r['name']).encode()))
        assert pool
        pools[category] = len(pool)
        selected.append(pool[0])
    assert len(selected) == len({tuple(r['group_members']) for r in selected}) == 4
    requests, sources = [], []
    for row in selected:
        path = root/'vendor/WorldCache/Evaluation/PAI-Eval/cosmos_eval_jsons_text_only'/(row['name']+'.json')
        raw = path.read_bytes(); original = json.loads(raw)
        assert sha(original['prompt'].encode()) == row['prompt_sha256']
        sources.append({**row, 'path': str(path.relative_to(root)), 'sha256': sha(raw),
                        'selection_rank_sha256': sha((protocol['salt']+'|'+row['name']).encode())})
    for seed in protocol['seeds_in_order']:
        for source in sources:
            value = json.loads((root/source['path']).read_text())
            value.update(name=source['name']+'_E2_seed'+str(seed), seed=seed, num_steps=35)
            assert (value['guidance'], value['resolution'], value['num_output_frames']) == (7, '432,768', 93)
            requests.append(value)
    requests_path.write_text(''.join(json.dumps(r)+'\n' for r in requests))
    confirmation = [{'slot': len(protocol['methods_in_order'])*i+j,
                     'request_name': request['name'], 'method': method, 'seed': request['seed']}
                    for i, request in enumerate(requests)
                    for j, method in enumerate(protocol['methods_in_order'])]
    timing = [{'slot': 40+16*i+4*round_index+position, 'CAL_name': name,
               'seed': 0, 'round': round_index+1, 'position': position+1, 'method': method}
              for i, name in enumerate(protocol['timing_CAL_input_names'])
              for round_index, order in enumerate(protocol['timing_orders'])
              for position, method in enumerate(order)]
    assert [r['slot'] for r in confirmation+timing] == list(range(72))
    value = {'identity': 'WC_E2_FULL72_INPUT_IDENTITY_FROZEN_NOT_GPU_CARD_R1_20261011',
             'frozen_unix': time.time(), 'protocol_ref': str(protocol_path.relative_to(root)),
             'protocol_sha256': sha(protocol_path.read_bytes()),
             'exposure_report_ref': str(report.relative_to(root)),
             'exposure_report_sha256': sha(report.read_bytes()),
             'excluded_observed_and_CAL_group_members': sorted(excluded_groups),
             'eligible_pool_counts': pools, 'selected_sources': sources,
             'requests_ref': str(requests_path.relative_to(root)),
             'requests_sha256': sha(requests_path.read_bytes()), 'requests': requests,
             'confirmation_slots': confirmation, 'timing_slots': timing,
             'complete_scope': {'confirmation_paths': 40, 'timing_paths': 32,
                               'complete_paths': 72, 'maximum_confirmation_fidelity_pairs': 32,
                               'solver_updates': 2592, 'CFG_calls': 5184},
             'co_primary_comparisons': protocol['co_primary_comparisons'],
             'input_selection_not_conditioned_on_endpoint_cost_or_rejection': True,
             'recording_or_session_independence_proven': False,
             'clean_implementation_CPU_acceptance_pending': True,
             'full_GPU_forecast_pending': True, 'GPU_execution_selected': False,
             'GPU_submissions': 0, 'human_review_required': False}
    manifest.write_text(json.dumps(value, indent=2)+'\n')
    print(json.dumps({'status': value['identity'], 'selected_base_names': [r['name'] for r in sources],
                      'eligible_pool_counts': pools, 'seeds': protocol['seeds_in_order'],
                      'local_files': len(local_files), 'remote_receipts': len(remote['receipts']),
                      'complete_scope': value['complete_scope'], 'GPU_submissions': 0}))


if __name__ == '__main__':
    main()
