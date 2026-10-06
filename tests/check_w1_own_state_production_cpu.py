"""New full-pipeline/bridge/summary and real CPU supervisor integration only."""
import argparse
import ast
import copy
from enum import Enum
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from typing import List,Optional,Tuple,Union
from unittest.mock import patch


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def selected_fixture(c):
    from wcomr.own_state_execution import APPROVAL,CARD
    out=copy.deepcopy(c)
    binding={'approved_card':CARD,'run_id':c['run_id'],'single_run_inclusive_cap_seconds':1800,
        'sample_indices':[4,7,0],'fixed_CFG_calls':[45,46,67,68],'planned_scenes':3,'planned_observations':12,
        'usage_reset':False,'source_user_text':'CPU_SYNTHETIC_NOT_DIRECT_HUMAN_APPROVAL','approval_ref':APPROVAL,'approval_sha256':'a'*64}
    out.update(GPU_execution_selected=True,gpu_uuid='GPU-CPU-SYNTHETIC-NOT-ADMISSION',execution_scope_authority=binding,
        production_cpu_stage='.sync/CPU_SYNTHETIC_NOT_ACTUAL',production_cpu_receipt_sha256='b'*64,
        production_cpu_payload_sha256=dict(c['payload_sha256'],**{'own-state-config.json':'c'*64}))
    out['payload_sha256'][APPROVAL]='a'*64;return out


def contracts(stage,c):
    from wcomr.own_state_execution import validate_config,reserve_budget,settle_budget
    validate_config(c);selected=selected_fixture(c);validate_config(selected,selected=True)
    refused=[]
    changes={'smaller_scene_scope':lambda v:v.update(sample_indices=[4,7]),
        'different_teacher_points':lambda v:v.update(fixed_CFG_calls=[47,48,67,68]),
        'changed_seed':lambda v:v.update(seed=1),'reset_denominator':lambda v:v.update(planned_observations=8),
        'changed_core':lambda v:v['payload_sha256'].update({'src/wcomr/own_state_shadow.py':'0'*64}),
        'longer_limit':lambda v:v['execution_limits'].update(timeout_seconds=2400),
        'teacher_anchor_write':lambda v:v.update(teacher_written_to_deployment=True),
        'all_win_gate':lambda v:v.update(all_scenes_must_improve=True),
        'budget_as_authority':lambda v:v.update(execution_scope_authority={'cap':24}),
        'missing_production_script':lambda v:v['payload_sha256'].pop('scripts/run_w1_own_state.py')}
    for name,change in changes.items():
        bad=copy.deepcopy(c);change(bad)
        try:validate_config(bad)
        except (ValueError,KeyError,TypeError):refused.append(name)
        else:raise RuntimeError('Scope failure accepted '+name)
    before=c['budget_snapshot'];prepaid=reserve_budget(before,selected,1001)
    assert prepaid['used_gpu_hours']==before['used_gpu_hours']+.5
    for wall in [.125,1000,1801]:
        actual=settle_budget(prepaid,before,selected,wall,1001)
        assert abs(actual['used_gpu_hours']-before['used_gpu_hours']-wall/3600)<1e-12
    for name,bad in [('foreign_inflight',dict(before,other_inflight={})),('insufficient_whole_card',dict(before,used_gpu_hours=23.6))]:
        try:reserve_budget(bad,selected,1001)
        except ValueError:refused.append(name)
        else:raise RuntimeError(name)
    bad=copy.deepcopy(prepaid);bad['used_gpu_hours']+=.1
    try:settle_budget(bad,before,selected,10,1001)
    except ValueError:refused.append('concurrent_ledger_preserved')
    else:raise RuntimeError('Overwrote concurrent ledger')
    return refused,selected


