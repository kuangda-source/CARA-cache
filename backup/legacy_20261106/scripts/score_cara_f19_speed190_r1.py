"""Released CAL35 RGB controls, 24 full LPIPS pairs and 84 original quality scores."""
import argparse,hashlib,json,os,signal,sys,time
from pathlib import Path


def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True)
    p.add_argument('--control',type=Path,required=True);a=p.parse_args()
    stage,control=a.stage,a.control;read=lambda p:json.loads(Path(p).read_text())
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    cfg=read(control/'score-config.json');reg=read(stage/'registration.json')
    assert sha(__file__)==reg['payload_sha256']['scripts/score_cara_f19_speed190_r1.py']
    release=read(control/'release.json')
    assert all(release[k] for k in ('GPU_released','mode_restored','cost_settled','original_processes_ended','container_exit_success'))
    assert sha(stage/'GPU-launch.json')==cfg['launch_sha256'] and sha(control/'release.json')==cfg['release_sha256']
    assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
    out=Path(cfg['output']);collection=read(out/'collection.json');card=read(stage/cfg['manifest'])
    assert sha(out/'collection.json')==cfg['collection_sha256'] and collection['scope_sha256']==card['scope_sha256']
    assert collection['status']=='COMPLETE35_PENDING_RELEASE_SCORING' and len(collection['rows'])==35
    assert all(r['status']=='COMPLETE' for r in collection['rows']) and len(collection['controls'])==2
    binding=read(stage/'reports/cara_CAL66_quality_binding_20261025.json')
    quality_root=Path(binding['registration']['stage'])
    overlay=Path(binding['dependency_overlay']);lock=overlay.parent/'dependency-overlay-manifest.json'
    assert sha(lock)==binding['dependency_overlay_manifest_sha256']
    deps=read(lock);assert deps['base_environment_modified'] is False
    assert all(sha(overlay/n)==h for n,h in deps['files'].items())
    sys.path[:0]=[str(quality_root/'src'),str(quality_root/'scripts'),str(overlay),cfg['piq_site']]
    import wcomr
    wcomr.__path__.append(str(stage/'src/wcomr'))
    import torch,lpips,piq,av,numpy as np
    torch.set_num_threads(2);torch.set_num_interop_threads(1)
    assert not torch.cuda.is_initialized() and piq.__version__=='0.8.0'
    def forbidden(*a,**kw):raise RuntimeError('Released CPU scoring forbids CUDA/downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    from wcomr.gpu_budget_pool_v2 import atomic_json
    from wcomr.cara_fast_fidelity_r1 import score_video_pair
    from wcomr.automatic_quality_models_r1 import OriginalMetricFactory
    from wcomr.automatic_quality_batch_r1 import validate_result
    from wcomr.automatic_quality_r1 import sampling_spec,text_sha
    from wcomr.policy_generator_r1.p2_quality_entry import validate_sources_and_decoder
    from wcomr.cara_fast_spec_r1 import digest
    target=control/'scores.json'
    assert not target.exists(),'Recover original scorer, never restart'
    state=dict(status='SCORING',scope_sha256=card['scope_sha256'],release=release,
        RGB=[],LPIPS=[],quality_rows=[],model_lifecycle=[],started_unix=time.time(),GPU_submissions=0)
    def save():atomic_json(target,state)
    def interrupted(signum,frame):raise TimeoutError('Original CAL scorer interrupted '+str(signum))
    signal.signal(signal.SIGALRM,interrupted);signal.signal(signal.SIGTERM,interrupted);signal.alarm(21600);save()
    try:
        for row in collection['rows']:
            slot,r=row['slot'],row['result'];v=r['video_artifact'];assert sha(v['path'])==v['sha256']
            h=hashlib.sha256();pts=[];count=0
            with av.open(v['path']) as con:
                stream=con.streams.video[0];assert stream.average_rate==16 and (stream.height,stream.width)==(432,768)
                for frame in con.decode(video=0):
                    rgb=frame.to_ndarray(format='rgb24');assert rgb.shape==(432,768,3) and rgb.dtype==np.uint8
                    assert frame.pts is not None
                    pts.append(str(frame.pts*frame.time_base));h.update(rgb.tobytes());count+=1
            assert count==93 and sha(v['path'])==v['sha256']
            state['RGB'].append(dict(slot_id=slot['id'],frames=93,RGB_sha256=h.hexdigest(),PTS=pts));save()
        indexed={r['slot']['id']:r for r in collection['rows']};RGB={r['slot_id']:r for r in state['RGB']}
        def equal(a,b):
            assert RGB[a]['RGB_sha256']==RGB[b]['RGB_sha256'] and RGB[a]['PTS']==RGB[b]['PTS']
        equal(card['matrix'][0]['id'],card['matrix'][2]['id']);equal(card['matrix'][1]['id'],card['matrix'][3]['id'])
        formal=[r for r in collection['rows'] if r['slot']['section']=='FORMAL']
        for r in collection['rows']:
            if r['slot']['section'] in ('GLOBAL_WARM','TIMING_REPEAT'):
                ref=next(f for f in formal if all(f['slot'][k]==r['slot'][k] for k in ('member','role')))
                equal(r['slot']['id'],ref['slot']['id'])
        state['RGB_controls_passed']=True;save()
        os.environ['TORCH_HOME']=cfg['torch_home']
        assert sha(Path(cfg['torch_home'])/'hub/checkpoints/alexnet-owt-7be5be79.pth')=='7be5be791159472b1fbf3c69796f7cb30dca7ad8466c2df70058c37116cdee02'
        assert sha(Path(lpips.__file__).parent/'weights/v0.1/alex.pth')=='df73285e35b22355a2df87cdb6b70b343713b667eddbda73e1977e0c860835c0'
        alex=lpips.LPIPS(net='alex',version='0.1',verbose=False).cpu().eval()
        for r in formal:
            slot=r['slot']
            if slot['role']=='NATIVE35':continue
            ref=next(f for f in formal if f['slot']['member']==slot['member'] and f['slot']['role']=='NATIVE35')
            result=score_video_pair(r['result']['video_artifact'],ref['result']['video_artifact'],alex)
            assert result['decoded_RGB_sha256']==[RGB[slot['id']]['RGB_sha256'],RGB[ref['slot']['id']]['RGB_sha256']]
            state['LPIPS'].append(dict(slot_id=slot['id'],role=slot['role'],member=slot['member'],result=result));save()
        del alex
        factory=OriginalMetricFactory(stage=quality_root,resources=binding['resources'],CPU_acceptance=binding['acceptance'],
            CPU_registration=binding['registration'],scorer_fingerprint=digest(binding['identity']),torch=torch,device='cpu')
        members={m['name']:m for m in card['inputs']}
        for dim in ('MUSIQ_LONGER512','subject_consistency','motion_smoothness'):
            life=dict(dimension=dim,status='ENTERING');state['model_lifecycle'].append(life);save()
            with factory(dim) as scorer:
                for r in formal:
                    slot=r['slot'];member=members[slot['member']];video=r['result']['video_artifact']
                    planned=dict(case_id=slot['member'],method=slot['id'],dimension=dim,seed=slot['seed'],role=slot['role'],
                        prompt=member['prompt'],prompt_sha256=text_sha(member['prompt']),input_status='READY_TO_SCORE',
                        video_path=video['path'],video_sha256=video['sha256'],request_sha256=digest(r['result']),
                        scorer_fingerprint=digest(binding['identity']),expected_sampling=sampling_spec(dim))
                    result=scorer.score(planned)
                    raw=control/(slot['id']+'-'+dim+'.raw.json');assert not raw.exists();atomic_json(raw,result)
                    validate_result(planned,result);validate_sources_and_decoder(binding['identity'],result)
                    state['quality_rows'].append(dict(planned=planned,result=result,status='SCORED',raw_sha256=sha(raw)));save()
            life['status']='RELEASED';save()
        assert len(state['LPIPS'])==24 and len(state['quality_rows'])==84 and len(state['RGB'])==35
        state['status']='COMPLETE35_RGB_24_LPIPS_84_QUALITY_PENDING_ACCEPTANCE'
    except BaseException as error:
        state.update(status='FAILED_NO_RETRY_DENOMINATOR_RETAINED',error_type=type(error).__name__,error=str(error));raise
    finally:
        signal.alarm(0);state.update(ended_unix=time.time(),CUDA_initialized=torch.cuda.is_initialized());save()


if __name__=='__main__':main()
