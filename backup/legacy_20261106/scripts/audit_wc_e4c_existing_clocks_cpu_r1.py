"""E4c read-only source-clock coverage audit of every captured complete path.

This does not estimate unrecorded beta, sigma, local error, or per-step wall
time. Deployment after-state and the source consumed before an action differ.
"""
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def clocks(row):
    deployment=row['collection_complete'].get('deployment')
    if deployment is None:
        if row['collect']!='SOURCE_RA':raise ValueError('Missing current-birth trace')
        return {'applicable':False,'reason':'ORIGINAL_RA_HAS_NO_P_WORKING_SOURCE','steps':[],'P_events':[]}
    history=deployment['history'];actions=row['actions']
    if len(history)!=36 or [h['step'] for h in history]!=list(range(1,37)) or [h['action'] for h in history]!=actions:
        raise ValueError('All36 original current-birth decisions required')
    previous=[None,None];previous_dense=[[],[]];events=[]
    for h in history:
        step=h['step'];action=h['action'];before=h['true_D_before'];after=h['true_D_after']
        if action not in ('CC','PP','DD') or before!=previous_dense or len(before)!=2 or len(after)!=2:
            raise ValueError('Actual two-branch before-state not continuous')
        working=h['working_sources'];ages=h['working_source_ages']
        if len(working)!=2 or len(ages)!=2:raise ValueError('Both current sources required')
        for branch,source in enumerate(working):
            if source['slot']!=branch or source['kind'] not in ('D','P') or ages[branch]!=step-source['created_step']:
                raise ValueError('Recorded source birth/after age differs')
            if ages[branch]<0:raise ValueError('Future source used')
            if action=='CC':
                if previous[branch] is None or source!=previous[branch] or after!=before:
                    raise ValueError('C changed a working source or true-D anchors')
            else:
                if source['kind']!=action[0] or source['created_step']!=step or ages[branch]!=0:
                    raise ValueError('Refresh did not create the recorded current source')
        if action=='PP' and before!=after:raise ValueError('P promoted approximate source to true D')
        if action=='DD' and after!=[(values+[step])[-2:] for values in before]:
            raise ValueError('Actual D anchor update differs')
        a=h['A_readout']
        if a['step']!=step or a['action']!=action or len(a['branch_status'])!=2:
            raise ValueError('A readout and semantic action not aligned')
        if a['working_source_kind']!=[s['kind'] for s in working]:
            raise ValueError('Readout source identity differs')
        policy=h['source_policy'];floor=policy['creation_floor_proxy_after']
        entry={'step':step,'action':action,'source_kind_before':[s['kind'] if s else None for s in previous],
            'source_created_step_before':[s['created_step'] if s else None for s in previous],
            'source_age_before':[step-s['created_step'] if s else None for s in previous],
            'source_kind_after':[s['kind'] for s in working],'source_age_after':ages,
            'source_created_step_after':[s['created_step'] for s in working],
            'true_D_steps_before':before,'true_D_steps_after':after,
            'true_D_last_age_before':[step-v[-1] if v else None for v in before],
            'true_D_interval_steps_before':[v[-1]-v[-2] if len(v)==2 else None for v in before],
            'shared_alpha':a['shared_alpha'],'A_branch_status':a['branch_status'],
            'A_past_D_steps':a['past_D_steps'],'extra_heads':a['extra_heads'],
            'creation_floor_proxy_after':floor,'accumulated_interval_proxy_after':policy['accumulated_interval_proxy_after'],
            'consecutive_P_after':policy['consecutive_P_after'],
            'actual_projection_updates':[{k:v.get(k) for k in ('step','slot','layer','action','tokens',
                'actual_MLP_rows','actual_fraction','fallback','full_MLP','last_actual_D',
                'projection_cache_bytes','provenance_bytes')} for v in h['actual_projection_records']],
            'controller_candidate_costs_are_frozen_proxies':True,'native_cycle_reset':h['native_cycle_reset'],
            'P_working_source_read_by_C':action=='CC' and all(s and s['kind']=='P' for s in previous),
            'P_to_P_source_transition':action=='PP' and all(s and s['kind']=='P' for s in previous),
            'numerical_beta_not_recorded':True,'numerical_sigma_not_in_this_step_record':True,
            'same_state_guided_error_not_measured':True,'actual_per_step_wall_not_recorded':True}
        events.append(entry)
        previous=copy.deepcopy(working);previous_dense=copy.deepcopy(after)
        if h['native_cycle_reset']:
            # Original deployment clears actual D history and working sources at cnt=0.
            previous=[None,None];previous_dense=[[],[]]
    p_events=[]
    for i,event in enumerate(events):
        if event['action']!='PP':continue
        following=events[i+1:];next_refresh=next((e for e in following if e['action']!='CC'),None)
        uses=[e for e in following if e['P_working_source_read_by_C']
            and e['source_created_step_before']==[event['step']]*2]
        p_events.append({'created_step':event['step'],'C_read_steps':[e['step'] for e in uses],
            'C_read_ages':[e['source_age_before'][0] for e in uses],
            'next_refresh_step':next_refresh['step'] if next_refresh else None,
            'next_refresh_action':next_refresh['action'] if next_refresh else None,
            'same_P_source_still_present_at_age':{str(age): any(e['step']==event['step']+age
                and e['source_created_step_before']==[event['step']]*2 for e in following) for age in (1,2,4)},
            'same_state_age1_2_4_quality_labels_exist':False})
    return {'applicable':True,'steps':events,'P_events':p_events,
        'C_reads_P_source':sum(e['P_working_source_read_by_C'] for e in events),
        'P_to_P_transitions':sum(e['P_to_P_source_transition'] for e in events),
        'P_to_D_transitions':sum(e['action']=='DD' and e['source_kind_before']==['P','P'] for e in events),
        'row_instrumented_pipeline_seconds':row['instrumented_parent_pipeline_wall_seconds'],
        'row_wall_is_not_sum_of_realized_action_costs':True,
        'source_lifetime_is_not_quality_or_latency_improvement':True}


