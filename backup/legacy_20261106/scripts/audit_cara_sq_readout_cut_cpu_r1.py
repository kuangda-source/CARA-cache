"""Accept bounded CPU evidence while retaining the original-C numerical failure."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_CHECKPOINT = '565bbb2c9645737327983f4461e4d32627bba465b0a8dc26447edea144e1ff47'


def accept(capture, profile):
    def require(condition, message):
        if not condition: raise ValueError(message)
    launch, result = capture['launch'], capture['result']
    state, limits = capture['container_state'], capture['host_config']
    require(state['Status']=='exited' and not state['Running'] and state['ExitCode']==0
            and not state['OOMKilled'] and not state['Error'], 'CPU container not cleanly terminal')
    require(limits==dict(DeviceRequests=None, NanoCpus=2_000_000_000, Memory=8*2**30,
        MemorySwap=8*2**30, CpusetCpus='4,5', NetworkMode='none', ReadonlyRootfs=True),
        'CPU resource/GPU/network boundary differs')
    require(capture['image']=='sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d',
        'Registered CPU image differs')
    require(capture['source_hashes_equal'] and capture['runtime_hashes_equal'], 'Source/runtime SHA differs')
    corrected = result['source_scope']['schema']=='SQ_READOUT_SUBGRAPH_CPU_CONTROL_R4'
    require(result['profile']==profile and result['fixture_checks']['tests']==(4 if corrected else 3)
            and result['fixture_checks']['failures']==result['fixture_checks']['errors']==0,
            'Affected source-cut fixture evidence missing')
    require(not result['CUDA_initialized'] and result['checkpoint']['sha256']==EXPECTED_CHECKPOINT,
            'GPU context or checkpoint mismatch')
    scope_name = 'Q1_READOUT_CONTROL_CPU_R4.json' if corrected else 'Q1_READOUT_CONTROL_CPU_R3.json'
    scope = json.loads((ROOT/'plans/cara_next_stage_20261028/sq'/scope_name).read_text())
    require(result['source_scope']==scope, 'Frozen CPU scope differs')
    for key in ('new_GPU_submissions','new_GPUh','ledger_writes'):
        require(result[key]==0 and capture.get(key,0)==0 and launch.get(key,0)==0,
                'CPU diagnostic carries GPU/budget actions')
    require(not result['GPU_ready'] and not result['complete_Q1_cohort']
            and result['codec_pairs']==result['new_states']==result['new_videos']==0,
            'CPU diagnostic upgraded to new scientific/deployment evidence')
    proof = result['source_proof']
    if corrected:
        selected = proof['selected_experiment_settings']
        require(selected['use_wan_fp32_strategy'] is True and selected['conditional_frame_timestep']==.1,
                'Original selected experiment overrides missing')
    require(proof['unchanged_whole_class'] and not proof['full_model_constructed']
            and proof['parameter_dtype']=='torch.float32' and not proof['outer_autocast']
            and proof['head_parameter_bytes']==6_815_744
            and proof['WC']['full_C_skip_branch_inverse_AST_equal']
            and proof['RF']['supplied_output_inverse_AST_equal'] and proof['RF']['net_calls']==0,
            'Complete source-cut or precision binding missing')
    original = json.loads((ROOT/'reports/cara_sq_q1_dual_cpu_accepted_r2_20261028.json').read_text())
    original = original['hosts'][profile]['head_metadata']['tensors']
    for name, value in proof['head_tensors'].items():
        registered = original['net.final_layer.'+name]
        require(value['shape']==registered['shape'] and value['sha256']==registered['sha256']
                and value['checkpoint_dtype']==registered['dtype'], 'Original head tensor differs')
    require(len(proof['head_tensors'])==3, 'Incomplete original head weights')
    if profile=='two_card':
        point = result['actual_saved_state']; controls = point['controls']
        require((point['prompt'],point['step'])==(scope['prompt'],22) and result['actual_weighted_head_executed'],
                'Wrong or absent single-state numerical control')
        require(controls['original_C_pairs']==controls['stored_dense_hidden_head_pairs']==1
                and controls['head_calls']==4 and controls['deep_calls']==controls['codec_pairs']==0,
                'Extra or missing readout execution')
        require(controls['inputs_and_CPU_RNG_unchanged'] and controls['weights_unchanged'],
                'Protected inputs/RNG/weights changed')
        for key in ('original_C','stored_dense_hidden_head'):
            rows = controls[key]['branches']
            require(len(rows)==2 and controls[key]['exact']==all(r['exact'] for r in rows),
                    'Numerical branch/aggregate disagreement')
            require(all(r['exact']==(r['max_absolute']==0 and r['MSE']==0) for r in rows),
                    'Falsely claimed numerical equality')
        exact = controls['original_C']['exact'] and controls['stored_dense_hidden_head']['exact']
        require(controls['original_controls_exact']==exact, 'Falsely claimed original C acceptance')
        expected = 'ORIGINAL_READOUT_CONTROLS_EXACT_CPU' if exact else 'ORIGINAL_READOUT_CONTROLS_MISMATCH_CPU_NO_CODEC_SCORING'
        require(result['status']==expected, 'Numerical failure was relabelled as accepted C parity')
        old = json.loads((ROOT/'reports/cara_sq_q1_two_card_cpu_capture1_r2_20261028.json').read_text())
        references = {r['name']:r for r in old['result']['verified_B1_files']}
        files = result['verified_B1_files']
        require(len(files)==len({r['name'] for r in files})==5
                and all(references.get(r['name'])==r for r in files), 'Wrong original B1 artifacts')
        require(result['condition_mode']=='EXISTING_PINNED_WHOLE_CLASS_CPU_COMPILATION'
                and not result['full_condition_module_imported'], 'Condition import scope overstated')
    else:
        require(result['actual_saved_state'] is None and not result['actual_weighted_head_executed']
                and result['status']=='PINNED_READOUT_CUT_HEAD_PREPARED_CPU', 'Ada B1 execution falsely claimed')
    require(0<result['wall_seconds']<1800 and 0<result['CPU_seconds']<3600
            and 0<result['peak_RSS_KiB']<8*2**20, 'Measured CPU resource bound exceeded')
    return dict(profile=profile, result_sha256=capture['result_sha256'], status=result['status'],
        source_revision=launch['source_revision'], CPU_seconds=result['CPU_seconds'],
        worker_wall_seconds=result['wall_seconds'], peak_RSS_GiB=result['peak_RSS_KiB']/2**20,
        actual_saved_states=1 if profile=='two_card' else 0,
        original_C_parity_accepted=(result['actual_saved_state']['controls']['original_controls_exact']
                                   if profile=='two_card' else False),
        GPU_ready=False, new_GPUh=0)
