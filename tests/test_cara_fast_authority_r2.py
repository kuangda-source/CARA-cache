import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from wcomr.cara_fast_execution_r2 import validate,RUN,SPEC,QUOTE,PROFILE

ROOT=Path(__file__).resolve().parents[1]


class AuthorityTests(unittest.TestCase):
    def fixture(self,project):
        stage=project/'.sync/CPU_AUTHORITY_CONTROL_ONLY'
        paths=[SPEC,QUOTE,PROFILE,'plans/cara_next_stage_20261028/mainline/RUN_MANIFEST.json']
        for name in paths:
            path=stage/name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes((ROOT/name).read_bytes())
        sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
        def write(path,value):
            path.write_text(json.dumps(value))
        scope=json.loads((stage/SPEC).read_text())['resolved_scope_sha256']
        registration=dict(source_revision='CPU_AUTHORITY_FIXTURE_NOT_HUMAN_AUTHORIZATION',
            payload_sha256={name:sha(stage/name) for name in paths},runtime_source_sha256={})
        write(stage/'registration.json',registration)
        proof=dict(passed=True,critical_source_sha256={PROFILE:sha(stage/PROFILE)})
        write(stage/'execution-CPU-proof.json',proof)
        authority=dict(direct_user_authorization=True,
            user_quote='SYNTHETIC UNIT INPUT, NOT ACTUAL USER GPU AUTHORITY',run_id=RUN,phase='A',
            physical_paths=32,whole_GPUh=5,authorizes_phase_B=False,host='two_card',
            scope_sha256=scope,source_revision=registration['source_revision'],
            registration_sha256=sha(stage/'registration.json'),CPU_proof_sha256=sha(stage/'execution-CPU-proof.json'),
            gpu_uuid='GPU-CPU-AUTHORITY-CONTROL',launch_id='NO_REAL_GPU_LAUNCH')
        write(stage/'pg-GPU-authorization.json',authority)
        job=dict(job_id=RUN,run_id=RUN,phase='A',host=authority['host'],gpu_uuid=authority['gpu_uuid'],
            launch_id=authority['launch_id'],registration_sha256=authority['registration_sha256'],
            billed_limit_GPUh=5,authorization_sha256=sha(stage/'pg-GPU-authorization.json'),status='RESERVED_OR_RUNNING')
        write(stage/'central-reservation.json',dict(central_ledger_host='four_card',new_reservation=True,job=job))
        write(stage/'launch-binding.json',dict(authorization_sha256=sha(stage/'pg-GPU-authorization.json'),
            central_reservation_sha256=sha(stage/'central-reservation.json')))
        return stage,authority,job

    def test_original_A32_source_and_envelope_are_consistent(self):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory)
            stage,authority,_=self.fixture(project)
            card,_,actual=validate(project,stage)
            self.assertEqual(actual,authority)
            self.assertEqual(card['counts']['stage_A_paths'],32)
            self.assertFalse(actual['authorizes_phase_B'])

    def test_absent_authority_B_amendment_and_wrong_envelope_refuse(self):
        for changed in ('no_authority','phase_B','different_host','different_bill'):
            with self.subTest(changed=changed),tempfile.TemporaryDirectory() as directory:
                project=Path(directory)
                stage,authority,job=self.fixture(project)
                if changed=='no_authority':
                    authority['direct_user_authorization']=False
                elif changed=='phase_B':
                    authority['phase']='B'
                    authority['authorizes_phase_B']=True
                elif changed=='different_host':
                    job['host']='four_card'
                else:
                    job['billed_limit_GPUh']=10
                (stage/'pg-GPU-authorization.json').write_text(json.dumps(authority))
                envelope=dict(central_ledger_host='four_card',new_reservation=True,job=job)
                (stage/'central-reservation.json').write_text(json.dumps(envelope))
                with self.assertRaises(ValueError):
                    validate(project,stage)


if __name__=='__main__':
    unittest.main()
