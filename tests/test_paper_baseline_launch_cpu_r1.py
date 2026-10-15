"""No actual GPU/network: prove full-card authority and original-N06 gate."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from wcomr.paper_baseline_production_r1 import CONFIG,RUN,PRODUCTION_CPU_STATUS,validate_launch_authority,verify_N06_prerequisite

ROOT=Path(__file__).resolve().parents[1]

class LaunchTests(unittest.TestCase):
    def test_complete_under12_authority_and_all_source_hash_bindings(self):
        c=json.loads((ROOT/CONFIG).read_text());reg=dict(source_revision='frozen')
        proof=dict(status=PRODUCTION_CPU_STATUS,exit_code=0,source_revision='frozen',config_sha256='config',registration_sha256='registration')
        auth=dict(source_revision='frozen',direct_user_authorization=True,autonomy_exclusive_upper_GPUh=12,
            user_reply_quote='批准，以后少于12gpuh时直接启动',launch_id='one',whole_card_run=RUN,gpu_uuid='GPU-own',
            config_sha256='config',production_CPU_sha256='production')
        kwargs=dict(revision='frozen',gpu_uuid='GPU-own',config_sha256='config',production_sha256='production',registration_sha256='registration')
        validate_launch_authority(c,reg,proof,auth,**kwargs)
        for key,value in [('source_revision','other'),('gpu_uuid','GPU-other'),('whole_card_run','shortened'),
                ('direct_user_authorization',False),('autonomy_exclusive_upper_GPUh',8),('production_CPU_sha256','wrong')]:
            bad={**auth,key:value}
            with self.assertRaises(ValueError):validate_launch_authority(c,reg,proof,bad,**kwargs)

    def test_early_gate_precedes_any_original_stage_or_GPU_query(self):
        with self.assertRaisesRegex(ValueError,'Before original N06 collection ETA'):
            verify_N06_prerequisite(Path('/N06_MUST_NOT_BE_READ'),{},now=1792097650.)

    def test_full_independent_acceptance_required_not_just_CPU_or_finance(self):
        for status in ('CPU_PASS','SIMPLE26D_ACTUAL_GPU_BILL','PARTIAL_ACCEPTED'):
            with self.assertRaisesRegex(ValueError,'Complete independently accepted'):
                verify_N06_prerequisite(Path('/N06_MUST_NOT_BE_READ'),dict(status=status,full_denominator=36,formal_denominator=24),now=1792097652.)

    def test_real_terminal_binding_and_stale_finance_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);stage=root/'.sync/wc-simple26d-memory-production-r2-20261015';stage.mkdir(parents=True)
            out=root/'outputs/wc-simple26d-memory-cal4-full36-r2';out.mkdir(parents=True)
            (stage/'CPU-final-results.json').write_text(json.dumps(dict(rows=[{}]*36,old28_memory_parity_controls=[dict(status='PASS')]*28)))
            (stage/'post-CPU-exit.json').write_text(json.dumps(dict(exit_code=0)))
            (out/'supervisor.json').write_text(json.dumps(dict(child_exit_code=0,source_revision='0795a008bc94401bcc30a5fb456a2620aae0f2ea')))
            (out/'billing.json').write_text(json.dumps(dict(actual_GPUh=2.)))
            acceptance=dict(status='SIMPLE26D_FULL36_INDEPENDENT_TERMINAL_ACCEPTED',full_denominator=36,formal_denominator=24,actual_GPUh=2.)
            self.assertEqual(verify_N06_prerequisite(root,acceptance,now=1792097652.)['status'],'ORIGINAL_N06_ACCEPTANCE_BOUND_BEFORE_N05_GPU')
            with self.assertRaises(ValueError):verify_N06_prerequisite(root,{**acceptance,'actual_GPUh':1.},now=1792097652.)
            (stage/'CPU-final-results.json').write_text(json.dumps(dict(rows=[{}]*36,old28_memory_parity_controls=[])))
            with self.assertRaises(ValueError):verify_N06_prerequisite(root,acceptance,now=1792097652.)

if __name__=='__main__':unittest.main()
