"""Independent collector analysis keeps all denominators and rejects false means."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

from wcomr.paper_baseline_grid_r1 import matrix,point
from wcomr.paper_baseline_post_r1 import summaries

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('n05_independent',ROOT/'scripts/analyze_wc_paper_N05_core66_r1.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def fixture(reject=False):
    scope=json.loads((ROOT/'manifests/wc_paper_N05_core66_preregistration_r1_20261016.json').read_text())
    scenes=[r['name'] for r in scope['requests']];rows=[]
    for planned in matrix(scenes):
        n=point(planned['method'])['actual_updates'];is_native=planned['method']=='NATIVE35'
        rows.append(dict(**planned,status='COMPLETE',core_seconds=300. if is_native else 120.,
            baseline_grid_point=point(planned['method']),solver_steps=n,guided_pairs=n,
            endpoint_audit='PASS',raw_model_audit='PASS',request_memory_lifecycle={'components_alive_after':0},
            decoded_video={'frames':93},video_artifact={'sha256':planned['id']}))
    for r in rows:
        if r['section']!='TIMED':continue
        reference=next(x for x in rows if x['section']=='TIMED' and x['scene']==r['scene'] and x['method']=='NATIVE35')
        distances=[0. if r['method']=='NATIVE35' else .2]*93
        r['LPIPS']=dict(frames=93,frame_distances=distances,mean_LPIPS=sum(distances)/93,
            reference_sha256=reference['id'],candidate_sha256=r['id'])
    if reject:
        r=next(r for r in rows if r['section']=='TIMED' and r['method']=='RA_DEFAULT')
        r.update(status='TEXT_REJECTED',solver_steps=0,guided_pairs=0);r.pop('LPIPS')
    final=dict(status='N05_CORE66_COMPLETE44_AUDITED_93FRAME_SCORED' if not reject else
        'N05_CORE66_FULL_SCOPE_REJECTIONS_OR_MISSING_REFERENCES_RETAINED',source_revision='source',
        scope_counts=scope['scope_counts'],rows=rows,audit_failures=[],
        warm_repeat_controls=[dict(status='PASS') for _ in range(11)],
        warm_guided_controls=[dict(status='PASS') for _ in range(5)],
        original420_default_controls=[dict(status='PASS') for _ in range(20)],**summaries(rows,scenes))
    launch=dict(run_id=scope['run_id'],scope_counts=scope['scope_counts'],source_revision='source',
        next_check_not_before_unix=100.,supervisor_identity=dict(pid=1,start_ticks=1),post_watcher_pid=2)
    supervisor=dict(source_revision='source',child_exit_code=0,child_identity=dict(pid=3,start_ticks=3),
        runner_sha256='runner_hash',billing_sha256='bill_hash',actual_GPUh=1.)
    job=dict(status='SETTLED',actual_GPUh=1.,billing_sha256='bill_hash')
    return dict(status='N05_CORE66_ORIGINAL_ONCE_CAPTURE',observed_unix=101.,launch=launch,
        final=final,runner=dict(source_revision='source',runs=copy.deepcopy(rows)),supervisor=supervisor,
        billing=dict(source_revision='source',wall_seconds=3600.,actual_GPUh=1.),
        production_CPU=dict(source_revision='source'),registration=dict(source_revision='source'),
        payload_verified={'critical':True},own_UUID_lock_free=True,post_exit=dict(exit_code=0),
        runner_sha256='runner_hash',billing_sha256='bill_hash',
        original_processes={k:dict(pid=i,state=None,start_ticks=None) for k,i in
            [('supervisor_pid',1),('post_watcher_pid',2),('child_pid',3)]},
        pool=dict(origin_used_gpu_hours=10.,cap_gpu_hours=20.,used_gpu_hours=11.,reserved_gpu_hours=0.,
            available_gpu_hours=9.,jobs={scope['run_id']:job}))

class IndependentAcceptance(unittest.TestCase):
    def test_complete66_and44_reconstructs_cost_and_all_frame_means(self):
        result=module.accept(fixture())
        self.assertEqual(result['status'],'N05_CORE66_INDEPENDENTLY_ACCEPTED')
        self.assertEqual(result['scored_formal_videos'],44)
        self.assertEqual(result['fresh_v2_remaining_GPUh'],9.)

    def test_rejection_keeps_denominator_without_fake_four_scene_mean(self):
        result=module.accept(fixture(True))
        self.assertEqual(result['formal_denominator'],44)
        self.assertEqual(result['scored_formal_videos'],43)
        row=next(r for r in result['independent_methods'] if r['method']=='RA_DEFAULT')
        self.assertIsNone(row['mean_seconds']);self.assertIsNone(row['mean_LPIPS'])

    def test_false_frame_mean_bad_bill_and_reduced_scope_all_refused(self):
        for kind in ('frame','bill','scope'):
            v=fixture()
            if kind=='frame':next(r for r in v['final']['rows'] if r.get('LPIPS'))['LPIPS']['mean_LPIPS']+=.1
            elif kind=='bill':v['billing']['actual_GPUh']=.5
            else:v['final']['rows'].pop()
            with self.assertRaises((AssertionError,ValueError)):module.accept(v)

if __name__=='__main__':unittest.main()