def load_bound(root,entry):
    capture=json.loads((root/entry['capture_ref']).read_text());item=capture['files'][entry['key']]
    if sha(root/entry['capture_ref'])!=entry['capture_sha256'] or item!=entry['capture_file_binding']:
        raise ValueError('Registered original capture changed')
    path=root/item.get('local_path',item.get('local_ref'));packed=path.read_bytes();raw=gzip.decompress(packed)
    compressed=item.get('compressed_sha256',item.get('gzip_sha256'))
    if hashlib.sha256(packed).hexdigest()!=compressed or len(raw)!=item['bytes'] or hashlib.sha256(raw).hexdigest()!=item['sha256']:
        raise ValueError('Original captured receipt bytes changed')
    result=json.loads(raw)
    if result['source_revision']!=entry['source_revision']:raise ValueError('Original receipt revision differs')
    return result


def main():
    root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'src'))
    reg_ref='manifests/wc_e4c_existing_trace_clocks_cpu_r1_20261011.json'
    reg=json.loads((root/reg_ref).read_text())
    for n,h in reg['source_sha256'].items():
        if sha(root/n)!=h:raise ValueError('Preregistered metadata reader/source changed: '+n)
    from wcomr.full64_partial_recovery_cpu import verifier,STRATEGIES,NAMES,METHODS
    old=load_bound(root,reg['original64']);check,proof=verifier(root,old['config']['payload_sha256'])
    expected=[(s,n,m) for s in STRATEGIES for n in NAMES for m in METHODS]
    declared={key:{'inventory':'ORIGINAL64','strategy':key[0],'sample_name':key[1],'method':key[2],
        'status':'UNSTARTED_RETAINED','source_receipt_sha256':reg['original64']['capture_file_binding']['sha256']} for key in expected}
    rows=[]
    for strategy,state in old['batches'].items():
        for request in state.get('requests',[]):
            for row in request.get('paths',[]):
                key=(strategy,request['sample_name'],row['collect']);record=declared[key]
                if record['status']!='UNSTARTED_RETAINED':raise ValueError('Duplicate original position')
                record['status']='COMPLETE_TRACE_READY' if row.get('status')=='COMPLETE_PARENT_PATH' else 'PARTIAL_OR_FAILED_RETAINED'
                if record['status']=='COMPLETE_TRACE_READY':rows.append((record,row))
    for entry in reg['E1_receipts']:
        receipt=load_bound(root,entry)
        for request in receipt['batch']['requests']:
            for row in request['paths']:
                record={'inventory':'E1_FULL8','arm':entry['arm'],'strategy':STRATEGIES[0],
                    'sample_name':request['sample_name'],'method':row['collect'],
                    'status':'COMPLETE_TRACE_READY' if row.get('status')=='COMPLETE_PARENT_PATH' else 'PARTIAL_OR_FAILED_RETAINED',
                    'source_receipt_sha256':entry['capture_file_binding']['sha256']}
                if record['status']!='COMPLETE_TRACE_READY':raise ValueError('Accepted E1 full8 receipt no longer complete')
                rows.append((record,row))
    inventory=list(declared.values());inventory.extend(record for record,row in rows if record['inventory']=='E1_FULL8')
    if (len(inventory)!=72 or len(rows)!=22 or sum(x['status']=='UNSTARTED_RETAINED' for x in inventory)!=49
            or sum(x['status']=='PARTIAL_OR_FAILED_RETAINED' for x in inventory)!=1):
        raise ValueError('Original64 plus E1full8 complete/failed/unstarted denominators differ')
    results=[]
    for record,row in rows:
        check(row,record['strategy']);result=clocks(row)
        results.append({**record,'trace':result,'guided_list_sha256':row['guided_list_sha256'],
            'final_latent_sha256':row['final_latent_sha256'],
            'numerical_identity_group':hashlib.sha256(json.dumps([record['strategy'],record['sample_name'],record['method'],
                row['guided_list_sha256'],row['final_latent_sha256']],separators=(',',':')).encode()).hexdigest()})
    spec=importlib.util.spec_from_file_location('E4c_reader_tests',root/'tests/check_e4c_source_clocks_cpu_r1.py')
    test=importlib.util.module_from_spec(spec);spec.loader.exec_module(test);controls=test.run(clocks)
    applicable=[r for r in results if r['trace']['applicable']]
    groups={}
    for r in applicable:
        key=r['numerical_identity_group']
        if key in groups and groups[key]['trace']!=r['trace']:
            # Different storage overhead can differ despite identical outputs.
            a={k:v for k,v in groups[key]['trace'].items() if k!='row_instrumented_pipeline_seconds'}
            b={k:v for k,v in r['trace'].items() if k!='row_instrumented_pipeline_seconds'}
            if a!=b:raise ValueError('Identical method/numeric group had different recorded source/action trace')
        groups.setdefault(key,r)
    summary={'registered_metadata_positions':72,'complete_captured_paths':22,'partial_retained':1,'unstarted_retained':49,
        'current_birth_trace_paths':len(applicable),'current_birth_trace_steps':36*len(applicable),
        'RA_without_P_source_trace_paths':22-len(applicable),'distinct_current_birth_method_output_groups':len(groups),
        'P_events_all_captured_paths':sum(len(r['trace']['P_events']) for r in applicable),
        'C_reads_P_all_captured_paths':sum(r['trace']['C_reads_P_source'] for r in applicable),
        'P_to_P_all_captured_paths':sum(r['trace']['P_to_P_transitions'] for r in applicable),
        'P_to_D_all_captured_paths':sum(r['trace']['P_to_D_transitions'] for r in applicable),
        'P_events_distinct_method_output_groups':sum(len(r['trace']['P_events']) for r in groups.values()),
        'C_reads_P_distinct_method_output_groups':sum(r['trace']['C_reads_P_source'] for r in groups.values()),
        'duplicate_stored_or_repeated_paths_not_independent_samples':True,
        'no_numerical_beta_sigma_local_error_or_actual_action_time_imputed':True,
        'CPU_existing_trace_not_new_GPU_or_quality_evidence':True}
    report={'status':'E4C_COMPLETE_EXISTING_TRACE_CLOCK_COVERAGE_READONLY_CPU_NOT_NEW_METHOD_RESULT',
        'registration_ref':reg_ref,'registration_sha256':sha(root/reg_ref),'scope_inventory_all72':inventory,
        'per_complete_path_all22':results,'summary':summary,'affected_reader_CPU_controls':controls,
        'original_per_row_verifier_source_proof':proof,'input_capture_sha256':reg['input_capture_sha256'],
        'source_sha256':reg['source_sha256'],'Torch_imported':'torch' in sys.modules,'GPU_submissions':0,'ledger_written':False}
    assert not report['Torch_imported'];target=root/'reports/wc_e4c_existing_trace_clocks_cpu_r1_20261011.json'
    assert not target.exists();target.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps(summary))


if __name__=='__main__':main()
