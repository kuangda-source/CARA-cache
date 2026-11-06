"""One technical halfway observation of the original full40 timing handles."""
import ast
import collections
import hashlib
import importlib.util
import inspect
import math
from pathlib import Path
from types import FunctionType

from . import frozen_shared_health_r1 as original

RUN='wc-paper-n08-balanced-full40-r1'
CONFIG='configs/wc_paper_N08_balanced_full40_production_r1_20261016.json'
ORIGINAL_SHA='a1690331e1e4cffa6a77fa751ad34cfe36f4c67b810984d3069d4ad525735a0f'
COLLECTOR='scripts/capture_wc_paper_N07_midpoint_health_r1.py'
COLLECTOR_SHA='e42a94748bf758aa8b7871d6aae59f24027ddc6e1725616df870636c73fb4d5e'
check_window=original.check_window


def bind(launch,admission):
    scope=launch['scope_counts']
    if (launch['run_id']!=RUN or admission.get('status')!='N08_FULL40_ORIGINAL_ONCE_CAPTURE'
            or admission.get('mode')!='admission' or admission.get('launch')!=launch
            or admission['registration_sha256']!=launch['registration_sha256']
            or admission['registration']['source_revision']!=launch['source_revision']
            or set(admission['payload_verified'])!=set(admission['registration']['payload_sha256'])
            or not admission['payload_verified'] or not all(v is True for v in admission['payload_verified'].values())
            or (scope['total_paths'],scope['full_warmup_paths'],scope['scientific_paths'])!=(40,10,30)):
        raise ValueError('Bind the original full40 launch and complete admitted source')
    start,mid,end=(launch[k] for k in ('started_unix','midpoint_health_not_before_unix','next_check_not_before_unix'))
    if (any(not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) for v in (start,mid,end))
            or not start<mid<end or not math.isclose(mid,(start+end)/2,rel_tol=0,abs_tol=1e-6)):
        raise ValueError('Use half of the recorded actual launch window; preserve final ETA')
    supervisor=admission['supervisor'];expected={}
    if any(supervisor[k]!=launch[k] for k in ('source_revision','launch_id','run_id','gpu_uuid','config_sha256','scope_counts')):
        raise ValueError('Original admitted supervisor and full timing scope required')
    for name,key,identity in (('supervisor','supervisor_pid',launch['supervisor_identity']),
            ('runner','child_pid',supervisor['child_identity']),('CPU_post','post_watcher_pid',launch['post_watcher_identity'])):
        actual=admission['original_processes'][key]
        if (any(type(identity.get(k)) is not int or identity[k]<=0 for k in ('pid','start_ticks'))
                or any(actual.get(k)!=identity[k] for k in ('pid','start_ticks'))
                or actual.get('state') in (None,'Z','X')):
            raise ValueError('Freeze all three original live admitted PID/start-ticks identities')
        expected[name]={k:identity[k] for k in ('pid','start_ticks')}
    if supervisor['child_pid']!=expected['runner']['pid']:
        raise ValueError('Original runner identity differs')
    return dict(project=launch['project'],stage=launch['stage'],run_id=RUN,
        **{k:launch[k] for k in ('source_revision','launch_id','gpu_uuid','config_sha256','registration_sha256','scope_counts')},
        processes=expected,health_not_before_unix=mid,final_not_before_unix=end)


def technical_progress(data):
    rows=data.get('runs',[]);finished={'COMPLETE','TEXT_REJECTED','VIDEO_REJECTED'}
    known=finished|{'RUNNING','TECH_FAILED','NOT_REACHED'}
    sections={}
    for name,total in (('WARMUP',10),('TIMED',30)):
        selected=[r for r in rows if r.get('section')==name]
        sections[name]=dict(registered=total,observed=len(selected),
            terminal_request_outcomes=sum(r.get('status') in finished for r in selected),
            running=sum(r.get('status')=='RUNNING' for r in selected),
            technical_failures=sum(r.get('status')=='TECH_FAILED' for r in selected),
            not_reached=max(0,total-len(selected)))
    allowed={'N08_FULL40_INITIALIZING_ONE_RESIDENT_MODEL','N08_FULL40_RUNNING',
        'N08_FULL40_GPU_COMPLETE_CPU_AUDIT_PENDING','N08_FULL40_TECHNICAL_FAILURE_FULL_SCOPE_RETAINED'}
    return dict(status=data.get('status') if data.get('status') in allowed else 'UNKNOWN_STATUS',
        registered_total=40,observed_positions=len(rows),terminal_request_outcomes=sum(r.get('status') in finished for r in rows),
        not_reached=max(0,40-len(rows)),excess_positions=max(0,len(rows)-40),sections=sections,
        generation_status_counts=dict(collections.Counter(r.get('status') if r.get('status') in known else 'UNKNOWN' for r in rows)),
        no_per_method_quality_or_timing_readout=True)


def remote_code(expected):
    if hashlib.sha256(Path(original.__file__).read_bytes()).hexdigest()!=ORIGINAL_SHA:
        raise ValueError('The original technical-only observer changed')
    copied=FunctionType(original.remote_code.__code__,{**vars(original),'technical_progress':technical_progress})
    source=copied(expected);changed=source
    edits=((original.RUN,RUN),(original.CONFIG,CONFIG),
        ('N07_MIDPOINT_READONLY_TECHNICAL_HEALTH','N08_MIDPOINT_READONLY_TECHNICAL_HEALTH'),
        ("'post-CPU-exit.json'","'N08-post-CPU-exit.json'"),
        ("'CPU-final-results.json'","'N08-CPU-final-results.json'"),
        ("'post-CPU.log'","'N08-post-CPU.log'"))
    for before,after in edits:
        if changed.count(before)!=1:raise ValueError('Exact N08 technical path/status binding required')
        changed=changed.replace(before,after)
    prefix='EXPECTED='+repr(expected)+'\n';restored=prefix+changed[len(prefix):]
    for before,after in reversed(edits):restored=prefix+restored[len(prefix):].replace(after,before)
    if restored!=source or ast.dump(ast.parse(restored))!=ast.dump(ast.parse(source)):
        raise ValueError('No extra operation may enter the midpoint observer')
    return changed


def collect(expected,output,*,now=None,execute=None):
    """Reuse the original time gates, once fence, cache and UNKNOWN behavior."""
    root=Path(__file__).resolve().parents[2];path=root/COLLECTOR
    if hashlib.sha256(path.read_bytes()).hexdigest()!=COLLECTOR_SHA:
        raise ValueError('Original once collector changed')
    spec=importlib.util.spec_from_file_location('original_N07_once_collector_for_N08',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    source=inspect.getsource(module.collect);changed=source.replace(
        'from wcomr.frozen_shared_health_r1 import check_window,remote_code',
        'from wcomr.balanced_repeat_health_r1 import check_window,remote_code').replace('N07_MIDPOINT','N08_MIDPOINT')
    restored=changed.replace('from wcomr.balanced_repeat_health_r1 import check_window,remote_code',
        'from wcomr.frozen_shared_health_r1 import check_window,remote_code').replace('N08_MIDPOINT','N07_MIDPOINT')
    if restored!=source or ast.dump(ast.parse(restored))!=ast.dump(ast.parse(source)):
        raise ValueError('Only the observer import and N08 result labels may differ')
    namespace={**vars(module)};exec(compile(changed,COLLECTOR+'#N08-midpoint','exec'),namespace)
    return namespace['collect'](expected,output,now=now,execute=execute)
