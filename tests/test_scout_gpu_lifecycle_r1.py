"""Lifecycle decision/control fixtures, never research tensors or GPU results."""
import ast
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

from wcomr.scout_gpu_lifecycle_r1 import (counts, RUNS, audit_registered_rows, repeat_and_prefix,
    validate_authority, alive, freeze_cal_gate, DEPENDENCIES, accept_terminal)
from wcomr.scout_sampling_r1 import matrix, plans, TIMING
from wcomr.gpu_budget_pool_v2 import DeviceLease, BudgetPool

ROOT = Path(__file__).resolve().parents[1]


def fixture(kind):
    c = json.loads((ROOT/('configs/wc_scout_'+kind.lower()+'_production_entry_r1_20261018.json')).read_text())
    rows = []
    for p in matrix(kind, [r['name'] for r in c['requests']]):
        mask = plans(kind)[p['method']]; native = p['method'] == 'NATIVE35'
        actions = None if native else ['DD' if a == 'D' else 'CC' for a in mask]
        hist = [] if native else [dict(action='DD' if a == 'D' else 'CC', teacher_calls=0,
            P_updates_true_D_or_zero_risk_RA_anchor=False, true_D_before=0, true_D_after=0,
            A_readout=dict(teacher_calls=0, extra_deep_blocks=0, readout_action=a, shared_alpha=1 if a == 'A' else 0, extra_heads=0)) for a in mask]
        rows.append(dict(p, status='COMPLETE', solver_steps=36, guided_pairs=36, audit=p['section']=='WARMUP',
            in_timing_guided_copies=36 if p['section']=='WARMUP' else 0, in_timing_hashes=0, research_checkpoints=0,
            write_deferred_after_main_timer=True, core_seconds=1., timing_claim=TIMING, semantic_plan=list(mask),
            actions=actions, source_history=hist, A_history=None if native else [],
            request_memory_lifecycle=dict(owners_alive_after=0, observed_owners=0 if native else 1),
            scout_observation=dict(observer_enabled=p['observer'], probe_copies=4, velocity_copies=2, teacher_calls=0,
                copies_and_hashes_in_request_clock=True, online_gate_executed=False,
                pre_action_input_sha256='state', actual_timestep=1),
            final_latent_sha256=p['method'], decoded_video=dict(RGB_sha256=p['method']), endpoint_audit='PASS',
            guided_step_sha256=['common']*20+[p['method']]*16,
            vector_audit='PASS' if p['observer'] else None,
            scout_vector_metadata={k: dict(tree_sha256=k, shape=[1], dtype='float') for k in ('p20_c','p20_u','p21_c','p21_u')}))
    return c, rows


