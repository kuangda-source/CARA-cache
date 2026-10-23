"""CPU-only acceptance faults; synthetic prices are never experimental results."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from wcomr.policy_price_terminal_r1 import accept,record,IMAGE,RUN
from wcomr.policy_price_refresh_contract_r1 import COUNTS,matrix
from wcomr.policy_price_refresh_audit_r1 import PROVENANCE,make_repriced_bundle
from wcomr.policy_interval_assets_r1 import ROUNDS
from wcomr.gpu_budget_pool_v2 import BudgetPool


def h(value):return hashlib.sha256(value.encode()).hexdigest()
def put(v,key,data):
    raw=json.dumps(data,sort_keys=True)
    v['files'][key]=dict(exists=True,raw_utf8=raw,bytes=len(raw.encode()),sha256=h(raw))
    return h(raw)


def fixture():
    old=json.loads((ROOT/'reports/wc_policy_assets_full1624_fourcard_GPU_terminal_20261023_0826.json').read_text())
    oldacc=json.loads((ROOT/'reports/wc_policy_assets_full1624_fourcard_GPU_accepted_20261023_0826.json').read_text())
    source=h('CPU fixture source');gpu='GPU-fixture';stage='/fixture'
    quote=json.loads((ROOT/'manifests/wc_policy_price_refresh_full1624_whole_quote_r1_20261023.json').read_text())
    oldhash={'runner.json':old['runner_sha256'],'post-results.json':old['files']['post']['sha256'],
             'generator-input-bundle.json':old['files']['bundle']['sha256']}
    config=dict(scope_counts=COUNTS,matrix=matrix(),accepted_original_files=oldhash,
                forecast_complete_GPUh=quote['forecast_complete_GPUh'],billed_limit_GPUh=11.5)
    v=dict(files={},original_live_handles=dict(guardian=False,supervisor=False,runner=False,post=False,container=False),
        own_UUID_lock_free=True,error_lines=[],artifact_checks=[],original_files_actual_sha256=oldhash)
    csha=put(v,'config',config);qsha=put(v,'quote',quote)
    reg=dict(source_revision=source,stage=stage,payload_sha256={'price-refresh-config.json':csha,'price-whole-quote.json':qsha},runtime_source_sha256={'fixture.py':h('runtime')})
    rsha=put(v,'registration',reg);v.update(payload_actual_sha256=reg['payload_sha256'],runtime_actual_sha256=reg['runtime_source_sha256'])
    identity=dict(pid=101,start_ticks=501,uid=1000);guardian=dict(pid=100,start_ticks=500)
    L=dict(run_id=RUN,launch_id='CPU-fixture',source_revision=source,gpu_uuid=gpu,stage=stage,
        scope_counts=COUNTS,billed_limit_GPUh=11.5,forecast_GPUh=quote['forecast_complete_GPUh'],config_sha256=csha,
        registration_sha256=rsha,guardian_identity=guardian)
    cpusha=put(v,'CPU_acceptance',dict(production_CPU_accepted=True,full_GPU_lifecycle_CPU_accepted=True,
        source_revision=source,registration_sha256=rsha))
    auth=dict(L,independent_CPU_acceptance_sha256=cpusha)
    L['authorization_sha256']=put(v,'authorization',auth);v['launch']=L
    v['container']=dict(state=dict(Running=False,ExitCode=0,OOMKilled=False),image=IMAGE,readonly_root=True,
        pid_mode='host',manifest_sha256=rsha,device_requests=[dict(DeviceIDs=[gpu])])
    def snap(active):return dict(gpu_uuid=gpu,compute_mode='Exclusive_Process',compute_apps=[dict(identity,gpu_uuid=gpu)] if active else [],mps_processes=[],observed_unix=100.)
    put(v,'guardian',dict(status='PRICE_HOST_GUARDIAN_TERMINAL',container_exit_code=0,gpu_uuid=gpu,
        identity=guardian,source_revision=source,mode_admission=dict(verified_snapshot=snap(False)),
        mode_restoration=dict(restored=True,status='PRIOR_MODE_RESTORED_IDLE')))
    put(v,'supervisor',dict(child_exit_code=0,post_exit_code=0,exclusive_monitor_accepted=True,
        child_identity=identity,**{k:L[k] for k in ('run_id','launch_id','source_revision','gpu_uuid','scope_counts')}))
    put(v,'ready',dict(identity=identity));put(v,'grant',dict(runner=identity,gpu_uuid=gpu,source_revision=source))
    rows=[dict(snapshot=snap(active),context_granted=active,monotonic_elapsed=elapsed) for active,elapsed in [(False,1.),(True,3.),(True,6.)]]
    v['monitor_raw_utf8']=''.join(json.dumps(r)+'\n' for r in rows)
    put(v,'monitor_final',dict(accepted=True,observations=len(rows),runner=identity,final_snapshot=snap(False),monitor_sha256=h(v['monitor_raw_utf8'])))
    bill=dict(wall_seconds=8.,actual_GPUh=8./3600,**{k:L[k] for k in ('run_id','launch_id','source_revision','gpu_uuid','scope_counts','billed_limit_GPUh')})
    bsha=put(v,'billing',bill);pool=copy.deepcopy(old['pool'])
    pool['jobs'][RUN]=dict(status='SETTLED',launch_id=L['launch_id'],actual_GPUh=bill['actual_GPUh'],billing_sha256=bsha)
    pool.update(BudgetPool.accounting(pool));v['pool']=pool
    originals={r['scene']:r for r in old['runner']['runs'] if r['mode']=='COLLECT' and r['section']=='FORMAL'}
    new=[]
    for p in matrix():
        prior=originals[p['scene']]
        r=dict(p,status='COMPLETE',solver_steps=36,guided_pairs=36,actions=['DD']*36,
            action_clocks=copy.deepcopy(prior['action_clocks']),core_seconds=prior['core_seconds'],
            request_memory_lifecycle=dict(owners_alive_after=0),guided_artifact=prior['guided_artifact'],final_latent_artifact=prior['final_latent_artifact'])
        if p['mode']=='PRICE':
            r['price_cells']=[dict(**{k:cell[k] for k in PROVENANCE},original_parent_hashes_equal=True,
                source_shadow_writes_parent=False,extra_deep_teacher_pairs=0,new_error_labels=0,raw_interval_tensors_written=0,
                price_trials=[dict(round=round_,action=action,seconds=.1,repeated_output_equal=True,
                    shared_prefix_included=False,restore_copy_hash_write_included=False,
                    boundary='AFTER_ALREADY_PAID_PROBES_THROUGH_WC_HEAD_RF_AND_SHARED_FUSION')
                    for round_,order in ROUNDS for action in order]) for cell in prior['interval_cells']]
        new.append(r)
        v['artifact_checks'].append(dict(id=p['id'],all93_old_Native_equal=True,RGB_frame_count=93,
            guided_sha256=r['guided_artifact']['sha256'],final_latent_sha256=r['final_latent_artifact']['sha256']))
    runner=dict(source_revision=source,registration_sha256=rsha,config_sha256=csha,model_loads=1,pid=identity['pid'],scope_counts=COUNTS,runs=new)
    runnersha=put(v,'runner',runner)
    bundle=make_repriced_bundle(new,old['runner']['runs'],old['files']['bundle']['data'],original_bundle_sha256=oldhash['generator-input-bundle.json'],
        prices_sha256=runnersha,profile_identity=rsha,exclusive_accepted=True,parity_accepted=True)
    bundlesha=put(v,'bundle',bundle)
    post=dict(runner_sha256=runnersha,registered_paths=10,error_rows=[],raw_parity_accepted=True,clean_action_prices_accepted=True,
        generator_input_bundle_sha256=bundlesha,rows=[dict(id=p['id'],accepted=True,all36_and_final_equal=True,all93_RGB_equal=True) for p in matrix()])
    postsha=put(v,'post',post);put(v,'post_exit',dict(exit_code=0,CPU_only_after_UUID_release=True,final_result_sha256=postsha))
    return v,old,oldacc


class TerminalAcceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.template,cls.old,cls.oldacc=fixture()
    def setUp(self):self.v=copy.deepcopy(self.template)
    def check(self):return accept(self.v,self.old,self.oldacc)
    def rewrite(self,key,fn):
        value=record(self.v,key);fn(value);put(self.v,key,value)
    def change_runner(self,fn):
        self.rewrite('runner',fn)
        self.rewrite('post',lambda p:p.update(runner_sha256=self.v['files']['runner']['sha256']))
        self.rewrite('post_exit',lambda p:p.update(final_result_sha256=self.v['files']['post']['sha256']))
    def change_journal(self,fn):
        rows=[json.loads(x) for x in self.v['monitor_raw_utf8'].splitlines()];fn(rows)
        self.v['monitor_raw_utf8']=''.join(json.dumps(x)+'\n' for x in rows)
        self.rewrite('monitor_final',lambda m:m.update(monitor_sha256=h(self.v['monitor_raw_utf8'])))
    def test_complete_full_domain_and_original_labels(self):
        r=self.check();self.assertTrue(r['clean_action_prices_accepted']);self.assertEqual(r['scope_counts']['total_readout_trials'],24360)
        self.assertFalse(r['endpoint_quality_or_deployment_speed_result'])
    def test_missing_non_nearest_repeat(self):
        self.change_runner(lambda r:r['runs'][1]['price_cells'][2]['price_trials'].pop())
        with self.assertRaisesRegex(ValueError,'All three balanced'):self.check()
    def test_changed_parent_hash(self):
        self.change_runner(lambda r:r['runs'][3]['price_cells'][2].update(older_source_sha256=h('wrong')))
        with self.assertRaisesRegex(ValueError,'provenance'):self.check()
    def test_missing_full_path(self):
        self.change_runner(lambda r:r['runs'].pop())
        with self.assertRaisesRegex(ValueError,'ten full'):self.check()
    def test_wrong_context_identity(self):
        self.change_journal(lambda rs:rs[1]['snapshot']['compute_apps'][0].update(start_ticks=999))
        with self.assertRaisesRegex(ValueError,'Exclusive journal'):self.check()
    def test_mps_rejects(self):
        self.change_journal(lambda rs:rs[1]['snapshot'].update(mps_processes=[999]))
        with self.assertRaisesRegex(ValueError,'Exclusive journal'):self.check()
    def test_monitor_gap_rejects(self):
        self.change_journal(lambda rs:rs[-1].update(monotonic_elapsed=50.))
        with self.assertRaisesRegex(ValueError,'gap exceeds'):self.check()
    def test_terminal_interval_not_covered(self):
        self.rewrite('billing',lambda b:b.update(wall_seconds=100.,actual_GPUh=100./3600))
        with self.assertRaisesRegex(ValueError,'terminal interval'):self.check()
    def test_bill_not_settled(self):
        self.v['pool']['jobs'][RUN]['status']='RESERVED_OR_RUNNING'
        with self.assertRaisesRegex(ValueError,'not settled'):self.check()
    def test_registered_source_changed(self):
        self.v['runtime_actual_sha256']={'fixture.py':h('changed')}
        with self.assertRaisesRegex(ValueError,'runtime changed'):self.check()
    def test_raw_bytes_changed(self):
        self.v['files']['runner']['raw_utf8']+=' '
        with self.assertRaisesRegex(ValueError,'captured bytes'):self.check()
    def test_all93_required(self):
        self.v['artifact_checks'][-1]['RGB_frame_count']=92
        with self.assertRaisesRegex(ValueError,'Raw artifact'):self.check()
    def test_original_native_mismatch(self):
        self.v['artifact_checks'][2]['all93_old_Native_equal']=False
        with self.assertRaisesRegex(ValueError,'Raw reference'):self.check()
    def test_deferred_restore_does_not_erase_clean_measurement(self):
        self.rewrite('guardian',lambda g:g.update(mode_restoration=dict(restored=False,status='RESTORE_DEFERRED_NO_FOREIGN_PROCESS_TOUCHED')))
        self.assertTrue(self.check()['mode_restoration_pending'])


class ControllerSyntax(unittest.TestCase):
    def test_remote_programs_compile_without_execution(self):
        import wc_four_card_price_refresh_gpu_r1 as ctl
        for code in [ctl.PREFLIGHT+'\nprint(json.dumps(value))',ctl.LAUNCH_PREFIX+ctl.PREFLIGHT.replace('p=json.load(sys.stdin);','')+ctl.LAUNCH_SUFFIX,ctl.CAPTURE_GPU]:
            compile(code,'CPU-only-remote-syntax','exec')
    def test_existing_once_only_intent_never_dispatches(self):
        import io,tempfile,contextlib
        from unittest.mock import patch
        import wc_four_card_price_refresh_gpu_r1 as ctl
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp,'price-GPU-intent.json').write_text(json.dumps(dict(launch_id='original',no_replay=True)))
            out=io.StringIO()
            namespace={}
            with patch('sys.stdin',io.StringIO(json.dumps(dict(CPU_launch=dict(stage=tmp))))),contextlib.redirect_stdout(out):
                try:
                    with self.assertRaises(SystemExit):exec(ctl.LAUNCH_PREFIX,namespace)
                finally:namespace['lock'].close()
            self.assertEqual(json.loads(out.getvalue())['original']['launch_id'],'original')
    def arguments(self,output):
        from types import SimpleNamespace
        return SimpleNamespace(cpu_capture=Path('reports/wc_policy_price_refresh_full1624_CPU_terminal_check_r1_20261023_0955.json'),
            cpu_acceptance=Path('reports/wc_policy_price_refresh_full1624_CPU_accepted_r1_20261023.json'),
            lifecycle_capture=Path('reports/wc_policy_price_refresh_lifecycle_CPU_capture_r1_20261023.json'),
            gpu_uuid='GPU-fixture',output=output)
    def test_busy_resource_never_requests_secret_or_dispatches(self):
        import tempfile
        from unittest.mock import patch
        import wc_four_card_price_refresh_gpu_r1 as ctl
        with tempfile.TemporaryDirectory() as tmp,patch.object(ctl,'published_controller',return_value=('CPU-fixture',{})),\
                patch.object(ctl,'ssh',return_value=dict(admissible=False,status='PRICE_RESOURCE_WAIT_NO_DISPATCH')) as ssh,\
                patch.object(ctl,'saved_secret') as secret:
            r=ctl.launch_gpu(self.arguments(Path(tmp)/'receipt.json'))
            self.assertFalse(r['admissible']);ssh.assert_called_once();secret.assert_not_called()
    def test_unknown_dispatch_retains_original_intent_without_secret(self):
        import tempfile
        from unittest.mock import patch
        import wc_four_card_price_refresh_gpu_r1 as ctl
        with tempfile.TemporaryDirectory() as tmp,patch.object(ctl,'published_controller',return_value=('CPU-fixture',{})),\
                patch.object(ctl,'ssh',side_effect=[dict(admissible=True),RuntimeError('synthetic-private-secret')]) as ssh,\
                patch.object(ctl,'saved_secret',return_value='synthetic-private-secret'):
            p=Path(tmp)/'receipt.json';r=ctl.launch_gpu(self.arguments(p))
            self.assertTrue(r['no_replay']);self.assertEqual(ssh.call_count,2)
            self.assertNotIn('synthetic-private-secret',p.read_text())
            self.assertNotIn('sudo_password',ssh.call_args.args[1])

if __name__=='__main__':unittest.main()
