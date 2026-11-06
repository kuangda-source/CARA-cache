"""Prospective fresh seeds; this manifest cannot grant a >2h exception."""
import copy
import json
from pathlib import Path

CARD = 'WC-W3-D46-FRESH-SEEDS-R1-20261008-A'
RUN = 'wc-w3-d46-fresh-seeds-r1'
COUNTS = {'Native_parents':2,'WC_parents':2,'complete_suffixes':12,'new_videos':10,'signed_policy_pairs':2}


def make_scope(original, cost):
    requests = []
    for seed in (1,2):
        row = copy.deepcopy(original)
        row.update(name='human_199_seed'+str(seed),seed=seed)
        requests.append(row)
    return {'card':CARD,'run_id':RUN,'original_CAL_index':2,'original_scene':'human_199',
            'seed_values':[1,2],'requests':requests,'scope_counts':COUNTS,
            'target_call':46,'selected_CFG_slot':1,'snapshot_step':22,
            'maximum_age_solver_steps':32,'baseline_action':'OFF_NATIVE_ADAPTIVE',
            'candidate_action':'ONE_D46_THEN_NATIVE_ADAPTIVE',
            'no_op_if_original_D46':True,'replacement_seed_or_target':False,
            'new_training_sparse_or_human_review':False,'independent_CONF':False,
            'counts_may_change':True,'clean_speed_measurement':False,
            'cost':cost,'cumulative_cap_gpu_hours':24,'GPU_execution_selected':False,
            'execution_scope_authority':None,'GPU_submissions':0}


def validate_scope(scope, original):
    expected = make_scope(original, scope['cost'])
    if scope != expected or scope['cost']['forecast_complete_GPUh'] <= 2:
        raise ValueError('Unselected complete two-seed preregistration differs')
    return {'scope_counts':COUNTS,'gt2h_exception_pending':True,'GPU_submissions':0}


def read_original(project):
    return json.loads((Path(project)/'configs/cal_w1d8.jsonl').read_text().splitlines()[2])
