#!/usr/bin/env python3
"""Index natural failure states from accepted records, never a generator."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CAPTURE='reports/wc_e3_complete64_terminal_r1_20261011_capture.json'
STRATEGY='WORKING_P_AGE_NONZERO_REBASE'
METHOD='A_CPD_BETA1_ONE_PHASE'

def main():
    cap=json.loads((ROOT/CAPTURE).read_text())
    assert cap['complete_scope_post_chain_verified'] and cap['whole64_all_scored']
    def original(name):
        ref=cap['originals'][name];packed=(ROOT/ref['local_ref']).read_bytes()
        assert hashlib.sha256(packed).hexdigest()==ref['local_gzip_sha256']
        raw=gzip.decompress(packed);assert hashlib.sha256(raw).hexdigest()==ref['sha256']
        return json.loads(raw)
    scope=original('scope');selected=original('selected_config')
    source_proofs={}
    for name in ('src/wcomr/partial_mlp_guided_readout.py','src/wcomr/cfg_guided_w1_deployment.py',
                 'src/wcomr/source_aware_current_birth_control_r1.py'):
        h=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
        assert h==selected['payload_sha256'][name];source_proofs[name]=h
    paths={}
    for block in scope['blocks']:
        if block['strategy']!=STRATEGY or not any(p['method']==METHOD for p in block['paths']):continue
        receipt=original(block['id']+'_receipt')
        for request in receipt['batch']['requests']:
            for row in request['paths']:
                if row['collect']==METHOD:paths[request['sample_name']]=row
    assert set(paths)==set(scope['sample_names']) and len(paths)==4
    states=[];bindings={};all_reads=[]
    for scene in scope['sample_names']:
        row=paths[scene];dep=row['collection_complete']['deployment'];history=dep['history']
        assert len(history)==36 and row['origins']==[]
        p_reads=[];d_reads=[]
        for h in history:
            if h['action']!='CC':continue
            a=h['A_readout'];w=h['working_sources'];decision=h['source_policy']['decision']
            assert h['true_D_before']==h['true_D_after']==a['past_D_steps']
            assert w[0]['kind']==w[1]['kind']
            r={'scene':scene,'step':h['step'],'source':w[0]['kind'],
               'working_created_step':w[0]['created_step'],'working_age':h['working_source_ages'][0],
               'true_D_reference_step':a['past_D_steps'][0][-1],
               'true_D_history':a['past_D_steps'],
               'D_reference_age_gap':w[0]['created_step']-a['past_D_steps'][0][-1],
               'shared_alpha':a['shared_alpha'],
               'risk_query_anchor':h['source_policy']['working_epoch_basis']['query_anchor'],
               'risk_local_proxy':decision['local_proxy'],'risk_gain':decision['gain'],
               'risk_source_floor':decision['state_before'][3],
               'risk_added':decision['added_risk'],
               'readout_reference':'LAST_TRUE_D_UNIT_INCREMENT',
               'actual_sigma_interval':'MISSING_IN_METADATA_CAPTURE_AT_RUNTIME_DIAGNOSTIC',
               'runtime_snapshot':'NOT_SERIALIZED_CHECKPOINT_HASHES_ONLY'}
            all_reads.append(r)
            if r['source']=='P':p_reads.append(r)
            elif len(a['past_D_steps'][0])==2:d_reads.append(r)
        assert len(p_reads)>=2 and d_reads
        first=min(p_reads,key=lambda r:r['step'])
        longest=min((r for r in p_reads if r['step']!=first['step']),
                    key=lambda r:(-r['D_reference_age_gap'],r['step']))
        control=min(d_reads,key=lambda r:r['step'])
        states.extend([{**first,'role':'FIRST_NATURAL_P_READ'},
                       {**longest,'role':'MAX_REFERENCE_GAP_EXCLUDING_FIRST'},
                       {**control,'role':'TRUE_D_SOURCE_REFERENCE_CONTROL'}])
        bindings[scene]={'final_latent_sha256':row['final_latent_sha256'],
                         'actions':row['actions'],'video_artifact':row['video_artifact'],
                         'vector_artifact':row['vector_artifact']}
    assert len(states)==12 and sum(s['source']=='P' for s in states)==8
    result={'identity':'WC_MATH_N0_NATURAL_SOURCE_STATE_INDEX_R1_20261012',
      'status':'N0_ACTUAL_SOURCE_CONTRACT_AND12_STATE_INDEX_CPU_RECONSTRUCTED',
      'source_capture_ref':CAPTURE,'source_capture_sha256':hashlib.sha256((ROOT/CAPTURE).read_bytes()).hexdigest(),
      'source_proofs':source_proofs,'strategy':STRATEGY,'parent_method':METHOD,
      'scenes':scope['sample_names'],'requests':scope['requests'],'states':states,
      'all_C_reads':all_reads,'original_parent_bindings':bindings,
      'selection_rule':'Per scene first natural P-source CC; remaining maximum D/P reference gap with earliest tie; earliest natural true-D CC with two anchors as control. No teacher or endpoint values used.',
      'P_primary_states':8,'D_reference_control_states':4,'serialized_full_state_snapshots_available':0,
      'requires_four_new_natural_parent_replays':True,
      'observed_reference_difference_not_unique_causal_bug_claim':True,
      'GPU_submissions':0,'teacher_calls':0,'ledger_written':False}
    target=ROOT/'manifests/wc_math_n1_natural_state_index_r1_20261012.json'
    assert not target.exists();target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'states':[{k:s[k] for k in
       ('scene','step','source','role','D_reference_age_gap')} for s in states],
       'serialized_snapshots':0,'GPU_submissions':0},ensure_ascii=False))

if __name__=='__main__':main()
