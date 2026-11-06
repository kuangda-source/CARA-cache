"""Decision-level negative controls for CPU continuation contracts."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from wcomr.policy_generator_r1.continuation_preparation import (
    TIME_BOUNDARY, generator_input, history_points, history_matrix,
    native_candidate_counts, select_native_by_time)
from wcomr.policy_generator_r1.interval_grammar import Profile, Edge, compile_policy

ROOT = Path(__file__).resolve().parents[1]


class ExposureClassificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import importlib.util
        spec=importlib.util.spec_from_file_location('select_exposure',ROOT/'scripts/audit_cara_cal_select_exposure_r1.py')
        cls.module=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.module)

    def test_registered_catalog_and_prompt_mentions_are_not_model_runs(self):
        refs=['reports/dataset_source_group_audit_20260930.json',
              'reports/wc_paper_N07_all1044_original_input_bytes_CPU_inventory_20261016.json',
              'reports/cara_ordered_preparation_existing_terminal_continuation_20261022.json',
              'reports/wc_four_card_BANK24_retry2_halfway_closed_terminal_preserved_20261022.json']
        for ref in refs:self.assertIsNotNone(self.module.metadata_reason(ref,json.loads((ROOT/ref).read_text())))

    def test_execution_identity_cannot_hide_in_planning_receipt(self):
        ref='reports/wc_four_card_BANK24_retry2_halfway_closed_terminal_preserved_20261022.json'
        d=json.loads((ROOT/ref).read_text());d['runs']=[{'name':'industry_057_generated'}]
        self.assertIsNone(self.module.metadata_reason(ref,d))

    def test_metadata_inventory_with_model_run_not_exempt(self):
        ref='reports/wc_paper_N07_all1044_original_input_bytes_CPU_inventory_20261016.json'
        d=json.loads((ROOT/ref).read_text());d['sampler_or_model_or_guardrails_run']=True
        self.assertIsNone(self.module.metadata_reason(ref,d))


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.profile = Profile(36, tuple(range(1,8))+(36,), 28, 2, 1, 'CPU_FIXTURE')

    def policy(self, ds):
        return compile_policy(self.profile, [Edge(a,b) for a,b in zip(ds,ds[1:]+[37])])

    def test_sparse_windows_and_preceding_shadow_are_selected_without_outcomes(self):
        p = self.policy(list(range(1,8))+[10,16,26,36])
        r = history_points(self.profile,p)
        self.assertEqual([(x['previous'],x['source'],x['target']) for x in r['points']], [(7,10,11),(10,16,17),(16,26,27)])
        self.assertEqual(r['shadow_pair_steps'], [9,11,15,17,25,27])
        self.assertEqual(r['paired_readouts'],18)

    def test_empty_bins_not_filled_by_changing_schedule(self):
        p = self.policy(list(range(1,8))+[36])
        r = history_points(self.profile,p)
        self.assertEqual(len(r['empty_bins']),3)
        self.assertEqual(r['shadow_D_pairs'],0)

    def test_mutated_compiled_action_is_rejected(self):
        p = self.policy(list(range(1,8))+[10,16,26,36]);p['actions'][10]='D'
        with self.assertRaises(ValueError): history_points(self.profile,p)

    def test_alias_dedup_preserves_roles_and_costs(self):
        p = self.policy(list(range(1,8))+[10,16,26,36])
        r = history_matrix(self.profile, {'CARA':p,'SIMPLE':p}, ['a','b'])
        self.assertEqual((r['physical_paths'],r['formal_paths'],r['total_CFG_calls']),(3,2,252))
        self.assertEqual(r['rows'][0]['roles'],['CARA','SIMPLE'])

    def test_full_two_policy_bound(self):
        p = self.policy(list(range(1,8))+[10,16,26,36])
        q = self.policy(list(range(1,8))+[11,17,27,36])
        r = history_matrix(self.profile, {'CARA':p,'SIMPLE':q}, ['a','b'])
        self.assertEqual((r['physical_paths'],r['formal_paths'],r['shadow_guided_pairs'],r['total_CFG_calls']), (6,4,36,504))


class NativeTests(unittest.TestCase):
    def setUp(self):
        self.candidates=[25,26,27,28];self.members=['a','b','c','d']
        self.rows=[dict(requested_steps=n,member=m,repeat=r,seconds=10.+(n-26),
            profile_identity='p',accepted=True,exclusive_acceptance_sha256='a'*64,timing_boundary=TIME_BOUNDARY)
            for n in self.candidates for m in self.members for r in (1,2,3)]

    def choose(self, rows=None, target=10.):
        return select_native_by_time(self.rows if rows is None else rows,candidates=self.candidates,
            members=self.members,target_seconds=target,profile_identity='p')

    def test_CPU_schedule_counts_not_requested_counts(self):
        schedules=[dict(requested_steps=n,actual_updates=n+1) for n in range(18,36)]
        r=native_candidate_counts(schedules,80,100)
        self.assertEqual(r['requested_steps'],[26,27,28,29])
        self.assertAlmostEqual(r['predicted_seconds']['28'],100*29/36)
        self.assertEqual(r['maximum_timing_paths'],56)

    def test_matched_selects_actual_time_only(self):
        self.assertEqual(self.choose()['selected_steps'],[26])

    def test_no_match_preserves_bracket_without_interpolation(self):
        r=self.choose(target=10.5)
        self.assertEqual(r['status'],'MEASURED_BRACKET_ONLY');self.assertEqual(r['selected_steps'],[26,27])

    def test_outside_range_not_called_match(self):
        self.assertEqual(self.choose(target=30)['status'],'NO_CAL_TIME_MATCH')

    def test_missing_repeat_fails(self):
        with self.assertRaises(ValueError):self.choose(self.rows[:-1])

    def test_duplicate_repeat_fails(self):
        with self.assertRaises(ValueError):self.choose(self.rows+[self.rows[0]])

    def test_quality_cannot_enter_step_selection(self):
        rows=copy.deepcopy(self.rows);rows[0]['LPIPS']=.1
        with self.assertRaises(ValueError):self.choose(rows)

    def test_wrong_profile_or_boundary_fails(self):
        for k,v in [('profile_identity','other'),('timing_boundary','CORE_ONLY'),('accepted',False)]:
            rows=copy.deepcopy(self.rows);rows[0][k]=v
            with self.assertRaises(ValueError):self.choose(rows)


class PinnedHistoryKernelTests(unittest.TestCase):
    def exercise(self, flow, osi):
        # Actual pinned WC skip/OSI/flow plus the actual ReadoutKernel.run;
        # explicit Toy head/RF and feature tensors. No model-trajectory claim.
        import ast
        from types import SimpleNamespace
        import torch
        import torch.nn.functional as F
        from einops import rearrange
        from wcomr.cfg_paired_probe_forward import _function, _compile, WC_PATH, WC_SHA
        from wcomr.policy_interval_readout_r1 import ReadoutKernel, compile_skip
        runtime=ROOT/'vendor/WorldCache/Models/Cosmos-Predict2.5'
        namespace=dict(torch=torch,F=F,rearrange=rearrange)
        for name in ('estimate_optical_flow','warp_feature','compute_optimal_gamma'):
            namespace[name]=_compile(_function(runtime,WC_PATH,WC_SHA,name),namespace,WC_PATH+'#'+name)
        original=_function(runtime,WC_PATH,WC_SHA,'worldcache_mini_train_dit_forward')
        nodes=[n for n in ast.walk(original) if isinstance(n,ast.If) and ast.unparse(n.test)==
               "getattr(self, 'worldcache_flow_enabled', False) and self.previous_input[current_idx] is not None"]
        self.assertEqual(len(nodes),1)
        warp=ast.parse('def candidate_warp(self,x_B_T_H_W_D,residual_x,T):\n current_idx=self.cnt%2\n return x_B_T_H_W_D').body[0]
        warp.body.insert(1,copy.deepcopy(nodes[0]))
        kernel=ReadoutKernel.__new__(ReadoutKernel)
        kernel.C,kernel.proof=compile_skip(runtime,namespace)
        kernel.warp=_compile(warp,namespace,WC_PATH+'#exact-warp')
        net=SimpleNamespace(worldcache_osi_enabled=osi,worldcache_flow_enabled=flow,worldcache_flow_scale=.5,
            final_layer=lambda x,*a,**kw:x+.01*x.square(),unpatchify=lambda x:x.movedim(-1,1))
        kernel.net=net;kernel.model=SimpleNamespace(net=net)
        kernel.to_velocity=lambda *a,**kw:kw['_supplied_net_output']*.9
        g=torch.Generator().manual_seed(417)
        tensor=lambda:torch.randn(1,2,8,8,4,generator=g)
        current=[];actual=[];adjacent=[]
        for _ in range(2):
            original=tensor();probe=original+tensor()
            current.append(dict(original=original,probe=probe,embedding=None,adaln=None))
            latest=tensor();residual=tensor()
            actual.append(dict(probe=latest,residual=residual,probe_window=[tensor(),latest],residual_window=[tensor(),residual]))
            adjacent.append(dict(probe=latest,residual=residual,probe_window=[tensor(),latest],residual_window=[tensor(),residual]))
        def fingerprints():
            tensors=[]
            def walk(x):
                if isinstance(x,torch.Tensor):tensors.append(hashlib.sha256(x.numpy().tobytes()).hexdigest())
                elif isinstance(x,dict):
                    for y in x.values():walk(y)
                elif isinstance(x,(tuple,list)):
                    for y in x:walk(y)
            walk((current,actual,adjacent));return tensors
        before=fingerprints();rng=torch.random.get_rng_state().clone()
        inputs=(None,torch.zeros(1),None,(None,None));outputs={}
        for label in ('C','A_HALF','A_ONE'):
            outputs[label]=[kernel.run(label,source=s,current=current,pair_inputs=inputs)[0] for s in (actual,adjacent)]
        self.assertTrue(all(torch.equal(a,b) for a,b in zip(*outputs['A_ONE'])))
        self.assertTrue(any(not torch.equal(a,b) for a,b in zip(*outputs['C'])))
        self.assertTrue(any(not torch.equal(a,b) for a,b in zip(*outputs['A_HALF'])))
        self.assertEqual(before,fingerprints());self.assertTrue(torch.equal(rng,torch.random.get_rng_state()))
        self.assertFalse(torch.cuda.is_initialized())

    def test_flow_off_osi_on(self):self.exercise(False,True)
    def test_flow_on_osi_on(self):self.exercise(True,True)
    def test_flow_off_osi_off(self):self.exercise(False,False)
    def test_flow_on_osi_off(self):self.exercise(True,False)


class BridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Labels are already accepted. Test prices/clocks are synthetic schema fixtures,
        # never written as a production bundle and never sent to the planner CLI.
        cap=json.loads((ROOT/'reports/wc_policy_assets_full1624_fourcard_GPU_terminal_20261023_0826.json').read_text())
        cls.old=cap['files']['bundle']['data']
        cls.oldraw=(json.dumps(cls.old,ensure_ascii=False,indent=2)+'\n').encode()
        assert hashlib.sha256(cls.oldraw).hexdigest()==cap['files']['bundle']['sha256']
        cls.oldaccept=json.loads((ROOT/'reports/wc_policy_assets_full1624_fourcard_GPU_accepted_20261023_0826.json').read_text())

    def setUp(self):
        self.new=copy.deepcopy(self.old)
        self.new.update(status='COMPLETE_OLD_LABELS_WITH_NEW_EXCLUSIVE_PRICES',clean_action_prices_accepted=True,
            exclusive_monitoring_accepted=True,original_label_bundle_sha256=hashlib.sha256(self.oldraw).hexdigest())
        self.accept=dict(status='FULL_PRICE_ORIGINALS_EXCLUSIVITY_AND_FINANCE_ACCEPTED',full_protocol_accepted=True,
            clean_action_prices_accepted=True,exclusive_monitoring={'accepted':True},
            original_label_bundle_sha256=hashlib.sha256(self.oldraw).hexdigest())
        self.clock=dict(status='CLEAN_NATIVE_CAL_COMPLETE_REQUEST_CLOCK_ACCEPTED',full_protocol_accepted=True,
            exclusive_monitoring_accepted=True,profile_identity=self.new['profile_identity'],timing_boundary=TIME_BOUNDARY,
            before_candidate_endpoints=True,rows=[dict(member=m,seed=0,requested_steps=35,actual_updates=36,
                accepted=True,seconds=100.,core_seconds=90.) for m in self.old['fit_members']])

    def build(self):
        raw=(json.dumps(self.new,ensure_ascii=False,indent=2)+'\n').encode()
        self.accept['replacement_bundle_sha256']=hashlib.sha256(raw).hexdigest()
        return generator_input(raw,self.accept,self.oldraw,self.oldaccept,self.clock)

    def test_consumer_schema_covers_full_graph_and_retains_teacher_boundary(self):
        r=self.build()
        self.assertEqual(r['budget_seconds'],80.)
        self.assertAlmostEqual(r['costs']['shared_seconds'],self.old['costs']['shared_seconds']+10.)
        self.assertEqual(len(r['statistics']),1624)
        self.assertIn('update',r['statistics'][0]);self.assertNotIn('target',r['statistics'][0])
        self.assertEqual(r['Q'],8);self.assertFalse(r['GPU_dispatch_ready'])

    def test_original_ready_flag_cannot_bypass_clean_price(self):
        self.new=copy.deepcopy(self.old)
        with self.assertRaises(ValueError):self.build()

    def test_bad_exclusivity_rejected(self):
        self.accept['exclusive_monitoring']['accepted']=False
        with self.assertRaises(ValueError):self.build()

    def test_changed_labels_rejected(self):
        self.new['statistics'][0]['e2']+=1
        with self.assertRaises(ValueError):self.build()

    def test_unclean_native_or_after_candidates_rejected(self):
        for k in ['exclusive_monitoring_accepted','before_candidate_endpoints']:
            original=self.clock[k];self.clock[k]=False
            with self.assertRaises(ValueError):self.build()
            self.clock[k]=original

    def test_replaced_or_missing_CAL_cannot_set_budget(self):
        self.clock['rows'][0]['member']='new_DEV'
        with self.assertRaises(ValueError):self.build()

    def test_changed_bytes_rejected(self):
        raw=json.dumps(self.new).encode();self.accept['replacement_bundle_sha256']='0'*64
        with self.assertRaises(ValueError):generator_input(raw,self.accept,self.oldraw,self.oldaccept,self.clock)


if __name__=='__main__': unittest.main()
