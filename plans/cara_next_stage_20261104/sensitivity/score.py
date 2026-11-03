"""Released CPU scoring: original CAL35 Alex/quality protocol, full 93 frames."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent


def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True)
    p.add_argument('--control',type=Path,required=True);args=p.parse_args()
    stage,control=args.stage,args.control
    read=lambda path:json.loads(Path(path).read_text())
    sha=lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    config=read(control/'score-config.json');release=read(control/'release.json')
    if not all(release[k] for k in ('GPU_released','mode_restored','cost_settled','original_processes_ended','container_exit_success')):
        raise ValueError('Successful original release and unique settlement required')
    if sha(stage/'GPU-launch.json')!=config['launch_sha256'] or sha(control/'release.json')!=config['release_sha256']:
        raise ValueError('Original released identity differs')
    if os.environ['CUDA_VISIBLE_DEVICES']!='' or os.environ['NVIDIA_VISIBLE_DEVICES']!='void':
        raise ValueError('CPU-only scoring required')
    card=read(HERE/'manifest.json');out=Path(card['output_root']);collection=read(out/'collection.json')
    if collection['status']!='COMPLETE_PENDING_RELEASE_SCORING' or len(collection['rows'])!=card['counts']['total_requests']:
        raise ValueError('Complete physical denominator required before scoring')
    if sha(out/'collection.json')!=config['collection_sha256'] or collection['scope_sha256']!=card['scope_sha256']:
        raise ValueError('Frozen collection differs')
    binding=read(stage/'reports/cara_CAL66_quality_binding_20261025.json')
    quality_root=Path(binding['registration']['stage']);overlay=Path(binding['dependency_overlay'])
    lock=overlay.parent/'dependency-overlay-manifest.json'
    if sha(lock)!=binding['dependency_overlay_manifest_sha256']:
        raise ValueError('Original scoring dependency lock differs')
    deps=read(lock)
    if any(sha(overlay/name)!=digest for name,digest in deps['files'].items()):
        raise ValueError('Original scoring dependency bytes differ')
    sys.path[:0]=[str(quality_root/'src'),str(quality_root/'scripts'),str(overlay),config['piq_site']]
    import wcomr
    wcomr.__path__.append(str(stage/'src/wcomr'))
    import torch,lpips,piq
    torch.set_num_threads(2);torch.set_num_interop_threads(1)
    def forbidden(*a,**kw):raise RuntimeError('CPU scorer forbids CUDA/downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    from wcomr.gpu_budget_pool_v2 import atomic_json
    from wcomr.cara_fast_fidelity_r1 import score_video_pair
    from wcomr.automatic_quality_models_r1 import OriginalMetricFactory
    from wcomr.automatic_quality_batch_r1 import validate_result
    from wcomr.automatic_quality_r1 import sampling_spec,text_sha
    from wcomr.policy_generator_r1.p2_quality_entry import validate_sources_and_decoder
    from wcomr.cara_fast_spec_r1 import digest
    target=control/'scores.json'
    if target.exists():raise ValueError('Recover existing original scores without replay')
    rows=collection['rows'];formal=[r for r in rows if r['slot']['section']=='c']
    recorded={r['slot']['member']:r for r in rows if r['slot']['section']=='a'}
    references={r['slot']['member']:r for r in formal if r['slot']['role']=='NATIVE35'}
    state=dict(status='SCORING',scope_sha256=card['scope_sha256'],LPIPS=[],sensitivity=[],quality_rows=[],RGB_controls=[],GPU_submissions=0)
    def save():atomic_json(target,state)
    # Decode controls without adding LPIPS runs or treating frames as samples.
    import av
    def RGB(row):
        video=row['result']['video_artifact']
        if sha(video['path'])!=video['sha256']:raise ValueError('Video bytes differ')
        digest=hashlib.sha256();pts=[]
        with av.open(video['path']) as container:
            stream=container.streams.video[0]
            if stream.average_rate!=16 or (stream.height,stream.width)!=(432,768):
                raise ValueError('Original control video geometry/cadence differs')
            for frame in container.decode(video=0):
                digest.update(frame.to_ndarray(format='rgb24').tobytes());pts.append(str(frame.pts*frame.time_base))
        if len(pts)!=93:raise ValueError('Full93 control required')
        return digest.hexdigest(),pts
    indexed={(r['slot']['member'],r['slot']['role'],r['slot']['target_update']):r for r in rows}
    for row in rows:
        slot=row['slot'];member=slot['member'];role=slot['role']
        if role in ('NATIVE35','RESUME_D'):reference=recorded[member]
        elif role=='FULL_SINGLE_C':reference=indexed[member,'SINGLE_C',slot['target_update']]
        else:continue
        if RGB(row)!=RGB(reference):raise ValueError('Released Native/resumed RGB/PTS bridge failed')
        state['RGB_controls'].append(dict(slot_id=slot['id'],reference=reference['slot']['id'],passed=True))
    os.environ['TORCH_HOME']=config['torch_home']
    if (sha(Path(config['torch_home'])/'hub/checkpoints/alexnet-owt-7be5be79.pth')!='7be5be791159472b1fbf3c69796f7cb30dca7ad8466c2df70058c37116cdee02'
            or sha(Path(lpips.__file__).parent/'weights/v0.1/alex.pth')!='df73285e35b22355a2df87cdb6b70b343713b667eddbda73e1977e0c860835c0'
            or piq.__version__!='0.8.0'):
        raise ValueError('CAL35 Alex/PIQ versions or weights differ')
    save()
    alex=lpips.LPIPS(net='alex',version='0.1',verbose=False).cpu().eval()
    for row in rows:
        slot=row['slot']
        if slot['section']=='b':reference=recorded[slot['member']]
        elif slot['section']=='c' and slot['role']!='NATIVE35':reference=references[slot['member']]
        else:continue
        score=score_video_pair(row['result']['video_artifact'],reference['result']['video_artifact'],alex)
        state['LPIPS'].append(dict(slot=slot,result=score))
        if slot['section']=='b':
            artifacts=[r['result']['latent_artifact'] for r in (row,reference)]
            if any(sha(a['path'])!=a['sha256'] for a in artifacts):
                raise ValueError('Endpoint latent bytes differ')
            c,n=[torch.load(a['path'],map_location='cpu',weights_only=True).float() for a in artifacts]
            state['sensitivity'].append(dict(member=slot['member'],t=slot['target_update'],
                latent_MSE=float((c-n).square().mean()),LPIPS_Alex=score['Alex'],
                local_guided_delta_RMS=row['result']['local_guided_delta_RMS']))
        save()
    del alex
    factory=OriginalMetricFactory(stage=quality_root,resources=binding['resources'],CPU_acceptance=binding['acceptance'],
        CPU_registration=binding['registration'],scorer_fingerprint=digest(binding['identity']),torch=torch,device='cpu')
    members={r['name']:r for r in card['inputs']}
    for dimension in ('MUSIQ_LONGER512','subject_consistency','motion_smoothness'):
        with factory(dimension) as scorer:
            for row in formal:
                slot=row['slot'];member=members[slot['member']];video=row['result']['video_artifact']
                planned=dict(case_id=slot['member'],method=slot['id'],dimension=dimension,seed=0,role=slot['role'],
                    prompt=member['prompt'],prompt_sha256=text_sha(member['prompt']),input_status='READY_TO_SCORE',
                    video_path=video['path'],video_sha256=video['sha256'],request_sha256=digest(row['result']),
                    scorer_fingerprint=digest(binding['identity']),expected_sampling=sampling_spec(dimension))
                result=scorer.score(planned);validate_result(planned,result);validate_sources_and_decoder(binding['identity'],result)
                state['quality_rows'].append(dict(planned=planned,result=result));save()
    if len(state['LPIPS'])!=124 or len(state['sensitivity'])!=112 or len(state['quality_rows'])!=48:
        raise ValueError('Complete score denominator differs')
    state.update(status='COMPLETE_PENDING_ANALYSIS',CUDA_initialized=torch.cuda.is_initialized());save()


if __name__=='__main__':main()
