"""Exact real accepted R2 cohort; no model/video/GPU/network access."""
import copy,hashlib,importlib.util,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    source=ROOT/'scripts/check_wc_N10_R2_actual_inputs_independent_r1.py'
    spec=importlib.util.spec_from_file_location('real_N10_metadata_checker',source)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    raw,prepared,protocol=[m.load(n) for n in (m.SOURCE,m.INPUTS,m.PROTOCOL)]
    result=m.verify(raw,prepared,protocol);assert result['expected_ready_scores']==645
    mutations=[
        ('missing_metric_position',lambda x:x['input_bundle']['rows'].pop()),
        ('filename_substituted_prompt',lambda x:x['input_bundle']['rows'][0].update(prompt='filename inference')),
        ('wrong_frame_selection',lambda x:x['input_bundle']['rows'][0]['expected_sampling'].update(frame_indices=[0])),
        ('shrunk_methods',lambda x:x['input_bundle']['methods'].pop()),
        ('posthoc_static_eligibility',lambda x:x['input_bundle']['cases'][0].update(static_eligible=True)),
        ('planned_identity_promoted_to_production',lambda x:x['input_bundle']['evaluator_identity'].update(production_eligible=True)),
        ('wrong_original_source',lambda x:x.update(source_N07_revision='f'*40)),
        ('rejected_video_invented',lambda x:next(q for q in x['input_bundle']['rows'] if q['input_status']=='VIDEO_UNAVAILABLE').update(input_status='READY_TO_SCORE',video_path='invented.mp4',video_sha256='a'*64)),
    ]
    accepted=[]
    for name,mutation in mutations:
        candidate=copy.deepcopy(prepared);mutation(candidate)
        bundle=candidate['input_bundle']
        bundle['scorer_fingerprint']=m.fingerprint(bundle['evaluator_identity'])
        for q in bundle['rows']:q['scorer_fingerprint']=bundle['scorer_fingerprint']
        bundle['fingerprint']=m.fingerprint({k:v for k,v in bundle.items() if k!='fingerprint'})
        try:m.verify(raw,candidate,protocol)
        except (AssertionError,KeyError,ValueError):accepted.append(name)
        else:raise AssertionError('Changed real cohort accepted: '+name)
    result=dict(status='N10_R2_REAL960_METADATA_POSITIVE_AND8_NEGATIVE_CONTROLS_PASS',positive_real_full960=1,
        negative_controls=accepted,checker_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        control_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        fingerprints_rebuilt_in_negative_cases=True,GPU_submissions=0,SSH_queries=0,model_imported=False)
    out=ROOT/'reports/wc_paper_N10_R2_actual960_metadata_negative_controls_v2_20261017.json'
    assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
