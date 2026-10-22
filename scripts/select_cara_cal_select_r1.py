#!/usr/bin/env python3
"""Freeze two development identities from committed inventories, without scores."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
PROTOCOL='plans/cara_policy_generator_20261020/cal_select_protocol_r1_20261022.json'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def exclusion_closure(records, documents, engineering):
    lookup={r['name']:r for r in records}
    if len(lookup)!=len(records):raise ValueError('Duplicate dataset identity')
    names=sorted(lookup,key=lambda n:(-len(n),n))
    hashes={}
    for r in records:
        hashes.setdefault(r['prompt_sha256'],set()).add(r['name'])
        if not set(r['group_members'])<=set(lookup):raise ValueError('Incomplete source group')
    excluded=set(engineering)
    for document in documents:
        for token in re.findall(r'(?:av|human|misc|robot)_[A-Za-z0-9_-]+',document):
            match=next((name for name in names if token==name or token.startswith(name+'_')),None)
            if match:excluded.add(match)
        for value in re.findall(r'\b[0-9a-f]{64}\b',document):excluded.update(hashes.get(value,()))
    while True:
        expanded=excluded|{n for name in excluded if name in lookup for n in lookup[name]['group_members']}
        # Also close inverse membership, so a malformed asymmetric declaration
        # cannot let a linked variant leak into selection.
        expanded|={r['name'] for r in records if excluded.intersection(r['group_members'])}
        if expanded==excluded:break
        excluded=expanded
    return excluded


def choose(records, excluded, protocol):
    lookup={r['name']:r for r in records};groups={}
    for r in records:
        members=tuple(sorted(r['group_members']))
        if set(members)&excluded:continue
        canonical=min(members)
        groups[canonical]=lookup[canonical]
    selected=[];available={}
    for stratum,count in protocol['strata'].items():
        if stratum not in ('av','non_av') or type(count) is not int or count<1:
            raise ValueError('Frozen positive stratum quota required')
        pool=[r for r in groups.values() if (r['category']=='av')==(stratum=='av')]
        pool.sort(key=lambda r:(sha((protocol['salt']+'|'+r['name']).encode()),r['name']))
        available[stratum]=len(pool)
        if len(pool)<count:raise ValueError('Insufficient unseen source groups; no silent quota change')
        selected.extend(pool[:count])
    if len(selected)!=protocol['count']:raise ValueError('Whole selection count changed')
    return selected,available


def freeze(output):
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    def committed(name):
        raw=subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT)
        if (ROOT/name).read_bytes()!=raw:raise ValueError('Selection inputs must be published unchanged: '+name)
        return raw
    protocol_raw=committed(PROTOCOL);protocol=json.loads(protocol_raw)
    audit_raw=committed(protocol['dataset_audit_ref']);audit=json.loads(audit_raw)
    documents=[];bindings=[]
    for name in protocol['exposure_inventory_refs']:
        raw=committed(name);documents.append(raw.decode());bindings.append(dict(ref=name,sha256=sha(raw)))
    excluded=exclusion_closure(audit['records'],documents,audit['engineering_excluded_groups'])
    selected,available=choose(audit['records'],excluded,protocol)
    sources=[];requests=[]
    for r in selected:
        name='vendor/WorldCache/Evaluation/PAI-Eval/cosmos_eval_jsons_text_only/'+r['name']+'.json'
        raw=committed(name);request=json.loads(raw)
        if sha(request['prompt'].encode())!=r['prompt_sha256']:raise ValueError('Original prompt identity changed')
        if (request['resolution'],request['num_output_frames'],request['guidance'])!=('432,768',93,7):
            raise ValueError('Original common evaluation protocol changed')
        request.update(name=r['name']+'_PG_SELECT_seed0',seed=0,num_steps=35)
        requests.append(request)
        sources.append({**r,'source_ref':name,'source_sha256':sha(raw),
                        'selection_rank_sha256':sha((protocol['salt']+'|'+r['name']).encode())})
    value=dict(status='P1_CAL_SELECT_LOCAL_IDENTITIES_FROZEN_RUNTIME_EXPOSURE_RECHECK_PENDING',
        source_revision=revision,protocol_ref=PROTOCOL,protocol_sha256=sha(protocol_raw),
        dataset_audit_sha256=sha(audit_raw),local_exposure_inventory_bindings=bindings,
        excluded_group_members=sorted(excluded),eligible_groups_per_stratum=available,
        selected_sources=sources,requests=requests,seed=0,
        rejection_policy='KEEP_REGISTERED_POSITIONS_NO_REPLACEMENT',
        runtime_exposure_reverification_complete=False,endpoint_scores_read=False,
        final_TEST_selected=False,final_TEST_excluded_groups=[r['group_members'] for r in sources],
        remote_calls=0,GPU_submissions=0)
    with Path(output).open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
    return value


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True)
    value=freeze(p.parse_args().output)
    print(json.dumps(dict(status=value['status'],selected=[r['name'] for r in value['selected_sources']])))
