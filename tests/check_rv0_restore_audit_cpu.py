"""Synthetic refusal controls for missing or corrupted restoration evidence."""
import copy
import importlib.util
import json
from pathlib import Path


def run(config=None):
    root=Path(__file__).resolve().parents[1]
    spec=importlib.util.spec_from_file_location('restore_receipt_audit',root/'src/wcomr/rv0_restore_audit.py')
    audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
    c=config if config is not None else json.loads((root/'configs/wc_rv0_restore_r1.json').read_text())
    mem={'status':'EXISTING_CUDA_CONTEXT_OBSERVED','GPU_measurement':True,'device':0,
         'free_bytes':20*(1<<30),'total_bytes':48*(1<<30),'allocated_bytes':10*(1<<30),
         'reserved_bytes':12*(1<<30),'max_allocated_bytes':11*(1<<30),'max_reserved_bytes':13*(1<<30)}
    r={'run_card':c['card'],'status':'UNCHANGED_REAL_MODEL_RESTORE_CONTROLS_RETURNED_REQUIRES_INDEPENDENT_AUDIT',
       'planned_parent_phases':2,'planned_suffix_controls':4,'planned_parent_outputs':2,'RV_labels':0,
       'action_interventions':0,'complete_video':True,'complete_RV0_acceptance':False,'clean_speed_measurement':False,'requests':[]}
    for name in c['sample_names']:
        row={'sample_name':name,'context':[c['run_id']+':'+name,'fixture','fixture'],
             'status':'RESTORE_CONTROLS_AND_ORDINARY_PARENT_CONTINUATION_PASS','prepare_calls':1,
             'inputs':list(range(72)),'outputs':list(range(72)),'deep':[26]*72,'solver_outputs':list(range(36)),
             'flags_before':{'fixture':True},'flags_after':{'fixture':True},'sample_return_sha256':'a'*64,
             'final_latent_sha256':'a'*64,'final_components':{'fixture':'b'*64},'controls':[],
             'decode_policy':'SCOPED_CUDNN_BENCHMARK_FALSE_DETERMINISTIC_TRUE',
             'condition_classes':{k:{'class':'fixture','frozen_dataclass':True} for k in ['condition','uncondition']},
             'capture_gate':{'logical_tensor_copy_bytes':1<<30,'GPU_logical_copy_bytes':1<<30,
                 'GPU_free_bytes':20*(1<<30),'transient_copy_factor':2,'workspace_reserve_bytes':4*(1<<30),'required_GPU_headroom_bytes':6*(1<<30)},
             'capture_inventory':{'clone_or_transfer_performed':False},'snapshot_and_validation_wall_seconds':1.,
             'parent_pipeline_including_diagnostics_wall_seconds':10.,
             'artifact':{'sha256':c['expected_parent_video_sha256'][name],'bytes':1}}
        for key in ['memory_before_parent','memory_before_snapshot','memory_after_snapshot','memory_after_parent']:row[key]=copy.deepcopy(mem)
        for label in ['A','B']:
            row['controls'].append({'label':label,'status':'UNCHANGED_SUFFIX_COMPLETE_NOT_ACTION_LABEL',
                'inputs':row['inputs'][44:],'outputs':row['outputs'][44:],'deep':row['deep'][44:],
                'solver_outputs':row['solver_outputs'][22:],'final_latent_sha256':'a'*64,'inclusive_wall_seconds':2.,
                'memory_after_suffix_and_restore':copy.deepcopy(mem),
                'record':{'label':label,'status':'UNCHANGED_SUFFIX_COMPLETE_NOT_RV_LABEL','completed_updates':22,
                    'planned_remaining_updates':14,'parent_restored':True,'current_action_intervention':False,
                    'counterfactual_label':False,'final_state_components':copy.deepcopy(row['final_components']),
                    'final_latent_sha256':'a'*64}})
        r['requests'].append(row)
    accepted=audit.audit_controls(r,c);tests=[]
    def refuse(name,change):
        changed=copy.deepcopy(r);change(changed)
        try:audit.audit_controls(changed,c)
        except (ValueError,KeyError):tests.append(name)
        else:raise AssertionError('Corrupt evidence accepted: '+name)
    refuse('missing_parent',lambda x:x['requests'].pop())
    refuse('missing_suffix',lambda x:x['requests'][0]['controls'].pop())
    refuse('shortened_parent',lambda x:x['requests'][0]['inputs'].pop())
    refuse('unequal_input',lambda x:x['requests'][0]['controls'][0]['inputs'].__setitem__(0,-1))
    refuse('unequal_deep',lambda x:x['requests'][0]['controls'][0]['deep'].__setitem__(0,0))
    refuse('unequal_solver',lambda x:x['requests'][0]['controls'][0]['solver_outputs'].__setitem__(0,-1))
    refuse('state_drift',lambda x:x['requests'][0]['controls'][0]['record']['final_state_components'].update(fixture='c'*64))
    refuse('no_restore',lambda x:x['requests'][0]['controls'][0]['record'].update(parent_restored=False))
    refuse('wrong_bridge',lambda x:x['requests'][0]['artifact'].update(sha256='c'*64))
    refuse('mutable_condition',lambda x:x['requests'][0]['condition_classes']['condition'].update(frozen_dataclass=False))
    refuse('insufficient_headroom',lambda x:x['requests'][0]['capture_gate'].update(GPU_free_bytes=0))
    refuse('missing_GPU_observation',lambda x:x['requests'][0]['memory_after_snapshot'].update(GPU_measurement=False))
    refuse('invalid_peak',lambda x:x['requests'][0]['memory_after_snapshot'].update(max_allocated_bytes=0))
    refuse('fake_label',lambda x:x.update(RV_labels=1))
    refuse('scope_enlarged',lambda x:x.update(complete_RV0_acceptance=True))
    refuse('nonfinite_wall',lambda x:x['requests'][0]['controls'][0].update(inclusive_wall_seconds=float('nan')))
    refuse('decode_policy_leak',lambda x:x['requests'][0]['flags_after'].update(fixture=False))
    return {'status':'SYNTHETIC_RESTORE_RECEIPT_REFUSALS_PASS_NOT_GPU_EVIDENCE','checks':len(tests)+1,
            'refusals':tests,'accepted_synthetic_fixture':accepted,'GPU_submissions':0}


if __name__=='__main__':print(json.dumps(run()))
