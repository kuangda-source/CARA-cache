"""Real accepted N06 metadata plus explicitly synthetic, unobserved N05 costs."""
import copy
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from wcomr.frozen_card_cost_r1 import CAP, ORIGIN, estimate, preview, source_costs
from wcomr.gpu_budget_pool_v2 import BudgetPool, SCHEMA

ROOT=Path(__file__).resolve().parents[1]
N06_CAPTURE=ROOT/'reports/wc_simple26d_memory_full36_collection_20261016_0455.json.gz'
N06_ACCEPTANCE=ROOT/'reports/wc_simple26d_memory_full36_independent_acceptance_20261016.json'


def synthetic_n05():
    from wcomr.paper_baseline_grid_r1 import METHODS,matrix
    plan=matrix(['SYNTHETIC_SCENE_'+str(i) for i in range(4)])
    rows=[];clock=1000.;load=100.
    for index,p in enumerate(plan):
        seconds=200.+3*METHODS.index(p['method'])+index%4
        rows.append(dict(p,status='COMPLETE',core_seconds=seconds-40.,started_unix=clock,ended_unix=clock+seconds))
        clock+=seconds+.5
    total=load+sum(r['ended_unix']-r['started_unix'] for r in rows)+120.
    revision='SYNTHETIC_N05_COSTS_NOT_CURRENT_EXPERIMENT'
    bill=dict(source_revision=revision,wall_seconds=total,actual_GPUh=total/3600)
    pool=dict(schema=SCHEMA,cap_gpu_hours=CAP,origin_used_gpu_hours=ORIGIN,origin_gpu_jobs_launched=0,
        jobs={'SYNTHETIC_ONLY':dict(status='SETTLED',actual_GPUh=bill['actual_GPUh'])},events=[])
    pool.update(BudgetPool.accounting(pool))
    value=dict(observed_unix=2000.,launch=dict(source_revision=revision),pool=pool,billing=bill,
        runner=dict(source_revision=revision,runs=rows,matrix=plan,load_seconds=load))
    return value


def encoded(value):
    raw=gzip.compress(json.dumps(value).encode());digest=hashlib.sha256(raw).hexdigest()
    accepted=dict(status='N05_CORE66_INDEPENDENTLY_ACCEPTED',full_denominator=66,formal_denominator=44,
        capture_sha256=digest,actual_GPUh=value['billing']['actual_GPUh'])
    return raw,accepted


