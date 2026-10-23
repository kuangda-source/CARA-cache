"""Original-byte evidence, full-video scoring and pre-search Native clock."""
import hashlib
import json
import math
from pathlib import Path
from .continuation_preparation import TIME_BOUNDARY, require
from ..policy_asset_price_review_r1 import exclusive_gate


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
    return h.hexdigest()


def artifact(path, root):
    path=Path(path);root=Path(root)
    require(not path.is_symlink() and path.resolve().is_relative_to(root.resolve()),'Artifact escapes original output')
    require(path.is_file() and path.stat().st_size>0,'Missing original artifact')
    return dict(path=str(path),bytes=path.stat().st_size,sha256=sha(path))


def verify_artifact(ref,root):
    require(artifact(ref['path'],root)==ref,'Original artifact changed')
    return Path(ref['path'])


def score_videos(reference,candidate,metric,*,root,metric_identity):
    from ..rv0_video_reader import decoded_video
    from ..rv0_lpips import score_pair
    left=verify_artifact(reference,root);right=verify_artifact(candidate,root)
    with decoded_video(left) as a,decoded_video(right) as b:
        score=score_pair(a,b,metric,reference_sha256=reference['sha256'],candidate_sha256=candidate['sha256'])
    # Bind the complete per-frame original, not only its scalar reduction.
    score.update(metric_identity=metric_identity,timing_boundary=TIME_BOUNDARY,
        geometry=[432,768,3],resize_crop_subsample=False,device='cpu')
    return score


def validate_score(score,reference,candidate,metric_identity):
    require(score['reference_sha256']==reference['sha256'] and score['candidate_sha256']==candidate['sha256'],'Wrong paired video')
    values=score['frame_distances'];pts=score['pts']
    require(score['frames']==len(values)==len(pts)==93 and len({tuple(p) for p in pts})==93,'Complete93 paired scores required')
    require(all(type(v) in (int,float) and math.isfinite(v) and v>=0 for v in values),'Invalid LPIPS frame distance')
    from fractions import Fraction
    stamps=[int(p)*Fraction(b) for p,b in pts]
    require(all(b-a==Fraction(1,16) for a,b in zip(stamps,stamps[1:])),'Missing/reordered scoring timestamp')
    require(score['mean_LPIPS']==sum(values)/93 and score['metric_identity']==metric_identity,'Changed metric or reduction')
    require(score['geometry']==[432,768,3] and score['resize_crop_subsample'] is False and score['device']=='cpu','Changed score protocol')
    return score['mean_LPIPS']


def native_clock(rows,*,fit_members,profile_identity,monitor_raw,runner,gpu_uuid,now,source_revision,launch_id):
    """Accept only the Native prefix; final terminal acceptance checks the suffix."""
    require(len(rows)==4 and [r['member'] for r in rows]==fit_members,'All four ordered Native FIT members required')
    samples=[json.loads(s) for s in monitor_raw.splitlines()];last_elapsed=0.;last_unix=None;active=False
    require(bool(samples),'Missing exclusive Native prefix')
    for sample in samples:
        snap=sample['snapshot'];elapsed=sample['monotonic_elapsed']
        require(math.isfinite(elapsed) and 0<=elapsed-last_elapsed<=45,'Native exclusive prefix gap')
        require(not active or sample['context_granted'],'Native context grant regressed')
        active=active or sample['context_granted'];last_elapsed=elapsed
        require(exclusive_gate(snap,gpu_uuid=gpu_uuid,phase='active' if active or snap['compute_apps'] else 'idle',runner=runner,now=snap['observed_unix'])['observation_passed'],'Native prefix foreign/unknown context')
        if last_unix is not None:require(snap['observed_unix']>=last_unix,'Reversed monitor time')
        last_unix=snap['observed_unix']
    require(active and 0<=now-last_unix<=45,'Native clock lacks fresh exclusive tail')
    out=[]
    for i,row in enumerate(rows):
        require(row['id']=='native_fit_'+str(i) and row['kind']=='NATIVE' and row['seed']==0 and row['status']=='COMPLETE','Native clock rejected/incomplete')
        require(row['solver_steps']==row['guided_pairs']==36 and row['timing_boundary']==TIME_BOUNDARY,'Native complete-request protocol differs')
        total=row['full_request_seconds'];core=row['core_seconds']
        require(math.isfinite(total) and math.isfinite(core) and 0<core<=total,'Invalid Native clock')
        require(samples[0]['snapshot']['observed_unix']<=row['started_unix']<=row['ended_unix']<=now,'Native outside monitor prefix')
        for key in ('video_artifact','final_latent_artifact','request_artifact'):
            require(len(row[key]['sha256'])==64 and row[key]['bytes']>0,'Missing Native original identity')
        out.append(dict(member=row['member'],seed=0,requested_steps=35,actual_updates=36,accepted=True,seconds=total,core_seconds=core,
            request_sha256=row['request_artifact']['sha256'],video_sha256=row['video_artifact']['sha256']))
    return dict(status='CLEAN_NATIVE_CAL_COMPLETE_REQUEST_CLOCK_ACCEPTED',full_protocol_accepted=True,
        exclusive_monitoring_accepted=True,profile_identity=profile_identity,timing_boundary=TIME_BOUNDARY,
        before_candidate_endpoints=True,rows=out,monitor_prefix_sha256=hashlib.sha256(monitor_raw.encode()).hexdigest(),
        observed_unix=now,source_revision=source_revision,launch_id=launch_id,gpu_uuid=gpu_uuid,runner=runner)
