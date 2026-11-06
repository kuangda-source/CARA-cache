"""Coverage/counterbalance, stopwatch boundaries, failures and retained rejects."""
import copy
import json
from pathlib import Path
import pytest
from wcomr.clean_timing import attempts,validate_protocol,synchronized_timer,summarize,FORBIDDEN

ROOT=Path(__file__).resolve().parents[1]
REFERENCE=json.loads((ROOT/'reports/w1d_cal8_r1_runner.json').read_text())
PRIOR=json.loads((ROOT/'reports/w1_replay_r1_runner.json').read_text())

def fixture():
    p=json.loads((ROOT/'manifests/w1_clean_timing_protocol.json').read_text())
    f=json.loads((ROOT/'manifests/w1_fixed_replay_protocol.json').read_text())
    prior=json.loads((ROOT/'reports/w1_replay_r1_runner.json').read_text())
    source={x['name']:x['scalar_off'] for x in prior['cases']}
    rows=[]
    for attempt in p['attempts']:
        old=source[attempt['name']];replay=copy.deepcopy(old['replay']);replay['mode']=attempt['arm']
        if attempt['arm']=='official':
            for r in replay['records']:r['prediction']=None
        rows.append({'attempt':attempt,'status':'AUDITED','end_to_end_seconds':100 if attempt['arm']=='official' else 110,
                     'disabled_observers':FORBIDDEN,'flags_before':old['flags_before'],'flags_after':old['flags_before'],
                     'decode_flags':[dict(old['flags_before'],cudnn_benchmark=False,cudnn_deterministic=True)],
                     'guardrail_events':[{'stage':'text','accepted':True},{'stage':'video','accepted':True}],
                     'outcome':'ACCEPTED','trace':old['trace'],'block_counts':old['block_counts'],'replay':replay,
                     'artifact':{'sha256':'0'*64,'frames':93,'shape':[432,768,3],'finite':True,'timestamps_strictly_increasing':True, 'decoded_rgb_sha256':
                       [x['sha256'] for x in (REFERENCE['cases'][0]['off'] if attempt['arm']=='official' else PRIOR['cases'][0]['scalar_off'])['decoded_rgb']] if not attempt['timed'] else ['0'*64]*93}})
    return {'status':'W1_CLEAN_TIMING_ALL50_AUDITED','protocol':p,'rows':rows},f


def test_original8_full_repeats_balance_and_warmups_are_explicit():
    r,f=fixture();p=r['protocol'];validate_protocol(p,f)
    assert len(p['attempts'])==50
    for repeat in range(3):
        rows=[x for x in p['attempts'] if x['repeat']==repeat];assert len(rows)==16
        assert {x['name'] for x in rows}==set(p['samples'])
        assert [rows[i]['name'] for i in range(0,16,2)]==p['samples'][repeat*3:]+p['samples'][:repeat*3]
        assert sum(rows[i]['arm']=='official' for i in range(0,16,2))==4
        for i in range(0,16,2): assert rows[i]['name']==rows[i+1]['name'] and rows[i]['arm']!=rows[i+1]['arm']
    assert all(not x['timed'] and x['repeat'] is None for x in p['attempts'][:2])
    s=summarize(r,f,REFERENCE,PRIOR);assert s['planned_scenes']==8 and s['timed_attempts']==48
    assert all(x['arms']['official']['median_all_attempt_seconds']==100 for x in s['scenes'])


def test_timer_includes_both_syncs_generation_but_excludes_audit_and_saves():
    t=[0];events=[]
    def clock():return t[0]
    def sync():events.append('sync');t[0]+=2
    events.append('preflight');t[0]+=100
    m={}
    with synchronized_timer(sync,m,clock):
        events.append('generation');t[0]+=10
    events.append('artifact_audit_and_receipt');t[0]+=500
    assert m['end_to_end_seconds']==12
    assert events==['preflight','sync','generation','sync','artifact_audit_and_receipt']


def test_timer_keeps_actual_failure_cost_and_exception():
    t=[0];m={}
    def sync():t[0]+=1
    with pytest.raises(RuntimeError,match='failure'):
        with synchronized_timer(sync,m,lambda:t[0]):
            t[0]+=4;raise RuntimeError('failure')
    assert m['end_to_end_seconds']==5


def test_warmups_never_enter_repeated_summary_even_if_huge():
    r,f=fixture();r['rows'][0]['end_to_end_seconds']=100000
    s=summarize(r,f,REFERENCE,PRIOR);assert s['scenes'][0]['arms']['official']['seconds']==[100,100,100]


def test_robot_rejection_retained_no_imputation_or_scene_replacement():
    r,f=fixture()
    for row in r['rows']:
        if row['attempt']['name']=='robot_054' and row['attempt']['arm']=='scalar':
            row['outcome']='VIDEO_REJECTED';row['guardrail_events'][-1]['accepted']=False;row['artifact']=None
    s=summarize(r,f,REFERENCE,PRIOR);assert s['outcome_counts']['scalar']['VIDEO_REJECTED']==3
    robot=next(x for x in s['scenes'] if x['name']=='robot_054')
    assert all(x['accepted_pair_official_over_scalar_ratio'] is None for x in robot['paired_repeats'])
    assert robot['arms']['scalar']['attempts']==3 and len(s['scenes'])==8


@pytest.mark.parametrize('mutation', ['partial','dropped','reordered','nan','observer','flags','future','counter','accepted_no_artifact','rejected_saved','calibration'])
def test_invalid_or_partial_evidence_cannot_produce_complete_cost_result(mutation):
    r,f=fixture();row=r['rows'][2]
    if mutation=='partial':r['status']='GENERATING'
    elif mutation=='dropped':r['rows'].pop()
    elif mutation=='reordered':r['rows'][2],r['rows'][3]=r['rows'][3],r['rows'][2]
    elif mutation=='nan':row['end_to_end_seconds']=float('nan')
    elif mutation=='observer':row['disabled_observers']=[]
    elif mutation=='flags':row['flags_after']=dict(row['flags_after'],cudnn_deterministic='drift')
    elif mutation=='future':
        row=next(x for x in r['rows'][2:] if x['attempt']['arm']=='scalar')
        item=next(x for x in row['replay']['records'] if x['prediction']);item['prediction']['history']['anchor_steps']=[item['cache_counter_before']]
    elif mutation=='counter':row['trace']=[]
    elif mutation=='accepted_no_artifact':row['artifact']=None
    elif mutation=='rejected_saved':row['outcome']='VIDEO_REJECTED';row['guardrail_events'][-1]['accepted']=False
    elif mutation=='calibration':row['replay']['calibration_params']['decay']=.9
    with pytest.raises(ValueError):summarize(r,f,REFERENCE,PRIOR)


def test_scope_changes_cannot_hide_original_scenes_or_repeats():
    r,f=fixture()
    for key,value in [('samples',r['protocol']['samples'][:-1]),('repeats',1),('max_gpu_seconds',900),('minimum_project_cap_gpu_hours',4)]:
        p=copy.deepcopy(r['protocol']);p[key]=value
        with pytest.raises(ValueError):validate_protocol(p,f)


def test_observer_removal_must_preserve_prior_warmup_rgb_before_timing_claim():
    r,f=fixture();r['rows'][0]['artifact']['decoded_rgb_sha256'][0]='1'*64
    with pytest.raises(ValueError,match='warmup RGB'):summarize(r,f,REFERENCE,PRIOR)
