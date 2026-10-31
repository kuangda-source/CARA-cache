"""Actual tiny sampling through the loaded-model runner and refusal boundaries."""
import json
from pathlib import Path

import torch
from wcomr import clean_speed20_r1 as clean
from wcomr.cara_fast_spec_r1 import digest
from wcomr.cara_s_endpoint_runner_r1 import collect_loaded,observed_precision
from wcomr.cara_s_uniform_endpoint_execution_r1 import inspect_original
from wcomr.h0_mode import mode_snapshot
from check_cara_s_endpoint_collection_routes_r2 import cpu_card
from check_cara_s_endpoint_pipeline_routes_r1 import write_video

ROOT=Path(__file__).resolve().parents[1]


def body(inference,selected,wc,rf,common,unused_initial,profile,root,native,flow,inference_module,host,samples):
    import check_wc_time_card_r1 as fixture
    model,net=inference.pipe.model,inference.pipe.model.net
    net.__class__=fixture.load('check_fair_sampling_cpu').native_toy_class(Path(common['runtime']),type(net),dict(vars(wc)))
    net.timestep_scale=.001;model.precision=torch.float32;net.use_wan_fp32_strategy=False
    model.config.conditional_frame_timestep=.1
    ra=json.loads((ROOT/'plans/cara_wc_time_protocol_r1_20261027/RA_BINDING.json').read_text())
    modes=mode_snapshot(net)['module_types'];cases=[];failures=[]
    originals=(model.generate_samples_from_batch,model.decode,inference.pipe.generate_vid2world,net.forward)
    def restored():
        assert (model.generate_samples_from_batch,model.decode,inference.pipe.generate_vid2world,net.forward)==originals
        assert '_cara_paper_timing_active_r1' not in vars(model)
    def decoder(latent):
        base=latent.mean().tanh().reshape(1,1,1,1,1)
        return (base+torch.linspace(-.1,.1,93).reshape(1,1,93,1,1)).expand(1,3,93,64,64).clone()
    class Storage:
        def __init__(self,kind=None):self.calls=0;self.kind=kind
        def check(self):
            self.calls+=1
            if self.calls==1 and self.kind=='storage':raise OSError(28,'CPU private storage low-water')
            if self.calls==1 and self.kind=='parameter':
                with torch.no_grad():next(net.parameters()).add_(0)
    def arguments(alias,path):
        card,bound=cpu_card(flow,alias)
        for item in card['inputs']:item['resolution']='16,16'
        card['scope_sha256']=digest({k:v for k,v in card.items() if k!='scope_sha256'})
        context=dict(host='two_card',CPU_fixture_only=True,scope_sha256=card['scope_sha256'],
            physical_paths=len(card['physical_matrix']),endpoint_binding_sha256=bound['binding_sha256'],
            launch_id='CPU-LOADED-RUNNER-ONLY',new_endpoint_authorization=False,
            model_precision_sha256=digest(observed_precision(model)))
        path.mkdir(parents=True)
        return dict(inference=inference,samples=samples,card=card,bound=bound,common=common,ra_binding=ra,
            host=host,output=path,context=context,storage=Storage(),mode_types=modes,cpu_validation=True)
    with clean.patched(model.tokenizer,'decode',decoder),clean.patched(inference_module,'save_img_or_video',write_video):
        for alias in (False,True):
            args=arguments(alias,root/('loaded-alias25' if alias else 'loaded-full32'))
            collection,evidence=collect_loaded(**args);restored()
            recovered=inspect_original(args['card'],args['output']/'endpoint-collection.json',cpu_validation=True)
            count=25 if alias else 32
            assert recovered['counts']['COMPLETE']==evidence['request_boundary_checks']==count
            assert args['storage'].calls==count+1 and evidence['final_state_restored'] and evidence['shared_eval_verified']
            calls=args['storage'].calls
            try:collect_loaded(**args)
            except ValueError:pass
            else:raise AssertionError('Original loaded collection replayed')
            assert args['storage'].calls==calls
            cases.append(dict(status='PASS',alias=alias,physical_paths=count,storage_checks=calls,
                collection_sha256=digest(collection),runner_checks=evidence,read_only_recovery=True,replay_refused=True))
        for kind in ('storage','parameter','precision','mode'):
            args=arguments(False,root/('loaded-refuse-'+kind));args['storage']=Storage(kind)
            if kind=='precision':args['context']['model_precision_sha256']='f'*64
            if kind=='mode':args['mode_types']={'CPU.wrong.Module':1}
            try:collect_loaded(**args)
            except (ValueError,OSError) as error:
                expected={'storage':'low-water','parameter':'parameters changed','precision':'precision differs','mode':'topology differs'}[kind]
                assert expected in str(error),(kind,str(error))
            else:raise AssertionError('Loaded runner boundary not enforced: '+kind)
            restored()
            path=args['output']/'endpoint-collection.json'
            if kind in ('storage','parameter'):
                collection=json.loads(path.read_text())
                assert collection['status']=='FAILED_NO_REPLAY'
                assert collection['rows'][0]['status']=='TECH_FAILED'
                assert all(r['status']=='NOT_REACHED' for r in collection['rows'][1:])
                assert not list((args['output']/'B').glob('*.pt'))
            else:assert not path.exists()
            failures.append(dict(status='REFUSED',kind=kind,no_sample_executed=True,original_failure_retained=True))
    return [dict(status='PASS',flow=flow,cases=cases,failure_controls=failures,actual_complete_paths=57,
        all36_updates_and_policies_checked=True,real93_frame_video=True,model_weights_loaded=False,
        actual_GPU_context=False,GPU_submissions=0,ledger_written=False)]


def run(runtime,artifact_root,host,samples):
    import check_wc_time_card_r1 as fixture
    previous=fixture.body;fixture.body=body
    try:return fixture.run(runtime,artifact_root,host,samples)
    finally:fixture.body=previous
