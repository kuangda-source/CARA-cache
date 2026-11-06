"""CPU-only boundary checks; no SSH, CUDA, ledger or active stage mutations."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import yaml
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'src')]
import run_card as card
import audit_cara_new_pool_delta_r1 as delta

class CardReader(unittest.TestCase):
    def setUp(self):
        self.actual=yaml.safe_load((ROOT/'cards/cal66_existing_r1.yaml').read_text())
        self.draft=yaml.safe_load((ROOT/'cards/TEMPLATE.yaml').read_text())
    def test_registered_reader_matches_accepted_closure_and_budget(self):
        result=card.validate(self.actual)
        self.assertEqual(result['launch_id'],'54eeebc7-00bb-4951-96cf-e2f66a85e344')
        self.assertEqual(result['physical_paths'],66)
        self.assertFalse(result['ready_for_new_GPU'])
    def test_template_cannot_observe_or_launch(self):
        self.assertFalse(card.validate(self.draft)['remote_actions_allowed'])
        for action in ('capture','launch-gpu','prepare','retry'):
            with self.assertRaises(ValueError):card.command(self.draft,action,ROOT/'reports/nonexistent-test.json')
    def test_registered_denominator_budget_alpha_evidence_mutations_rejected(self):
        for path,value in [(('scope','physical_paths'),65),(('budget','cap_gpuh'),9),
            (('budget','deployment_absolute_seconds'),260),(('authorization','new_gpu_dispatch'),True),
            (('backend','adapter'),'arbitrary'),(('post_release_cpu','cpus'),4),
            (('budget','acceptance'),{'point':'V_le_1','robust':'V_le_1'})]:
            v=copy.deepcopy(self.actual);v[path[0]][path[1]]=value
            with self.subTest(path=path),self.assertRaises(ValueError):card.validate(v)
        v=copy.deepcopy(self.actual);v['validation']['reused_evidence'][0]['sha256']='0'*64
        with self.assertRaises(ValueError):card.validate(v)
    def test_draft_input_ref_and_sha_required_together(self):
        self.draft['inputs']['exposure']={'path':'AGENTS.md','sha256':None}
        with self.assertRaises(ValueError):card.validate(self.draft)
    def test_reference_rejects_outside_symlink_and_wrong_sha(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'x').write_text('test');(root/'link').symlink_to(root/'x')
            for name,h in [('x','wrong'),('link',card.digest(b'test')),('../x','wrong')]:
                with self.subTest(name=name),self.assertRaises(ValueError):card.file_ref({'path':name,'sha256':h},root)
    def test_existing_adapter_builds_only_original_observation_commands(self):
        output=ROOT/'reports/UNCREATED_WORKFLOW_TEST.json'
        for action,flag in [('recover','--stage-ref'),('capture','--launch-ref')]:
            args=card.command(self.actual,action,output)
            self.assertIn(flag,args);self.assertNotIn('launch-gpu',args)
        for action in ('launch-gpu','retry','prepare'):
            with self.assertRaises(ValueError):card.command(self.actual,action,output)
        with self.assertRaises(ValueError):card.command(self.actual,'capture',ROOT/'README.md')
        with self.assertRaises(ValueError):card.command(self.actual,'capture',ROOT/self.actual['backend']['launch']['path'])
    def test_wrong_capture_launch_cannot_accept(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'reports').mkdir();p=root/'reports/cap.json'
            p.write_text(json.dumps({'launch':{'launch_id':'another'}}))
            with patch.object(card,'validate',return_value={'remote_actions_allowed':True,'adapter':'cal66_existing_r1','launch_id':'original'}):
                with self.assertRaises(ValueError):card.command(self.actual,'accept',root/'reports/new.json',capture=p,root=root)
    def test_complete_identity_and_preserved_physical_slots(self):
        identity={k:'fixed' for k in card.IDENTITY_FIELDS};identity['seed']=0
        slots=[dict(id=str(i),section=section,identity=copy.deepcopy(identity)) for i,section in enumerate(['QUALITY','QUALITY','TIMING_REPEAT','WARM','CONTROL','HISTORICAL_BRIDGE'])]
        before=copy.deepcopy(slots)
        self.assertEqual(card.alias_candidates(slots),[['0','1']]);self.assertEqual(slots,before)
        for field in ('alpha','seed','solver_grid','input_preprocessing','precision_runtime'):
            altered=copy.deepcopy(identity);altered[field]='different'
            self.assertNotEqual(card.execution_fingerprint(identity),card.execution_fingerprint(altered))
        del identity['alpha']
        with self.assertRaises(ValueError):card.execution_fingerprint(identity)

class ExposureDelta(unittest.TestCase):
    def test_frozen48_sources_and_split_are_unchanged(self):
        pool,prior,groups,roles,records=delta.protected_pool()
        self.assertEqual({k:len(v) for k,v in roles.items()},{'NEW_DEV_RESERVED':16,'FINAL_CONFIRMATION_RESERVED':16,'UNASSIGNED_RESERVE':16})
        self.assertEqual(len(pool['members']),48)
    def test_inventory_changed_removed_preserved(self):
        before=[{'ref':k,'sha256':'old'} for k in ('unchanged','changed','removed')]
        after=[{'ref':'unchanged','sha256':'old'},{'ref':'changed','sha256':'new'},{'ref':'added','sha256':'new'}]
        self.assertEqual(delta.delta_inventory(before,after,'ref'),{'added':['added'],'changed':['changed'],'removed':['removed']})
    def run_fixture(self,extra=None,remote=None):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for folder in ('reports','plans','manifests','cards','src/wcomr'):(root/folder).mkdir(parents=True)
            (root/'src/wcomr/frozen_input_exposure_r1.py').write_text('# fixture not executed')
            (root/delta.POOL).parent.mkdir(parents=True,exist_ok=True)
            (root/delta.POOL).write_text('{"members":[{"name":"av_1"}]}')
            prior_path='reports/prior.json';(root/prior_path).write_text('{"pool":[{"name":"av_1"}]}')
            old=b'{"ok":true}';(root/'reports/old.json').write_bytes(old)
            prior={'local_documents':[{'ref':'reports/old.json','sha256':delta.sha(old)}],
                'remote':{'documents':[]},'limits':['fixture scope']}
            pool={'audit_ref':prior_path,'audit_sha256':delta.sha((root/prior_path).read_bytes())}
            records=[dict(name='av_1',prompt_sha256=hashlib.sha256(b'prompt').hexdigest(),category='av',group_members=['av_1'])]
            if extra:
                name,raw=extra;(root/name).write_bytes(raw)
            reader=lambda payload:remote if remote is not None else {'documents':[],'identity_hits':{},'read_errors':[]}
            with patch.object(delta,'protected_pool',return_value=(pool,prior,{'av_1'},{'DEV':['av_1']},records)):
                return delta.audit(root,reader)
    def test_identical_history_reuse_and_exact_pool_metadata_exemption(self):
        result=self.run_fixture()
        self.assertTrue(result['scoped_no_execution_evidence']);self.assertEqual(result['local_unchanged_reused'],1)
        self.assertEqual(len(result['local_metadata_exemptions']),2)
        self.assertFalse(result['DEV_execution_ready']);self.assertFalse(result['pool_reselected'])
    def test_changed_or_new_raw_identity_blocks_without_exporting_values(self):
        raw=json.dumps({'raw':json.dumps({'name':'av_1','lpips':.987654321})}).encode()
        for name in ('reports/old.json','reports/new.json'):
            result=self.run_fixture((name,raw))
            self.assertFalse(result['scoped_no_execution_evidence']);self.assertTrue(result['local_blockers'])
            self.assertNotIn('0.987654321',json.dumps(result))
    def test_prompt_hash_alias_and_json_parse_failure_block(self):
        raw=json.dumps({'prompt_sha256':hashlib.sha256(b'prompt').hexdigest()}).encode()
        self.assertFalse(self.run_fixture(('reports/new.json',raw))['scoped_no_execution_evidence'])
        self.assertTrue(self.run_fixture(('reports/new.json',b'{'))['local_read_errors'])
    def test_remote_unknown_or_protected_hit_blocks(self):
        for remote in ({'status':'UNKNOWN'},{'documents':[],'identity_hits':{'av_1':['path']},'read_errors':[]}):
            self.assertFalse(self.run_fixture(remote=remote)['scoped_no_execution_evidence'])

if __name__=='__main__':unittest.main()
