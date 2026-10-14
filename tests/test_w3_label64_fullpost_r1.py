"""Whole90-file/1242-tensor CPU audit and complete failure denominators.

These are saved synthetic tensors and mock video decodes, never real teachers.
"""
import copy
from dataclasses import asdict
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

import torch

from wcomr.mid_coverage import tree_digest
from wcomr.p_acr_profile528_contract_r1 import H1_FP
from wcomr.w3_causal_trend_r1 import Observation,CausalHistory,SameStateLabel
from wcomr.w3_label64_post_r1 import full_matrix,audit_features
from wcomr.w3_label64_fullpost_r1 import audit_all
from wcomr.w3_label64_h1_owner_r1 import STEPS

spec=importlib.util.spec_from_file_location('independent_W3_post_fixture',Path(__file__).with_name('test_w3_label64_post_r1.py'))
fixture_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture_module)


def cohort(root):
    requests=[{'name':'CPU_ONLY_FULLPOST_'+str(i)} for i in range(8)]
    plan=full_matrix(requests);rows=[]
    def write(name,value):
        path=root/(name+'.pt');torch.save(value,path)
        return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'bytes':path.stat().st_size,'tensor_sha256':tree_digest(value)}
    for planned in plan:
        payload,record,_,history,shape,features,clock=fixture_module.fixture()
        for row in features:row['observation']['prompt']=planned['scene']
        causal=CausalHistory(planned['scene'],0)
        for row in features:
            fs=causal.push(Observation(**row['observation']))
            row['features']={m:{'names':f.names,'values':f.values,'prefix_steps':f.prefix_steps} for m,f in fs.items()}
        fs=audit_features(features,clock=clock)
        raw={'guided':[torch.full(shape,float(i)/100) for i in range(36)],'final_latent':torch.ones(shape)}
        row={**planned,'status':'COMPLETE','solver_steps':36,'guided_pairs':36,'method_fingerprint':H1_FP,
            'actions':['DD']*36,'A_history':[{'step':i,'action':'DD'} for i in range(1,37)],
            'source_history':history,'parent_vectors':write(planned['id']+'_parent',raw),
            'guided_sha256':[tree_digest(t) for t in raw['guided']],
            'final_latent_sha256':tree_digest(raw['final_latent']),'diagnostic_points':[],
            'actual_pair_computations':36 if planned['kind']=='BASELINE' else 60,'feature_rows':features}
        if planned['kind']=='DIAGNOSTIC':
            for step in STEPS:
                point=copy.deepcopy(payload);point['timestep']=torch.tensor([clock['timesteps'][step-1]])
                rec=copy.deepcopy(record);o=fs[step-1]['T1'].observation
                qC=(8*point['C'][0]-7*point['C'][1]).double().square().mean().item()
                qA=(8*point['A'][0]-7*point['A'][1]).double().square().mean().item()
                label=SameStateLabel(planned['scene'],0,step,o.state_id,qC,qA,'SYNTHETIC_CPU_INTERFACE')
                rec.update(step=step,pre_action_state=history[step-1]['joint_decision']['state_before'],
                    feature_state_id=o.state_id,sigma=o.sigma,label=asdict(label),
                    gain_squared_targets=label.target(fs[step-1]['T1']).tolist(),
                    artifact=write(planned['id']+'_point'+str(step),point))
                for t in rec['trials']:t['exact_original_70_call_cycle_clear']=step==35
                row['diagnostic_points'].append(rec)
        rows.append(row)
    def load(asset):
        path=Path(asset['path']).resolve()
        if (not path.is_relative_to(root.resolve()) or not path.exists()
                or hashlib.sha256(path.read_bytes()).hexdigest()!=asset['sha256']
                or path.stat().st_size!=asset['bytes']):raise ValueError('Immutable CPU raw asset changed')
        return torch.load(path,weights_only=True,map_location='cpu')
    return rows,requests,dict(clock=clock,expected_shape=shape,load_raw=load,
        read_video=lambda row:{'frames':93,'RGB_sha256':'MOCK93_ONLY_'+row['scene']},
        provenance='SYNTHETIC_CPU_INTERFACE')


