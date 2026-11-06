#!/usr/bin/env python3
"""Incremental fixed-pool identity audit. Never reselects inputs or exports outcomes."""
import argparse,gzip,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from wcomr.frozen_input_exposure_r1 import Identities
from audit_cara_new_pool_r1 import unpack
POOL='plans/cara_policy_generator_20261020/NEW_INPUT_POOL48_R1_20261025.json'
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def protected_pool(root=ROOT):
    pool=load(root/POOL);prior=load(root/pool['audit_ref'])
    if sha((root/pool['audit_ref']).read_bytes())!=pool['audit_sha256']:raise ValueError('Original audit changed')
    if not prior['scoped_clear'] or prior['local_read_errors'] or prior['remote']['read_errors']:raise ValueError('Original audit incomplete')
    if [{k:v for k,v in r.items() if k not in ('source_ref','source_sha256')} for r in pool['members']]!=prior['pool']:raise ValueError('Pool reselection forbidden')
    groups=set();roles={}
    for r in pool['members']:
        if sha((root/r['source_ref']).read_bytes())!=r['source_sha256']:raise ValueError('Input source changed')
        if groups.intersection(r['group_members']):raise ValueError('Overlapping source groups')
        groups.update(r['group_members']);roles.setdefault(r['role'],[]).append(r['name'])
    if {k:len(v) for k,v in roles.items()}!={'NEW_DEV_RESERVED':16,'FINAL_CONFIRMATION_RESERVED':16,'UNASSIGNED_RESERVE':16}:raise ValueError('16/16/16 split changed')
    if groups.intersection(prior['excluded_names']):raise ValueError('Originally excluded group in pool')
    cat=load(root/prior['catalog_ref'])
    if sha((root/prior['catalog_ref']).read_bytes())!=prior['catalog_sha256']:raise ValueError('Source catalog changed')
    return pool,prior,groups,roles,cat['records']
def delta_inventory(before,after,key):
    a={r[key]:r['sha256'] for r in before};b={r[key]:r['sha256'] for r in after}
    return dict(added=sorted(b.keys()-a.keys()),changed=sorted(k for k in a.keys()&b.keys() if a[k]!=b[k]),removed=sorted(a.keys()-b.keys()))
def classify(raw,index,protected):
    data=json.loads(raw);hits,_=index.document(unpack(data))
    return [h for h in hits if h['name'] in protected]
def audit(root=ROOT,remote_reader=None,prior_delta=None):
    started=time.time();pool,prior,protected,roles,records=protected_pool(root);idx=Identities(records)
    known={r['ref']:r['sha256'] for r in prior['local_documents']}
    metadata={POOL:sha((root/POOL).read_bytes()),pool['audit_ref']:pool['audit_sha256']}
    if prior_delta:
        old=load(root/prior_delta)
        if old['pool_sha256']!=metadata[POOL] or old['GPU_submissions']!=0 or old['endpoint_values_exported'] is not False:raise ValueError('Prior delta identity differs')
        metadata[prior_delta]=sha((root/prior_delta).read_bytes())
    docs=[];blockers=[];errors=[];reused=0;exempt=[]
    for folder in ('reports','plans','manifests','cards'):
        for p in sorted((root/folder).rglob('*')):
            if not p.is_file() or not str(p).endswith(('.json','.json.gz','.yaml','.yml')) or '.private.' in p.name:continue
            ref=str(p.relative_to(root))
            try:
                raw=p.read_bytes();h=sha(raw);docs.append(dict(ref=ref,sha256=h,bytes=len(raw)))
                if known.get(ref)==h:reused+=1;continue
                if metadata.get(ref)==h:exempt.append(dict(ref=ref,sha256=h,reason='EXACT_FROZEN_POOL_OR_AUDIT_METADATA'));continue
                payload=gzip.decompress(raw) if p.suffix=='.gz' else raw
                if p.suffix in ('.yaml','.yml'):
                    import yaml
                    payload=json.dumps(yaml.safe_load(payload)).encode()
                hits=classify(payload,idx,protected)
                if hits:blockers.append(dict(ref=ref,sha256=h,identity_locations=hits))
            except Exception as e:errors.append(dict(ref=ref,error_type=type(e).__name__))
    module=(root/'src/wcomr/frozen_input_exposure_r1.py').read_text()
    if remote_reader is None:
        from wc_four_card_policy_assets_r1 import ssh
        def remote_reader(payload):
            return ssh("""
import os,json,sys,hashlib
p=json.load(sys.stdin);assert hashlib.sha256(p['module'].encode()).hexdigest()==p['module_sha256']
os.nice(10)
ns={};exec(compile(p['module'],'READONLY_INPUT_IDENTITIES','exec'),ns)
v=ns['collect_outputs']('/data20t/gaokuangda/worldcache_workspace',p['records'])
print(json.dumps(v,allow_nan=False))
""",payload)
    remote=remote_reader(dict(module=module,module_sha256=sha(module.encode()),records=records))
    if not all(k in remote for k in ('identity_hits','documents','read_errors')):
        remote=dict(documents=[],identity_hits={},read_errors=[dict(kind='REMOTE_UNKNOWN')])
    remote_hits={n:v for n,v in remote['identity_hits'].items() if n in protected}
    clear=not(blockers or errors or remote_hits or remote['read_errors'])
    return dict(status='FIXED_POOL48_DELTA_SCOPED_CLEAR' if clear else 'FIXED_POOL48_DELTA_REVIEW_REQUIRED',started_unix=started,observed_unix=time.time(),pool_ref=POOL,pool_sha256=metadata[POOL],prior_audit_ref=pool['audit_ref'],prior_audit_sha256=pool['audit_sha256'],script_sha256=sha(Path(__file__).read_bytes()),identity_walker_sha256=sha(module.encode()),roles=roles,source_groups_disjoint=True,all48_source_bytes_match=True,pool_reselected=False,local_documents=docs,local_unchanged_reused=reused,local_delta=delta_inventory(prior['local_documents'],docs,'ref'),local_metadata_exemptions=exempt,local_blockers=blockers,local_read_errors=errors,remote=remote,remote_delta=delta_inventory(prior['remote']['documents'],remote['documents'],'path'),protected_remote_hits=remote_hits,scoped_no_execution_evidence=clear,first_use_delta_required=True,DEV_execution_ready=False,endpoint_values_exported=False,videos_or_tensors_decoded=False,GPU_submissions=0,ledger_written=False,limits=prior['limits']+['Current observation is not launch authorization or indefinite freshness; first-use audit required','Remote result metadata is parsed only for identities; no scientific values exported or interpreted'])
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--prior-delta');a=p.parse_args()
    if a.output.exists():raise ValueError('Preserve prior audit')
    v=audit(prior_delta=a.prior_delta)
    with a.output.open('x') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({k:v[k] for k in ('status','local_unchanged_reused','local_delta','remote_delta','local_blockers','local_read_errors','protected_remote_hits')},ensure_ascii=False))
    if not v['scoped_no_execution_evidence']:raise SystemExit(2)
if __name__=='__main__':main()
