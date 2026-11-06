#!/usr/bin/env python3
"""Independently reload every Toy endpoint suffix and check controller scope."""
import argparse,hashlib,json,os,sys
from pathlib import Path
from types import SimpleNamespace


def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES']='';sys.path.insert(0,str(a.stage/'src'))
    import torch
    from wcomr.mid_coverage import tree_digest
    from wcomr.pi0_readout_suffix8_r1 import FirstReadoutController
    from wcomr.cfg_ra_joint_control import Calibration
    from wcomr.source_aware_cpd_control import Costs
    from wcomr.source_aware_phase_control import CreationPhasePrior
    torch.set_num_threads(2);assert not torch.cuda.is_initialized()
    v=json.loads((a.stage/'CPU-result.json').read_text());reg=json.loads((a.stage/'registration.json').read_text())
    assert v['status']=='PI0_SUFFIX8_TWO_FLOW_FULL16_PARENTS16_ENDPOINT_SUFFIXES_CPU_PASS_NOT_GPU'
    assert v['actual_CPU_paths']==16 and v['endpoint_suffixes']==16 and v['events']==8
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert all(sha(a.stage/n)==h for n,h in reg['payload_sha256'].items())
    files=set();raw_tensors=0;cells={};requests=[]
    for flow in v['checks']:
        for parent in flow['checks']:
            assert parent['ordinary_parent_and_default_suffix_full_equal'] and parent['parent36_actions_guided_final_and_video_equal'] and parent['default_endpoint_decoder_writer_equal']
            point=parent['point'];n=point['chosen']['step'];event=parent['event']
            key=point['source']+'_'+point['phase'];cells[key]=cells.get(key,0)+1
            assert event['actual_teacher_calls']==0 and event['one_step_readout_only'] and len(event['serial_restores'])==4
            assert parent['actual_diagnostic_pairs']==36+2*(37-n)
            rows=[]
            for branch in event['branches']:
                path=Path(branch['artifact']['path']).resolve();assert path.is_relative_to((a.stage/'CPU-artifacts').resolve()) and path not in files
                files.add(path);raw=torch.load(path,weights_only=True,map_location='cpu')
                assert set(raw)=={'final_latent','guided'} and tree_digest(raw)==branch['artifact']['tensor_sha256']
                assert len(raw['guided'])==len(branch['actions'])==37-n
                assert tree_digest(raw['final_latent'])==branch['final_latent_sha256']
                assert [tree_digest(x) for x in raw['guided']]==branch['guided_sha256']
                assert all(bool(torch.isfinite(t).all()) for t in [raw['final_latent']]+raw['guided'])
                assert branch['source_policy_tail'][0]['source_policy']['decision']['reason']=='MATH_EVENT_SUFFIX_FIRST:'+branch['first_readout']
                assert all(not h['source_policy']['decision']['reason'].startswith('MATH_EVENT_SUFFIX_FIRST:') for h in branch['source_policy_tail'][1:])
                raw_tensors+=1+len(raw['guided']);rows.append({'label':branch['label'],'first_readout':branch['first_readout'],
                    'remaining_updates':len(raw['guided']),'raw_sha256':sha(path),'video_mock_sha256':sha(Path(branch['artifact']['video_path']))})
            requests.append({'flow':flow['flow'],'selection':point,'branches':rows,'parent_and_default_original_tail_equal':True})
    assert len(files)==16 and len(requests)==8 and all(cells[k]==2 for k in ('D_EARLY','D_LATE','P_EARLY','P_LATE'))
    # Use the actual controller with scalar paid packets: one legal first A,
    # ordinary future choices, exact prefix rollback, and explicit refusals.
    cal=Calibration('CPU_SCOPE_ONLY',{(7,n):.99 for n in range(8,12)},{n:1. for n in range(1,37)})
    def controller(P=False):
        c=FirstReadoutController(cal,10.,Costs('CPU_SCOPE_ONLY',1.,4.,.5 if P else None),
            CreationPhasePrior('CPU_SCOPE_ONLY',.0001,.3,early_creation_floor=.0001,late_creation_floor=10.) if P else None,registered_step=10)
        for n in range(1,8):c.commit_protected_dense(n,actual_action='D',pair_completed=True)
        for n in (8,9):
            d=c.decide(n,packets(n),both_sources_ready=True,partial_ready=False);c.commit(d,actual_action='C',pair_completed=True)
        return c
    def packets(n):return [SimpleNamespace(slot=b,counter=2*(n-1)+b,delta_y=.001) for b in (0,1)]
    c=controller();prefix=c.state_dict()
    with c.first('A'):
        d=c.decide(10,packets(10),both_sources_ready=True,partial_ready=False);assert d.action=='C' and d.reason.endswith(':A')
        c.commit(d,actual_action='C',pair_completed=True)
        future=c.decide(11,packets(11),both_sources_ready=True,partial_ready=False);assert future.reason=='cheapest_feasible_bound_action'
        c.commit(future,actual_action='C',pair_completed=True)
        try:c.state_dict()
        except ValueError:pass
        else:raise AssertionError('Active intervention snapshot accepted')
    c.restore(prefix);assert c.last_completed_step==9 and c.first_readout is None
    try:
        with c.first('P'):pass
    except ValueError:pass
    else:raise AssertionError('P readout intervention accepted')
    bad=controller(P=True)
    try:
        with bad.first('A'):bad.decide(10,packets(10),both_sources_ready=True,partial_ready=True)
    except ValueError as e:assert 'natural legal C' in str(e)
    else:raise AssertionError('Natural P silently changed into C/A')
    out={'status':'PI0_SUFFIX8_ALL16_RAW_TWO_FLOW_COMPLETE_TAIL_AND_SCOPE_CPU_PASS_NOT_GPU',
        'raw_files':16,'raw_tensors':raw_tensors,'source_phase_cells':cells,'requests':requests,
        'controller_one_step_future_unchanged_prefix_rollback':True,'active_snapshot_P_action_nonnatural_C_refused':True,
        'sampling_result_sha256':sha(a.stage/'CPU-result.json'),'GPU_submissions':0,'CUDA_initialized':False,'ledger_written':False}
    assert not a.output.exists();a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ('status','raw_files','raw_tensors','source_phase_cells','GPU_submissions')}))


if __name__=='__main__':main()
