"""Independent teacher/feature corruption and full-denominator controls."""
import copy
from dataclasses import asdict
import json
from pathlib import Path
import unittest

import torch

from wcomr.w3_causal_trend_r1 import Observation,CausalHistory,SameStateLabel
from wcomr.w3_label64_post_r1 import audit_features,audit_label,full_matrix

ROOT=Path(__file__).resolve().parents[1]


def fixture():
    clock=json.loads((ROOT/'reports/wc_w3_actual_schedule_native_CPU_replay_20261015.json').read_text())['result']
    history=CausalHistory('CPU_fixture_not_real_teacher',0);rows=[];parent=[]
    for step in range(1,37):
        source=None if step==1 else 'D';birth=None if step==1 else step-1 if step<=25 else 24 if step<=31 else 31
        age=None if birth is None else step-birth;protected=step<=7 or step==36;supported=not protected and step!=31
        state=(birth,source,birth,0.,0.,0,step-1,step-1,False)
        state_id='CPU_INPUT_HASH:'+str(state)
        o=Observation('CPU_fixture_not_real_teacher',0,step,state_id,clock['sigmas'][step-1],source,
            source+':'+str(birth) if source else None,age,0.,None if protected else .1,None if protected else .12,
            .2 if supported else None,.5 if supported else None,protected,supported)
        fs=history.push(o)
        rows.append({'step':step,'observation':asdict(o),'scheduler_pre_step_index':None if step==1 else step-1,
            'sigma_from_actual_first_grid_before_init':step==1,'ordinary_parent_only':True,'teacher_or_candidate_history_used':False,
            'features':{m:{'names':f.names,'values':f.values,'prefix_steps':f.prefix_steps} for m,f in fs.items()}})
        parent.append({'joint_decision':{'step':step,'state_before':state,'gain':o.gain},'action':'DD','A_readout':{'readout_action':'D'}})
    shape=(1,2,1,2,2);zero=torch.zeros(shape)
    payload={'C':(torch.full(shape,.09),torch.full(shape,.04)),
        'A':(torch.full(shape,.06),torch.full(shape,.02)),'D':(zero.clone(),zero.clone()),
        'actual_latent':zero.clone(),'timestep':torch.tensor([clock['timesteps'][9]])}
    def mse(pair):return (8*pair[0]-7*pair[1]).double().square().mean().item()
    o=history.rows[9];label=SameStateLabel(o.prompt,0,10,o.state_id,mse(payload['C']),mse(payload['A']),'SYNTHETIC_CPU_INTERFACE')
    fs=audit_features(rows,clock=clock)
    restores=[[{'stage':stage,'original_pre_snapshot_two_copy_gate_unchanged':True}
        for stage in ('physical_restore','owned_restore')] for _ in range(3)]
    record={'step':10,'label_provenance':'SYNTHETIC_CPU_INTERFACE','candidate_or_teacher_committed_to_parent':False,
        'pre_action_state':parent[9]['joint_decision']['state_before'],'parent_action':'DD','parent_readout':'D',
        'feature_state_id':o.state_id,'input_sha256':'CPU_INPUT_HASH','sigma':o.sigma,
        'status':'COMPLETE_SAME_STATE_CAD_LABEL_NOT_ONLINE_VALUE','extra_pairs':3,
        'same_state_snapshot_and_parent_restore_verified':True,'teacher_never_used_in_feature_inputs':True,
        'serial_restores':restores,'trials':[{'kind':name,'actual_readout':name,
            'actual_action':'DD' if name=='D' else 'CC','full_pair_seconds':.1} for name in ('C','A','D')],
        'label':asdict(label),'gain_squared_targets':label.target(fs[9]['T1']).tolist(),'artifact':{'CPU_fixture':True}}
    return payload,record,fs,parent,shape,rows,clock


def run(args):return audit_label(*args[:4],expected_shape=args[4],provenance='SYNTHETIC_CPU_INTERFACE')


