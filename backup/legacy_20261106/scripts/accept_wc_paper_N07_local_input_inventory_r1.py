#!/usr/bin/env python3
"""Independently reconstruct local snapshot exclusions, including JSON keys."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sha=lambda raw:hashlib.sha256(raw).hexdigest()

def accept(v):
    p=json.loads((ROOT/v['protocol_ref']).read_text())
    assert sha((ROOT/v['protocol_ref']).read_bytes())==v['protocol_sha256']
    records=json.loads((ROOT/'reports/dataset_source_group_audit_20260930.json').read_text())
    lookup={r['name']:r for r in records['records']};by_prompt={r['prompt_sha256']:r['name'] for r in records['records']}
    assert len(lookup)==len(by_prompt)==1044
    prefix={}
    for name in sorted(lookup,key=lambda x:(-len(x),x)):prefix.setdefault(name.split('_')[0],[]).append(name)
    def identity(x):
        if not isinstance(x,str):return None
        if sha(x.encode()) in by_prompt:return by_prompt[sha(x.encode())]
        return next((n for n in prefix.get(x.split('_')[0],[]) if x==n or x.startswith(n+'_')),None)
    hits=set();keys=set()
    def walk(x):
        if isinstance(x,dict):
            for key,value in x.items():
                name=identity(key)
                if name:keys.add(name)
                walk(value)
        elif isinstance(x,list):
            for y in x:walk(y)
        else:
            name=identity(x)
            if name:hits.add(name)
    for f in v['local_files']:
        path=ROOT/f['path'];raw=path.read_bytes();assert sha(raw)==f['sha256'] and len(raw)==f['bytes']
        walk([json.loads(l) for l in raw.decode().splitlines() if l.strip()] if path.suffix=='.jsonl' else json.loads(raw))
    assert hits==set(v['local_identity_hits'])
    previous=json.loads((ROOT/v['prior_remote_identity_snapshot']).read_text())['remote']
    assert not previous['read_errors'] and previous['no_endpoint_or_timing_values_extracted']
    excluded=hits|set(previous['identity_hits'])|set(records['engineering_excluded_groups'])
    excluded.update(r['name'] for r in json.loads((ROOT/'manifests/cal_v1.json').read_text())['cases'])
    for groups in v['protected_groups'].values():excluded.update(groups)
    full=set(excluded)
    for name in excluded:full.update(lookup[name]['group_members'])
    assert full==set(v['excluded_group_members']) and keys.issubset(full)
    groups={tuple(sorted(r['group_members'])) for r in records['records']}
    eligible=[lookup[min(g)] for g in groups if not full.intersection(g)]
    pools={c:sum(r['category']==c for r in eligible) for c in p['categories_in_order']}
    assert pools==v['eligible_group_counts'] and all(set(g).issubset(full) or not full.intersection(g) for g in groups)
    assert v['final_selected_sources'] is None and not v['remote_snapshot_is_fresh'] and v['SSH_queries']==0
    return dict(status='N07_LOCAL_INPUT_EXCLUSIONS_INDEPENDENTLY_ACCEPTED_NOT_FROZEN_TEST',
        local_files=len(v['local_files']),benchmark_records=1044,excluded_members=len(full),eligible_group_counts=pools,
        JSON_key_identity_hits=len(keys),JSON_dictionary_key_identities_also_covered=True,
        fresh_remote_audit_still_required=True,final_test_selected=False,GPU_submissions=0,SSH_queries=0)

def main():
    p=argparse.ArgumentParser();p.add_argument('--inventory',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    v=accept(json.loads(a.inventory.read_text()));v.update(input_ref=str(a.inventory),input_sha256=sha(a.inventory.read_bytes()),script_sha256=sha(Path(__file__).read_bytes()))
    a.output.write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))

if __name__=='__main__':main()
