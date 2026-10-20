import copy
import math
import os
from pathlib import Path
from types import SimpleNamespace
import unittest

import torch
from einops import rearrange

from wcomr import policy_interval_assets_r1 as A
from wcomr.policy_interval_readout_r1 import compile_skip, reduce_outputs, guided

ROOT=Path(__file__).resolve().parents[1]


class ScopeAndPrices(unittest.TestCase):
    def test_all1624_cells_without_skipping_legal_long_ages(self):
        rows=A.cells()
        self.assertEqual(len(rows),406)
        self.assertIn((7,35),rows)
        self.assertEqual(len(set(rows)),406)
        self.assertFalse(any(t in A.PROFILE['protected_dense'] for _,t in rows))
        self.assertEqual(sum(len(order) for s,t in rows for _,order in A.rounds_for(s,t))*5,13020)

    def test_complete14_native_off_on_and_warm(self):
        rows=A.matrix();self.assertEqual(len(rows),14)
        for scene in A.SCENES:
            self.assertEqual([r['mode'] for r in rows if r['scene']==scene and r['section']=='FORMAL'],['NATIVE','CONTROL','COLLECT'])
        self.assertEqual(sum(r['observer'] for r in rows),5)

    def test_failure_and_unreached_denominator(self):
        first={**A.matrix()[0],'status':'TECH_FAILED','error':'original'}
        rows=A.full_rows([first]);self.assertEqual(len(rows),14)
        self.assertEqual(rows[0]['error'],'original')
        self.assertTrue(all(r['status']=='NOT_REACHED' for r in rows[1:]))
        with self.assertRaises(ValueError):A.full_rows([{**first,'scene':'another'}])

    def test_quote_all_warm_trials_transfer_raw_post_not_fake_unit_prices(self):
        q=A.complete_quote(max_whole_request_seconds=320,load_seconds=90,
            readout_inclusive_planning_seconds=1.3,latent_elements=1990656,hidden_elements=63700992)
        self.assertEqual(q['terms_seconds']['all_readout_trials'],13020*1.3)
        self.assertGreater(q['raw_tensor_planning_bytes'],40*1024**3)
        self.assertGreater(q['terms_seconds']['source_transfer_planning'],0)
        self.assertFalse(q['action_unit_prices_measured'])
        self.assertEqual(q['specific_whole_card_confirmation_required'],q['billed_limit_GPUh']>=12)

    def test_no_unknown_zero_price_forecast(self):
        for value in (0,float('nan'),-1):
            with self.assertRaises(ValueError):A.complete_quote(max_whole_request_seconds=300,
                load_seconds=30,readout_inclusive_planning_seconds=value,latent_elements=10,hidden_elements=20)

    def test_no_foreign_fit_identity(self):
        with self.assertRaises(ValueError):A.matrix(A.SCENES[:-1]+('new',))

    def test_whole12_is_not_under12_authority(self):
        from wcomr.policy_interval_assets_lifecycle_r1 import validate_authority
        c=dict(forecast_complete_GPUh=9.9,billed_limit_GPUh=12.)
        auth=dict(run_id=A.RUN,scope_counts=A.COUNTS,registration_sha256='a'*64,
            production_CPU_sha256='b'*64,independent_CPU_acceptance_sha256='c'*64,
            forecast_GPUh=9.9,billed_limit_GPUh=12.,cumulative_cap_GPUh=226,
            budget_origin_used_GPUh=79.99637737158223,direct_user_authorization=True,
            user_reply_quote='strictly below12 authorized',launch_id='new',gpu_uuid='GPU-new')
        with self.assertRaisesRegex(ValueError,'At or above12'):validate_authority(auth,c,'a'*64,'b'*64,'c'*64)
        auth['specific_whole_card_approved']=True
        validate_authority(auth,c,'a'*64,'b'*64,'c'*64)
        with self.assertRaises(ValueError):validate_authority(auth,c,'d'*64,'b'*64,'c'*64)

    def test_under12_standing_authority_and_original_cap_preserved(self):
        from wcomr.policy_interval_assets_lifecycle_r1 import validate_authority
        c=dict(forecast_complete_GPUh=9.,billed_limit_GPUh=11.75)
        auth=dict(run_id=A.RUN,scope_counts=A.COUNTS,registration_sha256='a'*64,
            production_CPU_sha256='b'*64,independent_CPU_acceptance_sha256='c'*64,
            forecast_GPUh=9.,billed_limit_GPUh=11.75,cumulative_cap_GPUh=226,
            budget_origin_used_GPUh=79.99637737158223,direct_user_authorization=True,
            user_reply_quote='direct authorized',launch_id='new',gpu_uuid='GPU-new')
        validate_authority(auth,c,'a'*64,'b'*64,'c'*64)
        auth['cumulative_cap_GPUh']=227
        with self.assertRaises(ValueError):validate_authority(auth,c,'a'*64,'b'*64,'c'*64)