def terminal_fixture(kind):
    """Declared scalar-only lifecycle fixture; no inference or quality evidence."""
    c, rows = fixture(kind); h = '0'*64
    for r in rows:
        r['raw_model_audit']='PASS'; r['decoded_video'].update(frames=93, probe=dict(HWC=[432,768,3]))
        if r['section']=='TIMED' and r['method']!='NATIVE35':
            r['video_artifact']=dict(path='/fixture/'+r['id'],sha256=h,bytes=1)
            r['LPIPS']=dict(reference_sha256=h,candidate_sha256=h,frames=93,pts=list(range(93)),
                            frame_distances=[.1]*93,mean_LPIPS=sum([.1]*93)/93)
    L=dict(kind=kind,scope_counts=counts(kind),run_id=RUNS[kind],gpu_uuid='GPU-fixture',source_revision='life',
        launch_id='launch',supervisor_pid=1,registration_sha256=h,entry_registration_sha256=h,
        production_CPU_sha256=h,config_sha256=h,next_check_not_before_unix=0)
    bill={k:L[k] for k in ('launch_id','run_id','source_revision','gpu_uuid','scope_counts')}
    bill.update(wall_seconds=3600.,actual_GPUh=1.,billed_limit_GPUh=2.5 if kind=='CAL12' else 4.5)
    job=dict(L,status='SETTLED',actual_GPUh=1.,billing_sha256=h)
    pool=dict(schema='WC_GPU_BUDGET_POOL_V2',cap_gpu_hours=226.,origin_used_gpu_hours=79.99637737158223,
              origin_gpu_jobs_launched=0,jobs={L['run_id']:job});pool.update(BudgetPool.accounting(pool))
    memory=[dict(id=r['id'],**r['request_memory_lifecycle']) for r in rows]
    refs=[dict(scene=r['name'],video_artifact=dict(path='/ref/'+r['name'],sha256=h,bytes=1)) for r in c['requests']]
    final=dict(rows=rows,request_memory_records=memory,Native_reference_bindings=refs,**repeat_and_prefix(c,rows))
    if kind=='CAL12':
        final['old_CAL_bindings']=[dict(fixture=True)]*12
        final['old_prefix_controls']=[dict(method=m,compared_outputs=21,status='PASS_OLD_COMMON_PREFIX',
            old_guided_step_sha256=next(r for r in rows if r['id']=='warm_1_'+m)['guided_step_sha256']) for m in plans(kind)]
    v=dict(launch=L,mode='terminal',observed_unix=1,original_live_handles=dict(supervisor=False,runner=False,post=False),
        registration_sha256=h,registration=dict(source_revision='life',payload_sha256={'fixture':h},runtime_source_sha256={'fixture':h}),
        payload_actual_sha256={'fixture':h},runtime_actual_sha256={'fixture':h},config=c,
        entry_registration=dict(payload_sha256={'entry':h}),entry_payload_actual_sha256={'entry':h},entry_registration_sha256=h,
        runner=dict(source_revision='c1c95ce0c598fb7839b0b89f4a69bd45c8aef7c9',config_sha256=h,runs=copy.deepcopy(rows),request_memory_records=memory),
        entry_config_file_sha256=h,billing=bill,billing_sha256=h,pool=pool,
        supervisor=dict(billing_sha256=h,child_pid=2,child_exit_code=0),own_GPU='GPU-fixture, RTX A6000, 0, 0',
        compute_apps='',own_UUID_lock_free=True,final=final,post_exit=dict(exit_code=0,final_result_sha256=h),final_sha256=h,
        original_artifacts={r['video_artifact']['path']:dict(sha256=h,bytes=1) for r in rows if 'video_artifact' in r})
    return v,L


