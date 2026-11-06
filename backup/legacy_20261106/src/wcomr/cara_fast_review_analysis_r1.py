"""Single-reviewer diagnostic counts; no new veto, selection or independence claim."""
import math
from .cara_fast_review_r1 import AXES, CHOICES, validate_response

ROLES = ('NATIVE35','SHARED25_C','F19_C','F19_A1','UNIFORM19_C','WC_FAST','RA_FAST','NATIVE_K')


def playback_record(ranges, duration):
    if ranges is None:
        return dict(status='NO_PLAYBACK_METADATA', recorded_seconds=None)
    if not isinstance(ranges,list):
        return dict(status='INVALID_PLAYBACK_METADATA', recorded_seconds=None)
    intervals=[]
    for row in ranges:
        if (not isinstance(row,list) or len(row)!=2
                or any(type(v) not in (int,float) or not math.isfinite(v) for v in row)
                or not 0 <= row[0] <= row[1] <= duration+1e-6):
            return dict(status='INVALID_PLAYBACK_METADATA', recorded_seconds=None)
        intervals.append(row)
    end=0.;seconds=0.
    for start, stop in sorted(intervals):
        seconds += max(0., min(stop,duration)-max(start,end));end=max(end,stop)
    status=('NO_RECORDED_RANGE' if not intervals else 'FULL_DURATION_RECORDED'
            if seconds>=duration-1e-6 else 'PARTIAL_RECORDED_RANGE')
    return dict(status=status, recorded_seconds=seconds)


def summarize_response(plan, response):
    validate_response(plan['public'], response)
    if (response.get('schema')!='CARA_VIDEO_REVIEW_RESPONSE_R1'
            or response.get('status')!='COMPLETE_RESPONSE_NOT_INDEPENDENTLY_ACCEPTED'
            or response['reviewer'].startswith('CPU_TEST')):
        raise ValueError('Complete diagnostic review export required; not a UI QA record')
    by_id={row['case_id']:row for row in response['responses']}
    counts={role:dict(positions=0,all_axes_no_obvious_difference=0,
        axes={axis:{choice:0 for choice in CHOICES} for axis in AXES}) for role in ROLES}
    rows=[];duration=plan['public']['frames']/plan['public']['fps']
    for case in plan['cases']:
        raw=by_id[case['case_id']];role=case['role'];group=counts[role]
        group['positions']+=1
        same=all(raw[axis]=='no_obvious_difference' for axis in AXES)
        group['all_axes_no_obvious_difference']+=same
        for axis in AXES:group['axes'][axis][raw[axis]]+=1
        played=raw.get('played',{})
        if not isinstance(played,dict):played={}
        telemetry={side:playback_record(played.get(side),duration) for side in ('reference','candidate')}
        rows.append(dict(member=case['member'],role=role,
            ratings={axis:raw[axis] for axis in AXES},full_watch_attested=raw['full_watch_attested'],
            playback=telemetry,full_pair_duration_recorded=all(
                item['status']=='FULL_DURATION_RECORDED' for item in telemetry.values()),
            notes_present=bool(raw.get('notes'))))
        if role=='NATIVE35' and case['candidate']['sha256']!=case['reference']['sha256']:
            raise ValueError('Original Native self-control bytes differ')
    controls=[row for row in rows if row['role']=='NATIVE35']
    return dict(status='COMPLETE_SINGLE_REVIEWER_DIAGNOSTIC_RECORDED',package_id=plan['public']['package_id'],
        reviewer_count=1,assessment_kind='SINGLE_REVIEWER_DIAGNOSTIC',positions=32,input_clusters=4,
        full_watch_attestations=32,full_pair_playback_recorded=sum(r['full_pair_duration_recorded'] for r in rows),
        playback_metadata_gaps=[dict(member=r['member'],role=r['role'],playback=r['playback'])
            for r in rows if not r['full_pair_duration_recorded']],
        self_controls=4,self_control_all_axes_no_difference=sum(all(
            r['ratings'][a]=='no_obvious_difference' for a in AXES) for r in controls),
        by_role=counts,per_input=rows,notes_present_count=sum(r['notes_present'] for r in rows),
        telemetry_used_as_exclusion=False,excluded_positions=0,independent_human_evidence=False,
        new_scientific_gate=False,new_selection=False,automatic_scores_changed=False,GPU_submissions=0)
