import ast
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from four_card_policy_assets_port_r1 import (generated_sources,container_command,
    quote_from_bank24,ROOT as REMOTE,STAGE,RUN,CONFIG)
from wc_four_card_policy_assets_r1 import DEPLOY,LAUNCH_GPU,prepare


class Full1624Port(unittest.TestCase):
    def test_saved_package_roundtrip_is_dispatch_comparable(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'package.json'
            self.assertEqual(prepare(path),json.loads(path.read_text()))

    def test_every_substitution_is_reversible_and_compiles(self):
        generated,evidence=generated_sources(ROOT)
        for name,record in evidence.items():
            code=generated[name]
            ast.parse(code)
            for before,after,count in reversed(record['substitutions']):
                self.assertEqual(code.count(after),count)
                code=code.replace(after,before)
            self.assertEqual(code,(ROOT/name).read_text())
        self.assertNotIn('src/wcomr/policy_interval_assets_sampling_r1.py',generated)
        self.assertNotIn('src/wcomr/policy_interval_readout_r1.py',generated)

    def test_new_physical_identity_preserves_scientific_configuration(self):
        c=json.loads((ROOT/CONFIG).read_text())
        self.assertNotEqual(RUN,c['run_id'])
        self.assertEqual(c['scope_counts']['formal_source_time_cells'],1624)
        self.assertEqual(c['scope_counts']['total_paths'],14)
        sources,_=generated_sources(ROOT)
        self.assertIn('from wcomr.policy_interval_assets_r1 import *',sources['scripts/policy_assets_fourcard_contract.py'])
        self.assertIn('get_device_capability()==(8,9)',sources['scripts/run_wc_policy_interval_assets_r1.py'])

    def test_actual_CPU_command_has_no_GPU_exposure_or_writable_authority(self):
        stage=Path(REMOTE)/'.sync'/STAGE
        command=container_command(REMOTE,stage,'cpu-worker','a'*64,{},1000,1000)
        self.assertNotIn('--gpus',command)
        self.assertIn('NVIDIA_VISIBLE_DEVICES=void',command)
        self.assertIn('WC_SCOUT_KIND=CAL12',command)
        volumes=[command[i+1] for i,v in enumerate(command) if v=='-v']
        self.assertEqual(volumes,[REMOTE+':'+REMOTE+':ro',str(stage)+':'+str(stage)+':rw'])
        self.assertIn('--read-only',command)
        self.assertEqual(command[command.index('--network')+1],'none')

    def test_GPU_lease_stays_in_one_host_PID_namespace(self):
        stage=Path(REMOTE)/'.sync'/STAGE
        command=container_command(REMOTE,stage,'supervise','a'*64,{},1000,1000,'GPU-example')
        self.assertEqual(command[command.index('--pid')+1],'host')
        self.assertEqual(command[command.index('--gpus')+1],'device=GPU-example')
        source=generated_sources(ROOT)[0]['scripts/wc_policy_interval_assets_lifecycle_r1.py']
        self.assertIn('pass_fds=(lease.handle.fileno(),)',source)
        self.assertIn('finally:lease.close()',source)
        self.assertLess(source.index('finally:lease.close()'),source.index("command=[sys.executable,str(a.stage/'scripts/postprocess_wc_policy_interval_assets_r1.py')"))

    def test_no_GPU_command_from_CPU_mode_or_foreign_stage(self):
        with self.assertRaises(ValueError):
            container_command(REMOTE,Path(REMOTE)/'.sync'/STAGE,'cpu-worker','a'*64,{},1000,1000,'GPU-x')
        with self.assertRaises(ValueError):
            container_command(REMOTE,'/tmp/foreign','supervise','a'*64,{},1000,1000,'GPU-x')

    def quote_inputs(self):
        old=json.loads((ROOT/'manifests/wc_policy_interval_assets_full1624_whole_quote_r1_20261020.json').read_text())
        cap={'runner':{'load_seconds':240,'runs':[{'status':'COMPLETE','started_unix':0,'ended_unix':300} for _ in range(24)]}}
        return cap,{'full_protocol_accepted':True},old

    def test_quote_keeps_all_expensive_collection_terms(self):
        args=self.quote_inputs();q=quote_from_bank24(*args)
        for k in ['all_readout_trials','source_transfer_planning','raw_write_and_read_and_SHA','moments_and_full_output_equality']:
            self.assertEqual(q['terms_seconds'][k],args[2]['terms_seconds'][k])
        self.assertEqual(q['scope_counts']['total_readout_pair_trials'],13020)
        self.assertEqual(q['terms_seconds']['full14_requests'],4200)
        self.assertFalse(q['independent_Ada_action_prices_measured'])

    def test_full_quote_above12_is_not_shrunk_or_relabelled(self):
        cap,acc,old=self.quote_inputs()
        for r in cap['runner']['runs']:r['ended_unix']=1000
        q=quote_from_bank24(cap,acc,old)
        self.assertGreater(q['forecast_complete_GPUh'],12)
        self.assertFalse(q['within_approved_limit'])
        self.assertEqual(q['scope_counts']['total_paths'],14)

    def test_partial_or_unaccepted_bank_not_quoted(self):
        cap,acc,old=self.quote_inputs()
        with self.assertRaises(ValueError):quote_from_bank24(cap,{},old)
        cap['runner']['runs'].pop()
        with self.assertRaises(ValueError):quote_from_bank24(cap,acc,old)

    def test_nonfinite_time_rejected(self):
        cap,acc,old=self.quote_inputs();cap['runner']['load_seconds']=float('nan')
        with self.assertRaises(ValueError):quote_from_bank24(cap,acc,old)

    def test_real_remote_programs_compile(self):
        compile(DEPLOY,'DEPLOY','exec');compile(LAUNCH_GPU,'LAUNCH_GPU','exec')
        self.assertIn('confirmed_GPU_submission',DEPLOY)
        self.assertIn('fourcard-gpu-intent.json',LAUNCH_GPU)
        self.assertIn('os.fsync',LAUNCH_GPU)


if __name__=='__main__':unittest.main()