class ScoutLifecycle(unittest.TestCase):
    def test_whole_two_scopes_and_native_ownership(self):
        for kind in RUNS:
            c, rows = fixture(kind); audit_registered_rows(c, rows); repeat_and_prefix(c, rows)
            self.assertEqual(len(rows), counts(kind)['total_paths'])
            self.assertEqual(sum(r['section']=='TIMED' for r in rows), counts(kind)['formal_paths'])

    def test_scope_missing_duplicate_and_reorder_refused(self):
        c, r = fixture('CAL12')
        for changed in (r[:-1], r+[r[0]], list(reversed(r))):
            with self.assertRaises(ValueError): audit_registered_rows(c, changed)

    def test_refused_and_not_reached_positions_remain(self):
        c, rows = fixture('BANK24'); rows[0] = dict(rows[0], status='TEXT_REJECTED')
        rows[-1] = dict(rows[-1], status='NOT_REACHED_RETAINED'); audit_registered_rows(c, rows)
        self.assertEqual(len(rows), 24)

    def test_actual_owner_leak_refused(self):
        c, rows = fixture('CAL12'); rows[0]['request_memory_lifecycle']['owners_alive_after']=1
        with self.assertRaises(ValueError): audit_registered_rows(c, rows)

    def test_native_cannot_inherit_cache_owner(self):
        c, rows = fixture('BANK24'); next(r for r in rows if r['method']=='NATIVE35')['request_memory_lifecycle']['observed_owners']=1
        with self.assertRaises(ValueError): audit_registered_rows(c, rows)

    def test_cannot_add_current_teacher_or_C_head(self):
        for name in ('teacher', 'head', 'anchor'):
            c, rows = fixture('CAL12'); h=next(h for h in rows[0]['source_history'] if h['action']=='CC')
            if name=='teacher': h['teacher_calls']=1
            if name=='head': h['A_readout']['extra_heads']=1
            if name=='anchor': h['true_D_after']=1
            with self.subTest(name=name), self.assertRaises(ValueError): audit_registered_rows(c, rows)

    def test_observer_changed_one_guided_step_refused(self):
        c, rows = fixture('CAL12'); next(r for r in rows if r['id']=='warm_2_G01_LATE_A')['guided_step_sha256'][35]='different'
        with self.assertRaises(ValueError): repeat_and_prefix(c, rows)

    def test_formal_A_history_not_ignored(self):
        c, rows = fixture('CAL12'); next(r for r in rows if r['id']=='timed_0_G01_LATE_A')['A_history']=[1]
        with self.assertRaises(ValueError): repeat_and_prefix(c, rows)

    def test_same_state_requires_input_and_all_four_probes(self):
        for field in ('hash','probe'):
            c, rows = fixture('BANK24'); r=next(r for r in rows if r['id']=='timed_0_A21')
            if field=='hash': r['scout_observation']['pre_action_input_sha256']='other'
            else: r['scout_vector_metadata']['p20_u']['tree_sha256']='other'
            with self.subTest(field=field), self.assertRaises(ValueError): repeat_and_prefix(c, rows)

    def test_PID_reuse_not_original_alive(self):
        a=dict(pid=1,start_ticks=10); b=dict(pid=1,start_ticks=11,state='S')
        self.assertFalse(alive(a,b)); b['start_ticks']=10; self.assertTrue(alive(a,b))
        b['state']='Z'; self.assertFalse(alive(a,b))

    def test_v2_UUID_lease_collision_and_release(self):
        with tempfile.TemporaryDirectory() as directory:
            a,b=DeviceLease(directory,'GPU-fixture'),DeviceLease(directory,'GPU-fixture')
            with a:
                with self.assertRaises(BlockingIOError): b.acquire()
            with b: pass

    def test_v2_accounting_is_additive_not_reservations_as_expense(self):
        pool=dict(schema='WC_GPU_BUDGET_POOL_V2',cap_gpu_hours=226.,origin_used_gpu_hours=79.99637737158223,
                  origin_gpu_jobs_launched=1,jobs=dict(a=dict(status='SETTLED',actual_GPUh=2.),
                     b=dict(status='RESERVED_OR_RUNNING',billed_limit_GPUh=4.5,gpu_uuid='GPU-fixture')))
        v=BudgetPool.accounting(pool); self.assertEqual(v['used_gpu_hours'],81.99637737158223)
        self.assertEqual(v['reserved_gpu_hours'],4.5)

    def test_authority_exact_quote_scope_and_under12(self):
        c,_=fixture('CAL12'); d='0'*64
        a=dict(direct_user_authorization=True,user_reply_quote='approved',autonomy_exclusive_upper_GPUh=12,
            kind='CAL12',run_id=RUNS['CAL12'],scope_counts=counts('CAL12'),registration_sha256=d,
            independent_CPU_acceptance_sha256=d,production_CPU_sha256=d,dependency_sha256=d,
            bound_config_fingerprint=hashlib.sha256(json.dumps(c,sort_keys=True).encode()).hexdigest(),
            forecast_GPUh=c['forecast_complete_GPUh'],billed_limit_GPUh=c['billed_limit_GPUh'],cumulative_cap_GPUh=226,
            budget_origin_used_GPUh=79.99637737158223,upstream_originals_verified=True,upstream_capture_sha256=d,launch_id='id',gpu_uuid='GPU-fixture')
        validate_authority(a,c,d,d,d,d)
        for key,value in [('billed_limit_GPUh',12.),('upstream_originals_verified',False),('scope_counts',{})]:
            bad=dict(a,**{key:value})
            with self.subTest(key=key), self.assertRaises(ValueError): validate_authority(bad,c,d,d,d,d)

    def test_cal_gate_fit_uses_exact_four_CAL_only(self):
        c,rows=fixture('CAL12'); chosen=[r for r in rows if r['section']=='TIMED' and r['method']=='G01_LATE_A']
        for n,r in enumerate(chosen): r['visible_probe_delta']=dict(guided_probe_delta_RMS=float(n+1))
        v=dict(final=dict(rows=rows)); g=freeze_cal_gate(v,dict(kind='CAL12',full_protocol_accepted=True))
        self.assertEqual(g['mu_RMS'],2.5); self.assertEqual(g['direction'],'LARGER_Z_KEEP_D')
        self.assertFalse(g['DEV_used_for_fit'])
        with self.assertRaises(ValueError): freeze_cal_gate(dict(final=dict(rows=chosen[:-1])),dict(kind='CAL12',full_protocol_accepted=True))

    def test_all_new_production_sources_parse_and_entry_stage_retained(self):
        for name in ('supervise_wc_scout_gpu_r1.py','watch_wc_scout_post_cpu_r1.py','postprocess_wc_scout_gpu_r1.py',
                     'launch_wc_scout_gpu_r1.py','capture_wc_scout_gpu_r1.py','analyze_wc_scout_gpu_r1.py'):
            ast.parse((ROOT/'scripts'/name).read_text())
        s=(ROOT/'scripts/supervise_wc_scout_gpu_r1.py').read_text()
        self.assertIn("str(Path(meta['entry_stage'])/'scripts/run_wc_scout_production_entry_r1.py')",s)
        self.assertIn("'--source-revision', meta['entry_source_revision']",s)

    def test_deferred_remote_programs_compile(self):
        for filename, attribute in [('launch_wc_scout_gpu_r1.py','REMOTE'),('capture_wc_scout_gpu_r1.py','REMOTE'),
                                    ('wc_scout_gpu_lifecycle_cpu_r1.py','BOOT'),('capture_wc_scout_gpu_lifecycle_cpu_r1.py','CODE')]:
            spec=importlib.util.spec_from_file_location('fixture_cli_'+filename[:-3],ROOT/'scripts'/filename)
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            ast.parse(getattr(module,attribute))

    def test_scalar_terminal_fixtures_accept_both_complete_scopes(self):
        for kind in RUNS:
            v,L=terminal_fixture(kind);a=accept_terminal(v,L)
            self.assertTrue(a['full_protocol_accepted']);self.assertEqual(a['registered_paths'],counts(kind)['total_paths'])
            self.assertEqual(a['actual_GPUh'],1.)

    def test_terminal_frame_mean_not_trusted(self):
        v,L=terminal_fixture('BANK24')
        row=next(r for r in v['final']['rows'] if 'LPIPS' in r)
        row['LPIPS']['mean_LPIPS']=.2
        # Keep GPU runner's actual data separate from post-only score fields.
        for r in v['runner']['runs']:r.pop('LPIPS',None)
        with self.assertRaises(ValueError):accept_terminal(v,L)

    def test_terminal_cost_and_current_UUID_release_not_summary_flags(self):
        for field in ('cost','lock','pid'):
            v,L=terminal_fixture('CAL12')
            if field=='cost':v['billing']['actual_GPUh']=.5
            if field=='lock':v['own_UUID_lock_free']=False
            if field=='pid':v['compute_apps']='GPU-fixture, 2'
            with self.subTest(field=field), self.assertRaises(ValueError):accept_terminal(v,L)

    def test_terminal_reject_missing_original_bytes(self):
        v,L=terminal_fixture('BANK24');v['original_artifacts'].clear()
        with self.assertRaises(ValueError):accept_terminal(v,L)


if __name__ == '__main__': unittest.main()