def fixture():
    value=synthetic_n05();raw,accepted=encoded(value)
    one=source_costs(value,accepted,capture_sha256=hashlib.sha256(raw).hexdigest(),kind='N05')
    old=json.loads(gzip.decompress(N06_CAPTURE.read_bytes()));accept=json.loads(N06_ACCEPTANCE.read_text())
    two=source_costs(old,accept,capture_sha256=hashlib.sha256(N06_CAPTURE.read_bytes()).hexdigest(),kind='N06')
    path=Path(__file__).with_name('test_frozen_shared_production_r1.py')
    spec=importlib.util.spec_from_file_location('synthetic_cost_scope_fixture',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    _,bound=module.fixture()
    freeze=dict(method_ids=bound['method_ids'],parameters_frozen_from='DEVELOPMENT_ONLY',final_test_outputs_seen=False,
        repeat_timing_bindings=dict(FULL_NATIVE='NATIVE35',WORLD_CACHE='WC_DEFAULT',RA_CFG_CACHE='RA_DEFAULT',
            GCR_EFFICIENT='A_NO_P',CPA_HIGH_FIDELITY='TABLE_PHASE_H1'))
    return value,raw,accepted,bound,freeze,[one,two]


class WholeCardCostControls(unittest.TestCase):
    def test_accepted_real_N06_full_bill_load_requests_and_remainder_reconcile_readonly(self):
        original=N06_CAPTURE.read_bytes();v=json.loads(gzip.decompress(original));a=json.loads(N06_ACCEPTANCE.read_text())
        result=source_costs(v,a,capture_sha256=hashlib.sha256(original).hexdigest(),kind='N06')
        self.assertEqual(result['original_paths'],36)
        self.assertAlmostEqual(result['load_seconds']+result['sum_request_wall_seconds']+
            result['original_unattributed_seconds'],result['billed_wall_seconds'])
        self.assertEqual(len(result['methods']),6);self.assertGreater(result['original_unattributed_seconds'],0)
        self.assertEqual(N06_CAPTURE.read_bytes(),original)

    def test_original180_and40_scopes_price_one_load_each_without_admission(self):
        *_,bound,freeze,sources=fixture();before=copy.deepcopy((bound,freeze,sources))
        result=preview(bound,freeze,sources)
        self.assertEqual((bound,freeze,sources),before)
        self.assertEqual(result['N07']['complete_plan_positions'],180)
        self.assertEqual(result['N08']['complete_plan_positions'],40)
        from wcomr.balanced_repeat_execution_r1 import COUNTS
        self.assertEqual(result['N08']['scope_counts'],COUNTS)
        self.assertEqual(sum(c['paths'] for c in result['N07']['components']),180)
        self.assertEqual(sum(c['paths'] for c in result['N08']['components']),40)
        self.assertFalse(result['N07']['active_job_reservation_written']);self.assertEqual(result['GPU_submissions'],0)
        self.assertFalse(result['final_method_or_input_selection_made_by_estimator'])

    def test_metamorphic_core_timing_change_alone_cannot_manufacture_a_lower_fee(self):
        value,_,_,bound,freeze,sources=fixture();original=preview(bound,freeze,sources)
        for row in value['runner']['runs']:row['core_seconds']=1.
        raw,accepted=encoded(value)
        changed=source_costs(value,accepted,capture_sha256=hashlib.sha256(raw).hexdigest(),kind='N05')
        result=preview(bound,freeze,[changed,sources[1]])
        self.assertEqual(result['combined_estimate_GPUh'],original['combined_estimate_GPUh'])

    def test_fast_rejections_use_explicit_dense_proxy_without_dropping_the_method(self):
        value,_,_,bound,freeze,sources=fixture()
        for row in value['runner']['runs']:
            if row['method']=='WC_DEFAULT':row.update(status='TEXT_REJECTED',ended_unix=row['started_unix']+.001)
        raw,accepted=encoded(value);accepted['status']='N05_CORE66_ACCEPTED_WITH_REJECTIONS_RETAINED'
        source=source_costs(value,accepted,capture_sha256=hashlib.sha256(raw).hexdigest(),kind='N05')
        result=preview(bound,freeze,[source,sources[1]])
        self.assertIn('WC_DEFAULT',result['N07']['explicit_proxy_methods'])
        self.assertEqual(sum(c['paths'] for c in result['N07']['components'] if c['method']=='WC_DEFAULT'),18)
        self.assertTrue(all(c['planning_per_request_seconds']>1 for c in result['N07']['components'] if c['method']=='WC_DEFAULT'))

    def test_shortened_matrix_changed_roles_source_SHA_or_budget_window_are_refused(self):
        value,raw,accepted,bound,freeze,sources=fixture()
        for kind in ('prefix','reassigned','binding','seen_test'):
            b,f=copy.deepcopy((bound,freeze))
            if kind=='prefix':b['execution_plan'].pop()
            elif kind=='reassigned':b['execution_plan'][0]['method']='A_NO_P'
            elif kind=='binding':f['repeat_timing_bindings']['WORLD_CACHE']='RA_DEFAULT'
            else:f['final_test_outputs_seen']=True
            with self.subTest(kind=kind),self.assertRaises(ValueError):preview(b,f,sources)
        for kind in ('SHA','origin','clock'):
            v,a=copy.deepcopy((value,accepted));digest=hashlib.sha256(raw).hexdigest()
            if kind=='SHA':digest='0'*64
            elif kind=='origin':v['pool']['origin_used_gpu_hours']=0
            else:
                v['billing']['wall_seconds']=1.;v['billing']['actual_GPUh']=1./3600;a['actual_GPUh']=1./3600
            with self.subTest(kind=kind),self.assertRaises(ValueError):source_costs(v,a,capture_sha256=digest,kind='N05')

    def test_missing_dense_cost_stays_unknown_and_overhead_alone_can_cross_approval_limit(self):
        *_,bound,freeze,sources=fixture()
        missing=copy.deepcopy(sources);missing[0]['methods']['NATIVE35']['max_complete_request_seconds']=None
        result=preview(bound,freeze,missing)
        self.assertIsNone(result['N07']['forecast_complete_GPUh']);self.assertIsNone(result['combined_estimate_GPUh'])
        small=copy.deepcopy(sources)
        for s in small:
            s['load_seconds']=1.;s['residual_per_path_seconds']=0.
            for m in s['methods'].values():
                for key in ('max_complete_request_seconds','max_formal_request_seconds','max_warm_request_seconds'):
                    if m[key] is not None:m[key]=1.
        low=preview(bound,freeze,small)
        self.assertFalse(low['N07']['specific_card_approval_required_by_estimate'])
        small[0]['load_seconds']=12*3600
        high=preview(bound,freeze,small)
        self.assertTrue(high['N07']['specific_card_approval_required_by_estimate'])
        self.assertEqual(high['N07']['complete_plan_positions'],180)
        self.assertEqual(high['GPU_submissions'],0)

    def test_actual_cli_cold_stdlib_uses_complete_synthetic_N05_and_real_historical_N06(self):
        _,raw,accepted,bound,freeze,_=fixture()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);values={'N05-capture':root/'n05.gz','N05-acceptance':root/'n05.json',
                'N06-capture':N06_CAPTURE,'N06-acceptance':N06_ACCEPTANCE,
                'shared-bound-inputs':root/'bound.json','method-freeze':root/'freeze.json','output':root/'estimate.json'}
            values['N05-capture'].write_bytes(raw);values['N05-acceptance'].write_text(json.dumps(accepted))
            values['shared-bound-inputs'].write_text(json.dumps(bound));values['method-freeze'].write_text(json.dumps(freeze))
            command=[sys.executable,'-S',str(ROOT/'scripts/estimate_wc_paper_N07_N08_complete_cost_r1.py')]
            for k,v in values.items():command+=['--'+k,str(v)]
            child=subprocess.run(command,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,timeout=10)
            self.assertEqual(child.returncode,0,child.stderr.decode())
            result=json.loads(values['output'].read_text())
            self.assertEqual(result['N07']['complete_plan_positions'],180);self.assertEqual(result['N08']['complete_plan_positions'],40)
            self.assertEqual(result['server_ledger_written'],False);self.assertEqual(result['SSH_queries'],0)


if __name__=='__main__':unittest.main()
