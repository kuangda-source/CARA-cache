"""Freeze eight development prompts using identity-only exposure; no model/GPU."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tarfile
import time

ROOT=Path(__file__).resolve().parents[1]
PROTOCOL='manifests/wc_w3_expl_dev8_input_protocol_r1_20261015.json'
REPORT='reports/wc_w3_expl_dev8_identity_exposure_cpu_r1_20261015.json'
MANIFEST='manifests/wc_w3_expl_dev8_inputs_r1_20261015.json'
REQUESTS='configs/wc_w3_expl_dev8_requests_r1_20261015.jsonl'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    if any((ROOT/n).exists() for n in (REPORT,MANIFEST,REQUESTS)):raise ValueError('Keep existing frozen selection')
    protocol=json.loads((ROOT/PROTOCOL).read_text())
    for name,digest in protocol['frozen_sources'].items():
        if sha((ROOT/name).read_bytes())!=digest:raise ValueError('Bound selection source changed: '+name)
    audit=json.loads((ROOT/'reports/dataset_source_group_audit_20260930.json').read_text());records=audit['records']
    lookup={r['name']:r for r in records};by_prompt={r['prompt_sha256']:r['name'] for r in records}
    if len(records)!=1044 or len(lookup)!=1044 or len(by_prompt)!=1044:raise ValueError('Full registered benchmark groups required')
    prefixes={}
    for name in sorted(lookup,key=lambda n:(-len(n),n)):prefixes.setdefault(name.split('_')[0],[]).append(name)
    def identity(value):
        if not isinstance(value,str):return None
        if sha(value.encode()) in by_prompt:return by_prompt[sha(value.encode())]
        for name in prefixes.get(value.split('_')[0],[]):
            if value==name or value.startswith(name+'_'):return name
        return None
    hits={};files=[]
    def walk(value,source,at='$'):
        if isinstance(value,dict):
            for key,child in value.items():walk(child,source,at+'.'+key)
        elif isinstance(value,list):
            for i,child in enumerate(value):walk(child,source,at+'['+str(i)+']')
        else:
            name=identity(value)
            if name:hits.setdefault(name,[]).append({'source':source,'location':at})
    subprocess.run(['git','diff','--quiet','HEAD','--','configs','manifests'],cwd=ROOT,check=True)
    with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive','HEAD','configs','manifests'],cwd=ROOT))) as archive:
        tracked={m.name:archive.extractfile(m).read() for m in archive.getmembers() if m.isfile()}
    for directory in ('configs','manifests'):
        for path in sorted((ROOT/directory).iterdir()):
            if path.suffix not in ('.json','.jsonl'):continue
            name=str(path.relative_to(ROOT));raw=tracked[name] if name in tracked else path.read_bytes()
            value=[json.loads(l) for l in raw.decode().splitlines() if l.strip()] if path.suffix=='.jsonl' else json.loads(raw)
            walk(value,name);files.append({'path':name,'sha256':sha(raw),'bytes':len(raw)})
    old=ROOT/'scripts/prepare_wc_e2_confirmation_inputs_r1.py'
    spec=importlib.util.spec_from_file_location('original_readonly_identity_exposure',old)
    reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
    code='INPUT='+repr({'records':records})+'\n'+reader.REMOTE_AUDIT
    remote_call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen','python3 -'],
        input=code,text=True,capture_output=True,timeout=55)
    if remote_call.returncode:raise RuntimeError(remote_call.stderr[-2000:])
    remote=json.loads(remote_call.stdout)
    observation={'status':'W3_EXPL_DEV_PRESELECTION_FULL_LOCAL_REMOTE_IDENTITY_ONLY_CPU',
        'protocol_sha256':sha((ROOT/PROTOCOL).read_bytes()),'script_sha256':sha(Path(__file__).read_bytes()),
        'local_files':files,'local_identity_hits':hits,'remote':remote,'GPU_submissions':0,'ledger_written':False}
    (ROOT/REPORT).write_text(json.dumps(observation,indent=2)+'\n')
    if remote['read_errors']:raise ValueError('Incomplete exposure observation; do not freeze through errors')
    excluded=set(audit['engineering_excluded_groups'])|set(hits)|set(remote['identity_hits'])
    excluded.update(r['name'] for r in json.loads((ROOT/'manifests/cal_v1.json').read_text())['cases'])
    # Reserved E2 and exposed frozen-confirmation groups retain their role.
    for ref in protocol['protected_input_manifests']:
        excluded.update(r['name'] for r in json.loads((ROOT/ref).read_text())['selected_sources'])
    excluded_groups=set(excluded)
    for name in excluded:excluded_groups.update(lookup[name]['group_members'])
    seen=set();eligible=[]
    for row in records:
        group=tuple(row['group_members'])
        if group in seen or excluded_groups.intersection(group):continue
        seen.add(group);eligible.append(lookup[min(group)])
    selected=[];pools={}
    for category in protocol['categories_in_order']:
        pool=sorted((r for r in eligible if r['category']==category),key=lambda r:sha((protocol['salt']+'|'+r['name']).encode()))
        if len(pool)<2:raise ValueError('Two independent development groups unavailable: '+category)
        selected.extend(pool[:2]);pools[category]=len(pool)
    if len(selected)!=8 or len({tuple(r['group_members']) for r in selected})!=8:raise ValueError('Eight full development groups required')
    sources=[];requests=[]
    for row in selected:
        name='vendor/WorldCache/Evaluation/PAI-Eval/cosmos_eval_jsons_text_only/'+row['name']+'.json'
        raw=(ROOT/name).read_bytes();request=json.loads(raw)
        if sha(request['prompt'].encode())!=row['prompt_sha256'] or excluded_groups.intersection(row['group_members']):
            raise ValueError('Selected benchmark identity differs')
        request.update(name=row['name']+'_W3EXPLDEV_seed0',seed=0,num_steps=35)
        if (request['inference_type'],request['guidance'],request['resolution'],request['num_output_frames'])!=('text2world',7,'432,768',93):
            raise ValueError('Original task/spec/CFG protocol changed')
        sources.append({**row,'path':name,'sha256':sha(raw),'selection_rank_sha256':sha((protocol['salt']+'|'+row['name']).encode())})
        requests.append(request)
    (ROOT/REQUESTS).write_text(''.join(json.dumps(r)+'\n' for r in requests))
    result={'status':'W3_EXPL_DEV_EIGHT_PROMPTS_FROZEN_NOT_GPU_OR_PAPER_TEST',
        'role':'EXPL_DEV_ONLY_FOR_W3_LABELS_AND_GROUPED_DEVELOPMENT','frozen_unix':time.time(),
        'protocol_ref':PROTOCOL,'protocol_sha256':sha((ROOT/PROTOCOL).read_bytes()),
        'exposure_report_ref':REPORT,'exposure_report_sha256':sha((ROOT/REPORT).read_bytes()),
        'excluded_observed_CAL_and_reserved_group_members':sorted(excluded_groups),'eligible_pool_counts':pools,
        'selected_sources':sources,'requests_ref':REQUESTS,'requests_sha256':sha((ROOT/REQUESTS).read_bytes()),
        'requests':requests,'label_steps':protocol['label_steps'],'formal_labels_planned':64,
        'native_image_assets_required':False,'new_assets_downloaded':False,
        'selection_used_endpoint_cost_or_guardrail_outcome':False,
        'future_paper_test_must_exclude_all_selected_groups':True,
        'recording_session_or_semantic_independence_proven':False,
        'model_weights_or_sampler_parameters_changed':False,'real_teacher_labels_available':0,
        'production_CPU_accepted':False,'full_forecast_GPUh':None,'GPU_execution_selected':False,
        'GPU_submissions':0,'ledger_written':False,'human_review_required':False}
    (ROOT/MANIFEST).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'selected_names':[r['name'] for r in sources],
        'eligible_pools':pools,'excluded_groups':len(excluded_groups),'remote_receipts':len(remote['receipts']),
        'GPU_submissions':0,'full_forecast_GPUh':None}))


if __name__=='__main__':main()