class IndependentLabels(unittest.TestCase):
    def test_raw_teacher_and_CFG_Gram_targets(self):
        result=run(fixture());self.assertTrue(result['all8_point_tensors_read'])
        self.assertEqual(result['losses']['D']['as_executed_guided_MSE'],0)
        self.assertFalse(result['source_refreshed'])

    def test_saved_label_or_actual_branch_corruption_is_refused(self):
        args=fixture();args[1]['label']['q_A']+=.01
        with self.assertRaisesRegex(ValueError,'raw A'):run(args)
        args=fixture();args[0]['C'][1].add_(.01)
        with self.assertRaisesRegex(ValueError,'raw C'):run(args)

    def test_gain_twice_or_wrong_actual_state_is_refused(self):
        args=fixture();args[1]['gain_squared_targets']=[v*.25 for v in args[1]['gain_squared_targets']]
        with self.assertRaisesRegex(ValueError,'exactly once'):run(args)
        args=fixture();args[1]['label']['state_id']='other-trajectory-same-step'
        with self.assertRaisesRegex(ValueError,'Same actual state'):run(args)

    def test_missing_restore_or_committing_shadow_teacher_is_refused(self):
        args=fixture();args[1]['serial_restores'].pop()
        with self.assertRaises(ValueError):run(args)
        args=fixture();args[1]['candidate_or_teacher_committed_to_parent']=True
        with self.assertRaises(ValueError):run(args)

    def test_future_or_teacher_feature_changes_are_refused(self):
        args=fixture();rows=copy.deepcopy(args[5]);rows[9]['features']['T2']['prefix_steps']+=(11,)
        with self.assertRaisesRegex(ValueError,'causal ordinary prefix'):audit_features(rows,clock=args[6])
        rows=copy.deepcopy(args[5]);rows[9]['teacher_or_candidate_history_used']=True
        with self.assertRaises(ValueError):audit_features(rows,clock=args[6])
        rows=copy.deepcopy(args[5]);rows[9]['features']['T1']['values']+=(.4,)
        with self.assertRaises(ValueError):audit_features(rows,clock=args[6])

    def test_unsupported_label_position_keeps_denominator(self):
        args=fixture();args[1].update(status='UNKNOWN_ORIGINAL_SUPPORT_NOT_RELAXED',label=None,artifact=None,extra_pairs=0)
        args[1].pop('trials');args[1].pop('serial_restores')
        rows=copy.deepcopy(args[5]);rows[9]['observation'].update(calibration_supported=False,gain=None,local_proxy=None)
        h=CausalHistory(rows[0]['observation']['prompt'],0)
        for row in rows:
            fs=h.push(Observation(**row['observation']))
            row['features']={m:{'names':f.names,'values':f.values,'prefix_steps':f.prefix_steps} for m,f in fs.items()}
        features=audit_features(rows,clock=args[6]);args[3][9]['joint_decision']['gain']=None
        result=audit_label(None,args[1],features,args[3],expected_shape=args[4],provenance='SYNTHETIC_CPU_INTERFACE')
        self.assertTrue(result['denominator_kept']);self.assertFalse(result['labels_available'])
        args[1]['label']={'fabricated':True}
        with self.assertRaises(ValueError):audit_label(None,args[1],features,args[3],expected_shape=args[4],provenance='SYNTHETIC_CPU_INTERFACE')

    def test_complete18_parents_and864_planned_pairs(self):
        requests=[{'name':'CPU_fixture_'+str(i)} for i in range(8)];rows=full_matrix(requests)
        self.assertEqual(len(rows),18);self.assertEqual(sum(r['planned_ordinary_pairs']+r['planned_extra_pairs'] for r in rows),864)
        self.assertEqual(sum(len(r['planned_label_steps']) for r in rows),72)
        self.assertEqual(sum(r['section']=='FORMAL' for r in rows),16)
        with self.assertRaises(ValueError):full_matrix(requests[:-1])


if __name__=='__main__':unittest.main()
