"""Offline full-terminal/CLI exercises. All clocks, videos and scores are synthetic."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_cara_history104_combination_r1 import fixture
from test_policy_price_terminal_r1 import put
from wcomr.policy_price_terminal_r1 import record
from wcomr.policy_generator_r1.historical_terminal import accept, scientific
from wcomr.policy_generator_r1.historical_result_analysis_r1 import summarize, route
from analyze_cara_history104_results_r1 import verify_handoff, render

ROOT=Path(__file__).resolve().parents[1]


def set_clock(c, section, role, seconds):
    runner=record(c,'runner');changed=0
    for row in runner['batch']['rows']:
        slot=row['slot']
        if slot['section']==section and slot['role']==role:
            changed+=1
            row['result'].update(full_request_seconds=seconds,core_seconds=seconds-1)
            c['requests'][slot['id']]['result'].update(full_request_seconds=seconds,core_seconds=seconds-1)
    assert changed, 'Synthetic mutation must reach a registered row'
    put(c,'runner',runner)
    put(c,'post',dict(scientific=scientific(c),runner_sha256=c['files']['runner']['sha256']))
    postexit=record(c,'post_exit');postexit['final_result_sha256']=c['files']['post']['sha256'];put(c,'post_exit',postexit)


class Handoff(unittest.TestCase):
    def setUp(self):self.c=fixture()
    def summary(self):
        a=accept(self.c)
        return summarize(record(self.c,'card'),a['scientific'],self.c['requests'])
    def test_protocol_acceptance_survives_failed_timing_model(self):
        set_clock(self.c,'VALIDATION','S24_C',280.)
        a=accept(self.c);self.assertTrue(a['full_protocol_accepted']);self.assertFalse(a['timing_model_validated'])
        r=self.summary();self.assertEqual(r['P1_continuation']['diagnosis'],'COST_MODEL_NOT_VALIDATED')
        self.assertTrue(any(not x['passed'] for x in r['timing']['acceptance_checks']))
    def test_validation_round_failure_not_hidden_by_average(self):
        set_clock(self.c,'CALIBRATION','S25_C',240.)
        set_clock(self.c,'VALIDATION','S25_C',260.)
        r=next(x for x in self.summary()['budget_boundaries'] if x['role']=='S25_C')
        self.assertLess(r['full_request_mean_seconds'],256)
        self.assertFalse(r['validation_measured_feasible']);self.assertTrue(r['round_feasibility_disagrees'])
    def test_measured_exact_budget_inclusive_without_six_second_penalty(self):
        set_clock(self.c,'VALIDATION','S25_C',256.)
        r=next(x for x in self.summary()['budget_boundaries'] if x['role']=='S25_C')
        self.assertTrue(r['validation_measured_feasible']);self.assertEqual(r['validation_headroom_seconds'],0.)
        set_clock(self.c,'VALIDATION','S25_C',256.00001)
        self.assertFalse(next(x for x in self.summary()['budget_boundaries'] if x['role']=='S25_C')['validation_measured_feasible'])
    def test_warm_and_diagnostic_clocks_excluded_from_fit(self):
        before=self.summary()
        set_clock(self.c,'WARM','S24_C',300.)
        set_clock(self.c,'DIAGNOSTIC','S26_A_PHASE',301.)
        after=self.summary()
        self.assertEqual(before['timing']['frozen_result'],after['timing']['frozen_result'])
        self.assertEqual(before['baseline_role_table'],after['baseline_role_table'])
    def test_all_three_strong_baselines_retained_on_quality_loss(self):
        card=record(self.c,'card');s=accept(self.c)['scientific']
        for row in s['quality']['GRAPH_DIVERSE_ORIGINAL']:row['LPIPS']=.2
        r=summarize(card,s,self.c['requests'])
        self.assertEqual({x['right'] for x in r['strong_baseline_assessment']},{'S26_C','S26_A_PHASE','SHARED26_C'})
        self.assertTrue(all(x['LPIPS_delta']['positive_prompts']==4 for x in r['strong_baseline_assessment']))
        self.assertTrue(all(not x['equal_measured_time_claim'] for x in r['strong_baseline_assessment']))
        self.assertIsNone(r['P1_continuation']['selected_policy'])
    def test_all_preparation_branches_never_admit_next_gpu(self):
        cases=[(False,False,False,'COST_MODEL_NOT_VALIDATED'),
               (True,False,False,'TESTED_LAYOUTS_EXCEED_MEASURED_BUDGET'),
               (True,True,False,'MEASURED_FEASIBLE_BUT_NO_CONSERVATIVE_PROPOSAL_HEADROOM'),
               (True,True,True,'VALIDATED_MODEL_WITH_TESTED_PROPOSAL_HEADROOM')]
        for model,measured,predicted,expected in cases:
            r=route(dict(timing_model_validated=model),[dict(validation_measured_feasible=measured,planning_feasible_with_fixed_margin=predicted)])
            self.assertEqual(r['diagnosis'],expected);self.assertFalse(r['GPU_dispatch_ready']);self.assertFalse(r['PG_P2_input_ready'])
    def test_render_exposes_boundaries_and_each_frozen_timing_gate(self):
        text=render(self.summary())
        for x in ('第一轮','第二轮','跨轮越界','maximum_underestimate_seconds','no_false_feasible'):self.assertIn(x,text)
    def test_handoff_rejects_other_run_source_scope_and_card(self):
        L=self.c['launch'];spec={k:copy.deepcopy(L[k]) for k in ('launch_id','source_revision','run_id','scope_counts')}
        spec.update(launch_sha256='expected',card_sha256=self.c['files']['card']['sha256'])
        verify_handoff(spec,L,'expected',self.c)
        for key in ('launch_id','source_revision','run_id','scope_counts','launch_sha256','card_sha256'):
            wrong=copy.deepcopy(spec);wrong[key]='wrong'
            with self.assertRaises(ValueError):verify_handoff(wrong,L,'expected',self.c)
    def test_real_CLI_complete_replay_unique_outputs_and_invalid_prefix(self):
        with tempfile.TemporaryDirectory(prefix='cara104-synthetic-') as tmp:
            p=Path(tmp)
            def save(name,value):
                q=p/name;q.write_text(json.dumps(value,sort_keys=True));return q
            capture=save('capture.json',self.c);launch=save('launch.json',self.c['launch'])
            digest=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
            a=accept(self.c);a.update(capture_ref=str(capture),capture_sha256=digest(capture));accepted=save('accepted.json',a)
            spec={k:self.c['launch'][k] for k in ('launch_id','source_revision','run_id','scope_counts')}
            spec.update(launch_sha256=digest(launch),card_sha256=self.c['files']['card']['sha256']);handoff=save('handoff.json',spec)
            args=[sys.executable,str(ROOT/'scripts/analyze_cara_history104_results_r1.py'),'--capture',str(capture),'--accepted',str(accepted),'--launch-ref',str(launch),'--handoff-spec',str(handoff),'--output']
            env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1')
            def run(out):return subprocess.run(args+[str(out)],cwd=ROOT,env=env,capture_output=True,text=True,timeout=60)
            out=p/'analysis.json';r=run(out);self.assertEqual(r.returncode,0,r.stderr)
            result=json.loads(out.read_text());self.assertTrue(result['full_protocol_accepted']);self.assertFalse(result['P1_continuation']['GPU_dispatch_ready'])
            self.assertEqual(result['information_exposure']['cumulative_unique_if104_quality_used'],11)
            self.assertEqual(result['evidence']['handoff_spec']['sha256'],digest(handoff))
            second=p/'second.json';self.assertEqual(run(second).returncode,0);self.assertEqual(out.read_bytes(),second.read_bytes())
            original=out.read_bytes();self.assertNotEqual(run(out).returncode,0);self.assertEqual(out.read_bytes(),original)
            a['full_protocol_accepted']=False;save('accepted.json',a)
            invalid=p/'invalid.json';self.assertNotEqual(run(invalid).returncode,0);self.assertFalse(invalid.exists());self.assertFalse(invalid.with_suffix('.md').exists())


if __name__=='__main__':unittest.main()
