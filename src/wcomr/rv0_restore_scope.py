"""Pure CPU contract for the next bounded restoration diagnostic."""
import math


def validate_scope(c):
    fixed = {'run_id':'wc-rv0-restore-r1','card':'WC-RV0-UNCHANGED-RESTORE-R1-20261004-A',
             'snapshot_step':22,'suffix_labels':['A','B'],'parent_phases':2,
             'suffix_controls':4,'parent_output_files':2,'parent_solver_updates':36,
             'parent_CFG_calls':72,'suffix_solver_updates':14,'suffix_CFG_calls':28,
             'action_interventions':0,'RV_labels':0,'complete_RV0_acceptance':False,
             'clean_speed_measurement':False,'logical_copy_cap_bytes':6*(1<<30),
             'transient_copy_factor':2,'workspace_reserve_bytes':4*(1<<30),
             'timeout_seconds':3900,'child_timeout_seconds':3870,'kill_grace_seconds':5,
             'release_allowance_seconds':30}
    for name, expected in fixed.items():
        if c.get(name) != expected or type(c.get(name)) is not type(expected):
            raise ValueError('Frozen restore scope differs: '+name)
    names=['common_sense_6487f37f-ef57-49ca-afdc-d898922b5191','human_199']
    if c['sample_names'] != names or c['sample_indices'] != [1,2]:
        raise ValueError('Two exposed CAL identities required')
    if set(c['expected_parent_video_sha256']) != set(names):
        raise ValueError('Both complete ordinary WC bridges required')
    pins=c['upstream_source_sha256']
    required={'cosmos_predict2/inference.py','cosmos_predict2/_src/predict2/inference/video2world.py',
              'cosmos_predict2/_src/predict2/inference/worldcache_utils.py',
              'cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py',
              'cosmos_predict2/_src/predict2/models/fm_solvers_unipc.py',
              'cosmos_predict2/_src/predict2/conditioner.py'}
    if set(pins)!=required:raise ValueError('All six official sources must be frozen')
    digests=[*pins.values(),*c['expected_parent_video_sha256'].values(),c['cal_config_sha256'],c['f1_setup_sha256']]
    if any(type(s) is not str or len(s)!=64 or any(ch not in '0123456789abcdef' for ch in s) for s in digests):
        raise ValueError('Explicit hexadecimal provenance SHA required')


def budget_gate(budget, c):
    validate_scope(c)
    used=budget.get('used_gpu_hours')
    if (budget.get('cap_gpu_hours')!=12 or type(used) not in (int,float)
            or not math.isfinite(used) or used<0 or any(k.endswith('_inflight') for k in budget)):
        raise ValueError('Original cumulative12 budget or active reservation differs')
    required=c['timeout_seconds']+15
    if (12-used)*3600 < required:
        raise ValueError('Full independent timeout and admission allowance do not fit')
    return {'remaining_seconds':(12-used)*3600,'proposed_seconds_plus_admission':required,
            'fits':True,'reserved_seconds':0,'complete_scope_time_guaranteed':False}
