"""Full postrelease artifacts and nine RGB controls before a new score manifest.

No metric computation, GPU dispatch, freeze or ledger mutation occurs here.
The caller owns the original bounded CPU reader lifecycle.
"""
import copy
from fractions import Fraction
import hashlib
from pathlib import Path

from .cara_fast_b36_capture_r1 import captured_file,file_sha
from .cara_fast_scoring_manifest_r2 import comparison_input_digest
from .cara_fast_spec_r1 import digest
from .cara_s_endpoint_release_r1 import released_collection
from .cara_s_endpoint_scoring_manifest_r1 import SOURCE as MANIFEST_SOURCE,validate_pair_identities
from .cara_s_uniform_endpoint_plan_r1 import validate
from .policy_price_terminal_r1 import record,require

SOURCE='src/wcomr/cara_s_endpoint_artifacts_r1.py'
PROPOSAL='configs/cara_endpoint_proposal.json'
ORIGINAL_SCORES='configs/cara_endpoint_original_B36_scores.json'
SHAPE=(93,432,768,3)


def verify_file(artifact,*,original_output=False):
    path=Path(artifact['path'])
    require(path.is_file() and (not original_output or not path.is_symlink())
            and artifact['bytes']>0 and path.stat().st_size==artifact['bytes']
            and file_sha(path)==artifact['sha256'],'Original artifact bytes differ')


def decode_video(artifact,*,shape=SHAPE):
    """Hash all RGB24 frames and exact rational PTS without loading model weights."""
    import av
    import numpy as np
    verify_file(artifact)
    fingerprint=hashlib.sha256();pts=[]
    with av.open(artifact['path']) as container:
        require(len(container.streams.video)==1,'Exactly one original video stream required')
        stream=container.streams.video[0]
        stream.codec_context.thread_count=1
        require(stream.average_rate==16 and (stream.height,stream.width,3)==tuple(shape[1:]),
                'Original fps/geometry differs; no resampling')
        for frame in container.decode(video=0):
            require(len(pts)<shape[0] and frame.pts is not None,'Full registered frame count/PTS required')
            current=frame.pts*frame.time_base
            require(not pts or current-pts[-1]==Fraction(1,16),'Original frame cadence differs')
            value=frame.to_ndarray(format='rgb24')
            require(value.shape==tuple(shape[1:]) and value.dtype==np.uint8,'Original RGB24 geometry differs')
            fingerprint.update(value.tobytes());pts.append(current)
    require(len(pts)==shape[0],'Full registered frame count required')
    verify_file(artifact)
    return dict(RGB_sha256=fingerprint.hexdigest(),frames=len(pts),shape=list(shape),fps=16,
                PTS=[[p.numerator,p.denominator] for p in pts])


def original_arguments(descriptor):
    # Historical output directories may be established symlinks. Preserve their
    # descriptor path; read the resolved regular argument file without rewriting it.
    saved=captured_file(Path(descriptor['path']).with_suffix('.json').resolve())
    arguments=record(dict(files={'arguments':saved}),'arguments')
    require(saved['sha256']==descriptor['argument_file_sha256']
            and digest(arguments)==descriptor['execution_request_sha256']
            and comparison_input_digest(arguments)==descriptor['comparison_input_sha256'],
            'Original saved request identity differs')
    return arguments


