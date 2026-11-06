"""Independent acceptance of synthetic raw-role artifacts, without SSH or Torch."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
F=load('synthetic_bundle_fixture',ROOT/'tests/test_N10_model_cpu_bundle_r1.py')
A=load('independent_cpu_acceptor',ROOT/'scripts/accept_wc_N10_models_cpu_r1.py')


def fixture():
    reg,resources,values=F.fixture();reg['purpose']='N10_FULL_FIVE_METRIC_MODEL_CPU_ONLY_NOT_SCORING'
    hashes={r:hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest() for r,v in values.items()}
    bundle=F.M.drive(reg,'d'*64,resources,lambda role:dict(exit_code=0,data=copy.deepcopy(values[role]),
        result_sha256=hashes[role]));bundle['wall_seconds']=.5
    files={'model-resources.json':dict(exists=True,data=dict(resources=resources)),
           'CPU-model-bundle-result.json':dict(exists=True,data=bundle)}
    for role,value in values.items():files['CPU-model-'+role+'.json']=dict(exists=True,sha256=hashes[role],data=value)
    return dict(status='N10_ORIGINAL_FIVE_MODEL_CPU_ONCE_CAPTURE',
        launch=dict(registration_sha256='d'*64,source_revision=reg['source_revision'],first_collection_not_before_unix=6.),
        observed_unix=7.,registration=reg,registration_sha256='d'*64,
        payload_verified={n:True for n in reg['payload_sha256']},original_process_alive=False,
        files=files,role_result_files_present=list(F.M.ROLES),GPU_submissions=0,ledger_written=False)


class IndependentModelCPURawControls(unittest.TestCase):
    def test_whole_five_rebuilt_from_separate_raw_files(self):
        result=A.accept(fixture());self.assertTrue(result['CPU_accepted'])
        self.assertEqual(result['accepted_models'],5);self.assertFalse(result['paper_quality_scores_generated'])

    def test_tampered_raw_cannot_be_hidden_by_success_summary(self):
        for forge_embedded in (False,True):
            value=fixture();raw=value['files']['CPU-model-ViCLIP.json']['data']
            raw['actual']['outputs']['text_features']['finite']=False
            if forge_embedded:value['files']['CPU-model-bundle-result.json']['data']['rows'][3]['data']=copy.deepcopy(raw)
            result=A.accept(value);self.assertFalse(result['CPU_accepted']);self.assertEqual(result['accepted_models'],4)

    def test_missing_role_and_original_failure_keep_five_denominator(self):
        value=fixture();value['files']['CPU-model-AMT_S.json']=dict(exists=False)
        result=A.accept(value);self.assertEqual(result['registered_model_denominator'],5)
        self.assertEqual(result['accepted_models'],4);self.assertFalse(result['CPU_accepted'])

    def test_live_original_or_missing_whole_result_not_complete(self):
        value=fixture();value['original_process_alive']=True
        self.assertFalse(A.accept(value)['CPU_accepted'])
        value=fixture();value['files']['CPU-model-bundle-result.json']=dict(exists=False)
        self.assertFalse(A.accept(value)['CPU_accepted'])

    def test_bad_source_or_early_capture_cannot_accept_cpu(self):
        for kind in ('payload','clock','purpose','denominator'):
            value=fixture()
            if kind=='payload':value['payload_verified'][next(iter(value['payload_verified']))]=False
            elif kind=='clock':value['observed_unix']=5.
            elif kind=='purpose':value['registration']['purpose']='SYNTHETIC_OTHER_TASK'
            else:value['files']['CPU-model-bundle-result.json']['data']['role_denominator']=4
            with self.subTest(kind=kind),self.assertRaises(ValueError):A.accept(value)


if __name__=='__main__':unittest.main()
