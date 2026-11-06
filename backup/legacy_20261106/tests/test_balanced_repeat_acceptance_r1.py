"""Independent reconstructed full40 acceptance; every receipt is synthetic."""
import copy
import importlib.util
from pathlib import Path
import unittest

from wcomr.balanced_repeat_acceptance_r1 import accept
from wcomr.balanced_repeat_execution_r1 import observed_timers
from wcomr.balanced_repeat_post_r1 import GPU_TERMINAL_STATUS, repeat_controls, summarize
from wcomr.balanced_repeat_production_r1 import RUN
from wcomr.frozen_shared_production_r1 import fingerprint
from wcomr.gpu_budget_pool_v2 import BudgetPool, SCHEMA


def module(name):
    path = Path(__file__).with_name(name + '.py')
    spec = importlib.util.spec_from_file_location('synthetic_accept_' + name, path)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result); return result


def fixture():
    post = module('test_balanced_repeat_post_r1'); bound, runs = post.fixture()
    cpu_helper = module('test_balanced_repeat_cpu_acceptance_r1'); cpu = cpu_helper.fixture()
    config = cpu['files']['config']['data']; proof = cpu['files']['proof']['data']; registration = cpu['registration']
    root = '/SYNTHETIC_PROJECT/outputs/' + RUN
    for row in runs:
        row['video_path'] = root + '/' + row['id'] + '/video.mp4'
        row['final_artifact']['path'] = root + '/' + row['id'] + '/final.pt'
        if row['section'] == 'WARMUP': row['warm_guided_artifact']['path'] = root + '/' + row['id'] + '/warm.pt'
        row['core_seconds'] = {'FULL_NATIVE': 3., 'WORLD_CACHE': 2.5, 'RA_CFG_CACHE': 2.,
                               'GCR_EFFICIENT': 1.5, 'CPA_HIGH_FIDELITY': 2.8}[row['slot']]
        row['guarded_pipeline_without_write_seconds'] = row['core_seconds'] + .2
        row['timing_intervals'] = observed_timers(row)
    final = post.evaluate(bound, runs)
    final['artifact_inventory'] = [{k: info[k] for k in ('path', 'bytes', 'sha256')}
        for row in final['rows'] for name in ('final_artifact', 'warm_guided_artifact', 'video_artifact')
        if (info := row.get(name)) is not None]
    own = dict(pid=1001, start_ticks=10010); child = dict(pid=1003, start_ticks=10030); watcher = dict(pid=1002, start_ticks=10020)
    source = registration['source_revision']
    authority = dict(source_revision=source, config_sha256=cpu['files']['config']['sha256'],
        production_CPU_sha256=cpu['files']['proof']['sha256'], bound_timing_fingerprint=fingerprint(bound),
        bound_input_fingerprint=fingerprint(bound), scope_counts=config['scope_counts'], whole_card_run=RUN,
        gpu_uuid='GPU-SYNTHETIC-OWN', forecast_complete_GPUh=config['forecast_complete_GPUh'],
        billed_limit_GPUh=config['billed_limit_GPUh'], cumulative_cap_GPUh=config['cumulative_cap_GPUh'],
        budget_origin_used_GPUh=config['budget_origin_used_GPUh'], direct_user_authorization=True,
        user_reply_quote='SYNTHETIC_NOT_REAL_AUTHORIZATION', launch_id='SYNTHETIC_NOT_LAUNCHED', kind='STANDING_STRICT_UNDER12')
    launch = dict(run_id=RUN, source_revision=source, launch_id=authority['launch_id'], gpu_uuid=authority['gpu_uuid'],
        scope_counts=config['scope_counts'], config_sha256=authority['config_sha256'], registration_sha256=cpu['registration_sha256'],
        production_CPU_sha256=authority['production_CPU_sha256'], authorization_sha256='8' * 64,
        bound_timing_fingerprint=fingerprint(bound), bound_input_fingerprint=fingerprint(bound),
        supervisor_pid=own['pid'], supervisor_identity=own, post_watcher_pid=watcher['pid'], post_watcher_identity=watcher,
        next_check_not_before_unix=4000.)
    supervisor = dict(status=GPU_TERMINAL_STATUS, pid=own['pid'], start_ticks=own['start_ticks'], child_pid=child['pid'],
        child_identity=child, child_exit_code=0, billing_sha256='9' * 64, runner_sha256='a' * 64,
        actual_GPUh=1., started_unix=100., **{k: launch[k] for k in ('source_revision', 'launch_id', 'run_id', 'gpu_uuid',
        'scope_counts', 'config_sha256', 'bound_timing_fingerprint', 'registration_sha256')})
    bill = dict(status='N08_FULL40_ACTUAL_GPU_BILL', original_output_root_available=True, actual_GPUh=1., wall_seconds=3600.,
        ended_unix=3700., billed_limit_GPUh=config['billed_limit_GPUh'],
        **{k: launch[k] for k in ('source_revision', 'launch_id', 'run_id', 'gpu_uuid', 'scope_counts', 'config_sha256')})
    job = dict(status='SETTLED', kind='V2', actual_GPUh=1., billing_sha256='9' * 64,
        forecast_GPUh=config['forecast_complete_GPUh'], billed_limit_GPUh=config['billed_limit_GPUh'], reserved_unix=90., settled_unix=3710.,
        **{k: launch[k] for k in ('source_revision', 'launch_id', 'gpu_uuid', 'scope_counts', 'config_sha256',
                                'production_CPU_sha256', 'bound_input_fingerprint', 'bound_timing_fingerprint')})
    pool = dict(schema=SCHEMA, cap_gpu_hours=config['cumulative_cap_GPUh'], origin_used_gpu_hours=config['budget_origin_used_GPUh'],
                origin_gpu_jobs_launched=1, jobs={RUN: job}, events=[]); pool.update(BudgetPool.accounting(pool))
    def observation(section, at, identity=None):
        return dict(section=section, id=identity, unix=at, other_registered_GPU_jobs_active=[], project_CPU_metric_entrypoints=[],
                    observation_only_not_entire_interval_cleanliness=True)
    resources = [observation('BEFORE_LOAD', 120.)]
    for i, row in enumerate(bound['execution_plan']):
        resources.extend([observation('BEFORE_PATH', 150. + i * 50, row['id']), observation('AFTER_PATH', 151. + i * 50, row['id'])])
    resources.append(observation('AFTER_ALL', 2200.))
    runner = dict(runs=runs, source_revision=source, config_sha256=launch['config_sha256'], bound_timing_fingerprint=fingerprint(bound),
        scope_counts=config['scope_counts'], bindings=bound['bindings'], matrix=bound['execution_plan'], model_load_calls=1,
        model_loads_completed=1, resource_observations=resources)
    final.update(source_revision=source, config_sha256=launch['config_sha256'], bound_timing_fingerprint=fingerprint(bound),
        scope_counts=config['scope_counts'], GPU_supervisor=copy.deepcopy(supervisor), CUDA_initialized=False,
        resource_boundary_observations=copy.deepcopy(resources))
    result = dict(status='N08_FULL40_ORIGINAL_ONCE_CAPTURE', mode='terminal', observed_unix=5000., launch=launch,
        registration=registration, registration_sha256=cpu['registration_sha256'], payload_verified=cpu['payload_verified'],
        config=config, config_sha256=launch['config_sha256'], production_CPU=proof, production_CPU_sha256=launch['production_CPU_sha256'],
        production_CPU_bundle=cpu['files']['bundle']['data'], authorization=authority, authorization_sha256=launch['authorization_sha256'],
        supervisor=supervisor, runner=runner, runner_sha256='a' * 64, billing=bill, billing_sha256='9' * 64, pool=pool,
        own_UUID_lock_free=True, own_GPU=launch['gpu_uuid'] + ', NVIDIA RTX A6000, 24', compute_apps='', output_root=root,
        original_processes={k: dict(pid=v['pid'], start_ticks=None, state=None) for k, v in (
            ('supervisor_pid', own), ('child_pid', child), ('post_watcher_pid', watcher))},
        post_exit=dict(status='N08_FULL40_POST_CPU_TERMINAL', exit_code=0, original_supervisor=own,
            source_revision=source, config_sha256=launch['config_sha256'], final_result_sha256='b' * 64), final=final, final_sha256='b' * 64)
    for key in ('timing_protocol', 'shared_config', 'method_freeze'):
        result[key] = cpu['files'][key]['data']; result[key + '_sha256'] = cpu['files'][key]['sha256']
    return result, launch, bound