def pipeline(stage,runtime,c):
    import torch
    from einops import rearrange
    from wcomr.own_state_sampling import run_request,run_batch,historical_bridge
    from wcomr.own_state_summary import summarize
    from wcomr.decoder_policy import backend_flags
    torch.cuda._lazy_init=lambda *a,**k:(_ for _ in ()).throw(RuntimeError('CPU fixture denies CUDA'))
    tree=ast.parse((runtime/'cosmos_predict2/_src/predict2/inference/worldcache_utils.py').read_text())
    selected={'compute_optimal_gamma','estimate_optical_flow','warp_feature','worldcache_mini_train_dit_forward','apply_worldcache'}
    tree.body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in selected]
    class DataType(Enum):VIDEO=1
    ns=dict(torch=torch,amp=torch.amp,F=torch.nn.functional,rearrange=rearrange,DataType=DataType,
        Optional=Optional,List=List,Tuple=Tuple,Union=Union,log=SimpleNamespace(info=lambda *a:None))
    exec(compile(tree,str(runtime/'cosmos_predict2/_src/predict2/inference/worldcache_utils.py'),'exec'),ns)
    class Block(torch.nn.Module):
        def __init__(self,f):super().__init__();self.f=f
        def forward(self,x,**kwargs):return x*self.f+.01
    class Toy(torch.nn.Module):
        def __init__(self):
            super().__init__();self.blocks=torch.nn.ModuleList([Block(1.02),Block(1.03),Block(1.04)])
            self.patch_spatial=self.patch_temporal=1;self.use_crossattn_projection=self.use_wan_fp32_strategy=False
            self.t_embedder=lambda t:(t.unsqueeze(-1),None);self.t_embedding_norm=lambda t:t
            self.final_layer=lambda x,*a,**k:x
        def prepare_embedded_sequence(self,x,**kwargs):return x.permute(0,2,3,4,1).contiguous(),None,None
        def unpatchify(self,x):return x.permute(0,4,1,2,3).contiguous()
    old=json.loads((stage/'reports/w1_replay_r1_runner.json').read_text());frozen=copy.deepcopy(old)
    original=ns['worldcache_mini_train_dit_forward']
    class FlowUniPCMultistepScheduler:
        def __init__(self):self.timesteps=torch.tensor(old['sampling_protocol']['timesteps'])
    class Inference:
        def __init__(self,scenario='normal'):
            net=ns['apply_worldcache'](Toy(),num_steps=70,ret_ratio=.2,rel_l1_thresh=1,
                probe_depth=1,osi_enabled=True,flow_enabled=True,flow_scale=1).eval()
            vae_model=SimpleNamespace(_feat_map=None,_conv_idx=0,_enc_feat_map=None,_enc_conv_idx=0)
            vae=SimpleNamespace(model=torch.nn.Linear(1,1).eval())
            vae.model._feat_map=None;vae.model._conv_idx=0;vae.model._enc_feat_map=None;vae.model._enc_conv_idx=0
            for k in ['scale','img_mean','img_std','video_mean','video_std']:setattr(vae,k,1)
            for k in ['dtype','is_amp','is_parallel','temporal_window','context_parallel_enabled','benchmark']:setattr(vae,k,'CPU_TOY')
            self.tokenizer=SimpleNamespace(model=vae,keep_decoder_cache=False,keep_encoder_cache=False,chunk_duration=93,cp_initialized=False)
            self.model=SimpleNamespace(net=net,sample_scheduler=FlowUniPCMultistepScheduler(),
                config=SimpleNamespace(use_kerras_sigma_at_inference=True),tokenizer=self.tokenizer)
            self.pipe=SimpleNamespace(model=self.model);self.scenario=scenario
            self.presets=SimpleNamespace(run_text_guardrail=lambda p:True,run_video_guardrail=lambda v:v)
            def writer(value,path):
                if scenario=='writer_failure':raise OSError('CPU_SIMULATED_WRITER_FAILURE')
                path.write_bytes(value.detach().numpy().tobytes())
            self.module=SimpleNamespace(guardrail_presets=self.presets,save_img_or_video=writer)
            self.model.generate_samples_from_batch=self.generate_samples_from_batch;self.model.decode=lambda x:x
            self.initial_forward=vars(net)['forward']
        def generate_samples_from_batch(self,batch):
            x=batch
            for step in range(36):
                v=[self.model.net(x,torch.tensor([1-step/36]),torch.ones(1,2,3)) for _ in range(2)]
                x=x-(v[0]+v[1])*.00015
            return x
        def generate(self,samples,output_dir):
            sample=samples[0];self.model.net.cnt=0
            self.presets.run_text_guardrail(sample.prompt)
            x=torch.linspace(.7,1.3,72).reshape(1,3,2,3,4)
            x=self.model.generate_samples_from_batch(x);x=self.model.decode(x);x=self.presets.run_video_guardrail(x)
            path=output_dir/'CPU_MOCK_NOT_VIDEO';self.module.save_img_or_video(x,path);return [str(path)]
    def reader(path):
        return [{'shape':[432,768,3],'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                 'pts':i,'time_base':'1/16'} for i in range(93)]  # Explicit simulated records, no codec/geometry claim.
    samples=[SimpleNamespace(**old['cases'][i]['sample']) for i in c['sample_indices']]
    inference=Inference();flags=backend_flags();snapshots=[]
    def clean():
        assert inference.model.net.forward==inference.initial_forward and not inference.model.net._forward_hooks
        assert all(not b._forward_pre_hooks for b in inference.model.net.blocks)
        assert backend_flags()==flags and not torch.cuda.is_initialized()
    with tempfile.TemporaryDirectory(prefix='own-pipeline-CPU-',dir=stage) as d:
        destination=Path(d)
        for i,sample in zip(c['sample_indices'],samples):
            case={};entry=old['protocol']['samples'][i]
            off=run_request(inference,sample,entry,params=old['protocol']['calibration_defaults'],calls=c['fixed_CFG_calls'],
                original=original,sampling=old['sampling_protocol'],inference_module=inference.module,
                destination=destination/'OFF'/sample.name,holder=case,save=lambda:None,synchronize=lambda:None,reader=reader,diagnostic=False)
            frozen['cases'][i]['scalar_off']=off;clean()
        state={}
        run_batch(inference,samples,frozen,c,state=state,save=lambda:snapshots.append(copy.deepcopy(state)),
            output=destination/'ON',inference_module=inference.module,original=original,synchronize=lambda:None,reader=reader)
        clean();summary=summarize(state,c)
        assert summary['valid_scene_count']==3 and len(state['cases'])==3
        assert sum(len(x['observed']['shadow_records']) for x in state['cases'])==12
        refused=[]
        for label,key in [('forward_hash','forward_output_sha256'),('cache_hash','cache_end_sha256'),('calibration_hash','calibration_end_sha256'),
                          ('video_hash','video_sha256'),('RGB_hash','decoded_rgb'),('solver_grid','sampling'),('pipeline','pipeline_events')]:
            obs=copy.deepcopy(state['cases'][0]['observed']);obs[key]=None
            try:historical_bridge(frozen['cases'][4]['scalar_off'],obs,old['protocol']['samples'][4],c['fixed_CFG_calls'])
            except (ValueError,TypeError):refused.append(label)
            else:raise RuntimeError('Identity mismatch accepted '+label)
        partial=copy.deepcopy(state);partial['cases']=partial['cases'][:2]
        assert summarize(partial,c)['status']=='PARTIAL_DIAGNOSTIC_NOT_FULL_CARD'
        mixed=copy.deepcopy(state)
        for j,case in enumerate(mixed['cases']):
            for r in case['observed']['shadow_records']:
                for metric in r['candidates']['official'].values():metric['mse']=1
                for metric in r['candidates']['scalar'].values():metric['mse']=[.5,2,1][j]
        mixed_summary=summarize(mixed,c)
        assert [r['errors']['velocity']['official_minus_scalar'] for r in mixed_summary['rows']]==[.5,-1,0]
        bad=copy.deepcopy(state);bad['cases'][0]['observed']['shadow_records'][0]['candidates']['scalar']['velocity']['mse']=float('nan')
        try:summarize(bad,c)
        except ValueError:refused.append('nonfinite_summary')
        else:raise RuntimeError('NaN accepted')
        failure=Inference('writer_failure');inference=failure;case={}
        try:run_request(failure,samples[0],old['protocol']['samples'][4],params=old['protocol']['calibration_defaults'],
            calls=c['fixed_CFG_calls'],original=original,sampling=old['sampling_protocol'],inference_module=failure.module,
            destination=destination/'FAIL',holder=case,save=lambda:None,synchronize=lambda:None,reader=reader)
        except OSError:refused.append('writer_failure_cleanup')
        else:raise RuntimeError('Writer failure not propagated')
        clean();assert case['observed']['status']=='FAILED_RETAINED_NOT_A_SCIENTIFIC_ROW'
    return {'complete_CPU_pipeline_scenes':3,'OFF_and_ON_full_pipelines':6,'teacher_observations':12,
        'bridge_refusals':refused,'mixed_signed_summary_preserved':True,'partial_scope_not_full':True,
        'hooks_forward_flags_restored':True,'mock_writer_and_mock_RGB_only':True,'real_video_codec_verified':False,
        'new_core_eight_fixtures_not_rerun':True,'CUDA_initialized':False,'snapshots':len(snapshots)}


def supervised(stage,c):
    sup=load(stage/'scripts/supervise_w1_own_state.py','own_state_supervisor_CPU');real=sup.subprocess.Popen;results=[]
    for scenario in ['normal_CPU_child','spawn_failure','foreign_GPU_stop_own_CPU_child']:
        with tempfile.TemporaryDirectory(prefix='own-supervisor-CPU-',dir=stage) as d:
            root=Path(d);(root/'.sync').mkdir();(root/'reports').mkdir();(root/'runtime').mkdir()
            budget=c['budget_snapshot'];(root/'reports/budget.json').write_text(json.dumps(budget))
            child_stage=root/'.sync/selected';child_stage.mkdir();(child_stage/'own-state-config.json').write_text(json.dumps(selected_fixture(c)))
            (child_stage/'src').symlink_to(stage/'src',target_is_directory=True)
            args=SimpleNamespace(project=root,stage=child_stage,output=root/'outputs'/c['run_id'],gpu_uuid='GPU-CPU-SYNTHETIC-NOT-ADMISSION',source_revision='d'*40)
            queries=[0]
            def query(command,**kwargs):
                if '--query-gpu=uuid,name,memory.used,compute_cap' in command:return args.gpu_uuid+', NVIDIA RTX A6000, 0, 8.6\n'
                queries[0]+=1
                return args.gpu_uuid+', '+str(os.getpid())+'\n' if scenario.startswith('foreign_') and queries[0]>2 else ''
            def launch(command,**kwargs):
                if scenario=='spawn_failure':raise OSError('CPU_SIMULATED_SPAWN_FAILURE')
                assert kwargs['start_new_session'] and len(kwargs['pass_fds'])==1
                return real([sys.executable,'-c','import time;time.sleep('+str(5 if scenario.startswith('foreign_') else .01)+')'],**kwargs)
            with patch.object(sup.argparse.ArgumentParser,'parse_args',return_value=args),patch.object(sup.subprocess,'check_output',side_effect=query),\
                patch.object(sup.subprocess,'run',return_value=SimpleNamespace(returncode=0)),patch.object(sup.subprocess,'Popen',side_effect=launch):sup.main()
            r=json.loads((args.output/'supervisor.json').read_text());after=json.loads((root/'reports/budget.json').read_text())
            assert abs(after['used_gpu_hours']-budget['used_gpu_hours']-r['wall_seconds']/3600)<1e-12
            assert after['gpu_jobs_launched']==budget['gpu_jobs_launched']+1 and not any(k.endswith('_inflight') for k in after)
            if r['child_pid']:
                try:os.kill(r['child_pid'],0)
                except ProcessLookupError:pass
                else:raise RuntimeError('Own CPU child still live')
            os.kill(os.getpid(),0)
            results.append({'scenario':scenario,'status':r['status'],'actual_failure_wall_charged_in_temporary_CPU_ledger':True,'child_reaped':True})
    return results


def actual_import(stage,runtime,c):
    import torch
    def forbidden(*a,**k):raise RuntimeError('Production CPU import denies weights/CUDA')
    torch.cuda._lazy_init=forbidden;torch.load=forbidden
    import triton
    class ImportOnlyDriver:
        def get_benchmarker(self):return forbidden
        def __getattr__(self,n):raise RuntimeError('No CPU Triton '+n)
    triton.runtime.driver.active=ImportOnlyDriver()
    import transformers.utils as hf
    from transformers.utils import import_utils
    before=(hf.is_flash_attn_2_available,import_utils.is_flash_attn_2_available,torch.cuda.current_device)
    hf.is_flash_attn_2_available=lambda:True;import_utils.is_flash_attn_2_available=lambda:True;torch.cuda.current_device=lambda:0
    try:arguments=importlib.import_module('cosmos_predict2.config')
    finally:hf.is_flash_attn_2_available,import_utils.is_flash_attn_2_available,torch.cuda.current_device=before
    runner=load(stage/'scripts/run_w1_own_state.py','own_state_CPU_typed_arguments')
    old=json.loads((stage/'reports/w1_replay_r1_runner.json').read_text())
    setup,samples=runner.build_arguments(old,c,stage/'CPU_ARGUMENTS_ONLY',arguments)
    for name in ['own_state_sampling','own_state_shadow','own_state_execution','own_state_summary']:
        module=importlib.import_module('wcomr.'+name)
        assert Path(module.__file__).resolve().is_relative_to((stage/'src').resolve())
    assert not torch.cuda.is_initialized()
    return {'actual_original_typed_requests':3,'changed_setup_keys':['output_dir'],'CUDA_initialized':False,'model_constructed':False,'weights_loaded':False}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stage',type=Path,required=True);p.add_argument('--runtime',type=Path,required=True)
    p.add_argument('--actual-import',action='store_true');a=p.parse_args()
    sys.path[:0]=[str(a.stage/'src'),str(a.runtime),str(a.runtime/'packages/cosmos-oss'),str(a.runtime/'packages/cosmos-cuda')]
    c=json.loads((a.stage/'own-state-config.json').read_text())
    if a.actual_import:r=actual_import(a.stage,a.runtime,c)
    else:
        refused,selected=contracts(a.stage,c);r={'scope_and_cost_refusals':refused,'pipeline':pipeline(a.stage,a.runtime,c),'supervised':supervised(a.stage,c)}
    r.update(status='OWN_STATE_PRODUCTION_CPU_CHECK_PASS_NOT_GPU',GPU_submissions=0,scientific_labels=0)
    print(json.dumps(r,allow_nan=False))


if __name__=='__main__':main()
