"""Independent receipt reconstruction controls; every capture here is synthetic."""
import copy
import importlib.util
from pathlib import Path
import unittest

from wcomr.frozen_shared_acceptance_r1 import accept
from wcomr.frozen_shared_production_r1 import PRODUCTION_CPU_STATUS, RUN, fingerprint
from wcomr.frozen_shared_post_r1 import GPU_TERMINAL_STATUS
from wcomr.gpu_budget_pool_v2 import BudgetPool, SCHEMA


def module(name):
    path = Path(__file__).with_name(name + '.py')
    spec = importlib.util.spec_from_file_location('synthetic_acceptance_' + name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


def fixture():
    post = module('test_frozen_shared_post_r1')
    config, bound, plan, runs = post.fixture()
    root = '/home/gaokuangda/data/gkd/worldcache_omr/outputs/' + RUN
    for row in runs:
        row['video_path'] = root + '/' + row['id'] + '/video.mp4'
        row['final_artifact'] = dict(path=root + '/' + row['id'] + '/final.pt',
                                    sha256=row['final_latent_sha256'], bytes=1)
        if row['section'] == 'WARMUP':
            row['warm_guided_artifact'] = dict(path=root + '/' + row['id'] + '/guided.pt', sha256='1' * 64, bytes=1)
            row['warm_guided_tree_sha256'] = '2' * 64
    final = post.evaluate(bound, plan, runs)
    final['artifact_inventory'] = [dict(path=a['path'], bytes=a['bytes'], sha256=a['sha256'])
        for row in final['rows'] for key in ('final_artifact', 'warm_guided_artifact', 'video_artifact')
        if (a := row.get(key)) is not None]
    config['references'] = dict(bound_inputs=dict(ref='SYNTHETIC_BOUND.json', sha256='3' * 64))
    config['first_collection_delay_seconds'] = 120
    args = dict(revision='SYNTHETIC_NOT_DISPATCHED', gpu_uuid='GPU-SYNTHETIC-OWN', config_sha256='4' * 64,
                proof_sha256='5' * 64, registration_sha256='6' * 64)
    registration = dict(source_revision=args['revision'],
        payload_sha256={'scripts/run_wc_paper_N07_frozen_shared180_r1.py': '7' * 64})
    own = dict(pid=1001, start_ticks=10010)
    child, watcher = dict(pid=1003, start_ticks=10030), dict(pid=1002, start_ticks=10020)
    authority = dict(source_revision=args['revision'], config_sha256=args['config_sha256'],
        production_CPU_sha256=args['proof_sha256'], bound_input_fingerprint=fingerprint(bound),
        scope_counts=config['scope_counts'], whole_card_run=RUN, gpu_uuid=args['gpu_uuid'],
        forecast_complete_GPUh=config['forecast_complete_GPUh'], billed_limit_GPUh=config['billed_limit_GPUh'],
        cumulative_cap_GPUh=config['cumulative_cap_GPUh'], budget_origin_used_GPUh=config['budget_origin_used_GPUh'],
        direct_user_authorization=True, user_reply_quote='SYNTHETIC ONLY; NO HUMAN APPROVAL ISSUED',
        launch_id='SYNTHETIC-NO-LAUNCH', kind='STANDING_STRICT_UNDER12')
    proof = dict(status=PRODUCTION_CPU_STATUS, exit_code=0, source_revision=args['revision'],
        registration_sha256=args['registration_sha256'], config_sha256=args['config_sha256'],
        actual_sample_argument_variants=160, matrix=plan, CUDA_initialized=False, model_weights_loaded=0,
        runner_source_sha256='7' * 64)
    launch = dict(status='N07_SHARED180_DISPATCHED_FRESH_ADMISSION_PENDING', run_id=RUN,
        source_revision=args['revision'], launch_id=authority['launch_id'], gpu_uuid=args['gpu_uuid'],
        scope_counts=config['scope_counts'], config_sha256=args['config_sha256'],
        registration_sha256=args['registration_sha256'], production_CPU_sha256=args['proof_sha256'],
        authorization_sha256='8' * 64, bound_input_fingerprint=fingerprint(bound),
        supervisor_pid=own['pid'], supervisor_identity=own, post_watcher_pid=watcher['pid'],
        post_watcher_identity=watcher, next_check_not_before_unix=1000.)
    supervisor = dict(status=GPU_TERMINAL_STATUS, pid=own['pid'], start_ticks=own['start_ticks'],
        child_identity=child, child_exit_code=0, billing_sha256='9' * 64, actual_GPUh=1., runner_sha256='a' * 64,
        **{k: launch[k] for k in ('source_revision', 'launch_id', 'run_id', 'gpu_uuid',
               'scope_counts', 'config_sha256', 'bound_input_fingerprint', 'registration_sha256')})
    bill = dict(status='N07_SHARED180_ACTUAL_GPU_BILL', original_output_root_available=True,
        actual_GPUh=1., wall_seconds=3600., billed_limit_GPUh=config['billed_limit_GPUh'],
        **{k: launch[k] for k in ('source_revision', 'launch_id', 'run_id', 'gpu_uuid', 'scope_counts', 'config_sha256')})
    job = dict(status='SETTLED', kind='V2', actual_GPUh=1., billing_sha256='9' * 64,
        forecast_GPUh=config['forecast_complete_GPUh'], billed_limit_GPUh=config['billed_limit_GPUh'],
        **{k: launch[k] for k in ('source_revision', 'launch_id', 'gpu_uuid', 'config_sha256',
                                   'scope_counts', 'production_CPU_sha256', 'bound_input_fingerprint')})
    pool = dict(schema=SCHEMA, cap_gpu_hours=config['cumulative_cap_GPUh'],
        origin_used_gpu_hours=config['budget_origin_used_GPUh'], origin_gpu_jobs_launched=100,
        jobs={RUN: job}, events=[])
    pool.update(BudgetPool.accounting(pool))
    final.update(source_revision=args['revision'], config_sha256=args['config_sha256'],
        bound_input_fingerprint=fingerprint(bound), scope_counts=config['scope_counts'],
        GPU_supervisor=copy.deepcopy(supervisor), CUDA_initialized=False)
    runner = dict(runs=runs, source_revision=args['revision'], config_sha256=args['config_sha256'],
        bound_input_fingerprint=fingerprint(bound), scope_counts=config['scope_counts'],
        cases=bound['cases'], methods=bound['method_ids'], matrix=plan, model_load_calls=1, model_loads_completed=1)
    value = dict(status='N07_SHARED180_ORIGINAL_ONCE_CAPTURE', mode='terminal', observed_unix=2000., launch=launch,
        registration=registration, registration_sha256=args['registration_sha256'],
        payload_verified={k: True for k in registration['payload_sha256']},
        config=config, config_sha256=args['config_sha256'], bound_inputs=bound, bound_inputs_sha256='3' * 64,
        production_CPU=proof, production_CPU_sha256=args['proof_sha256'],
        authorization=authority, authorization_sha256='8' * 64, supervisor=supervisor, runner=runner, runner_sha256='a' * 64,
        original_processes={k: dict(pid=p['pid'], start_ticks=None, state=None) for k, p in (
            ('supervisor_pid', own), ('child_pid', child), ('post_watcher_pid', watcher))},
        billing=bill, billing_sha256='9' * 64, pool=pool, own_UUID_lock_free=True,
        own_GPU=args['gpu_uuid'] + ', NVIDIA RTX A6000, 24', compute_apps='', output_root=root,
        post_exit=dict(status='N07_SHARED180_POST_CPU_TERMINAL', exit_code=0, original_supervisor=own,
            source_revision=args['revision'], config_sha256=args['config_sha256'], final_result_sha256='b' * 64),
        final=final, final_sha256='b' * 64)
    return value, launch


class IndependentAcceptanceControls(unittest.TestCase):
    def test_complete160_both_seed_stats_and_actual_receipt_binding(self):
        value, launch = fixture(); result = accept(value, launch, bootstrap_repetitions=8)
        self.assertTrue(result['scientific_full_scope_accepted'])
        self.assertEqual(result['scored_scientific_videos'], 160)
        self.assertEqual(result['actual_GPUh'], 1.)
        self.assertEqual(result['grouped_statistics']['registered_prompt_groups'], 8)

    def test_actual_source_payload_or_early_capture_is_refused(self):
        original, launch = fixture()
        for kind in ('payload', 'time', 'source', 'proof', 'load'):
            value = copy.deepcopy(original)
            if kind == 'payload': value['payload_verified'][next(iter(value['payload_verified']))] = False
            elif kind == 'time': value['observed_unix'] = 999.
            elif kind == 'source': value['supervisor']['source_revision'] = 'OTHER'
            elif kind == 'proof': value['production_CPU']['actual_sample_argument_variants'] = 159
            else: value['runner']['model_load_calls'] = 2
            with self.assertRaises(ValueError): accept(value, launch, bootstrap_repetitions=8)

    def test_live_exact_handle_waits_but_reused_PID_is_not_an_original_job(self):
        value, launch = fixture()
        value['original_processes']['supervisor_pid'].update(state='R', start_ticks=10010)
        result = accept(value, launch, bootstrap_repetitions=8)
        self.assertTrue(result['original_live_handles']['supervisor'])
        self.assertFalse(result['scientific_full_scope_accepted'])
        value['original_processes']['supervisor_pid']['start_ticks'] = 999999
        self.assertTrue(accept(value, launch, bootstrap_repetitions=8)['scientific_full_scope_accepted'])

    def test_changed_frame_scores_aggregate_original_outcome_or_warm_trace_refused(self):
        original, launch = fixture()
        for kind in ('score', 'aggregate', 'outcome', 'warm'):
            value = copy.deepcopy(original)
            if kind == 'score':
                row = next(r for r in value['final']['rows'] if 'LPIPS' in r)
                row['LPIPS']['reference_sha256'] = '0' * 64
            elif kind == 'aggregate': value['final']['grouped_statistics']['methods'][0]['full_registered_mean_LPIPS'] = .999
            elif kind == 'outcome': value['final']['rows'][21]['status'] = 'TEXT_REJECTED'
            else: value['final']['warm_repeat_controls'][2]['all_guided_outputs_equal'] = 36
            with self.assertRaises(ValueError): accept(value, launch, bootstrap_repetitions=8)

    def test_original_artifact_bytes_path_and93_RGB_denominator_refused(self):
        original, launch = fixture()
        for kind in ('bytes', 'path', 'RGB'):
            value = copy.deepcopy(original); row = value['final']['rows'][25]
            if kind == 'bytes': row['video_artifact']['bytes'] = 2
            elif kind == 'path': row['video_artifact']['path'] = '/FOREIGN/video.mp4'
            else: row['video_artifact']['decoded_rgb_sha256'].pop()
            with self.assertRaises(ValueError): accept(value, launch, bootstrap_repetitions=8)

    def test_foreign_GPU_job_is_independent_but_own_cost_or_origin_cannot_change(self):
        value, launch = fixture()
        value['pool']['jobs']['OTHER_REGISTERED_JOB'] = dict(status='RESERVED_OR_RUNNING',
            billed_limit_GPUh=2., gpu_uuid='GPU-SYNTHETIC-OTHER')
        value['pool'].update(BudgetPool.accounting(value['pool']))
        value['compute_apps'] = 'GPU-SYNTHETIC-OTHER, 12345\n'
        self.assertTrue(accept(value, launch, bootstrap_repetitions=8)['scientific_full_scope_accepted'])
        for kind in ('cost', 'origin', 'ownlease'):
            changed = copy.deepcopy(value)
            if kind == 'cost': changed['pool']['jobs'][RUN]['actual_GPUh'] = 2.
            elif kind == 'origin':
                changed['pool']['origin_used_gpu_hours'] = 1.
                changed['pool'].update(BudgetPool.accounting(changed['pool']))
            else: changed['own_UUID_lock_free'] = False
            with self.assertRaises(ValueError): accept(changed, launch, bootstrap_repetitions=8)

    def test_CPU_failure_remains_cpu_repair_without_GPU_rerun(self):
        value, launch = fixture()
        value['final']['status'] = 'N07_SHARED180_CPU_TECHNICAL_FAILURE_FULL_SCOPE_RETAINED'
        value['final']['CPU_terminal_error'] = 'SYNTHETIC_METRIC_RESOURCE_UNAVAILABLE'
        value['post_exit']['exit_code'] = 1
        result = accept(value, launch, bootstrap_repetitions=8)
        self.assertFalse(result['scientific_full_scope_accepted'])
        self.assertTrue(result['no_GPU_relaunch_authorized'])
        self.assertEqual(result['actual_GPUh'], 1.)

    def test_one_original_video_rejection_is_registered_missingness_not_full_success(self):
        value, launch = fixture()
        original = next(r for r in value['runner']['runs'][40:] if r['method'] == 'A_NO_P')
        row = next(r for r in value['final']['rows'] if r['id'] == original['id'])
        removed = row.pop('video_artifact')['path']; row.pop('decoded_video'); row.pop('LPIPS')
        original.update(status='VIDEO_REJECTED', video_path=None)
        row.update(status='VIDEO_REJECTED', video_path=None, endpoint_audit='NOT_APPLICABLE_VIDEO_REJECTION_RETAINED',
                   LPIPS_missing_reason='ORIGINAL_CANDIDATE_UNAVAILABLE_OR_AUDIT_FAILED')
        value['final']['artifact_inventory'] = [a for a in value['final']['artifact_inventory'] if a['path'] != removed]
        from wcomr.frozen_shared_post_r1 import summarize
        value['final'].update(summarize(value['final'], value['bound_inputs'], observed_paths=180,
                                       child_exit_code=0, bootstrap_repetitions=8))
        result = accept(value, launch, bootstrap_repetitions=8)
        self.assertFalse(result['scientific_full_scope_accepted'])
        self.assertTrue(result['scientific_available_cohorts_with_registered_missingness'])
        self.assertEqual(result['scored_scientific_videos'], 159)
        self.assertEqual(result['original_status_counts']['VIDEO_REJECTED'], 1)


if __name__ == '__main__': unittest.main()
