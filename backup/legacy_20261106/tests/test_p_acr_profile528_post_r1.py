"""Formula corruption, missing scope and rejected-parent controls on CPU."""
import copy
import json
from pathlib import Path
import unittest

import torch
from wcomr.p_acr_profile20_owner_r1 import trial_plan
from wcomr.p_acr_profile528_post_r1 import audit_point
from wcomr.p_acr_profile528_production_r1 import matrix,validate_parent

ROOT=Path(__file__).resolve().parents[1]


def fixture():
    c=json.loads((ROOT/'configs/wc_p_acr_local12_profile528_production_r1_20261015.json').read_text())
    cf=json.loads((ROOT/c['references']['coefficients']['ref']).read_text())
    p=c['states'][0];shape=(1,2,1,2,2)
    zero=torch.zeros(shape);A=(torch.full(shape,.07),torch.full(shape,.03));D=(zero.clone(),zero.clone())
    x={'C':(torch.full(shape,.09),torch.full(shape,.04)),'A':A,'D':D,'actual_latent':zero.clone(),'timestep':torch.tensor([.2])}
    g=cf['cells']['D_EARLY'];ts=[]
    for name,rep,section in trial_plan():
        t={'kind':name,'repetition':rep,'section':section,'actual_heads':None,'actual_Linear_observers':None,
            'observers':{'pure_observers_suspended':9},'per_action_compiler_preparation_is_charged':True,
            'snapshot_hash_restore_IO_outside_timer':True,'full_pair_seconds':.2,'action_preparation_seconds':.01,
            'charged_action_seconds':.21000000000000002}
        if name in ('Pc','Pu'):
            coefficient=g['Pc_eta' if name=='Pc' else 'Pu_zeta'];side=0 if name=='Pc' else 1;delta=D[side]-A[side]
            y=(D[0],A[1]+coefficient*delta) if name=='Pc' else (A[0]+coefficient*delta,D[1])
            x[name+'_REP'+str(rep)]=tuple(v.clone() for v in y)
            x['FC_STYLE_'+name+'_REP'+str(rep)]=tuple(v.clone() for v in D)
            t.update(coefficient=coefficient,actual_dense_branches=1,paid_prefixes=2,source_refresh=False)
        ts.append(t)
    record={'point':p,'coefficients_fingerprint':c['coefficients_fingerprint'],
        'parent_pre_action':(11,'D',11,0.,0.,0,11,11,False),'parent_readout':'D','all20_trials_restored':True,
        'candidate_or_teacher_committed_to_parent':False,'serial_restores':[None]*20,'trials':ts,'sigma':.2}
    return x,record,c,cf,{'joint_decision':{'step':12,'gain':1.2}},shape


class FullPointAudit(unittest.TestCase):
    def test_complete_actual_formula_and_Gram(self):
        out=audit_point(*fixture())
        self.assertTrue(out['all40_point_tensors_read'])
        self.assertEqual(out['losses']['D']['absolute_guided_MSE'],0)
        self.assertEqual(len(out['formal_charged_seconds']['Pc']),3)

    def test_corrupted_uncomputed_branch_refused(self):
        args=fixture();args[0]['Pu_REP2'][0].add_(.02)
        with self.assertRaisesRegex(ValueError,'actual innovation'):audit_point(*args)

    def test_missing_candidate_and_uncharged_setup_refused(self):
        args=fixture();args[0].pop('Pc_REP3')
        with self.assertRaises(ValueError):audit_point(*args)
        args=fixture();args[1]['trials'][0]['charged_action_seconds']=.2
        with self.assertRaises(ValueError):audit_point(*args)

    def test_missing_restore_and_source_refresh_refused(self):
        args=fixture();args[1]['serial_restores'].pop()
        with self.assertRaises(ValueError):audit_point(*args)
        args=fixture();args[1]['trials'][3]['source_refresh']=True
        with self.assertRaises(ValueError):audit_point(*args)

    def test_all8_rejected_positions_are_preserved(self):
        c=fixture()[2];plan=matrix(c);self.assertEqual(len(plan),8)
        for p in plan:
            validate_parent({**p,'status':'TEXT_REJECTED','solver_steps':0,'guided_pairs':0},p)
        p=plan[1]
        bad={**p,'status':'VIDEO_REJECTED','solver_steps':35,'guided_pairs':35,'guided_sha256':[],
            'method_fingerprint':c['H1_fingerprint'],'parent_vectors':{'path':'bad'}}
        with self.assertRaises(ValueError):validate_parent(bad,p)


if __name__=='__main__':unittest.main()
