"""Independent complete CAL35 acceptance; every arm and missing denominator kept."""
import argparse,itertools,json,math,statistics
from pathlib import Path


def mean(x):return statistics.mean(x)


def paired_interval(differences):
    # Four exposed CAL prompts: exact prompt bootstrap; descriptive only.
    values=sorted(mean(sample) for sample in itertools.product(differences,repeat=len(differences)))
    return [values[math.floor(.025*(len(values)-1))],values[math.ceil(.975*(len(values)-1))]]


def analyze(card,collection,scores,release):
    from wcomr.cara_f19_speed190_card_r1 import validate,ROLES
    validate(card)
    assert all(release[k] for k in ('GPU_released','mode_restored','cost_settled','original_processes_ended','container_exit_success'))
    assert not release['hard_limit_exceeded'] and release['actual_GPUh']<=3.
    assert collection['scope_sha256']==scores['scope_sha256']==card['scope_sha256']
    assert collection['status']=='COMPLETE35_PENDING_RELEASE_SCORING' and len(collection['rows'])==35
    assert [r['slot'] for r in collection['rows']]==card['matrix']
    assert all(r['status']=='COMPLETE' and not r['result']['CPU_fixture'] for r in collection['rows'])
    assert scores['status']=='COMPLETE35_RGB_24_LPIPS_84_QUALITY_PENDING_ACCEPTANCE'
    assert not scores['CUDA_initialized'] and scores['RGB_controls_passed']
    assert len(scores['RGB'])==35 and len(scores['LPIPS'])==24 and len(scores['quality_rows'])==84
    formal=[r for r in collection['rows'] if r['slot']['section']=='FORMAL']
    members=card['FIT']+card['CHECK'];dims=list(card['success']['independent_quality_min_differences'])
    latency={};quality={};fidelity={};role_rows=[]
    for r in collection['rows']:
        slot,res=r['slot'],r['result']
        assert res['guided_pairs']==res['solver_steps']==36 and res['scope_sha256']==card['scope_sha256']
        if slot['eligible_clean_time']:
            assert all(res[k]==0 for k in ('in_timing_guided_copies','in_timing_hashes','research_checkpoints'))
            assert all(math.isfinite(res[k]) and res[k]>0 for k in ('T_DD','T_request'))
        if slot['section']=='FORMAL':latency[slot['member'],slot['role']]=res
    for row in scores['quality_rows']:
        p=row['planned'];v=row['result'];assert row['status']=='SCORED' and v['status']=='SCORED' and math.isfinite(v['value'])
        slot=next(r['slot'] for r in formal if r['slot']['id']==p['method'])
        assert p['case_id']==slot['member'] and p['role']==slot['role']
        key=(slot['member'],slot['role'],p['dimension']);assert key not in quality;quality[key]=v['value']
    for row in scores['LPIPS']:
        key=(row['member'],row['role']);assert key not in fidelity
        v=row['result'];assert v['status']=='COMPLETE' and v['frames']==93 and len(v['Alex_frames'])==93
        assert math.isfinite(v['Alex']);fidelity[key]=v['Alex']
    assert len(quality)==84 and len(fidelity)==24
    native=mean(latency[m,'NATIVE35']['T_DD'] for m in members)
    for role in ROLES:
        t=mean(latency[m,role]['T_DD'] for m in members)
        lp=0. if role=='NATIVE35' else mean(fidelity[m,role] for m in members)
        gates=[]
        for ref in card['success']['quality_references']:
            for dim in dims:
                diff=[quality[m,role,dim]-quality[m,ref,dim] for m in members]
                threshold=card['success']['independent_quality_min_differences'][dim]
                gates.append(dict(reference=ref,dimension=dim,mean_difference=mean(diff),
                    exact_four_prompt_bootstrap95=paired_interval(diff),minimum_difference=threshold,
                    passed=mean(diff)>=threshold))
        passed=native/t>=1.9 and t<=133. and lp<=.27 and all(r['passed'] for r in gates)
        role_rows.append(dict(role=role,T_DD=t,T_request=mean(latency[m,role]['T_request'] for m in members),
            speedup_T_DD=native/t,LPIPS_Alex=lp,quality={d:mean(quality[m,role,d] for m in members) for d in dims},
            quality_gates=gates,meets_frozen_CAL_target=passed))
    return dict(status='CAL35_FULL_ACCEPTED',scope_sha256=card['scope_sha256'],release=release,
        physical_paths=35,actual_guided_pairs=1260,formal_positions=28,RGB_positions=35,LPIPS_pairs=24,quality_positions=84,
        controls=collection['controls'],rows=role_rows,independent_new_inputs=False,old_CHECK_exposed=True,
        passing_roles=[r['role'] for r in role_rows if r['meets_frozen_CAL_target']],
        conclusion_scope='Four exposed CAL inputs; no independent generalization or paper result claim',
        shared25_independent_confirmation_planning_GPUh_preserved=10.)


def main():
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
    p=argparse.ArgumentParser()
    for k in ('card','collection','scores','release','output'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();read=lambda p:json.loads(p.read_text())
    result=analyze(*(read(getattr(a,k)) for k in ('card','collection','scores','release')))
    with a.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
