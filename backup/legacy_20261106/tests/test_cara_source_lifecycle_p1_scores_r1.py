"""Full52 score/alias accounting and release-first refusal, no metric computation."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch

import check_cara_source_lifecycle_p1_score_fixture_r1 as fixture
from wcomr import cara_source_lifecycle_p1_artifacts_r1 as artifacts
from wcomr.cara_source_lifecycle_p1_scores_r1 import bind_post_scorer,validate_config,accept_scores,pair_key
from wcomr.cara_fast_spec_r1 import digest


class P1FinalScoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.f,cls.packet=fixture.packet()

    @classmethod
    def tearDownClass(cls):cls.f.doCleanups()

    def configured(self):
        packet=copy.deepcopy(self.packet)
        config=bind_post_scorer(packet,dict(torch_home='/CPU/torch',piq_site='/CPU/piq',weights_sha256={}),cpu_validation=True)
        identity=dict(pid=123,start_ticks=456,host_view={'EXPLICIT_CPU_METADATA':True})
        result=dict(status='P1_COMPLETE_NEW_PAIRS_PENDING_INDEPENDENT_ACCEPTANCE',config_sha256=digest(config),
            source_sha256=config['source_sha256'],CPU_fixture_only=True,CUDA_initialized=False,GPU_submissions=0,
            original_identity=identity,registered_pairs=[p['id'] for p in config['manifest']['new_pairs']],rows=[])
        for pair in config['manifest']['new_pairs']:
            result['rows'].append(dict(id=pair['id'],**fixture.metric(pair,packet['decoded'])))
        execution=dict(kind='ACTUAL_CPU_FIXTURE_CHILD',original_identity=identity,original_process_ended=True,
            original_observation=dict(original_live=False,original_pid=identity['pid'],original_start_ticks=identity['start_ticks'],
                                      observed_host_view=identity['host_view']),
            config_sha256=digest(config),result_sha256=digest(result),source_sha256=config['source_sha256'],
            exit_code=0,GPU_hidden=True,wall_seconds=1.)
        return packet,config,result,execution

    def test_original_full146_becomes_full52_and_at_most32_new_unique_scores(self):
        packet,config,result,execution=self.configured()
        accepted=accept_scores(packet,config,result,execution,cpu_validation=True)
        self.assertEqual(accepted['logical_quality_positions'],52)
        self.assertEqual(len(accepted['rows']),52)
        self.assertLessEqual(accepted['new_scored_pairs'],32)
        self.assertEqual(accepted['internal_scores_recomputed'],0)
        for row in accepted['rows']:
            if row['metric_source']=='SEALED_INTERNAL':
                self.assertEqual(row['metrics'],packet['manifest']['internal_rows'][row['pair_key']]['metrics'])

    def test_missing_one_new_pair_or_one_old_row_cannot_yield_partial_acceptance(self):
        packet,config,result,execution=self.configured()
        result['rows'].pop();execution['result_sha256']=digest(result)
        with self.assertRaisesRegex(ValueError,'Complete original'):accept_scores(packet,config,result,execution,cpu_validation=True)
        packet=copy.deepcopy(self.packet)
        packet['manifest']['internal_rows'].pop(next(iter(packet['manifest']['internal_rows'])))
        with self.assertRaisesRegex(ValueError,'unique final pair'):bind_post_scorer(packet,{},cpu_validation=True)

    def test_internal_pair_cannot_be_added_to_new_score_work(self):
        packet=copy.deepcopy(self.packet)
        original=next(iter(packet['manifest']['internal_rows'].values()))['pair']
        packet['manifest']['new_pairs'].append(dict(id='ATTEMPT_RECOMPUTE_INTERNAL',**original))
        with self.assertRaisesRegex(ValueError,'exactly once'):bind_post_scorer(packet,{},cpu_validation=True)

    def test_new_rows_must_match_full_released_rgb_and_original_metrics(self):
        for fault in ('rgb','frame','mean','mse','member'):
            packet,config,result,execution=self.configured()
            row=result['rows'][0]
            if fault=='rgb':row['decoded_RGB_sha256'][0]='f'*64
            if fault=='frame':row['Alex_frames'].pop()
            if fault=='mean':row['Alex']+=.01
            if fault=='mse':row['MSE_video']=-1
            if fault=='member':row['member']='NOT_REGISTERED'
            execution['result_sha256']=digest(result)
            with self.subTest(fault=fault),self.assertRaises(ValueError):
                accept_scores(packet,config,result,execution,cpu_validation=True)

    def test_original_cpu_must_end_before_any_score_acceptance(self):
        packet,config,result,execution=self.configured()
        execution['original_observation']['original_live']=None
        with self.assertRaisesRegex(ValueError,'must have ended'):accept_scores(packet,config,result,execution,cpu_validation=True)

    def test_release_gate_precedes_any_science_or_model_artifact_read(self):
        with patch.object(artifacts,'released_lifecycle',return_value=dict(container_exit_success=False)), \
                patch.object(artifacts,'read_record',side_effect=AssertionError('Read science before original release')):
            with self.assertRaisesRegex(ValueError,'before P1 science'):
                artifacts.released_artifacts({},'a'*64,{},cpu_validation=True)


if __name__=='__main__':unittest.main()
