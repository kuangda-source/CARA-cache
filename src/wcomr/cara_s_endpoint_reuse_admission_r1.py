"""Fresh read-only admission of original A32/B36 endpoint reuse assets."""
from pathlib import Path
import time

from .cara_s_endpoint_artifacts_r1 import PROPOSAL,ORIGINAL_SCORES,verify_file,original_arguments
from .cara_s_uniform_endpoint_plan_r1 import validate
from .cara_fast_spec_r1 import digest
from .cara_budget_search_journal_r1 import read_record
from .gpu_budget_pool_v2 import sha
from .policy_price_terminal_r1 import require

SOURCE='src/wcomr/cara_s_endpoint_reuse_admission_r1.py'
ORIGINAL_RUNS=('cara-fast-cal-a32-r2-20261028','cara-fast-f19-b36-r1-20261029')


def expected_sources(proposal,scores,*,cpu_validation=False):
    validate(proposal)
    require(proposal.get('CPU_fixture_only',False) is cpu_validation
            and proposal['scope_sha256']==digest({k:v for k,v in proposal.items() if k!='scope_sha256'}),
            'Original proposal identity and fixture mode required')
    require(scores['status']=='ACCEPTED_COMPLETE' and len(scores['rows'])==32
            and scores['scope_sha256']==proposal['parent_B36_scope_sha256']
            and scores['protocol_sha256']==proposal['fidelity_protocol_sha256'],
            'Original complete32 accepted scores required')
    old={r['id']:r for r in scores['rows']}
    require(len(old)==32,'Original32 score IDs must be unique')
    members=proposal['FIT']+proposal['CHECK'];references={};sources=[]
    require(len(proposal['reference_sources'])==4
            and {r['member'] for r in proposal['reference_sources']}==set(members),
            'All four original Native references required')
    for item in proposal['reference_sources']:
        row=old[item['score_id']];source=item['source']
        require(row['member']==item['member'] and row['role']=='NATIVE35'
                and digest(row)==item['score_row_sha256'] and row['candidate']==row['reference']==source
                and row['status']=='COMPLETE' and row['frames']==93 and row['PTS_equal'] is True
                and row['decoded_RGB_sha256']==[item['decoded_RGB_sha256']]*2,
                'Original Native row/descriptor differs')
        references[item['member']]=source;sources.append(source)
    reused=[r for r in proposal['formal_matrix'] if r['mode']=='REUSE_COMPLETE_SCORE']
    require(len(reused)==12 and len({r['score_id'] for r in reused})==12,'All12 original reused rows required')
    for item in reused:
        row=old[item['score_id']]
        require(row['member']==item['member'] and row['role']==item['role']
                and digest(row)==item['score_row_sha256'] and row['candidate']==item['source']
                and row['reference']==item['reference']==references[item['member']]
                and row['decoded_RGB_sha256']==item['decoded_RGB_sha256']
                and row['status']=='COMPLETE' and row['frames']==93 and row['PTS_equal'] is True,
                'Original reused complete score row/descriptor differs')
        sources.append(row['candidate'])
    require(len(sources)==len({r['path'] for r in sources})==16
            and all(r['host']=='two_card' and r['gpu_uuid']==proposal['gpu_uuid'] and r['seed']==0
                    and r['model_sha256']==proposal['model_sha256'] and r['precision']==proposal['precision_sha256']
                    and r['comparison_input_sha256']==references[r['member']]['comparison_input_sha256']
                    and r['execution_request_sha256']==references[r['member']]['execution_request_sha256']
                    for r in sources),'Exact sixteen original input/model/precision identities required')
    return sources


def verify_reuse(project,proposal,scores,*,cpu_validation=False):
    project=Path(project);sources=expected_sources(proposal,scores,cpu_validation=cpu_validation)
    roots=[project/'CPU-historical'] if cpu_validation else [project/'outputs'/r for r in ORIGINAL_RUNS]
    started=time.time();files=[]
    for descriptor in sources:
        video=Path(descriptor['path']);arguments=video.with_suffix('.json')
        require(video.is_absolute() and '..' not in video.parts and video.suffix=='.mp4'
                and any(video.is_relative_to(r) and video.resolve().is_relative_to(r.resolve())
                        and arguments.resolve().is_relative_to(r.resolve()) for r in roots),
                'Only completed original A32/B36 reuse assets may be read')
        paths=(video,arguments);before=[p.stat() for p in paths]
        verify_file(descriptor);original_arguments(descriptor)
        after=[p.stat() for p in paths]
        require(all((a.st_ino,a.st_size,a.st_mtime_ns)==(b.st_ino,b.st_size,b.st_mtime_ns)
                    for a,b in zip(before,after)), 'Original reuse asset changed during admission')
        for p,state,fingerprint in zip(paths,after,(descriptor['sha256'],descriptor['argument_file_sha256'])):
            files.append(dict(path=str(p),resolved_path=str(p.resolve()),bytes=state.st_size,
                              sha256=fingerprint,stable_during_read=True))
    require(len(files)==len({r['path'] for r in files})==32,'Complete32 original files required')
    return dict(status='ORIGINAL_ENDPOINT_REUSE_ASSETS_VERIFIED',started_unix=started,ended_unix=time.time(),
        proposal_scope_sha256=proposal['scope_sha256'],original_scores_digest=digest(scores),
        files=files,original_videos=16,original_argument_files=16,reused_score_rows=12,
        read_bytes=sum(r['bytes'] for r in files),CPU_fixture_only=cpu_validation,
        metrics_computed=0,GPU_submissions=0,ledger_written=False,active_GPU_outputs_read=False,
        future_availability_proven=False)


def verify_stage(stage,*,cpu_validation=False):
    stage=Path(stage);registration=read_record(stage/'registration.json');payload=registration['payload_sha256']
    require(payload[SOURCE]==sha(__file__)==sha(stage/SOURCE)
            and all(payload[p]==sha(stage/p) for p in (PROPOSAL,ORIGINAL_SCORES)),
            'Registered original reuse reader/proposal/scores differ')
    result=verify_reuse(stage.parent.parent,read_record(stage/PROPOSAL),read_record(stage/ORIGINAL_SCORES),
                        cpu_validation=cpu_validation)
    result.update(registration_sha256=sha(stage/'registration.json'),
                  original_scores_sha256=payload[ORIGINAL_SCORES],reader_sha256=payload[SOURCE])
    return result
