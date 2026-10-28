"""Pure-data identities shared by Q1 collection and host-side execution."""
RUN = 'cara-sq-q1-saved-r1-20261028'
SCOPE = 'plans/cara_next_stage_20261028/sq/Q1_WHOLE_SCOPE_R1.json'
PROFILE = 'plans/cara_next_stage_20261028/sq/Q1_EXECUTION_PROFILE_R1.json'
QUOTES = {host:'plans/cara_next_stage_20261028/sq/Q1_WHOLE_QUOTE_'+host.upper()+'_R1.json'
          for host in ('two_card','four_card')}
PROMPTS = ('av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632','human_199')
STEPS = (22,23,25,33,34,35)
STATE_KEYS = tuple((prompt,step) for prompt in PROMPTS for step in STEPS)
COUNTS = dict(states=12,formal_C_pairs=96,formal_head_calls=192,
              warm_C_pairs=2,preview_original_C_pairs=1,stored_dense_hidden_head_pairs=12,
              complete_readout_pairs=111,complete_head_calls=222,codec_C_pairs=72,
              new_deep_pairs=0,new_parent_paths=0,new_videos=0)
LIMITS = {'two_card':1.25,'four_card':2.}
MANIFEST_SHA = '5487f8db32d45a5d0f3304333bf362d9d6ec46fb3181c735d7267b78a6e398fa'
CHECKPOINT_SHA = '565bbb2c9645737327983f4461e4d32627bba465b0a8dc26447edea144e1ff47'
CHECKPOINT_BYTES = 4118575006
ASSETS = 'outputs/cara-ig-b1-r2-20261027/assets'
WEIGHT = ('cache/huggingface/hub/models--nvidia--Cosmos-Predict2.5-2B/'
          'snapshots/15a82a2ec231bc318692aa0456a36537c806e7d4/'
          'base/post-trained/81edfebe-bd6a-4039-8c1d-737df1a790bf_ema_bf16.pt')

# These execution boundaries must all be present in the affected CPU proof.
# The complete registration also binds inherited unchanged source files.
EXECUTION_CRITICAL = (
    'src/wcomr/sq_q1_spec_r1.py','src/wcomr/sq_q1_execution_r1.py',
    'src/wcomr/sq_q1_terminal_r1.py','src/wcomr/sq_q1_assets_r1.py',
    'src/wcomr/sq_q1_collection_r1.py','src/wcomr/sq_q1_readout_r1.py',
    'src/wcomr/sq_readout_subgraph_r1.py','src/wcomr/sq_codec_r1.py',
    'src/wcomr/gpu_budget_pool_v2.py','src/wcomr/wc73_execution_r1.py',
    'src/wcomr/wc73_exclusive_r1.py','src/wcomr/history104_storage_r2.py',
    'src/wcomr/policy_price_mode_guard_r1.py',
    'scripts/run_cara_sq_q1_r1.py','scripts/cara_sq_q1_worker_r1.py',
    'scripts/cara_sq_q1_guardian_r1.py','scripts/cara_fast_worker_r2.py',
    'scripts/cara_fast_host_guardian_r2.py',
    'scripts/four_card_policy_assets_port_r1.py',
    'scripts/four_card_bank24_execution_tools_r1.py',
    'src/wcomr/sq_q1_stage_r1.py','src/wcomr/sq_q1_capture_r1.py',
    'scripts/cara_sq_q1_control_r1.py','scripts/cara_sq_q1_assets_cpu_r1.py',
    'scripts/postprocess_cara_sq_q1_r1.py')
RUNTIME_REQUIRED = (
    'cosmos_predict2/_src/predict2/networks/minimal_v4_dit.py',
    'cosmos_predict2/_src/predict2/inference/worldcache_utils.py',
    'cosmos_predict2/_src/predict2/models/video2world_model_rectified_flow.py',
    'cosmos_predict2/_src/predict2/configs/video2world/experiment/reason_embeddings/model_2B_reason_1p1_rectified_flow.py',
    'cosmos_predict2/_src/predict2/configs/video2world/experiment/specialized_model/SFT_2B_RF.py',
    'cosmos_predict2/_src/predict2/utils/model_loader.py',
    'cosmos_predict2/_src/imaginaire/config.py',
    'cosmos_predict2/_src/predict2/conditioner.py',
    'cosmos_predict2/_src/predict2/configs/video2world/defaults/conditioner.py')
