#!/usr/bin/env python3
"""Five-reference identity and complete pipeline CPU fixtures, never generation."""
import argparse
import copy
import hashlib
import importlib
import inspect
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace


def pure_checks(draft, replay, cal):
    from wcomr.w1_native_reference_scope import validate_reference_scope
    selected = validate_reference_scope(draft, replay, cal)
    refused = []
    mutations = {
        'wrong_card': lambda d: d.update(card='WC_OTHER'),
        'reduced_five_scope': lambda d: d.update(new_Native_generation_phases=4),
        'replacement_robot': lambda d: d['rows'][6].update(generate_new_Native_in_proposed_card=True),
        'drop_original_rejection': lambda d: d.update(original_W1_rejected=0),
        'changed_seed': lambda d: d['rows'][0]['request'].update(seed=1),
        'changed_prompt': lambda d: d['rows'][0]['request'].update(prompt='replacement'),
        'changed_steps': lambda d: d['rows'][0]['request'].update(num_steps=23),
        'changed_video': lambda d: d['rows'][0]['W1_scalar'].update(sha256='0'*64),
        'discard_existing_reference': lambda d: d['rows'][1].update(matched_Native=None),
        'new_algorithm': lambda d: d['planned_changes_to_generation'].update(worldcache_rel_l1_thresh=.08),
        'GPU_selected': lambda d: d.update(GPU_execution_selected=True),
        'authority_from_budget': lambda d: d.update(execution_scope_authority={'cap':24}),
        'draft_as_authorization': lambda d: d.update(cap_is_GPU_authorization=True),
        'changed_model': lambda d: d['model_setup_from_original_W1'].update(model='14B/post-trained'),
        'changed_decoder': lambda d: d.update(decoder_checkpoint_sha256='0'*64),
        'changed_solver': lambda d: d['sampling_protocol']['timesteps'].__setitem__(0,994),
    }
    for name, mutate in mutations.items():
        damaged = copy.deepcopy(draft); mutate(damaged)
        try: validate_reference_scope(damaged, replay, cal)
        except (ValueError, KeyError): refused.append(name)
        else: raise RuntimeError('Damaged reference contract accepted: '+name)
    return selected, refused