def postrelease_manifest(capture,expected_launch_sha256,settlement,proposal,card,bound,*,
                         cpu_validation=False,cpu_shape=None):
    # The complete financial/resource gate runs before reading any artifact,
    # historical score payload, decoded frame or scientific collection here.
    release=released_collection(capture,expected_launch_sha256,settlement,card,bound,cpu_validation=cpu_validation)
    require(cpu_shape is None or cpu_validation,'Tiny geometry is CPU-fixture-only')
    shape=SHAPE if cpu_shape is None else tuple(cpu_shape)
    require(shape[0]==93 and shape[-1]==3,'All93 RGB frames required even in CPU fixtures')
    validate(proposal)
    require(proposal.get('CPU_fixture_only',False) is cpu_validation
            and proposal['scope_sha256']==digest({k:v for k,v in proposal.items() if k!='scope_sha256'})
            and proposal['scope_sha256']==card['endpoint_proposal_sha256']==bound['proposal_scope_sha256'],
            'Original registered proposal and fixture mode required')
    registration=record(capture,'registration');launch=record(capture,'launch')
    require(record(capture,'endpoint_proposal')==proposal
            and capture['files']['endpoint_proposal']['sha256']==registration['payload_sha256'][PROPOSAL]
            and capture['files']['original_scores']['sha256']==registration['payload_sha256'][ORIGINAL_SCORES]
            and registration['payload_sha256'][SOURCE]==file_sha(__file__)
            and registration['payload_sha256'][MANIFEST_SOURCE]==file_sha(Path(__file__).with_name('cara_s_endpoint_scoring_manifest_r1.py')),
            'Original registered proposal/scores/reader sources differ')
    require(launch['host']==proposal['host']=='two_card' and launch['gpu_uuid']==proposal['gpu_uuid']
            and launch['model_sha256']==proposal['model_sha256']
            and digest(record(capture,'precision'))==proposal['precision_sha256']
            and card['fidelity_protocol_sha256']==proposal['fidelity_protocol_sha256'],
            'Original endpoint model/precision/protocol differs')
    original=record(capture,'original_scores')
    require(original['status']=='ACCEPTED_COMPLETE' and len(original['rows'])==32
            and original['scope_sha256']==proposal['parent_B36_scope_sha256']
            and original['protocol_sha256']==proposal['fidelity_protocol_sha256'],
            'Original complete32 accepted B36 scores required')
    old={r['id']:r for r in original['rows']}
    require(len(old)==32,'Original score IDs must be unique')
    references={};reference_decoded={};reused=[]
    for item in proposal['reference_sources']:
        row=old[item['score_id']];descriptor=item['source'];member=item['member']
        require(digest(row)==item['score_row_sha256'] and row['candidate']==row['reference']==descriptor
                and row['status']=='COMPLETE' and row['frames']==93 and row['PTS_equal'] is True
                and row['decoded_RGB_sha256']==[item['decoded_RGB_sha256']]*2,
                'Original Native source/row identity differs')
        verify_file(descriptor);original_arguments(descriptor)
        decoded=decode_video(descriptor,shape=shape)
        require(decoded['RGB_sha256']==item['decoded_RGB_sha256'],'Original Native decoded identity differs')
        references[member]=copy.deepcopy(descriptor);reference_decoded[member]=decoded
    for item in proposal['formal_matrix']:
        if item['mode']!='REUSE_COMPLETE_SCORE':continue
        row=old[item['score_id']]
        require(digest(row)==item['score_row_sha256'] and row['candidate']==item['source']
                and row['reference']==item['reference']==references[item['member']]
                and row['decoded_RGB_sha256']==item['decoded_RGB_sha256'],
                'Original reused score row changed')
        verify_file(row['candidate']);original_arguments(row['candidate'])
        reused.append(copy.deepcopy(row))
    collection=record(capture,'collection');requests={r['name']:r for r in card['inputs']}
    output=Path(launch['stage']).parents[1]/'outputs'/launch['run_id']/'B'
    artifacts={};descriptors={};decoded={}
    for row in collection['rows']:
        slot,result=row['slot'],row['result'];identifier=slot['id']
        video=result['endpoint_video_artifact'];tensor=row['tensor_artifact']
        require(video['path']==result['video_path']==str(output/identifier/(slot['member']+'.mp4'))
                and tensor['path']==str(output/(identifier+'.pt')),
                'Original endpoint output location differs')
        verify_file(video,original_output=True);verify_file(tensor,original_output=True)
        saved=captured_file(Path(video['path']).with_suffix('.json'))
        arguments=record(dict(files={'arguments':saved}),'arguments')
        expected={k:v for k,v in requests[slot['member']].items() if k!='partition'}
        expected.update(seed=slot['seed'],num_steps=card['roles'][slot['role']]['requested_steps'])
        require(all(arguments.get(k)==v for k,v in expected.items()),'Saved endpoint arguments differ from registered request')
        descriptor=dict(video,slot_id=identifier,member=slot['member'],role=slot['role'],concrete_role=slot['role'],
            seed=slot['seed'],host=launch['host'],gpu_uuid=launch['gpu_uuid'],model_sha256=launch['model_sha256'],
            scope_sha256=card['scope_sha256'],precision=proposal['precision_sha256'],source_phase='ENDPOINT',
            comparison_input_sha256=comparison_input_digest(arguments),execution_request_sha256=digest(arguments),
            registered_request_sha256=digest(expected),argument_file_sha256=saved['sha256'],
            request_identity_kind='ACTUAL_SAVED_INFERENCE_ARGUMENTS_MATCH_REGISTERED_VARIANT')
        require(descriptor['comparison_input_sha256']==references[slot['member']]['comparison_input_sha256'],
                'Complete conditioning/default request identity differs from original reference')
        decoded[identifier]=decode_video(video,shape=shape)
        require(decoded[identifier]['PTS']==reference_decoded[slot['member']]['PTS'],
                'Endpoint and original reference PTS differ')
        artifacts[identifier]=dict(video=copy.deepcopy(video),tensor=copy.deepcopy(tensor),arguments=saved)
        descriptors[identifier]=descriptor
    slots={(r['slot']['purpose'],r['slot']['member'],r['slot']['role']):r['slot']['id'] for r in collection['rows']}
    controls=[]
    for control in proposal['identity_controls']:
        if control['kind']=='FRESH_VS_ORIGINAL_DECODED_RGB':
            identifier=slots[('REPLAY_CONTROL',control['member'],control['role'])]
            expected=old[control['original_score_id']]['decoded_RGB_sha256'][0]
            require(expected==control['original_decoded_RGB_sha256'],'Original RGB control changed')
        else:
            require(control['kind']=='FRESH_NATIVE_VS_ALLD_DECODED_RGB','Unknown RGB control')
            identifier=slots[('ALLD_EQUIVALENCE',control['member'],'ALLD')]
            expected=decoded[slots[('WARM',control['member'],'NATIVE35')]]['RGB_sha256']
        require(decoded[identifier]['RGB_sha256']==expected,'Complete endpoint RGB identity control failed')
        controls.append(dict(control=copy.deepcopy(control),slot_id=identifier,RGB_sha256=expected,passed=True))
    controls_required=13 if proposal.get('endpoint7') else 9
    positions_required=28 if proposal.get('endpoint7') else 24
    require(len(controls)==controls_required,'Complete RGB identity controls required')
    pairs=[];positions=[];seen={}
    for i,item in enumerate(bound['formal_matrix']):
        position=dict(id=f'ENDPOINT_FORMAL_{i+1:03d}',member=item['member'],role=item['role'],mode=item['mode'])
        if item['mode']=='REUSE_COMPLETE_SCORE':position['score_id']=item['score_id']
        else:
            identifier=item['physical_slot_id']
            if identifier not in seen:
                seen[identifier]='ENDPOINT_PAIR_'+identifier
                pairs.append(dict(id=seen[identifier],candidate=descriptors[identifier],reference=references[item['member']]))
            position.update(score_id=seen[identifier],counts_as_independent_sample_from_alias=False)
        positions.append(position)
    manifest=dict(schema='CARA_ENDPOINT_CROSS_ALLOCATION_SCORING_R1',run_id=launch['run_id'],launch_id=launch['launch_id'],
        analysis_scope_sha256=card['scope_sha256'],original_B36_scope_sha256=proposal['parent_B36_scope_sha256'],
        proposal_sha256=proposal['scope_sha256'],endpoint_binding_sha256=bound['binding_sha256'],
        original_budget_freeze_sha256=bound['original_freeze_sha256'],protocol_sha256=proposal['fidelity_protocol_sha256'],
        release_sha256=digest(release),collection_sha256=release['collection_sha256'],
        original_scores_sha256=capture['files']['original_scores']['sha256'],
        members=proposal['FIT']+proposal['CHECK'],original_references=references,reused_rows=reused,
        formal_positions=positions,pairs=pairs,unique_new_scoring_pairs=len(pairs),formal_logical_positions=positions_required,
        budget_role_representative=bound['budget_role_representative'],physical_paths=len(collection['rows']),
        artifact_sha256=digest(artifacts),decoded_identity_sha256=digest(decoded),identity_controls=controls,
        identity_controls_passed=controls_required,GPU_released=True,CPU_fixture_only=cpu_validation,
        CPU_bound=dict(cpus=2,memory_GiB=8,wall_hours=4,max_pairs=12),
        metrics_computed=0,scoring_dispatch_allowed=False,whole_GPU_card_accepted=False,
        authorizes_replay=False,independent_new_inputs=False,GPU_submissions=0,ledger_written=False)
    if proposal.get('endpoint7'):
        manifest.update(endpoint7=True,CPU_bound=dict(cpus=2,memory_GiB=8,wall_hours=2,max_pairs=16))
    validate_pair_identities(manifest)
    return dict(status='COMPLETE_ENDPOINT_ARTIFACTS_AND_CROSS_SCOPE_MANIFEST_NOT_SCORED',
        manifest=manifest,artifacts=artifacts,decoded=decoded,release=release,CPU_fixture_only=cpu_validation,
        reader_sha256=file_sha(__file__),manifest_validator_sha256=file_sha(Path(__file__).with_name('cara_s_endpoint_scoring_manifest_r1.py')))