class IndependentFull40Acceptance(unittest.TestCase):
    def test_complete30_reconstructs_rounds_actual_cost_and_recorded_resources(self):
        value, launch, _ = fixture(); original = copy.deepcopy(value); result = accept(value, launch)
        self.assertEqual(value, original)
        self.assertTrue(result['scientific_full_scope_accepted']); self.assertTrue(result['stable_repeated_clean_speed_claim'])
        self.assertEqual(result['scored_scientific_videos'], 30)
        ratio = next(r for r in result['timing_statistics']['contrasts'] if r['candidate'] == 'GCR_EFFICIENT' and r['baseline'] == 'FULL_NATIVE')
        self.assertEqual(ratio['full_registered_speedup'], 2.)
        self.assertEqual(result['resource_controls']['observed_boundary_observations'], 82)

    def test_source_payload_original_load_or_early_time_cannot_change(self):
        for kind in ('source', 'payload', 'load', 'time'):
            value, launch, _ = fixture()
            if kind == 'source': value['supervisor']['source_revision'] = 'OTHER'
            elif kind == 'payload': value['payload_verified'].pop(next(iter(value['payload_verified'])))
            elif kind == 'load': value['runner']['model_load_calls'] = 2
            else: value['observed_unix'] = 3999.
            with self.subTest(kind=kind), self.assertRaises(ValueError): accept(value, launch)

    def test_live_original_is_wait_and_reused_PID_is_not_the_original(self):
        value, launch, _ = fixture(); value['original_processes']['post_watcher_pid'].update(state='R', start_ticks=10020)
        self.assertIn('STILL_RUNNING', accept(value, launch)['status'])
        value['original_processes']['post_watcher_pid']['start_ticks'] = 10021
        self.assertTrue(accept(value, launch)['scientific_full_scope_accepted'])

    def test_frame_score_aggregate_original_outcome_and_artifact_corruption_refused(self):
        for kind in ('score', 'aggregate', 'outcome', 'artifact', 'RGB', 'timer'):
            value, launch, _ = fixture(); row = next(r for r in value['final']['rows'] if r['section'] == 'TIMED')
            if kind == 'score': row['LPIPS']['reference_sha256'] = '0' * 64
            elif kind == 'aggregate': value['final']['timing_statistics']['contrasts'][0]['full_registered_speedup'] = 99.
            elif kind == 'outcome': row['status'] = 'TEXT_REJECTED'
            elif kind == 'artifact': row['video_artifact']['bytes'] += 1
            elif kind == 'RGB': row['video_artifact']['decoded_rgb_sha256'].pop()
            else: row['timing_intervals']['core_text_denoise_VAE_seconds'] += 1.
            with self.subTest(kind=kind), self.assertRaises(ValueError): accept(value, launch)

    def test_later_other_GPU_is_independent_but_transient_overlap_invalidates_only_clean_claim(self):
        value, launch, _ = fixture()
        value['pool']['jobs']['OTHER_GPU_JOB'] = dict(status='RESERVED_OR_RUNNING', billed_limit_GPUh=2.,
            gpu_uuid='GPU-SYNTHETIC-OTHER', reserved_unix=4500.)
        value['pool'].update(BudgetPool.accounting(value['pool'])); value['compute_apps'] = 'GPU-SYNTHETIC-OTHER, 2001\n'
        self.assertTrue(accept(value, launch)['stable_repeated_clean_speed_claim'])
        value['pool']['jobs']['OTHER_GPU_JOB']['reserved_unix'] = 500.
        result = accept(value, launch)
        self.assertTrue(result['full_raw_and_fidelity_scope_accepted']); self.assertFalse(result['stable_repeated_clean_speed_claim'])
        self.assertEqual(result['scored_scientific_videos'], 30)

    def test_original_budget_origin_settlement_and_own_UUID_cannot_change(self):
        for kind in ('origin', 'cost', 'lock'):
            value, launch, _ = fixture()
            if kind == 'origin': value['pool']['origin_used_gpu_hours'] = 0.; value['pool'].update(BudgetPool.accounting(value['pool']))
            elif kind == 'cost': value['pool']['jobs'][RUN]['actual_GPUh'] = 2.
            else: value['own_UUID_lock_free'] = False
            with self.subTest(kind=kind), self.assertRaises(ValueError): accept(value, launch)

    def test_CPU_failure_is_readonly_repair_not_GPU_relaunch(self):
        value, launch, _ = fixture(); value['final'].update(status='N08_FULL40_CPU_TECHNICAL_FAILURE_FULL_SCOPE_RETAINED',
                                                         CPU_terminal_error='SYNTHETIC_METRIC_LOAD_FAILURE')
        value['post_exit']['exit_code'] = 1
        result = accept(value, launch)
        self.assertFalse(result['scientific_full_scope_accepted']); self.assertTrue(result['no_GPU_relaunch_authorized'])
        self.assertEqual(result['actual_GPUh'], 1.)

    def test_original_rejection_preserves_all40_and_available29_scores(self):
        value, launch, bound = fixture()
        original = next(r for r in value['runner']['runs'] if r['section'] == 'TIMED' and r['slot'] == 'GCR_EFFICIENT')
        row = next(r for r in value['final']['rows'] if r['id'] == original['id'])
        removed = row.pop('video_artifact')['path']; row.pop('decoded_video'); row.pop('LPIPS')
        original.update(status='VIDEO_REJECTED', video_path=None)
        row.update(status='VIDEO_REJECTED', video_path=None, endpoint_audit='NOT_APPLICABLE_VIDEO_REJECTION_RETAINED')
        final = value['final']; final['artifact_inventory'] = [r for r in final['artifact_inventory'] if r['path'] != removed]
        warm, repeated, failed = repeat_controls(final['rows'], bound)
        self.assertEqual(failed, []); final.update(warm_trace_controls=warm, formal_to_warm_controls=repeated)
        final.update(summarize(final, bound, observed_paths=40, child_exit_code=0))
        result = accept(value, launch)
        self.assertFalse(result['scientific_full_scope_accepted']); self.assertEqual(result['scored_scientific_videos'], 29)
        self.assertEqual(result['original_status_counts']['VIDEO_REJECTED'], 1)


if __name__ == '__main__': unittest.main()
