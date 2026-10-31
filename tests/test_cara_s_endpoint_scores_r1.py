"""Complete synthetic score receipts test acceptance; no metrics are computed."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from wcomr import cara_s_endpoint_artifacts_r1 as artifacts
from wcomr import cara_s_endpoint_scores_r1 as scores
from wcomr.cara_fast_spec_r1 import digest
from check_cara_s_endpoint_artifact_fixture_r2 import packet
from test_cara_s_endpoint_artifacts_r1 import write_media,decode


def fixture(root,*,alias=False):
    args=packet(root,write_media,decode,alias=alias,shape=(93,64,64,3))
    with patch.object(artifacts,'decode_video',side_effect=decode):saved=artifacts.postrelease_manifest(**args)
    config=scores.bind_scorer(saved,dict(torch_home='/CPU-ONLY/torch',piq_site='/CPU-ONLY/site',weights_sha256={}),cpu_validation=True)
    manifest_sha=hashlib.sha256((json.dumps(config,indent=2)+'\n').encode()).hexdigest()
    native={c['control']['member']:c['RGB_sha256'] for c in config['identity_controls']
        if c['control']['kind']=='FRESH_VS_ORIGINAL_DECODED_RGB' and c['control']['role']=='NATIVE35'}
    rows=[]
    for pair in config['pairs']:
        candidate=pair['candidate'];alex=[.3]*93;ssim=[.8]*93
        rows.append(dict(id=pair['id'],member=candidate['member'],role=candidate['role'],
            candidate=copy.deepcopy(candidate),reference=copy.deepcopy(pair['reference']),status='COMPLETE',
            frames=93,temporal_frame_pairs=92,PTS_equal=True,
            decoded_RGB_sha256=[saved['decoded'][candidate['slot_id']]['RGB_sha256'],native[candidate['member']]],
            Alex_frames=alex,SSIM_frames=ssim,Alex=sum(alex)/93,SSIM=sum(ssim)/93,
            Alex_worst=.3,Alex_q95_higher=.3,Alex_first_worst_frame_zero_based=0,
            MSE_video=.01,PSNR_is_infinite=False,PSNR_video_dB=20.,reference_temporal_L1=.1,
            reference_gradient_L1=.2,candidate_gradient_energy=1.,reference_gradient_energy=1.,
            gradient_energy_ratio=1.,gradient_ratio_status='FINITE'))
    identity=dict(pid=100,start_ticks=1000,host_view=dict(boot_id='CPU-FIXTURE',pid_namespace_inode=123))
    result=dict(status='COMPLETE_NOT_INDEPENDENTLY_ACCEPTED',registered_pairs=[p['id'] for p in config['pairs']],rows=rows,
        manifest_sha256=manifest_sha,analysis_scope_sha256=config['analysis_scope_sha256'],protocol_sha256=config['protocol_sha256'],
        worker_sha256=config['scorer_source_sha256'][scores.WORKER],CPU_fixture_only=True,CUDA_initialized=False,
        GPU_submissions=0,source_actual_sha256=config['scorer_source_sha256'],original_identity=identity)
    execution=dict(kind='ACTUAL_CPU_FIXTURE_CHILD',exit_code=0,original_process_ended=True,GPU_hidden=True,
        original_identity=identity,original_observation=dict(original_live=False,status='ORIGINAL_NOT_LIVE',
            original_pid=100,original_start_ticks=1000,observed_host_view=identity['host_view']),
        manifest_sha256=manifest_sha,source_actual_sha256=config['scorer_source_sha256'],wall_seconds=1.,result_sha256=digest(result))
    return dict(packet=saved,config=config,manifest_sha256=manifest_sha,result=result,execution=execution,cpu_validation=True)


class ScoreControls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.args=fixture(Path(self.temp.name)/'full')

    def run_accept(self):return scores.accept_scores(**self.args)

    def reject_row(self,change,message):
        change(self.args['result']['rows'][0]);self.args['execution']['result_sha256']=digest(self.args['result'])
        with self.assertRaisesRegex(ValueError,message):self.run_accept()

    def test_full12_new_12_unchanged(self):
        accepted=self.run_accept();self.assertEqual(accepted['formal_logical_positions'],24)
        self.assertEqual(accepted['new_scored_pairs'],12)
        self.assertTrue(all(accepted['source_rows'][r['id']]==r for r in self.args['config']['reused_rows']))

    def test_alias8_new_preserves24_logical(self):
        self.args=fixture(Path(self.temp.name)/'alias',alias=True);accepted=self.run_accept()
        self.assertEqual(accepted['new_scored_pairs'],8);self.assertEqual(len(accepted['source_rows']),20)
        self.assertEqual(len(accepted['positions']),24)

    def test_no_partial_new_result(self):
        self.args['result']['rows'].pop();self.args['execution']['result_sha256']=digest(self.args['result'])
        with self.assertRaisesRegex(ValueError,'denominator'):self.run_accept()

    def test_no_reordered_result(self):
        self.args['result']['rows'].reverse();self.args['execution']['result_sha256']=digest(self.args['result'])
        with self.assertRaisesRegex(ValueError,'denominator'):self.run_accept()

    def test_no_changed_decoded_rgb(self):
        self.reject_row(lambda r:r.update(decoded_RGB_sha256=['0'*64]*2),'decoded RGB')

    def test_no_missing_frame_curve(self):
        self.reject_row(lambda r:r['Alex_frames'].pop(),'frame curves')

    def test_no_changed_reduction(self):
        self.reject_row(lambda r:r.update(Alex=.99),'reductions')

    def test_psnr_infinity_identity(self):
        self.reject_row(lambda r:r.update(MSE_video=0,PSNR_is_infinite=False),'Zero-MSE')

    def test_undefined_gradient_preserved(self):
        row=self.args['result']['rows'][0];row.update(reference_gradient_energy=0,gradient_energy_ratio=None,gradient_ratio_status='ZERO_REFERENCE_ENERGY')
        self.args['execution']['result_sha256']=digest(self.args['result']);self.run_accept()
        self.reject_row(lambda r:r.update(gradient_energy_ratio=0),'Zero-reference')

    def test_cpu_child_must_exit(self):
        self.args['execution']['original_process_ended']=False
        with self.assertRaisesRegex(ValueError,'child must exit'):self.run_accept()

    def test_original_handle_not_replaced(self):
        self.args['execution']['original_observation']['original_start_ticks']+=1
        with self.assertRaisesRegex(ValueError,'handle identity'):self.run_accept()

    def test_source_unchanged(self):
        self.args['result']['worker_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'result/source'):self.run_accept()

    def test_cpu_mode_cannot_be_production(self):
        self.args['cpu_validation']=False
        with self.assertRaisesRegex(ValueError,'fixture mode'):self.run_accept()


if __name__=='__main__':unittest.main()