def torch_checks(rows, sampling, destination):
    import torch
    from wcomr.decoder_policy import backend_flags
    from wcomr.w1_native_reference_sampling import run_native_batch, run_native_request
    assert not torch.cuda.is_initialized()
    def forbidden(*a, **k): raise RuntimeError('CUDA forbidden in W1 Native CPU fixture')
    torch.cuda._lazy_init = forbidden
    class Box:
        def __init__(self, shape): self.shape, self.dtype = shape, torch.float32
    class Sample:
        def __init__(self, request): self.request=request; self.__dict__.update(request)
        def model_dump_json(self): return json.dumps(self.request)
    class FlowUniPCMultistepScheduler:
        def __init__(self): self.timesteps=torch.tensor(sampling['timesteps'])
        def step(self, value): return value
    class MinimalV1LVGDiT(torch.nn.Module):
        def __init__(self, scenario):
            super().__init__(); self.blocks=torch.nn.ModuleList([torch.nn.Linear(2,2) for _ in range(28)])
            self.scenario=scenario; self.worldcache_enabled=True
        def forward(self, value):
            for index, block in enumerate(self.blocks):
                if index==27 and self.scenario=='skipped_deep': continue
                value=block(value)
            return value
    # Explicit stand-in class identity; the real class origin is checked separately.
    MinimalV1LVGDiT.forward.__module__='cosmos_predict2._src.predict2.networks.minimal_v1_lvg_dit'
    MinimalV1LVGDiT.forward.__qualname__='MinimalV1LVGDiT.forward'
    class Model:
        def __init__(self, scenario):
            self.net=MinimalV1LVGDiT(scenario).eval(); self.sample_scheduler=FlowUniPCMultistepScheduler()
            self.config=SimpleNamespace(use_kerras_sigma_at_inference=True); self.scenario=scenario
        def generate_samples_from_batch(self, batch):
            value=torch.ones(1,2)
            for _ in range(35 if self.scenario=='short_sampling' else 36):
                value=self.net(value); value=self.net(value); self.sample_scheduler.step(value)
            return value
        def decode(self, value): return Box([1,3,93,432,768])
    class Pipe:
        def __init__(self, scenario): self.model=Model(scenario); self.worldcache_enabled=True
        def _get_data_batch_input(self, request): return torch.ones(1,2)
    class Inference:
        def __init__(self, scenario, rejections=None):
            self.pipe=Pipe(scenario); self.scenario=scenario; self.rejections=rejections or {}
            self.current=None; self.patch_calls=0
            def stale_cache_forward(value): self.patch_calls+=1; raise RuntimeError('Stale cache patch executed')
            self.stale=stale_cache_forward; self.pipe.model.net.forward=self.stale
            self.presets=SimpleNamespace(
                run_text_guardrail=lambda text:self.rejections.get(self.current)!='text',
                run_video_guardrail=lambda video:None if self.rejections.get(self.current)=='video' else video,
            )
            def save_video(video, path):
                if self.scenario=='writer_failure': raise OSError('simulated disk write error')
                if self.scenario!='missing_artifact':
                    path.parent.mkdir(parents=True,exist_ok=False)
                    path.write_bytes(b'MOCK_WRITER_ONLY_NOT_VIDEO_OR_CODEC_EVIDENCE')
            self.module=SimpleNamespace(guardrail_presets=self.presets,save_img_or_video=save_video)
        def generate(self, samples, output_dir):
            sample=samples[0]; self.current=sample.name
            assert not self.pipe.worldcache_enabled and not self.pipe.model.net.worldcache_enabled
            if not self.presets.run_text_guardrail(sample.prompt): return []
            batch=self.pipe._get_data_batch_input(sample)
            if self.scenario=='double_prepare': self.pipe._get_data_batch_input(sample)
            value=self.pipe.model.generate_samples_from_batch(batch)
            if self.scenario=='wrong_grid': self.pipe.model.sample_scheduler.timesteps[0]=994
            value=self.pipe.model.decode(value)
            value=Box([93,432,768,3])
            value=self.presets.run_video_guardrail(value)
            if value is None: return []
            path=output_dir/(sample.name+'.mp4')
            self.module.save_img_or_video(Box([3,93,432,768]),path)
            return [str(path)]
    samples=[Sample(r['request']) for r in rows]; flags=backend_flags(); snapshots=[]
    def check_restored(inference):
        assert inference.patch_calls==0 and inference.pipe.worldcache_enabled
        assert inference.pipe.model.net.worldcache_enabled
        assert vars(inference.pipe.model.net)['forward'] is inference.stale
        assert all(not b._forward_pre_hooks for b in inference.pipe.model.net.blocks)
        assert backend_flags()==flags and not torch.cuda.is_initialized()
    batches=[]
    for name,rejections in [('all_accepted',{}),('retained_rejections',{samples[0].name:'text',samples[1].name:'video'})]:
        inference=Inference('normal',rejections);state={}
        run_native_batch(inference,samples,rows,state=state,save=lambda:snapshots.append(copy.deepcopy(state)),
            output=destination/name,inference_module=inference.module,sampling_policy=sampling,
            expected_flags=flags,synchronize=lambda:None)
        check_restored(inference)
        assert len(state['cases'])==5 and state['planned_references']==5 and state['original_denominator']==[8,7,1]
        assert state['accepted_references']==(5 if name=='all_accepted' else 3)
        if name=='retained_rejections':
            assert state['cases'][0]['CFG_calls']==0 and state['cases'][0]['artifact'] is None
            assert state['cases'][1]['CFG_calls']==72 and state['cases'][1]['artifact'] is None
        assert all(c['full_frame_decode_status']=='PENDING_CPU_AFTER_GPU_RELEASE' for c in state['cases'])
        batches.append(state)
    refused=[]
    for scenario in ['skipped_deep','short_sampling','double_prepare','wrong_grid','missing_artifact','writer_failure']:
        inference=Inference(scenario);state={'status':'STARTED'}
        try:
            run_native_request(inference,samples[0],state=state,save=lambda:snapshots.append(copy.deepcopy(state)),
                output=destination/scenario,inference_module=inference.module,sampling_policy=sampling,
                expected_flags=flags,synchronize=lambda:None)
        except (ValueError,RuntimeError,OSError):
            assert state['status']=='TECH_BLOCKED_NATIVE_REFERENCE'; refused.append(scenario)
        else: raise RuntimeError('Bad Native generation accepted: '+scenario)
        check_restored(inference)
    inference=Inference('normal');state={'status':'STARTED'}
    inference.pipe.model.net.train()
    try:
        run_native_request(inference,samples[0],state=state,save=lambda:None,output=destination/'training',
            inference_module=inference.module,sampling_policy=sampling,expected_flags=flags,synchronize=lambda:None)
    except ValueError: refused.append('training_mode')
    else: raise RuntimeError('Training mode accepted')
    check_restored(inference)
    state={};inference=Inference('normal')
    try:
        run_native_batch(inference,samples[:-1],rows[:-1],state=state,save=lambda:None,
            output=destination/'short_scope',inference_module=inference.module,sampling_policy=sampling,
            expected_flags=flags,synchronize=lambda:None)
    except ValueError: refused.append('short_scope')
    else: raise RuntimeError('Reduced five-reference batch accepted')
    check_restored(inference)
    return {'batches':batches,'generation_refusals':refused,'persisted_snapshots':len(snapshots),
            'CPU_mock_writer':True,'real_video_or_codec_verified':False,
            'old_instance_patch_never_executed':True,'hooks_and_forward_restored':True,
            'CUDA_initialized':False,'weights_loaded':False}