class FullPost(unittest.TestCase):
    def test_all90_saved_files1242_tensors18_parents72_positions(self):
        with tempfile.TemporaryDirectory() as td:
            rows,requests,kw=cohort(Path(td));before=tree_digest(rows)
            result=audit_all(rows,requests,**kw)
            self.assertEqual(result['status'],'W3_FULL18_LABEL72_RAW_PARENT_CPU_AUDITED')
            self.assertEqual((result['raw_files'],result['raw_tensors'],result['actual_pairs']),(90,1242,864))
            self.assertEqual((len(result['parents']),len(result['labels']),result['actual_available_labels']),(18,72,72))
            self.assertEqual(result['scored_control_frames'],18*93)
            self.assertTrue(result['full90_1242_raw_scope_audited'])
            self.assertFalse(result['real_teacher_claim']);self.assertEqual(tree_digest(rows),before)

    def test_parent_corruption_or_missing_raw_retains_all_denominators(self):
        with tempfile.TemporaryDirectory() as td:
            rows,requests,kw=cohort(Path(td));rows[3]['A_history'][8]['action']='CC'
            result=audit_all(rows,requests,**kw)
            self.assertIn(rows[3]['id'],result['audit_failed_parent_ids'])
            self.assertEqual((len(result['parents']),len(result['labels'])),(18,72))
        with tempfile.TemporaryDirectory() as td:
            rows,requests,kw=cohort(Path(td));Path(rows[1]['diagnostic_points'][2]['artifact']['path']).unlink()
            result=audit_all(rows,requests,**kw)
            self.assertIn(rows[1]['id'],result['audit_failed_parent_ids']);self.assertEqual(len(result['labels']),72)

    def test_all_text_rejections_preserve18_and64plus8_without_fabrication(self):
        requests=[{'name':'CPU_REJECT_'+str(i)} for i in range(8)];rows=full_matrix(requests)
        for row in rows:row.update(status='TEXT_REJECTED',solver_steps=0,guided_pairs=0)
        _,_,_,_,shape,_,clock=fixture_module.fixture()
        def forbidden(*args):raise AssertionError('No generated raw/video exists for text rejection')
        result=audit_all(rows,requests,clock=clock,expected_shape=shape,load_raw=forbidden,
            read_video=forbidden,provenance='SYNTHETIC_CPU_INTERFACE')
        self.assertEqual((len(result['parents']),len(result['labels'])),(18,72))
        self.assertEqual(sum(r['section']=='FORMAL' for r in result['labels']),64)
        self.assertEqual((result['actual_pairs'],result['actual_available_labels'],result['raw_files']),(0,0,0))

    def test_cycle_label_swap_and_incomplete_video_never_accept_whole_scope(self):
        with tempfile.TemporaryDirectory() as td:
            rows,requests,kw=cohort(Path(td));rows[1]['diagnostic_points'][-1]['trials'][0]['exact_original_70_call_cycle_clear']=False
            result=audit_all(rows,requests,**kw);self.assertIn(rows[1]['id'],result['audit_failed_parent_ids'])
        with tempfile.TemporaryDirectory() as td:
            rows,requests,kw=cohort(Path(td));kw['read_video']=lambda row:{'frames':92,'RGB_sha256':'MOCK_INCOMPLETE'}
            result=audit_all(rows,requests,**kw);self.assertEqual(len(result['audit_failed_parent_ids']),18)
            self.assertEqual((len(result['parents']),len(result['labels'])),(18,72))

    def test_missing_or_reordered_registered_parent_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            rows,requests,kw=cohort(Path(td))
            with self.assertRaisesRegex(ValueError,'All18'):audit_all(rows[:-1],requests,**kw)
            rows[0],rows[1]=rows[1],rows[0]
            result=audit_all(rows,requests,**kw);self.assertEqual(len(result['labels']),72)
            self.assertIn(rows[0]['id'],result['audit_failed_parent_ids'])

    def test_technical_partial_points_are_read_without_promoting_to_full_labels(self):
        with tempfile.TemporaryDirectory() as td:
            rows,requests,kw=cohort(Path(td));row=rows[1]
            row.update(status='TECHNICAL_FAILURE',solver_steps=17,guided_pairs=17,
                parent_vectors=None,actual_pair_computations=23,
                diagnostic_points=row['diagnostic_points'][:2],feature_rows=row['feature_rows'][:17],
                source_history=row['source_history'][:17])
            result=audit_all(rows,requests,**kw)
            partial=[r for r in result['labels'] if r['parent_id']==row['id']]
            self.assertEqual(len(partial),8);self.assertEqual(sum(r.get('available_raw8_read',False) for r in partial),2)
            self.assertTrue(all(not r['labels_available'] for r in partial))
            self.assertEqual((result['actual_pairs'],result['verified_complete_parent_pairs']),(827,804))
            self.assertEqual((result['raw_files'],result['raw_tensors']),(83,1157))

    def test_saved_before_label_failure_orphan_raw_is_audited_but_not_used_for_training(self):
        with tempfile.TemporaryDirectory() as td:
            rows,requests,kw=cohort(Path(td));row=rows[1];original=row['diagnostic_points']
            row.update(status='TECHNICAL_FAILURE',parent_vectors=None,actual_pair_computations=23,
                diagnostic_points=original[:2],feature_rows=row['feature_rows'][:17],source_history=row['source_history'][:17],
                raw_point_artifacts=[{'step':r['step'],'artifact':r['artifact']} for r in original[:3]])
            result=audit_all(rows,requests,**kw);parent=result['parents'][1]
            self.assertEqual(parent['unrecorded_saved_points_retained'],[{'step':23,'all8_saved_tensors_read':True,'admitted_to_training':False}])
            self.assertEqual((result['raw_files'],result['raw_tensors']),(84,1165))
            self.assertEqual(sum(r['labels_available'] for r in result['labels'] if r['parent_id']==row['id']),0)


if __name__=='__main__':unittest.main()
