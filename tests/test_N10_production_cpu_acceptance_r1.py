"""Synthetic original CPU receipts bound to real unscored complete960 scope."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from wcomr.automatic_quality_production_cpu_r1 import accept,STATUS,PATTERNS
from wcomr.automatic_quality_production_r1 import CPU_STATUS

ROOT=Path(__file__).resolve().parents[1]


def fixture():
    c=json.loads((ROOT/'configs/wc_paper_N10_full960_production_r1_20261018.json').read_text())
    source='a'*40;pid=dict(pid=100,start_ticks=90,state='S');stage='/SYNTHETIC_N10_CPU_ONLY'
    launch=dict(source_revision=source,stage=stage,project='/SYNTHETIC_ROOT',registration_sha256='b'*64,
        identity=pid,final_not_before_unix=10.)
    payload={**{'tests/'+n:'c'*64 for n in PATTERNS},'N10-production-config.json':'d'*64,
        'scripts/score_wc_paper_N10_full960_r1.py':'e'*64}
    files={}
    for name in ('unpriced_scope','whole_card_cost'):
        ref=c['references'][name];payload[ref['ref']]=ref['sha256']
        files[name]=dict(data=json.loads((ROOT/ref['ref']).read_text()),sha256=ref['sha256'])
    commands=[[str(ROOT/'.venv/bin/python'),'-m','unittest','discover','-s',stage+'/tests','-p',n,'-v'] for n in PATTERNS]
    commands.append([str(ROOT/'.venv/bin/python'),stage+'/scripts/score_wc_paper_N10_full960_r1.py',
        '--project',launch['project'],'--stage',stage,'--cpu-check'])
    proof=dict(status=CPU_STATUS,exit_code=0,source_revision=source,registration_sha256='b'*64,
        config_sha256='d'*64,scope_counts=c['scope_counts'],metric_positions=960,
        input_bundle_fingerprint=c['input_bundle_fingerprint'],runner_source_sha256='e'*64,
        neural_framework_imported=False,GPU_submissions=0,ledger_written=False)
    bundle=dict(status=STATUS,exit_code=0,source_revision=source,stage=stage,project=launch['project'],
        registration_sha256='b'*64,config_sha256='d'*64,python_executable=str(ROOT/'.venv/bin/python'),
        commands=[dict(command=x,exit_code=0) for x in commands],actual_original_five_model_proof_reaccepted=True,
        control_source_sha256={'tests/'+n:'c'*64 for n in PATTERNS},proof_sha256='f'*64,
        GPU_submissions=0,ledger_written=False,model_weights_loaded=0,wall_seconds=5.)
    files.update(config=dict(data=c,sha256='d'*64),proof=dict(data=proof,sha256='f'*64),bundle=dict(data=bundle,sha256='1'*64),
        exit=dict(data=dict(exit_code=0,source_revision=source,original_CPU_identity=dict(pid=100,start_ticks=90,state='R'),bundle_sha256='1'*64)))
    return dict(status='N10_PRODUCTION_CPU_ORIGINAL_ONCE_CAPTURE',launch=launch,observed_unix=11.,
        registration=dict(source_revision=source,payload_sha256=payload),registration_sha256='b'*64,
        payload_actual_sha256=copy.deepcopy(payload),GPU_submissions=0,ledger_written=False,
        process=dict(pid=100,start_ticks=None,state=None),files=files)


class ActualProductionCPUReceiptControls(unittest.TestCase):
    def test_cold_import_without_neural_framework_or_site_packages(self):
        code='import sys;sys.path.insert(0,'+repr(str(ROOT/'src'))+');import wcomr.automatic_quality_production_cpu_r1;assert "torch" not in sys.modules'
        result=subprocess.run([sys.executable,'-S','-c',code],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_full_original_five_commands_price_and_no_model_boundary(self):
        r=accept(fixture());self.assertTrue(r['CPU_accepted']);self.assertEqual(r['CPU_commands'],5)
        self.assertEqual((r['forecast_GPUh'],r['billed_limit_GPUh']),(4.915,6.25))

    def test_live_original_waits_but_reused_pid_is_not_original(self):
        v=fixture();v['process']=dict(pid=100,start_ticks=90,state='S')
        self.assertFalse(accept(v)['CPU_accepted']);v['process']['start_ticks']=91
        self.assertTrue(accept(v)['CPU_accepted'])

    def test_early_failed_or_missing_results_are_not_success(self):
        v=fixture();v['observed_unix']=9
        with self.assertRaises(ValueError):accept(v)
        for name in ('bundle','proof','exit'):
            v=fixture();v['files'][name]['data']=None
            self.assertFalse(accept(v)['CPU_accepted'])

    def test_changed_price_source_command_or_payload_refused(self):
        for mode in ('price','command','payload','weights'):
            with self.subTest(mode=mode):
                v=fixture()
                if mode=='price':v['files']['config']['data']['billed_limit_GPUh']=1.
                elif mode=='command':v['files']['bundle']['data']['commands'].pop()
                elif mode=='payload':v['payload_actual_sha256'].pop('N10-production-config.json')
                else:v['files']['bundle']['data']['model_weights_loaded']=1
                with self.assertRaises(ValueError):accept(v)


if __name__=='__main__':unittest.main()
