"""Independent direct original-history arithmetic, no clocks() reuse."""
import gzip
import hashlib
import json
from pathlib import Path
from collections import Counter


def main():
    root=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    reg_ref='manifests/wc_e4c_existing_trace_clocks_cpu_r1_20261011.json'
    report_ref='reports/wc_e4c_existing_trace_clocks_cpu_r1_20261011.json'
    reg=json.loads((root/reg_ref).read_text());report=json.loads((root/report_ref).read_text())
    assert report['registration_sha256']==sha(root/reg_ref)
    for name,value in reg['source_sha256'].items():assert sha(root/name)==value
    def load(entry):
        c=json.loads((root/entry['capture_ref']).read_text());b=c['files'][entry['key']]
        raw=gzip.decompress((root/b.get('local_path',b.get('local_ref'))).read_bytes())
        assert b==entry['capture_file_binding'] and len(raw)==b['bytes'] and hashlib.sha256(raw).hexdigest()==b['sha256']
        return json.loads(raw)
    original=load(reg['original64']);rows=[]
    for strategy,batch in original['batches'].items():
        for request in batch.get('requests',[]):
            for row in request.get('paths',[]):
                if row.get('status')=='COMPLETE_PARENT_PATH':
                    rows.append(('ORIGINAL64',None,strategy,request['sample_name'],row))
    for entry in reg['E1_receipts']:
        receipt=load(entry)
        for request in receipt['batch']['requests']:
            for row in request['paths']:
                rows.append(('E1_FULL8',entry['arm'],'WORKING_P_AGE_KEEP_INTERVAL',request['sample_name'],row))
    assert len(rows)==22
    all_P=all_C_P=to_P=to_D=0;per_path=[];next_reason=Counter();candidate_C_after_P=0
    alias_P={};observed_scenes=set()
    for inventory,arm,strategy,name,row in rows:
        matches=[x for x in report['per_complete_path_all22'] if x['inventory']==inventory and x.get('arm')==arm
            and x['strategy']==strategy and x['sample_name']==name and x['method']==row['collect']]
        assert len(matches)==1;derived=matches[0];d=row['collection_complete'].get('deployment');observed_scenes.add(name)
        if d is None:
            assert not derived['trace']['applicable'];continue
        h=d['history'];p=[i for i in range(36) if h[i]['action']=='PP']
        c=[i for i in range(36) if h[i]['action']=='CC' and all(s['kind']=='P' for s in h[i]['working_sources'])]
        pp=sum(i+1<36 and h[i+1]['action']=='PP' for i in p)
        pd=sum(i+1<36 and h[i+1]['action']=='DD' for i in p)
        all_P+=len(p);all_C_P+=len(c);to_P+=pp;to_D+=pd
        assert len(p)==len(derived['trace']['P_events']) and len(c)==derived['trace']['C_reads_P_source']
        assert pp==derived['trace']['P_to_P_transitions'] and pd==derived['trace']['P_to_D_transitions']
        assert [x['created_step'] for x in derived['trace']['P_events']]==[i+1 for i in p]
        for i,event in enumerate(h):
            x=derived['trace']['steps'][i]
            assert x['source_age_after']==event['working_source_ages']
            assert x['true_D_steps_before']==event['true_D_before'] and x['true_D_steps_after']==event['true_D_after']
            assert x['shared_alpha']==event['A_readout']['shared_alpha']
            assert x['A_branch_status']==event['A_readout']['branch_status']
        # Direct read of the recorded next-step options; no risk threshold or
        # hypothetical local error calculation is introduced by this auditor.
        for i in p:
            if i+1==36:continue
            decision=h[i+1]['source_policy']['decision'];next_reason[decision['reason']]+=1
            candidate_C_after_P+=any(v[0]=='C' for v in decision['candidates'])
        alias=(strategy,name,row['collect'],row['guided_list_sha256'],row['final_latent_sha256'])
        if alias in alias_P:assert alias_P[alias]==len(p)
        alias_P[alias]=len(p)
        per_path.append({'inventory':inventory,'arm':arm,'strategy':strategy,'sample_name':name,'method':row['collect'],
            'direct_P_events':len(p),'direct_C_reads_P':len(c),'immediate_P_successors':pp,'immediate_D_successors':pd,
            'raw_receipt_sha256':derived['source_receipt_sha256']})
    summary=report['summary']
    assert (all_P,all_C_P,to_P,to_D)==tuple(summary[k] for k in
        ('P_events_all_captured_paths','C_reads_P_all_captured_paths','P_to_P_all_captured_paths','P_to_D_all_captured_paths'))
    assert len(alias_P)==summary['distinct_current_birth_method_output_groups']
    assert sum(alias_P.values())==summary['P_events_distinct_method_output_groups']
    assert len(report['scope_inventory_all72'])==72 and sum(x['status']=='UNSTARTED_RETAINED' for x in report['scope_inventory_all72'])==49
    result={'status':'E4C_ORIGINAL_HISTORY_DIRECT_COUNTS_INDEPENDENTLY_PASS_NOT_NEW_QUALITY_RESULT',
        'report_ref':report_ref,'report_sha256':sha(root/report_ref),'registration_sha256':sha(root/reg_ref),
        'auditor_source_sha256':sha(Path(__file__)),'complete_paths':22,'current_birth_steps':720,
        'P_events':all_P,'C_reads_P':all_C_P,'immediate_P_successors':to_P,'immediate_D_successors':to_D,
        'recorded_next_decision_reasons':dict(next_reason),'recorded_C_candidates_after_P':candidate_C_after_P,
        'distinct_method_output_groups':len(alias_P),'P_events_in_distinct_method_output_groups':sum(alias_P.values()),
        'observed_scenes':sorted(observed_scenes),'scene_count':len(observed_scenes),
        'method_output_groups_are_not_independent_scenes':True,'per_path':per_path,
        'no_clocks_function_imported_or_reused':True,'no_new_quality_error_beta_sigma_or_action_time_values':True,
        'GPU_submissions':0,'ledger_written':False,'Torch_imported':False}
    target=root/'reports/wc_e4c_existing_trace_clocks_cpu_r1_independent_20261011.json'
    assert not target.exists();target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='per_path'}))


if __name__=='__main__':main()
