"""Real tiny CPU tensors and temporary ledger; CUDA/scoring/processes are doubles."""
import copy
import gzip
import json
from pathlib import Path
import tempfile
import unittest

from test_runtime_profile40_supervision_r1 import fixture as supervision_fixture, run_supervisor
from test_runtime_profile40_post_r1 import fixture as tensor_fixture, rewrite_profile, video, SHAPE
from wcomr import runtime_profile40_post_r1 as post
from wcomr.runtime_profile40_acceptance_r1 import accept
from wcomr.runtime_profile40_cpu_acceptance_r1 import ACCEPTED_STATUS, PATTERNS
from wcomr.runtime_profile40_production_r1 import CONFIG, CPU_RESULT, RUN, COUNTS
from wcomr.frozen_shared_production_r1 import fingerprint, sha, write
from wcomr.gpu_budget_pool_v2 import BudgetPool


def fixture(root):
    config,bound,stage,registration,authority,pool=supervision_fixture(root,with_references=True)
    proof_sha=sha(stage/CPU_RESULT);bundle_sha=sha(stage/'N09-CPU-bundle-result.json')
    cpu_launch=json.loads((stage/'N09-production-CPU-launch.json').read_text())
    accepted=dict(status=ACCEPTED_STATUS,CPU_accepted=True,source_revision=registration['source_revision'],
        registration_sha256=sha(stage/'registration.json'),config_sha256=sha(stage/CONFIG),
        production_CPU_sha256=proof_sha,production_CPU_bundle_sha256=bundle_sha,
        original_CPU_identity=cpu_launch['identity'],bound_profile_fingerprint=fingerprint(bound),
        scope_counts=COUNTS,CPU_commands=len(PATTERNS)+1)
    write(stage/'N09-production-CPU-independent-acceptance.json',accepted)
    authority['independent_CPU_acceptance_sha256']=sha(stage/'N09-production-CPU-independent-acceptance.json')
    write(stage/'N09-launch-authorization.json',authority)
    supervisor,_,_=run_supervisor(root,(config,bound,stage,registration,authority,pool))
    output=root/'outputs'/RUN
    actual_bound,rows=tensor_fixture(output)
    assert actual_bound==bound
    # CUDA measurements are explicitly synthetic scalar data, never device calls.
    cell=dict(available=True,allocated_bytes=100,reserved_bytes=200,
        peak_allocated_bytes=100,peak_reserved_bytes=200)
    memory=dict(device='cuda:0',memory_before=cell,memory_after=dict(cell),
        peak_reset_before_request=True,request_profile_wall_seconds=100.)
    for row in rows:
        row['request_memory_observation']=copy.deepcopy(memory)
        if row['component_profile']:
            def change(value):
                value.update(copy.deepcopy(memory))
                for span in value['intervals']:span['CUDA_elapsed_ms']=span['CPU_seconds']*1000
                for group in value['components'].values():group['inclusive_CUDA_ms']=group['inclusive_CPU_seconds']*1000
            rewrite_profile(row,change)
    runner=dict(source_revision=registration['source_revision'],config_sha256=sha(stage/CONFIG),
        bound_profile_fingerprint=fingerprint(bound),scope_counts=COUNTS,matrix=bound['execution_plan'],
        bindings=bound['bindings'],runs=rows,model_load_calls=1,model_loads_completed=1,resource_observations=[])
    write(output/'runner.json',runner);supervisor['runner_sha256']=sha(output/'runner.json')
    write(output/'supervisor.json',supervisor)
    def inspector(row):
        observed=video(row);observed['video_artifact'].update(fps=16,width=768,height=432)
        return observed
    final=post.audit_rows(rows,bound,
        lambda r,p,b:post.audit_payload(r,p,b,output,expected_shape=SHAPE),inspector,
        lambda r,p:post.audit_profile(r,p,output),expected_device='cuda:0')
    controls,failures=post.parity_controls(final['rows'],bound)
    final.update(controls);final['audit_failures'].extend(failures)
    final.update(post.summarize(final,bound,observed_paths=40,child_exit_code=0))
    assert final['status']==post.COMPLETE_STATUS,final['audit_failures']
    final.update(source_revision=registration['source_revision'],config_sha256=sha(stage/CONFIG),
        bound_profile_fingerprint=fingerprint(bound),scope_counts=COUNTS,GPU_supervisor=supervisor,
        resource_boundary_observations=[],CUDA_initialized=False,
        artifact_inventory=[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size)
            for p in sorted(output.rglob('*')) if p.is_file()
            and (p.suffix in ('.pt','.mp4') or p.name=='profile-scalars.json')])
    write(stage/'N09-CPU-final-results.json',final)
    post_exit=dict(status='N09_FULL40_POST_CPU_TERMINAL',exit_code=0,source_revision=registration['source_revision'],
        original_supervisor={k:supervisor[k] for k in ('pid','start_ticks')},
        config_sha256=sha(stage/CONFIG),final_result_sha256=sha(stage/'N09-CPU-final-results.json'))
    write(stage/'N09-post-CPU-exit.json',post_exit)
    launch=dict(project=str(root),stage=str(stage),run_id=RUN,source_revision=registration['source_revision'],
        launch_id=authority['launch_id'],gpu_uuid=authority['gpu_uuid'],scope_counts=COUNTS,
        supervisor_identity=supervisor['supervisor_identity'],supervisor_pid=supervisor['pid'],
        post_watcher_identity=dict(pid=123456,start_ticks=1234560),post_watcher_pid=123456,
        registration_sha256=sha(stage/'registration.json'),config_sha256=sha(stage/CONFIG),
        bound_profile_fingerprint=fingerprint(bound),bound_input_fingerprint=fingerprint(bound),
        production_CPU_sha256=proof_sha,authorization_sha256=sha(stage/'N09-launch-authorization.json'),
        independent_CPU_acceptance_sha256=authority['independent_CPU_acceptance_sha256'],
        midpoint_health_not_before_unix=100.,next_check_not_before_unix=200.)
    captured=dict(status='N09_FULL40_ORIGINAL_ONCE_CAPTURE',mode='terminal',observed_unix=201.,launch=launch,
        registration=registration,registration_sha256=launch['registration_sha256'],output_root=str(output),
        payload_actual_sha256=registration['payload_sha256'],payload_verified={n:True for n in registration['payload_sha256']},
        pool=pool.read(),own_UUID_lock_exists=True,own_UUID_lock_free=True,
        own_GPU=authority['gpu_uuid']+', NVIDIA RTX A6000, 0',compute_apps='',
        original_processes={},profile_scalar_originals={})
    paths=dict(config=stage/CONFIG,authorization=stage/'N09-launch-authorization.json',
        independent_CPU_acceptance=stage/'N09-production-CPU-independent-acceptance.json',
        production_CPU=stage/CPU_RESULT,production_CPU_bundle=stage/'N09-CPU-bundle-result.json',
        production_CPU_launch=stage/'N09-production-CPU-launch.json',
        production_CPU_exit=stage/'N09-production-CPU-exit.json',
        supervisor=output/'supervisor.json',billing=output/'billing.json',runner=output/'runner.json',
        final=stage/'N09-CPU-final-results.json',post_exit=stage/'N09-post-CPU-exit.json')
    paths.update({name:stage/ref['ref'] for name,ref in config['references'].items()})
    for name,path in paths.items():
        raw=path.read_bytes();captured[name]=json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)
        captured[name+'_sha256']=sha(path)
    for row in rows:
        if row['component_profile']:
            info=row['component_profile_artifact'];path=Path(info['path'])
            captured['profile_scalar_originals'][str(path)]=dict(info,data=json.loads(path.read_text()),
                matches_original_row_identity=True)
    return captured,launch


