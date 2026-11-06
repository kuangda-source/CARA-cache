"""N09 cost policy using synthetic N05 prices and real historical N06 metadata.

These controls do not quote the current card; the actual saved-source CLI run
is a separate receipt. No model, codec, server, GPU or real ledger is written.
"""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_frozen_card_cost_r1 import fixture as cost_fixture, N06_CAPTURE, N06_ACCEPTANCE
from wcomr.runtime_profile40_cost_r1 import estimate

ROOT=Path(__file__).resolve().parents[1]


def inputs():
    scope=json.loads((ROOT/'manifests/wc_paper_N09_runtime_profile40_scope_r1_20261016.json').read_text())
    protocol=json.loads((ROOT/'manifests/wc_paper_N08_balanced_repeat40_protocol_r1_20261016.json').read_text())
    freeze=json.loads((ROOT/'manifests/wc_paper_N07_N08_method_freeze_r1_20261016.json').read_text())
    return scope,protocol,freeze,cost_fixture()[-1]


class RuntimeProfileWholeCostControls(unittest.TestCase):
    def test_whole40_and_actual_mode_labels_are_not_reclassified_as_warmups(self):
        scope,protocol,freeze,sources=inputs();before=copy.deepcopy((scope,protocol,freeze,sources))
        result=estimate(scope,protocol,freeze,sources)
        self.assertEqual((scope,protocol,freeze,sources),before)
        self.assertEqual(len(result['positions']),40);self.assertEqual(result['scope_counts'],scope['scope_counts'])
        self.assertEqual(sum(r['section']=='WARMUP' for r in result['positions']),10)
        self.assertEqual(sum(r['section']=='PROFILE_CONTROL' for r in result['positions']),30)
        self.assertEqual(result['actual_mode_counts'],{m:10 for m in ['ORIGINAL_AUDIT_WARMUP','ORIGINAL_AUDIT','PROFILE_AUDIT','PROFILE_LEAN']})
        self.assertEqual(result['trace_planning_headroom_total_seconds'],1800.)
        self.assertEqual(result['component_profile_planning_headroom_total_seconds'],600.)
        self.assertFalse(result['component_observer_cost_measured']);self.assertFalse(result['active_job_reservation_written'])

    def test_audited_vs_lean_request_prices_and_one_resident_load_reconcile(self):
        scope,protocol,freeze,sources=inputs()
        for source in sources:
            source['load_seconds']=100.;source['residual_per_path_seconds']=0.
            for record in source['methods'].values():
                record.update(max_complete_request_seconds=100.,max_warm_request_seconds=100.,max_formal_request_seconds=80.)
        result=estimate(scope,protocol,freeze,sources)
        # 30 trace paths *100 +10 lean *80 +1800 trace allowance +600 observer allowance.
        self.assertEqual(result['projected_complete_requests_seconds'],6200.)
        self.assertEqual(result['one_resident_load_seconds'],100.)
        self.assertEqual(result['projected_seconds_before_margin'],6600.)
        self.assertEqual(result['forecast_complete_GPUh'],2.2)

    def test_missing_successes_keep_all_method_positions_with_explicit_dense_proxy(self):
        scope,protocol,freeze,sources=inputs()
        record=sources[0]['methods']['RA_DEFAULT']
        for key in ('max_complete_request_seconds','max_warm_request_seconds','max_formal_request_seconds'):record[key]=None
        result=estimate(scope,protocol,freeze,sources)
        self.assertEqual(result['explicit_proxy_methods'],['RA_DEFAULT'])
        selected=[r for r in result['positions'] if r['method']=='RA_DEFAULT']
        self.assertEqual(len(selected),8);self.assertTrue(all(r['planned_complete_request_seconds']>60 for r in selected))
        self.assertTrue(all(r['observed_successful_request_max_seconds'] is None for r in selected))
        sources[0]['methods']['NATIVE35']['max_complete_request_seconds']=None
        unknown=estimate(scope,protocol,freeze,sources)
        self.assertIsNone(unknown['forecast_complete_GPUh']);self.assertEqual(unknown['complete_plan_positions'],40)

    def test_changed_mode_role_input_counts_duplicate_sources_and_nonfinite_prices_refused(self):
        for mode in ('mode','role','seed','renamed_both','count','duplicate','invalid_price'):
            with self.subTest(mode=mode):
                scope,protocol,freeze,sources=inputs()
                if mode=='mode':scope['complete_matrix'][10]['audit_guided']=False
                elif mode=='role':freeze['repeat_timing_bindings']['RA_CFG_CACHE']='RA_DOUBLE'
                elif mode=='seed':scope['requests'][0]['seed']=17
                elif mode=='renamed_both':
                    scope['requests'][0]['name']=protocol['requests'][0]['name']='FOREIGN_INPUT'
                elif mode=='count':scope['scope_counts']['profiled_paths']=19
                elif mode=='duplicate':sources.append(copy.deepcopy(sources[0]))
                else:sources[0]['methods']['A_NO_P']['max_warm_request_seconds']=float('nan')
                with self.assertRaises(ValueError):estimate(scope,protocol,freeze,sources)

    def test_whole_load_overhead_can_trigger_exact12_approval_without_shortening(self):
        scope,protocol,freeze,sources=inputs();low=estimate(scope,protocol,freeze,sources)
        self.assertFalse(low['specific_card_confirmation_required_by_forecast'])
        sources[0]['load_seconds']=12*3600
        high=estimate(scope,protocol,freeze,sources)
        self.assertTrue(high['specific_card_confirmation_required_by_forecast'])
        self.assertEqual(len(high['positions']),40);self.assertFalse(high['whole_card_selected'])

    def test_actual_cli_cold_stdlib_full40_and_original_source_bindings(self):
        scope,protocol,freeze,sources=inputs();_,raw,accepted,*_=cost_fixture()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            paths={'N05-capture':root/'synthetic_N05.gz','N05-acceptance':root/'synthetic_N05.json',
                'N06-capture':N06_CAPTURE,'N06-acceptance':N06_ACCEPTANCE,
                'scope':root/'scope.json',
                'timing-protocol':ROOT/'manifests/wc_paper_N08_balanced_repeat40_protocol_r1_20261016.json',
                'method-freeze':ROOT/'manifests/wc_paper_N07_N08_method_freeze_r1_20261016.json',
                'output':root/'estimate.json'}
            paths['N05-capture'].write_bytes(raw);paths['N05-acceptance'].write_text(json.dumps(accepted))
            paths['scope'].write_text(json.dumps(scope))
            command=[sys.executable,'-S',str(ROOT/'scripts/estimate_wc_paper_N09_runtime40_complete_cost_r1.py')]
            for name,path in paths.items():command+=['--'+name,str(path)]
            result=subprocess.run(command,capture_output=True,text=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
            self.assertEqual(result.returncode,0,result.stderr)
            value=json.loads(paths['output'].read_text());self.assertEqual(len(value['positions']),40)
            self.assertFalse(value['neural_framework_imported']);self.assertEqual(value['GPU_submissions'],0)
            self.assertEqual(len(value['references']),3);self.assertEqual(len(value['sources']),2)
            self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0)


if __name__=='__main__':unittest.main()
