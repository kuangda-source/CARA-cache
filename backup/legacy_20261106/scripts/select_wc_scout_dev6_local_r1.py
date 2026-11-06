#!/usr/bin/env python3
"""Deterministic local identity freeze only; fresh remote exposure remains required."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'plans/scouts_20261018'


def main():
    sha=lambda b:hashlib.sha256(b).hexdigest()
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    def committed(ref):
        return subprocess.check_output(['git','show',revision+':'+ref],cwd=ROOT)
    audit=json.loads(committed('reports/dataset_source_group_audit_20260930.json'))
    records=audit['records'];lookup={r['name']:r for r in records}
    by_hash={r['prompt_sha256']:r['name'] for r in records}
    excluded=set(audit['engineering_excluded_groups']);scan=[]
    category_rows={k:sorted([r['name'] for r in records if r['category']==k],key=lambda n:-len(n))
                   for k in ('av','human','misc','robot')}
    required=['manifests/cal_v1.json','manifests/wc_paper_N07_actual_selected_unexposed_inputs_r1_20261016.json',
              'manifests/wc_source_conditional_confirmation_inputs_r1_20261013.json',
              'manifests/wc_e2_confirmation_full72_inputs_r1_20261011.json','manifests/wc_w3_expl_dev8_inputs_r1_20261015.json',
              'manifests/wc_paper_N07_actual_bound_inputs_r1_20261016.json']
    # These are the current authoritative exposure inventories. Do not fetch
    # every historical file (including unavailable cloud placeholders).
    for name in required:
            p=ROOT/name
            raw=committed(name);text=raw.decode();scan.append(dict(path=name,sha256=sha(raw),source_revision=revision))
            tokens=re.findall(r'(?:av|human|misc|robot)_[A-Za-z0-9_-]+',text)
            hits=set()
            for token in tokens:
                for name in category_rows.get(token.split('_')[0],[]):
                    if token==name or token.startswith(name+'_'):
                        hits.add(name);break
            hits.update(by_hash[h] for h in re.findall(r'\b[0-9a-f]{64}\b',text) if h in by_hash)
            for name in hits:excluded.update(lookup[name]['group_members'])
    assert all(p in {s['path'] for s in scan} for p in required)
    salt='WC-SCOUT-SGATE-EXPLDEV6-R1-20261018';quota=dict(av=2,human=2,misc=1,robot=1);selected=[]
    for category,n in quota.items():
        groups=set();pool=[]
        for r in records:
            g=tuple(r['group_members'])
            if r['category']!=category or g in groups or excluded.intersection(g):continue
            groups.add(g);pool.append(lookup[min(g)])
        pool.sort(key=lambda r:sha((salt+'|'+r['name']).encode()))
        assert len(pool)>=n;selected.extend(pool[:n])
    requests=[];sources=[]
    for r in selected:
        p=ROOT/'vendor/WorldCache/Evaluation/PAI-Eval/cosmos_eval_jsons_text_only'/(r['name']+'.json')
        raw=committed(str(p.relative_to(ROOT)));q=json.loads(raw);assert sha(q['prompt'].encode())==r['prompt_sha256']
        archive=DEST/'prompt_sources'/(r['name']+'.json');assert not archive.exists()
        archive.parent.mkdir(parents=True,exist_ok=True);archive.write_bytes(raw)
        sources.append({**r,'source_ref':str(archive.relative_to(ROOT)),'source_sha256':sha(raw),
                        'selection_rank_sha256':sha((salt+'|'+r['name']).encode())})
        q.update(name=r['name']+'_SCOUT_DEV_seed0',seed=0,num_steps=35)
        assert (q['resolution'],q['num_output_frames'],q['guidance'])==('432,768',93,7)
        requests.append(q)
    manifest=dict(status='EXPLDEV6_LOCAL_IDENTITIES_FROZEN_FRESH_REMOTE_EXPOSURE_AND_RESOURCE_CHECK_PENDING',
        salt=salt,selection_rule='SHA256(salt|canonical group), first per category quota, no endpoint or rejection screening',
        quota=quota,seed=0,selected_sources=sources,requests=requests,backups=[],
        rejection_policy='retain all six registered positions; no replacement or rerun to complete pairs',
        local_identity_sources=scan,excluded_group_members=sorted(excluded),fresh_remote_exposure_audit_complete=False,
        future_final_test_selected=False,future_final_test_must_exclude_these_groups=True,
        calibration_z_from_original_CAL4_required_before_DEV_screening=True,GPU_submissions=0,
        Native35_references_existing=False,new_Native35_formal_paths_required=6)
    p=DEST/'SCOUT_EXPL_DEV6_INPUTS.json';assert not p.exists()
    p.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(dict(selected=[r['name'] for r in selected],local_sources_scanned=len(scan),
                         excluded_members=len(excluded),new_references=6)))


if __name__=='__main__':main()
