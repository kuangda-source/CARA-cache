"""Full60 CAL curve; accepted numerical methods and immutable production scope."""
import json
import math
from pathlib import Path

from . import source_phase_h1_production_r1 as base
from .h1_cost_curve_batch_r1 import METHODS, matrix, lambda_variants
from .source_phase_fixed_mask_r1 import CAL_MASK_A, CAL_MASK_C, mask_fingerprint

UUID, MODE_REF, sha, write, verify_admission = (
    base.UUID, base.MODE_REF, base.sha, base.write, base.verify_admission)
CONFIG = 'configs/wc_h1_cost_curve_full60_production_r1_20261013.json'
RUN = 'wc-h1-cost-curve-static-full60-r1'
CARD = 'WC-H1-CAL-COST-CURVE-STATIC-FULL60-R1-20261013-A'
STRATEGY = base.STRATEGY
COUNTS = dict(requests=4, methods=10, scientific_paths=40, full_warmup_paths=20,
              total_paths=60, ordinary_pairs=2160, ordinary_CFG_calls=4320,
              loads=1, teacher_pairs=0, score_videos=40,
              warm_guided_control_paths=4, warm_guided_control_outputs=144)
CPU_STATUS = 'H1_COST_CURVE_TWO_FLOW_ALL160_CPU_PASS_NOT_GPU'
PRODUCTION_CPU_STATUS = 'H1_COST_CURVE_FULL60_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU'
CURVE = [131.28658774523498, 525.1463509809399, 2100.5854039237597]
FINGERPRINT = '34ef948ed2a309e8b1cae4b72b780c14e21d63383fa1eadcdfc8803c3d5beef8'


def diagnostic_warm(row):
    return row['section'] == 'WARMUP' and row['method'] in ('H1_MID', 'FIXED_A')


def previous_confirmation_contract(final, post):
    if (post['exit_code'] != 0 or final['status'] not in (
            'SOURCE_CONFIRMATION_FULL40_SCIENCE_ALL50_AUDITED_93FRAME_SCORED',
            'SOURCE_CONFIRMATION_FULL_SCOPE_REJECTIONS_OR_MISSING_REFERENCE_RETAINED')
            or len(final['rows']) != 50
            or sum(r['section'] == 'TIMED' for r in final['rows']) != 40
            or any(r['status'] not in ('COMPLETE', 'VIDEO_REJECTED', 'TEXT_REJECTED')
                   for r in final['rows'])
            or any(r.get('endpoint_audit') != 'PASS' for r in final['rows']
                   if r['status'] == 'COMPLETE')):
        raise ValueError('Full original CONF and successful terminal post required before next GPU')


def validate_contract(c):
    if (c['card'] != CARD or c['run_id'] != RUN or c['scope_counts'] != COUNTS
            or c['methods'] != list(METHODS) or c['strategy'] != STRATEGY
            or c['A_method'] != 'BETA1_ONE_PHASE' or c['warmup_repeats'] != 2
            or c['automatic_single_job_GPUh'] != 8
            or c['cumulative_cap_GPUh'] != 104.97136333301378
            or c['main_timing'] != 'SYNCHRONIZED_TEXT_ENCODING_DENOISING_VAE_DECODING'
            or c['lambda_grid'] != CURVE or c['middle_parameters_fingerprint'] != FINGERPRINT
            or c['fixed_A_plan'] != list(CAL_MASK_A) or c['fixed_plain_plan'] != list(CAL_MASK_C)
            or c['warm_guided_control_methods'] != ['H1_MID', 'FIXED_A']
            or not math.isfinite(c['forecast_complete_GPUh'])
            or not 0 < c['forecast_complete_GPUh'] <= 8
            or any(c[k] for k in ('head_elision', 'training', 'online_teachers',
                                 'real_new_input_confirmation', 'endpoint_tuning',
                                 'F_B_enabled', 'GPU_execution_selected'))
            or len(c['requests']) != 4
            or any(r['seed'] != 0 or r['num_steps'] != 35 or r['num_output_frames'] != 93
                   or r['resolution'] != '432,768' or r['guidance'] != 7
                   for r in c['requests'])):
        raise ValueError('Exact frozen full60 CAL curve and four diagnostic warm paths required')
    plan = matrix([r['name'] for r in c['requests']])
    if sum(diagnostic_warm(r) for r in plan) != 4:
        raise ValueError('Full four warm guided controls required')
    mask_fingerprint(c['fixed_A_plan']); mask_fingerprint(c['fixed_plain_plan'])


def validate(project, stage):
    project, stage = Path(project), Path(stage)
    # Reuse the accepted physical model/input/resources contract, without
    # altering its old36 config or claiming that it verifies the new60 scope.
    old_config, reg, old, inputs, tables, previous = base.validate(project, stage)
    c = json.loads((stage / CONFIG).read_text()); validate_contract(c)
    if c['requests'] != old_config['requests']:
        raise ValueError('Curve must retain all original four CAL inputs')
    cost = json.loads((stage / c['cost_ref']).read_text())
    assert sha(stage / c['cost_ref']) == c['cost_sha256']
    assert cost['total_paths'] == 60 and cost['scientific_paths'] == 40 and cost['warmup_paths'] == 20
    assert cost['forecast_complete_GPUh'] == c['forecast_complete_GPUh']
    assert c['authority_ref'] == old_config['authority_ref']
    assert c['baseline_ref'] == old_config['baseline_ref']
    assert c['table_parameters'] == old_config['table_parameters']
    assert tables['SOURCE_PHASE']['fingerprint'] == FINGERPRINT
    assert [p['lambda_seconds_per_weighted_absolute_MSE']
            for p in lambda_variants(tables['SOURCE_PHASE']).values()] == CURVE
    proof = json.loads((stage / 'curve-sampling-CPU-result.json').read_text())
    assert proof['status'] == CPU_STATUS and proof['actual_CPU_paths'] == 160
    assert proof['complete_method_paths'] == proof['clean_control_paths'] == 80
    assert not proof['CUDA_initialized'] and proof['GPU_submissions'] == 0
    assert {x['flow'] for x in proof['checks']} == {False, True}
    assert all(x['complete_CPU_paths'] == 80 and x['ordinary_initial_state_restored']
               and x['all36_clean_outputs_actions_video_equal'] for x in proof['checks'])
    for name, digest in proof['payload_sha256'].items():
        assert reg['payload_sha256'].get(name) == digest
    binding = json.loads((stage / c['middle_baseline_ref']).read_text())
    assert sha(stage / c['middle_baseline_ref']) == c['middle_baseline_sha256']
    assert len(binding['rows']) == 4 and binding['middle_parameters_fingerprint'] == FINGERPRINT
    assert {r['scene'] for r in binding['rows']} == {r['name'] for r in c['requests']}
    for r in binding['rows']:
        assert r['method'] == 'TABLE_PHASE_H1'
        for key in ('video_artifact', 'final_artifact'):
            a = r[key]; p = Path(a['path'])
            assert sha(p) == a['sha256'] and p.stat().st_size == a['bytes']
    return c, reg, old, inputs, tables, previous
