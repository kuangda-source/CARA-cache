import copy
import unittest

from wcomr.cara_fast_scoring_manifest_r2 import comparison_input_digest,validate_pair_identities
from wcomr.cara_fast_spec_r1 import digest


class ScoringIdentityTests(unittest.TestCase):
    def pair(self):
        native=dict(name='CPU_CONTROL',prompt='synthetic',negative_prompt='',seed=0,
                    guidance=7,num_output_frames=93,resolution='432,768',num_steps=35)
        short=dict(native,num_steps=22)
        shared=dict(member='CPU_CONTROL',seed=0,host='CPU_CONTROL',gpu_uuid='NO_GPU',
                    model_sha256=digest('CPU_CONTROL'),precision='RGB24',scope_sha256=digest('scope'),
                    comparison_input_sha256=comparison_input_digest(native))
        pair=dict(id='control',candidate=dict(shared,role='NATIVE22',execution_request_sha256=digest(short)),
                  reference=dict(shared,role='NATIVE35',execution_request_sha256=digest(native)))
        return dict(scope_sha256=shared['scope_sha256'],pairs=[pair]),native,short

    def test_native_k_uses_same_content_and_distinct_execution(self):
        config,native,short=self.pair()
        self.assertEqual(comparison_input_digest(native),comparison_input_digest(short))
        self.assertNotEqual(digest(native),digest(short))
        self.assertEqual(validate_pair_identities(config),['control'])

    def test_changed_conditioning_seed_or_geometry_changes_identity(self):
        config,native,_=self.pair()
        for update in (dict(seed=1),dict(prompt='other'),dict(guidance=8),dict(resolution='768,432')):
            value=comparison_input_digest(dict(native,**update))
            self.assertNotEqual(value,comparison_input_digest(native))
            bad=copy.deepcopy(config)
            bad['pairs'][0]['candidate']['comparison_input_sha256']=value
            with self.assertRaises(ValueError):
                validate_pair_identities(bad)

    def test_wrong_reference_host_or_duplicate_refused(self):
        config,_,_=self.pair()
        for key,value in [('role','NATIVE26'),('gpu_uuid','OTHER'),('scope_sha256','OTHER')]:
            bad=copy.deepcopy(config)
            bad['pairs'][0]['reference'][key]=value
            with self.assertRaises(ValueError):
                validate_pair_identities(bad)
        config['pairs'].append(copy.deepcopy(config['pairs'][0]))
        with self.assertRaises(ValueError):
            validate_pair_identities(config)


if __name__=='__main__':
    unittest.main()