class IndependentProfileAcceptanceControls(unittest.TestCase):
    def test_all40_original_scalars_all36_and_all93_reconstructed_without_clean_claim(self):
        with tempfile.TemporaryDirectory() as folder:
            value,launch=fixture(Path(folder).resolve());before=copy.deepcopy(value)
            observed=accept(value,launch)
            self.assertTrue(observed['full_runtime_profile_scope_accepted'])
            self.assertEqual((observed['original_runner_paths'],observed['accepted_93frame_videos'],
                observed['accepted_complete_mode_groups'],observed['independently_reconstructed_scalar_files']),
                (40,40,10,20))
            self.assertFalse(observed['clean_repeated_latency_claim'])
            self.assertFalse(observed['action_unit_prices_measured'])
            self.assertEqual(value,before)

    def test_health_early_or_original_live_handle_is_never_terminal_acceptance(self):
        with tempfile.TemporaryDirectory() as folder:
            original,launch=fixture(Path(folder).resolve())
            for mutate in (lambda v:v.update(mode='health'),lambda v:v.update(observed_unix=199.)):
                value=copy.deepcopy(original);mutate(value)
                with self.assertRaises(ValueError):accept(value,launch)
            value=copy.deepcopy(original)
            value['original_processes']['supervisor_pid']=dict(launch['supervisor_identity'],state='S')
            self.assertFalse(accept(value,launch)['full_runtime_profile_scope_accepted'])

    def test_changed_original_source_CPU_timer_or_billing_cannot_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            original,launch=fixture(Path(folder).resolve())
            mutations=(lambda v:v['payload_actual_sha256'].update({'injected':'0'*64}),
                lambda v:v['production_CPU_exit']['original_CPU_identity'].update(start_ticks=-1),
                lambda v:v['final']['rows'][1].update(core_seconds=-2),
                lambda v:v['billing'].update(actual_GPUh=50.),
                lambda v:v['final']['rows'][1]['video_artifact'].update(frames=92))
            for mutate in mutations:
                value=copy.deepcopy(original);mutate(value)
                with self.subTest(change=mutate),self.assertRaises(ValueError):accept(value,launch)

    def test_valid_profile_file_identity_does_not_excuse_forged_interval_summary(self):
        with tempfile.TemporaryDirectory() as folder:
            original,launch=fixture(Path(folder).resolve());value=copy.deepcopy(original)
            info=next(iter(value['profile_scalar_originals'].values()))
            info['data']['intervals'][2]['CUDA_elapsed_ms']+=3.
            with self.assertRaisesRegex(ValueError,'interval'):accept(value,launch)
            value=copy.deepcopy(original)
            row=next(r for r in value['final']['rows'] if r['component_profile'])
            row['audited_component_profile']['components']['solver_update']['calls']=999
            with self.assertRaises(ValueError):accept(value,launch)

    def test_other_GPU_is_allowed_own_lock_and_missing_CPU_are_retained(self):
        with tempfile.TemporaryDirectory() as folder:
            original,launch=fixture(Path(folder).resolve());value=copy.deepcopy(original)
            value['compute_apps']='GPU-OTHER, 100000\n'
            self.assertTrue(accept(value,launch)['full_runtime_profile_scope_accepted'])
            value['own_UUID_lock_free']=False
            self.assertFalse(accept(value,launch)['full_runtime_profile_scope_accepted'])
            value=copy.deepcopy(original);value.pop('final')
            self.assertFalse(accept(value,launch)['full_runtime_profile_scope_accepted'])

    def test_CPU_failure_keeps_whole_scope_finance_and_original_error(self):
        with tempfile.TemporaryDirectory() as folder:
            value,launch=fixture(Path(folder).resolve())
            value['final'].update(status='N09_FULL40_CPU_TECHNICAL_FAILURE_FULL_SCOPE_RETAINED',
                CPU_terminal_error='SYNTHETIC_CODEC_FAILURE')
            value['post_exit']['exit_code']=1
            observed=accept(value,launch)
            self.assertFalse(observed['full_runtime_profile_scope_accepted'])
            self.assertTrue(observed['own_GPU_finance_released'])
            self.assertEqual(observed['original_CPU_error'],'SYNTHETIC_CODEC_FAILURE')

    def test_actual_billed_overrun_is_preserved_even_if_all_profile_controls_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            value,launch=fixture(Path(folder).resolve())
            value['billing'].update(actual_GPUh=5.,wall_seconds=18000.)
            value['billing_sha256']='5'*64
            value['supervisor'].update(actual_GPUh=5.,billing_sha256='5'*64)
            value['final']['GPU_supervisor']=copy.deepcopy(value['supervisor'])
            value['pool']['jobs'][RUN].update(actual_GPUh=5.,billing_sha256='5'*64)
            value['pool'].update(BudgetPool.accounting(value['pool']))
            with self.assertRaisesRegex(ValueError,'overrun'):accept(value,launch)
            value['pool']['budget_overrun_recorded']=True
            observed=accept(value,launch)
            self.assertTrue(observed['full_runtime_profile_scope_accepted'])
            self.assertFalse(observed['full_protocol_including_billed_limit_accepted'])
            self.assertEqual(observed['actual_GPUh'],5.)


if __name__=='__main__':unittest.main()
