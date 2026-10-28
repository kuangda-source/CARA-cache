"""Q wire correctness, S refusal, and pinned C/RF small-tensor integration."""
import copy
import unittest

import torch

from wcomr.sq_codec_r1 import (encode_tensor, decode_tensor, tensor_info, encode_pair,
    transform_roundtrip, packed_source, readout_C, storage_bytes, leave_one_prompt_out)
from wcomr.sq_risk_r1 import (branch_moments, aggregate, coverage, F19, TARGETS,
    PROTECTED, exchanges, choose, histories)


class SQTests(unittest.TestCase):
    def test_signed_nibbles_rounding_zero_tail_and_corruption(self):
        x=torch.zeros((2,129));x[0,:7]=torch.tensor([-7.,-1.,-.5,0.,.5,1.,7.]);x[1,128]=3
        blob=encode_tensor(x,4);i=tensor_info(blob);y=decode_tensor(blob)
        self.assertEqual(i['tail_channels_per_token'],127)
        self.assertTrue(torch.equal(y[0,:7],torch.tensor([-7.,-1.,0.,0.,0.,1.,7.])))
        self.assertEqual(y[1,128],3)
        self.assertEqual(len(blob),i['header_bytes']+i['scale_bytes']+i['payload_bytes']+i['padding_bytes'])
        self.assertEqual(len(blob)%64,0)
        broken=bytearray(blob);broken[i['payload_offset']]=0x88
        with self.assertRaises(ValueError):decode_tensor(bytes(broken))
        with self.assertRaises(ValueError):decode_tensor(blob[:-1])
        with self.assertRaises(ValueError):encode_tensor(torch.tensor([float('nan')]),8)

    def test_int8_bounds_and_original_dtype_pair_bytes(self):
        generator=torch.Generator().manual_seed(20261028)
        for dtype in (torch.float16,torch.bfloat16,torch.float32):
            c=torch.randn((1,2,3,4,257),generator=generator).to(dtype)
            u=(c.float()*.8+.1).to(dtype)
            by_rate={}
            for basis in ('I','M'):
                for bits in ((8,8),(4,8),(8,4)):
                    p=encode_pair(c,u,basis=basis,bits=bits);out=p.decode();i=p.info()
                    self.assertTrue(all(x.shape==c.shape and x.dtype==dtype and torch.isfinite(x).all() for x in out))
                    self.assertEqual(len(p.wire),i['pair_header_bytes']+sum(j['actual_bytes'] for j in i['components']))
                    by_rate.setdefault(sum(bits),set()).add(len(p.wire))
            self.assertTrue(all(len(x)==1 for x in by_rate.values()))
            a,b=transform_roundtrip(c,u)
            self.assertTrue(torch.allclose(a,c,atol=.01,rtol=.01) and torch.allclose(b,u,atol=.01,rtol=.01))
        x=torch.randn(3,256,generator=generator);b=encode_tensor(x,8);y=decode_tensor(b)
        bound=x.reshape(-1,128).abs().amax(-1)/127/2+1e-6
        self.assertTrue(((x-y).reshape(-1,128).abs().amax(-1)<=bound).all())

    def test_full_window_aliases_stale_entry_and_denominator(self):
        r=[torch.ones((1,1,1,1,129))*i for i in (1,2,3)]
        p=torch.zeros_like(r[0]);source=[dict(residual=r[-1],residual_window=r,probe=p,probe_window=[p,p]) for _ in (0,1)]
        before=copy.deepcopy(source)
        view,info,pairs=packed_source(source,basis='I',bits=(8,8))
        self.assertEqual(info['window_slots'],3);self.assertEqual(info['unique_pairs'],3)
        self.assertEqual(info['slot_to_pair'],[0,1,2,2])
        self.assertIs(view[0]['residual'],view[0]['residual_window'][-1])
        self.assertEqual(info['raw_r_unique_storage_bytes'],storage_bytes(r))
        self.assertEqual(storage_bytes(source),storage_bytes(r)+storage_bytes(p))
        for s,b in zip(source,before):self.assertTrue(torch.equal(s['residual'],b['residual']))

    def test_source_bound_C_warp_head_RF_for_all_codecs(self):
        from test_scout_readout_v22 import fixture
        from wcomr.full_sampling import CompleteStateRoundtrip
        for flow in (False,True):
            k,a=fixture(flow=flow,step=33)
            source=[dict(probe=b.probe,residual=b.residual,probe_window=[o.probe,b.probe],residual_window=[o.residual,b.residual]) for o,b in a['anchors']]
            snapshot=CompleteStateRoundtrip(k.net,k.model.sample_scheduler,a['pair_inputs'][1]);before=snapshot.fingerprint()
            outputs=[]
            for basis in ('I','M'):
                for bits in ((8,8),(4,8),(8,4)):
                    v,info=readout_C(k,source=source,current=a['current'],pair_inputs=a['pair_inputs'],basis=basis,bits=bits)
                    self.assertEqual(snapshot.fingerprint(),before)
                    self.assertTrue(all(torch.isfinite(x).all() for x in v))
                    self.assertTrue(torch.equal(v[0][:,:,0],torch.full_like(v[0][:,:,0],.8)))
                    outputs.append(v)
            self.assertTrue(any(not torch.equal(outputs[0][0],v[0]) for v in outputs[1:]))

    def test_FP64_cross_cancellation_and_zero_teacher(self):
        d=torch.ones((2,3));c=d+7;u=d+8
        v=branch_moments((c,u),(d,d))
        self.assertEqual(v['CFG'],0);self.assertGreater(v['DIAG'],0)
        for seed in (1,2,3):
            g=torch.Generator().manual_seed(seed);xs=[torch.randn(2,7,generator=g) for _ in range(4)]
            v=branch_moments(tuple(xs[:2]),tuple(xs[2:]));self.assertLessEqual(v['identity_abs_error'],v['identity_tolerance'])
        with self.assertRaises(ValueError):branch_moments((d,d),(d*0,d*0))

    def test_missing_parent_or_step_refuses_s_plan(self):
        prompts=('a','b');parents={'Shared25-C':.5,'F19-C':.5}
        rows=[dict(prompt=p,parent=h,step=t,moments={'normalized':dict(BR=1.,DIAG=2.,CFG=3.)}) for p in prompts for h in parents for t in TARGETS]
        self.assertTrue(coverage(rows,prompts,tuple(parents))['complete'])
        out=aggregate(rows,prompts=prompts,parent_weights=parents,propagation={t:1. for t in TARGETS})
        self.assertEqual(out['CFG'][22],3)
        with self.assertRaisesRegex(ValueError,'INCOMPLETE'):aggregate(rows[:-1],prompts=prompts,parent_weights=parents,propagation={t:1. for t in TARGETS})
        with self.assertRaises(ValueError):coverage(rows+[rows[0]],prompts,tuple(parents))

    def test_common_exchanges_support_tie_and_equivalence(self):
        cs=exchanges(max_age=6,supports_history=lambda *h:True)
        self.assertGreater(len(cs),0)
        for c in cs:
            self.assertEqual(len(c['dense']),19);self.assertTrue(set(PROTECTED)<=set(c['dense']))
            self.assertTrue(all(t-last<=6 for t,old,last in c['history']))
        self.assertEqual(exchanges(max_age=6,supports_history=lambda *h:False),[])
        out=choose({j:{t:1. for t in TARGETS} for j in ('BR','DIAG','CFG')},cs,execution_identity={'fixture':True})
        self.assertEqual(len(out['equivalence_classes']),1)
        self.assertTrue(all(v['dense']==list(F19) for v in out['choices'].values()))
        with self.assertRaises(ValueError):choose({'CFG':{22:1}},cs,execution_identity={'fixture':True})

    def test_lopo_selects_one_training_direction_and_refuses_raw(self):
        rows=[]
        for p in ('a','b'):
            for s in (22,23):
                for d in ((4,8),(8,4)):
                    score=1. if (p=='a')==(d==(4,8)) else 10.
                    rows.append(dict(prompt=p,state=s,basis='M',rate='R12',bits=list(d),BR=score,CFG=score,
                                     actual_bytes=512,coordinate='ACTUAL_C_POST_RF'))
        folds=leave_one_prompt_out(rows,basis='M',rate='R12',objective='CFG')
        self.assertTrue(all(f['heldout_mean']==10 for f in folds))
        with self.assertRaises(ValueError):leave_one_prompt_out([dict(r,coordinate='RAW') for r in rows],basis='M',rate='R12',objective='CFG')
        rows[0]['actual_bytes']+=64
        with self.assertRaises(ValueError):leave_one_prompt_out(rows,basis='M',rate='R12',objective='CFG')


if __name__ == '__main__':
    unittest.main()
