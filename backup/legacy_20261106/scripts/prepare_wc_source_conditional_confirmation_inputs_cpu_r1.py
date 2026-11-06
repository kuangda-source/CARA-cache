#!/usr/bin/env python3
"""Freeze new confirmation inputs only; keep original E2 reserved groups intact."""
import hashlib,importlib.util,io,json,subprocess,tarfile,time
from pathlib import Path

R=Path(__file__).resolve().parents[1]
PROTOCOL='manifests/wc_source_conditional_confirmation_input_protocol_r1_20261013.json'
REPORT='reports/wc_source_conditional_confirmation_input_exposure_r1_20261013.json'
MANIFEST='manifests/wc_source_conditional_confirmation_inputs_r1_20261013.json'
REQUESTS='configs/wc_source_conditional_confirmation_requests_r1_20261013.jsonl'
sha=lambda raw:hashlib.sha256(raw).hexdigest()


def main():
    protocol=json.loads((R/PROTOCOL).read_text())
    assert not any((R/n).exists() for n in (REPORT,MANIFEST,REQUESTS))
    for name,h in protocol['frozen_sources'].items():assert sha((R/name).read_bytes())==h
    spec=importlib.util.spec_from_file_location('existing_identity_reader',R/'scripts/prepare_wc_e2_confirmation_inputs_r1.py')
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    audit=json.loads((R/'reports/dataset_source_group_audit_20260930.json').read_text());records=audit['records']
    assert len(records)==audit['counts']['joined']==1044
    lookup={r['name']:r for r in records};by_prompt={r['prompt_sha256']:r['name'] for r in records}
    assert len(lookup)==len(by_prompt)==1044
    prefixes={}
    for name in sorted(lookup,key=lambda n:(-len(n),n)):prefixes.setdefault(name.split('_')[0],[]).append(name)
    def identity(x):
        if not isinstance(x,str):return None
        if sha(x.encode()) in by_prompt:return by_prompt[sha(x.encode())]
        for name in prefixes.get(x.split('_')[0],[]):
            if x==name or x.startswith(name+'_'):return name
        return None
    hits={};files=[]
    def walk(value,source,at='$'):
        if isinstance(value,dict):
            for k,x in value.items():walk(x,source,at+'.'+k)
        elif isinstance(value,list):
            for i,x in enumerate(value):walk(x,source,at+'['+str(i)+']')
        else:
            name=identity(value)
            if name:hits.setdefault(name,[]).append({'source':source,'location':at})
    # Tracked inputs are unchanged; batch read their exact Git blobs rather
    # than repeatedly blocking in the macOS working-file read path. Untracked
    # current inputs remain part of the identity scan, never silently omitted.
    subprocess.run(['git','diff','--quiet','HEAD','--','configs','manifests'],cwd=R,check=True)
    with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive','HEAD','configs','manifests'],cwd=R))) as archive:
        tracked={m.name:archive.extractfile(m).read() for m in archive.getmembers() if m.isfile()}
    for directory in ('configs','manifests'):
        for p in sorted((R/directory).iterdir()):
            if p.suffix not in ('.json','.jsonl'):continue
            name=str(p.relative_to(R));raw=tracked[name] if name in tracked else p.read_bytes()
            value=[json.loads(line) for line in raw.decode().splitlines() if line.strip()] if p.suffix=='.jsonl' else json.loads(raw)
            files.append({'path':name,'sha256':sha(raw),'bytes':len(raw)});walk(value,name)
    code='INPUT='+repr({'records':records})+'\n'+old.REMOTE_AUDIT;compile(code,'<readonly-exposure>','exec')
    process=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen','python3 -'],input=code,text=True,capture_output=True,timeout=55)
    if process.returncode:raise RuntimeError(process.stderr[-2000:])
    remote=json.loads(process.stdout)
    observation={'identity':'SOURCE_CONDITIONAL_CONFIRMATION_PRESELECTION_IDENTITY_ONLY_CPU_R1',
        'protocol_sha256':sha((R/PROTOCOL).read_bytes()),'script_sha256':sha(Path(__file__).read_bytes()),
        'existing_remote_reader_sha256':sha((R/'scripts/prepare_wc_e2_confirmation_inputs_r1.py').read_bytes()),
        'local_files':files,'local_identity_hits':hits,'remote':remote,'GPU_submissions':0,'ledger_written':False}
    (R/REPORT).write_text(json.dumps(observation,indent=2)+'\n');assert not remote['read_errors']
    e2=json.loads((R/protocol['original_E2_inputs_ref']).read_text());reserved={r['name'] for r in e2['selected_sources']}
    excluded=set(audit['engineering_excluded_groups'])|reserved|set(hits)|set(remote['identity_hits'])
    excluded.update(r['name'] for r in json.loads((R/'manifests/cal_v1.json').read_text())['cases'])
    groups=set(excluded)
    for name in excluded:groups.update(lookup[name]['group_members'])
    seen=set();eligible=[]
    for row in records:
        group=tuple(row['group_members'])
        if group in seen or groups.intersection(group):continue
        seen.add(group);eligible.append(lookup[min(group)])
    selected=[];pools={}
    for category in protocol['categories_in_order']:
        pool=sorted((r for r in eligible if r['category']==category),key=lambda r:sha((protocol['salt']+'|'+r['name']).encode()))
        assert pool;selected.append(pool[0]);pools[category]=len(pool)
    assert len(selected)==len({tuple(r['group_members']) for r in selected})==4
    sources=[]
    for row in selected:
        name='vendor/WorldCache/Evaluation/PAI-Eval/cosmos_eval_jsons_text_only/'+row['name']+'.json';raw=(R/name).read_bytes();request=json.loads(raw)
        assert sha(request['prompt'].encode())==row['prompt_sha256'] and not groups.intersection(row['group_members'])
        sources.append({**row,'path':name,'sha256':sha(raw),'selection_rank_sha256':sha((protocol['salt']+'|'+row['name']).encode())})
    requests=[]
    for seed in protocol['seeds_in_order']:
        for source in sources:
            request=json.loads((R/source['path']).read_text());request.update(name=source['name']+'_SOURCECONF_seed'+str(seed),seed=seed,num_steps=35)
            assert (request['guidance'],request['resolution'],request['num_output_frames'])==(7,'432,768',93);requests.append(request)
    (R/REQUESTS).write_text(''.join(json.dumps(r)+'\n' for r in requests))
    value={'identity':'SOURCE_CONDITIONAL_CONFIRMATION_FOUR_NEW_PROMPTS_TWO_SEEDS_FROZEN_NOT_GPU_CARD_R1',
        'frozen_unix':time.time(),'protocol_ref':PROTOCOL,'protocol_sha256':sha((R/PROTOCOL).read_bytes()),
        'exposure_report_ref':REPORT,'exposure_report_sha256':sha((R/REPORT).read_bytes()),
        'excluded_observed_CAL_and_reserved_E2_group_members':sorted(groups),'reserved_original_E2_names':sorted(reserved),
        'eligible_pool_counts':pools,'selected_sources':sources,'requests_ref':REQUESTS,'requests_sha256':sha((R/REQUESTS).read_bytes()),
        'requests':requests,'methods':protocol['methods_in_order'],'method_positions':40,'warmups_planned':10,
        'candidate_frozen':False,'production_CPU_accepted':False,'GPU_execution_selected':False,
        'original_E2_full76_unchanged':True,'old_P13h_remains_deferred':True,'GPU_submissions':0,'ledger_written':False,
        'independence_boundary':protocol['reference_and_lexical_independence_limit']}
    (R/MANIFEST).write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps({'status':value['identity'],'selected_names':[r['name'] for r in sources],
        'eligible_pools':pools,'remote_receipts':len(remote['receipts']),'GPU_submissions':0,'candidate_frozen':False}))


if __name__=='__main__':main()
