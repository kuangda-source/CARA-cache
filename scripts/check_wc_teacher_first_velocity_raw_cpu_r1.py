"""Reload all teacher-first Toy raw files independently of the sampling test."""
import argparse,hashlib,json,os,sys
from pathlib import Path
from types import SimpleNamespace


def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES']='';sys.path.insert(0,str(a.stage/'src'))
    import torch
    from wcomr.mid_coverage import tree_digest
    from wcomr.teacher_first_velocity_alignment_r1 import TeacherFirstController
    from wcomr.cfg_ra_joint_control import Calibration
    from wcomr.source_aware_cpd_control import Costs
    torch.set_num_threads(2);assert not torch.cuda.is_initialized()
    def forbid(*args,**kwargs):raise RuntimeError('Raw CPU audit forbids CUDA/downloads')
    torch.cuda._lazy_init=forbid;torch.hub.download_url_to_file=forbid
    sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    result=json.loads((a.stage/'CPU-result.json').read_text())
    reg=json.loads((a.stage/'registration.json').read_text())
    assert result['status']=='TEACHER_FIRST_TWO_FLOW_FULL24_PARENTS32_ENDPOINT_SUFFIXES_CPU_PASS_NOT_GPU'
    assert result['actual_CPU_parents']==24 and result['endpoint_suffixes']==32 and result['teacher_pairs']==8
    assert all(sha(a.stage/n)==h for n,h in reg['payload_sha256'].items())
    raw_root=(a.stage/'CPU-artifacts').resolve();files=set();tensor_count=0;rows=[];cells={}
    def load(bound,expected_keys):
        nonlocal tensor_count
        path=Path(bound['path']).resolve()
        assert path.is_relative_to(raw_root) and path not in files
        files.add(path);value=torch.load(path,weights_only=True,map_location='cpu')
        assert set(value)==expected_keys and tree_digest(value)==bound['tensor_sha256']
        def tensors(v):
            if isinstance(v,torch.Tensor):return [v]
            if isinstance(v,dict):return [t for x in v.values() for t in tensors(x)]
            if isinstance(v,(tuple,list)):return [t for x in v for t in tensors(x)]
            raise ValueError('Raw payload contains a non-tensor leaf')
        ts=tensors(value);tensor_count+=len(ts)
        assert all(bool(torch.isfinite(t).all()) for t in ts)
        return value
    for flow in result['checks']:
        assert flow['ordinary_initial_state_restored'] and flow['four_cells']
        for parent in flow['checks']:
            point=parent['point'];step=point['chosen']['step'];event=parent['event']
            key=point['source']+'_'+point['phase'];cells[key]=cells.get(key,0)+1
            assert parent['actual_diagnostic_pairs']==36+2*(37-step)+1
            assert event['actual_teacher_pairs']==1 and event['actual_teacher_calls']==2
            assert event['only_first_returned_velocity_changed'] and not event['teacher_committed_to_parent_or_suffix']
            teacher_record=event['teacher_record']
            teacher=load(teacher_record['artifact'],{'teacher_velocity','actual_latent','noise','timestep'})
            assert tree_digest((teacher['noise'],teacher['actual_latent'],teacher['timestep']))==teacher_record['input_sha256']
            assert tree_digest(teacher['teacher_velocity'])==teacher_record['teacher_velocity_sha256']
            assert not teacher_record['teacher_committed'] and len(teacher_record['serial_restores'])==1
            assert teacher_record['prefix_physical_sha256']==event['prefix_physical_sha256']
            assert teacher_record['prefix_owned_sha256']==event['prefix_owned_sha256']
            assert teacher_record['history']['action']=='DD'
            assert all(h[-1]==step for h in teacher_record['history']['true_D_after'])
            by={b['label']:b for b in event['branches']}
            assert set(by)=={'C_REPLAY','TEACHER_FIRST'} and len(event['serial_restores'])==4
            teacher_guided=teacher['teacher_velocity'][0]+7*(teacher['teacher_velocity'][0]-teacher['teacher_velocity'][1])
            for label,branch in by.items():
                raw=load(branch['artifact'],{'final_latent','guided','first_C_velocity'})
                assert len(raw['guided'])==len(branch['actions'])==37-step
                assert [tree_digest(t) for t in raw['guided']]==branch['guided_sha256']
                assert tree_digest(raw['final_latent'])==branch['final_latent_sha256']
                assert tree_digest(raw['first_C_velocity'])==branch['first_C_velocity_sha256']
                assert branch['first_readout']=='C' and branch['actions'][0]=='CC'
                first=branch['source_policy_tail'][0]
                assert first['true_D_before']==first['true_D_after']
                assert all(h[-1]==point['chosen']['true_D_anchor'] for h in first['true_D_after'])
                assert first['source_policy']['decision']['reason']=='MATH_EVENT_SUFFIX_FIRST:C'
                assert all(not h['source_policy']['decision']['reason'].startswith('MATH_EVENT_SUFFIX_FIRST:') for h in branch['source_policy_tail'][1:])
                if label=='TEACHER_FIRST':
                    assert branch['teacher_velocity_injected'] and torch.equal(raw['guided'][0],teacher_guided)
                    assert branch['first_returned_velocity_sha256']==teacher_record['teacher_velocity_sha256']
                else:
                    assert not branch['teacher_velocity_injected']
                    assert branch['first_returned_velocity_sha256']==branch['first_C_velocity_sha256']
                    assert torch.equal(raw['guided'][0],raw['first_C_velocity'][0]+7*(raw['first_C_velocity'][0]-raw['first_C_velocity'][1]))
            assert by['C_REPLAY']['first_C_cache_state_sha256']==by['TEACHER_FIRST']['first_C_cache_state_sha256']
            assert by['C_REPLAY']['first_C_velocity_sha256']==by['TEACHER_FIRST']['first_C_velocity_sha256']
            assert parent['ordinary_and_old_and_new_parent_complete_equal'] and parent['new_C_and_original_C_full_suffix_equal']
            rows.append({'flow':flow['flow'],'point':point,'teacher_raw_sha256':sha(teacher_record['artifact']['path']),
                'teacher_restored_not_committed':True,'two_first_C_caches_equal':True,
                'first_returned_teacher_raw_exact':True,'old_C_and_parent_complete_equal':True})
    expected=sum(2*(40-r['point']['chosen']['step'])+5 for r in rows)
    assert len(files)==24 and len(rows)==8 and tensor_count==expected
    assert all(cells[k]==2 for k in ('D_EARLY','D_LATE','P_EARLY','P_LATE'))
    cal=Calibration('TEACHER_SCOPE_CPU',{(7,n):.99 for n in range(8,12)},{n:1. for n in range(1,37)})
    def packets(n):return [SimpleNamespace(slot=b,counter=2*(n-1)+b,delta_y=.001) for b in (0,1)]
    c=TeacherFirstController(cal,10.,Costs('TEACHER_SCOPE_CPU',1.,4.,None),None,registered_step=10)
    for n in range(1,8):c.commit_protected_dense(n,actual_action='D',pair_completed=True)
    for n in (8,9):
        d=c.decide(n,packets(n),both_sources_ready=True,partial_ready=False);c.commit(d,actual_action='C',pair_completed=True)
    prefix=c.state_dict()
    with c.teacher():
        try:c.state_dict()
        except ValueError:pass
        else:raise AssertionError('Active teacher snapshot accepted')
        d=c.decide(10,packets(10),both_sources_ready=True,partial_ready=False)
        assert d.action=='D' and d.reason=='MATH_EVENT_TEACHER_FIRST_OFFLINE:D'
        c.commit(d,actual_action='D',pair_completed=True)
    c.restore(prefix);assert c.state_dict()==prefix and not c.offline_teacher
    with c.first('C'):
        d=c.decide(10,packets(10),both_sources_ready=True,partial_ready=False)
        assert d.action=='C' and d.reason=='MATH_EVENT_SUFFIX_FIRST:C'
        c.commit(d,actual_action='C',pair_completed=True)
        future=c.decide(11,packets(11),both_sources_ready=True,partial_ready=False)
        assert future.reason=='cheapest_feasible_bound_action'
    out={'status':'TEACHER_FIRST_ALL24_RAW_TWO_FLOW_FRESH_TEACHER_AND_C_CACHE_CPU_PASS_NOT_GPU',
        'raw_files':24,'raw_tensors':tensor_count,'source_phase_cells':cells,'rows':rows,
        'one_teacher_strict_restore_first_C_and_future_pi0':True,
        'active_teacher_snapshot_refused':True,'sampling_result_sha256':sha(a.stage/'CPU-result.json'),
        'sampling_source_revision':reg['source_revision'],'GPU_submissions':0,'CUDA_initialized':False,'ledger_written':False}
    assert not a.output.exists();a.output.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:out[k] for k in ('status','raw_files','raw_tensors','GPU_submissions')}))


if __name__=='__main__':main()
