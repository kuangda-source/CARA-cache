#!/usr/bin/env python3
"""Identity-only local inventory; no final selection, GPU, SSH or scores."""
import argparse
import hashlib
import json
from pathlib import Path
import time

ROOT=Path(__file__).resolve().parents[1]
PROTOCOL='manifests/wc_paper_N07_common_input_protocol_r1_20261016.json'

def sha(raw):return hashlib.sha256(raw).hexdigest()

def collect():
    protocol=json.loads((ROOT/PROTOCOL).read_text())
    for name,digest in protocol['frozen_sources'].items():
        assert sha((ROOT/name).read_bytes())==digest,name
    raw=json.loads((ROOT/'reports/dataset_source_group_audit_20260930.json').read_text())
    records=raw['records'];lookup={r['name']:r for r in records};by_prompt={r['prompt_sha256']:r['name'] for r in records}
    assert len(records)==len(lookup)==len(by_prompt)==1044
    prefixes={}
    for name in sorted(lookup,key=lambda n:(-len(n),n)):prefixes.setdefault(name.split('_')[0],[]).append(name)
    def identity(value):
        if not isinstance(value,str):return None
        digest=sha(value.encode())
        if digest in by_prompt:return by_prompt[digest]
        for name in prefixes.get(value.split('_')[0],[]):
            if value==name or value.startswith(name+'_'):return name
        return None
    hits={};files=[]
    def walk(value,source,at='$'):
        if isinstance(value,dict):
            for key,child in value.items():walk(child,source,at+'.'+key)
        elif isinstance(value,list):
            for index,child in enumerate(value):walk(child,source,at+'['+str(index)+']')
        else:
            name=identity(value)
            if name:hits.setdefault(name,[]).append(dict(source=source,location=at))
    for directory in ('configs','manifests'):
        for path in sorted((ROOT/directory).iterdir()):
            if path.suffix not in ('.json','.jsonl'):continue
            name=str(path.relative_to(ROOT));data=path.read_bytes()
            value=[json.loads(line) for line in data.decode().splitlines() if line.strip()] if path.suffix=='.jsonl' else json.loads(data)
            walk(value,name);files.append(dict(path=name,sha256=sha(data),bytes=len(data)))
    previous=json.loads((ROOT/protocol['prior_remote_identity_snapshot']).read_text())['remote']
    assert previous['no_endpoint_or_timing_values_extracted'] and not previous['read_errors']
    protected={};excluded=set(hits)|set(previous['identity_hits'])|set(raw['engineering_excluded_groups'])
    excluded.update(r['name'] for r in json.loads((ROOT/'manifests/cal_v1.json').read_text())['cases'])
    for ref in protocol['protected_input_manifests']:
        value=json.loads((ROOT/ref).read_text());names=set()
        for row in value['selected_sources']:names.update(row['group_members'])
        protected[ref]=sorted(names);excluded.update(names)
    groups=set(excluded)
    for name in excluded:groups.update(lookup[name]['group_members'])
    full_groups={tuple(sorted(r['group_members'])) for r in records}
    eligible=[lookup[min(group)] for group in sorted(full_groups) if not groups.intersection(group)]
    pools={category:sum(r['category']==category for r in eligible) for category in protocol['categories_in_order']}
    assert all(n>=protocol['prompts_per_category'] for n in pools.values())
    assert set(protected['manifests/wc_w3_expl_dev8_inputs_r1_20261015.json']).issubset(groups)
    return dict(status='N07_LOCAL_ONLY_INPUT_EXCLUSION_INVENTORY_NOT_FROZEN_TEST',observed_unix=time.time(),
        protocol_ref=PROTOCOL,protocol_sha256=sha((ROOT/PROTOCOL).read_bytes()),local_files=files,
        benchmark_records=1044,benchmark_groups=len(full_groups),local_identity_hits=hits,
        prior_remote_identity_snapshot=protocol['prior_remote_identity_snapshot'],prior_remote_observed_unix=previous['observed_unix'],
        remote_snapshot_is_fresh=False,protected_groups=protected,excluded_group_members=sorted(groups),
        eligible_group_counts=pools,final_selected_sources=None,final_requests=None,
        final_methods_pending_N05_N06=True,template_prompts=8,template_seeds=protocol['seeds_in_order'],
        template_methods=10,template_formal_paths=160,template_full_warmup_paths=20,template_total_paths=180,
        final_input_freeze_requires_fresh_server_identity_audit=True,method_or_full_GPU_card_selected=False,
        full_GPU_forecast=None,no_endpoint_cost_or_rejection_screening=True,recording_or_semantic_independence_proven=False,
        original_N06_N05_stage_read=False,GPU_submissions=0,SSH_queries=0,ledger_written=False,human_review_required=False)

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    result=collect();result['script_sha256']=sha(Path(__file__).read_bytes())
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],local_files=len(result['local_files']),benchmark_records=1044,
        excluded_members=len(result['excluded_group_members']),eligible_group_counts=result['eligible_group_counts'],
        final_selected_sources=None,GPU_submissions=0,SSH_queries=0)))

if __name__=='__main__':main()
