#!/usr/bin/env python3
"""Conservative grouped identity audit; outcome values never exported or ranked."""
import argparse,gzip,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from wcomr.frozen_input_exposure_r1 import Identities
from wc_four_card_policy_assets_r1 import ssh

def digest(raw):return hashlib.sha256(raw).hexdigest()
def unpack(x):
    if isinstance(x,dict):return {k:unpack(v) for k,v in x.items()}
    if isinstance(x,list):return [unpack(v) for v in x]
    if isinstance(x,str) and x.lstrip().startswith(('{','[')):
        try:return unpack(json.loads(x))
        except (ValueError,RecursionError):return x
    return x

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    if a.output.exists():raise ValueError('New immutable observation required')
    cat_ref='reports/dataset_source_group_audit_20260930.json';raw=(ROOT/cat_ref).read_bytes();cat=json.loads(raw)
    records=cat['records'];idx=Identities(records);docs=[];hits={};errors=[]
    exempt={cat_ref:'PRIMARY_SOURCE_CATALOG',
        'reports/wc_paper_N07_all1044_original_input_bytes_CPU_inventory_20261016.json':'ALL_INPUT_BYTES_NOT_EXECUTION'}
    for folder in ('reports','plans','manifests'):
        for path in sorted((ROOT/folder).rglob('*')):
            if not path.is_file() or not str(path).endswith(('.json','.json.gz')) or '.private.' in path.name:continue
            ref=str(path.relative_to(ROOT))
            try:
                raw=path.read_bytes();data=json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)
                docs.append(dict(ref=ref,sha256=digest(raw),bytes=len(raw)))
                if ref in exempt:
                    if 'INPUT_BYTES' in exempt[ref]:
                        assert data['sampler_or_model_or_guardrails_run'] is False and data['GPU_submissions']==0
                    continue
                found,_=idx.document(unpack(data))
                # All mentions outside the two proven catalogs conservatively exclude a group,
                # including planned/CPU-only/unused rows. No need to infer execution from scores.
                for h in found:hits.setdefault(h['name'],set()).add(ref)
            except Exception as e:errors.append(dict(ref=ref,error_type=type(e).__name__,error=str(e)[:300]))
    module=(ROOT/'src/wcomr/frozen_input_exposure_r1.py').read_text()
    remote=ssh("""
import json,sys,hashlib
p=json.load(sys.stdin);assert hashlib.sha256(p['module'].encode()).hexdigest()==p['sha256']
ns={};exec(compile(p['module'],'identity_only','exec'),ns)
print(json.dumps(ns['collect_outputs']('/data20t/gaokuangda/worldcache_workspace',p['records'])))
""",dict(module=module,sha256=digest(module.encode()),records=records))
    if not all(k in remote for k in ('identity_hits','documents','read_errors')):
        remote=dict(read_errors=[dict(kind='REMOTE_UNKNOWN')],documents=[],identity_hits={},original=remote)
    excluded=set(hits)|set(remote['identity_hits'])|set(cat['engineering_excluded_groups'])
    protected=json.loads((ROOT/'plans/cara_policy_generator_20261020/CAL_SELECT_INPUTS_R1_20261022.json').read_text())
    excluded.update(n for r in protected['selected_sources'] for n in r['group_members'])
    for r in records:
        if excluded.intersection(r['group_members']):excluded.update(r['group_members'])
    candidates=[r for r in records if not excluded.intersection(r['group_members'])]
    # Category round-robin, then fixed salted identity hash. Pool membership is not quality-selected.
    cats=sorted({r['category'] for r in candidates});queues={c:sorted([r for r in candidates if r['category']==c],key=lambda r:digest(('CARA_POOL_R1_20261025:'+r['name']).encode())) for c in cats}
    selected=[];seen=set()
    while len(selected)<48 and any(queues.values()):
        for c in cats:
            while queues[c]:
                r=queues[c].pop(0);group=tuple(sorted(r['group_members']))
                if group not in seen:
                    seen.add(group);selected.append(r);break
            if len(selected)==48:break
    clear=not errors and not remote['read_errors'] and len(selected)==48
    # Roles reserved before outcomes; no new inputs used on the CAL exploration card.
    pool=[dict(r,pool_position=i,role='NEW_DEV_RESERVED' if i<16 else 'FINAL_CONFIRMATION_RESERVED' if i<32 else 'UNASSIGNED_RESERVE') for i,r in enumerate(selected)]
    result=dict(status='GROUPED_NEW_POOL_SCOPED_EXPOSURE_AUDIT',observed_unix=time.time(),
        catalog_ref=cat_ref,catalog_sha256=digest((ROOT/cat_ref).read_bytes()),
        local_documents=docs,local_excluded_mentions={k:sorted(v) for k,v in hits.items()},local_read_errors=errors,
        remote=remote,eligible_groups=len({tuple(r['group_members']) for r in candidates}),
        excluded_names=sorted(excluded),pool=pool,scoped_clear=clear,pool_frozen=clear,
        rule='CATEGORY_ROUND_ROBIN_FIXED_SALTED_SHA256_NO_OUTCOMES',
        limits=['Known local JSON/gzip and four-card project outputs only; no claim about unrecorded/external jobs',
                'Retired two-card covered only by local saved receipts; no reconnection',
                'First-use delta exposure audit required; no replacement after seeing endpoint or refusal'],
        endpoint_values_exported=False,GPU_submissions=0,ledger_written=False)
    with a.output.open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(clear=clear,local_documents=len(docs),local_errors=len(errors),remote_errors=len(remote['read_errors']),eligible_groups=result['eligible_groups'],pool=len(pool))))
    if not clear:raise SystemExit(2)
if __name__=='__main__':main()