class ActualCoordinateControls(unittest.TestCase):
    def test_raw_guided_quadratic_and_real_half_not_hidden_interpolation(self):
        torch.manual_seed(14)
        C=tuple(torch.randn(1,2,1,3,3) for _ in range(2))
        P=tuple(torch.randn_like(v) for v in C);D=tuple(torch.randn_like(v) for v in C)
        H=tuple(a+.5*(b-a) for a,b in zip(C,P))
        stats,raw=reduce_outputs(C,P,D,H)
        e=guided(C).double()-guided(D).double()
        self.assertEqual(stats['e2'],e.square().mean().item())
        self.assertLess(abs(stats['actual_half_MSE']-stats['quadratic_half_MSE']),1e-4)
        self.assertEqual(set(raw),{'C','Phi','A_HALF'})

    def test_nonfinite_output_kept_as_failure(self):
        v=(torch.full((1,2,1,2,2),float('nan')),torch.ones(1,2,1,2,2))
        with self.assertRaises(ValueError):reduce_outputs(v,v,v,v)

    def test_wrong_half_fusion_refused(self):
        C=(torch.zeros(1,1,1,1,1),torch.zeros(1,1,1,1,1))
        P=tuple(v+1 for v in C);wrong=tuple(v+10 for v in C)
        with self.assertRaises(ValueError):reduce_outputs(C,P,C,wrong)

    def test_source_exact_C_extrapolation_and_only_shadow_cache_mutated(self):
        runtime=Path(os.environ.get('WC_POLICY_ASSETS_RUNTIME',ROOT/'cache/runtime'))
        if not runtime.exists():self.skipTest('Pinned runtime supplied by production CPU command')
        ns=dict(torch=torch,rearrange=rearrange,
            compute_optimal_gamma=lambda x,y:torch.tensor(1.5),
            estimate_optical_flow=lambda a,b,scale_factor:None,
            warp_feature=lambda x,f:x)
        fn,proof=compile_skip(runtime,ns)
        self.assertTrue(proof['full_C_skip_branch_inverse_AST_equal'])
        for flow in (False,True):
            original=torch.ones(1,1,2,2,2);probe=original*2
            source=torch.ones_like(original)*4;older=source*.5
            proxy=SimpleNamespace(cnt=0,residual_cache=[source,None],
                previous_input=[None,None],previous_internal_states=[None,None],
                residual_window=[[older,source],[]],
                probe_residual_window=[[older,source],[]],worldcache_osi_enabled=True,
                worldcache_flow_enabled=flow,worldcache_flow_scale=2.)
            before=source.clone();pre,result=fn(proxy,original,probe,1)
            self.assertTrue(torch.equal(pre,original+older+1.5*(source-older)))
            self.assertTrue(torch.equal(source,before))
            self.assertIs(proxy.previous_input[0],original)


if __name__=='__main__':unittest.main()
