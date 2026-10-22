"""Read six frozen same-state C/A/D banks on CPU; no new teacher call."""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);p.add_argument('--diagnostics-source',type=Path,required=True);a=p.parse_args()
    sys.path[:0]=[str(a.stage),str(a.stage/'inputs/src')]
    from four_card_bank24_execution_tools_r1 import verify_registration,read,sha
    import importlib.util
    spec=importlib.util.spec_from_file_location('registered_XR_diagnostics',a.diagnostics_source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    amplitude_and_direction=module.amplitude_and_direction
    from wcomr.mid_coverage import tree_digest
    import torch
    torch.set_num_threads(2)
    assert not list(Path('/dev').glob('nvidia*'))
    torch.cuda._lazy_init=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('No CUDA in X-R'))
    reg=verify_registration(a.stage);original=read(a.stage/'CPU-final-results.json')
    rows=[r for r in original['rows'] if r['section']=='TIMED' and r['method']!='NATIVE35'];assert len(rows)==12
    result=[]
    for scene in dict.fromkeys(r['scene'] for r in rows):
        d=next(r for r in rows if r['scene']==scene and r['method']=='D21')
        arow=next(r for r in rows if r['scene']==scene and r['method']=='A21')
        assert d['scout_observation']['pre_action_input_sha256']==arow['scout_observation']['pre_action_input_sha256']
        banks=[]
        for r in (d,arow):
            assert r['vector_audit']==r['raw_model_audit']=='PASS'
            info=r['scout_vectors_artifact'];assert sha(info['path'])==info['sha256']
            bank=torch.load(info['path'],map_location='cpu',weights_only=True)
            assert all(tree_digest(t)==r['scout_vector_metadata'][name]['tree_sha256'] for name,t in bank.items())
            banks.append(bank)
        db,ab=banks
        assert all(torch.equal(db[k],ab[k]) for k in ('p20_c','p20_u','p21_c','p21_u'))
        assert d['scout_observation']['actual_action']=='DD' and arow['scout_observation']['actual_action']=='CC'
        # The hook records physical CC output before A's post-RF fusion, and
        # returned A after fusion. D comes from the paired equal-state path.
        c,phi,teacher=ab['v_actual21'],ab['v_returned21'],db['v_actual21']
        metrics=amplitude_and_direction(c,phi,teacher,torch=torch)
        metrics.update(visible_C_RMS=float(c.double().square().mean().sqrt()),
            visible_correction_RMS=float((phi.double()-c.double()).square().mean().sqrt()))
        result.append(dict(scene=scene,metrics=metrics,pre_action_input_sha256=d['scout_observation']['pre_action_input_sha256'],
            D_vectors=d['scout_vectors_artifact'],A_vectors=arow['scout_vectors_artifact']))
        del db,ab,banks,c,phi,teacher
    assert len(result)==6 and not torch.cuda.is_initialized()
    print(json.dumps(dict(status='BANK24_SIX_SAME_STATE_FIXED_XR_CPU_DIAGNOSTICS',rows=result,
        original_final_sha256=sha(a.stage/'CPU-final-results.json'),registration_sha256=sha(a.stage/'registration.json'),
        scientific_source_sha256=sha(a.diagnostics_source),
        GPU_submissions=0,new_teacher_calls=0,DEV_fit=False,quality_labels_read=False),allow_nan=False))


if __name__=='__main__':main()