def actual_import(stage,runtime,draft):
    import torch
    assert not torch.cuda.is_initialized()
    def forbidden(*a,**k): raise RuntimeError('Weights/model CUDA execution forbidden during CPU imports')
    torch.cuda._lazy_init=forbidden;torch.load=forbidden
    import triton
    class ImportOnlyDriver:
        def get_benchmarker(self):return forbidden
        def __getattr__(self,name):raise RuntimeError('CPU import forbids Triton driver '+name)
    triton.runtime.driver.active=ImportOnlyDriver()
    # The same exiting-process import adapters used by the verified conditioner checker.
    import transformers.utils as hf_utils
    from transformers.utils import import_utils
    import importlib.metadata
    from packaging.version import Version
    assert Version(importlib.metadata.version('flash_attn'))>=Version('2.1.0')
    previous=(hf_utils.is_flash_attn_2_available,import_utils.is_flash_attn_2_available,torch.cuda.current_device)
    hf_utils.is_flash_attn_2_available=lambda:True
    import_utils.is_flash_attn_2_available=lambda:True
    torch.cuda.current_device=lambda:0
    try:
        config=importlib.import_module('cosmos_predict2.config')
        native=importlib.import_module('cosmos_predict2._src.predict2.networks.minimal_v1_lvg_dit')
    finally:
        hf_utils.is_flash_attn_2_available,import_utils.is_flash_attn_2_available,torch.cuda.current_device=previous
    from wcomr.w1_native_reference_sampling import NATIVE_FORWARD
    fn=native.MinimalV1LVGDiT.forward
    source=runtime/'cosmos_predict2/_src/predict2/networks/minimal_v1_lvg_dit.py'
    assert Path(native.__file__).resolve()==source.resolve()
    assert fn.__module__+'.'+fn.__qualname__==NATIVE_FORWARD
    assert Path(inspect.getsourcefile(fn)).resolve()==source.resolve()
    requests=[config.InferenceArguments(**row['request']) for row in draft['rows']]
    assert [json.loads(r.model_dump_json()) for r in requests]==[r['request'] for r in draft['rows']]
    params=dict(draft['model_setup_from_original_W1']);params.update(worldcache_enabled=False,output_dir=str(stage/'native-setup-CPU-only'))
    setup=config.SetupArguments(**params);actual=json.loads(setup.model_dump_json())
    expected=dict(draft['model_setup_from_original_W1']);expected.update(worldcache_enabled=False,output_dir=str(stage/'native-setup-CPU-only'))
    assert actual==expected
    assert not torch.cuda.is_initialized()
    return {'status':'ACTUAL_NATIVE_CLASS_AND_ORIGINAL_ARGUMENTS_CPU_IMPORT_PASS',
            'forward_identity':NATIVE_FORWARD,'native_class_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'parsed_original_requests':8,'changed_setup_keys':['worldcache_enabled','output_dir'],
            'GPU_runtime_import_adapters':False,'CUDA_initialized':False,'weights_loaded':False,'model_instantiated':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['project','stage','runtime']:p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--pure-only',action='store_true');p.add_argument('--actual-import',action='store_true')
    a=p.parse_args()
    os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    sys.path[:0]=[str(a.stage/'src'),str(a.runtime),str(a.runtime/'packages/cosmos-oss'),str(a.runtime/'packages/cosmos-cuda')]
    read=lambda name:json.loads((a.stage/name).read_text())
    draft=read('w1-reference-draft.json');replay=read('reports/w1_replay_r1_runner.json');cal=read('reports/w1d_cal8_r1_runner.json')
    rows,refused=pure_checks(draft,replay,cal)
    if a.actual_import:
        print(json.dumps(actual_import(a.stage,a.runtime,draft)));return
    result={'status':'W1_NATIVE_REFERENCE_SCOPE_CPU_PASS','scope_refusals':refused,'science_reference_slots':[r['original_CAL_index'] for r in rows],
            'GPU_submissions':0,'production_supervisor_ready':False}
    if not a.pure_only:
        import torch
        if torch.__version__!='2.7.1+cu128':raise ValueError('Pinned real-host CPU Torch differs')
        result.update(torch_checks(rows,replay['sampling_protocol'],a.stage/'mock-native-output'))
        result['status']='W1_NATIVE_REFERENCE_COMPLETE_FIVE_SCOPE_CPU_FIXTURES_PASS_NOT_GPU'
    print(json.dumps(result))


if __name__=='__main__':main()
