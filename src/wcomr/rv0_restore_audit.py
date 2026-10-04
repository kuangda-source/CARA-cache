"""Independent structural/fieldwise receipt audit; no Torch or generation."""
import math


def require(value,message):
    if not value:raise ValueError(message)


def positive(value):
    return type(value) in (int,float) and math.isfinite(value) and value>0


def memory(value,gpu_required):
    if not gpu_required:
        require(value=={'status':'CUDA_NOT_INITIALIZED','GPU_measurement':False},'CPU observer initialized CUDA')
        return
    require(value['status']=='EXISTING_CUDA_CONTEXT_OBSERVED' and value['GPU_measurement'] is True,'Real GPU observation missing')
    for name in ['free_bytes','total_bytes','allocated_bytes','reserved_bytes','max_allocated_bytes','max_reserved_bytes']:
        require(type(value[name]) is int and value[name]>=0,'Invalid memory bytes: '+name)
    require(value['total_bytes']>0 and value['free_bytes']<=value['total_bytes'],'GPU free/total invalid')
    require(value['max_allocated_bytes']>=value['allocated_bytes'] and value['max_reserved_bytes']>=value['reserved_bytes'],'Peak memory receipt invalid')


def audit_controls(r,c,*,gpu_required=True):
    require(r['run_card']==c['card'],'Independent run card differs')
    require(r['status']=='UNCHANGED_REAL_MODEL_RESTORE_CONTROLS_RETURNED_REQUIRES_INDEPENDENT_AUDIT','Restore run not complete')
    for name,n in [('planned_parent_phases',2),('planned_suffix_controls',4),('planned_parent_outputs',2),('RV_labels',0),('action_interventions',0)]:
        require(type(r[name]) is int and r[name]==n,'Restore denominator or label differs: '+name)
    require(r['complete_video'] is True and r['complete_RV0_acceptance'] is False and r['clean_speed_measurement'] is False,'Scope falsely enlarged')
    require([row['sample_name'] for row in r['requests']]==c['sample_names'],'Two parent identities incomplete')
    for row in r['requests']:
        require(row['status']=='RESTORE_CONTROLS_AND_ORDINARY_PARENT_CONTINUATION_PASS','Parent not accepted')
        require(row['context'][0]==c['run_id']+':'+row['sample_name'],'Request identity differs')
        require(row['prepare_calls']==1,'Ordinary prepare count differs')
        require(len(row['inputs'])==len(row['outputs'])==len(row['deep'])==72 and len(row['solver_outputs'])==36,'Parent complete CFG/solver coverage missing')
        require([v['label'] for v in row['controls']]==['A','B'],'Four complete suffix denominator missing')
        require(row['sample_return_sha256']==row['final_latent_sha256'],'Sampler final return differs')
        require(row['flags_before']==row['flags_after'] and row['decode_policy']=='SCOPED_CUDNN_BENCHMARK_FALSE_DETERMINISTIC_TRUE','Scoped decoder flags differ')
        require(set(row['condition_classes'])=={'condition','uncondition'} and all(v['frozen_dataclass'] is True for v in row['condition_classes'].values()),'Actual frozen conditions missing')
        gate=row['capture_gate']
        require(0<gate['logical_tensor_copy_bytes']<=c['logical_copy_cap_bytes'],'Capture copy cap exceeded')
        require(gate['transient_copy_factor']==2 and gate['workspace_reserve_bytes']==c['workspace_reserve_bytes'],'Capture memory policy differs')
        require(gate['required_GPU_headroom_bytes']==2*gate['GPU_logical_copy_bytes']+c['workspace_reserve_bytes'],'Capture headroom arithmetic differs')
        if gpu_required:
            require(gate['GPU_logical_copy_bytes']>0 and type(gate['GPU_free_bytes']) is int and gate['GPU_free_bytes']>=gate['required_GPU_headroom_bytes'],'Live copy headroom was insufficient')
        require(row['capture_inventory']['clone_or_transfer_performed'] is False,'Inventory already allocated snapshots')
        require(positive(row['snapshot_and_validation_wall_seconds']) and positive(row['parent_pipeline_including_diagnostics_wall_seconds']),'Measured full stage times missing')
        for name in ['memory_before_parent','memory_before_snapshot','memory_after_snapshot','memory_after_parent']:memory(row[name],gpu_required)
        for child in row['controls']:
            require(child['status']=='UNCHANGED_SUFFIX_COMPLETE_NOT_ACTION_LABEL','Suffix failed or action substituted')
            for key in ['inputs','outputs','deep']:require(child[key]==row[key][44:],'Suffix differs from parent continuation: '+key)
            require(child['solver_outputs']==row['solver_outputs'][22:],'Suffix solver differs')
            require(child['final_latent_sha256']==row['final_latent_sha256'],'Suffix final latent differs')
            record=child['record']
            require(record['label']==child['label'] and record['completed_updates']==22 and record['planned_remaining_updates']==14,'Suffix snapshot or horizon differs')
            require(record['status']=='UNCHANGED_SUFFIX_COMPLETE_NOT_RV_LABEL' and record['parent_restored'] is True,'Parent restore incomplete')
            require(record['current_action_intervention'] is False and record['counterfactual_label'] is False,'Action or label substituted')
            require(record['final_state_components']==row['final_components'] and record['final_latent_sha256']==row['final_latent_sha256'],'Final complete state differs')
            require(positive(child['inclusive_wall_seconds']),'Full suffix/restore wall missing')
            memory(child['memory_after_suffix_and_restore'],gpu_required)
        require(row['artifact']['sha256']==c['expected_parent_video_sha256'][row['sample_name']] and row['artifact']['bytes']>0,'Historical encoded official bridge differs')
    return {'status':'TWO_PARENT_FOUR_UNCHANGED_SUFFIX_FIELDWISE_RESTORE_AUDIT_PASS',
            'GPU_observation_required':gpu_required,'parent_phases':2,'complete_suffixes':4,
            'complete_parent_outputs':2,'RV_labels':0,'full_RV0_acceptance':False,
            'quality_or_clean_speed_acceptance':False}
