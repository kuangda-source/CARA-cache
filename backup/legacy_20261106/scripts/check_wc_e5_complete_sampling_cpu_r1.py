"""E5 affected full sampler and actual native meta head contract, CPU only."""
import argparse
import ast
import importlib.util
import inspect
import json
import os
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True)
    p.add_argument('--runtime',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();assert not args.output.exists()
    os.environ['CUDA_VISIBLE_DEVICES']=''
    sys.path[:0]=[str(args.stage/'src'),str(args.stage/'tests')]
    import torch
    torch.set_num_threads(2)
    def forbidden(*a,**k):raise RuntimeError('E5 complete CPU forbids CUDA/download')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    from wcomr.early_head_elision_sampling_r1 import NativeHeadGuard
    # Reuse the source-bound actual native meta constructor and eval gate,
    # adding only the head/unpatchify validator before its unchanged report.
    old=args.stage/'scripts/check_wc_h0_native_mode_cpu.py'
    spec=importlib.util.spec_from_file_location('E5_actual_native_meta',old)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    source=inspect.getsource(module.main);needle='    print(json.dumps({'
    assert source.count(needle)==1
    injected='    _e5_native_meta_check(net,args.runtime)\n'
    changed=source.replace(needle,injected+needle)
    assert changed.replace(injected,'')==source and ast.dump(ast.parse(changed.replace(injected,'')))==ast.dump(ast.parse(source))
    meta=[]
    def native_check(net,runtime):
        guard=NativeHeadGuard(net,runtime)
        assert net.final_layer.use_adaln_lora and net.final_layer.use_wan_fp32_strategy
        assert guard.unpatchify_contract=='PINNED_NATIVE_UNPATCHIFY'
        epsilon=net.final_layer.layer_norm.eps;net.final_layer.layer_norm.eps=epsilon*2
        try:
            try:guard.validate()
            except ValueError:refused=True
            else:raise AssertionError('Changed native head child config accepted')
        finally:net.final_layer.layer_norm.eps=epsilon
        guard.validate()
        meta.append({'native_head_class':type(net.final_layer).__module__+'.'+type(net.final_layer).__qualname__,
            'hidden_size':net.final_layer.hidden_size,'AdaLN_LoRA':True,'Wan_FP32':True,
            'unpatchify':guard.unpatchify_contract,'native_child_config_mutation_refused':refused,
            'parameter_count':sum(p.numel() for p in net.parameters()),'meta_weights_not_real_forward':True})
    namespace={**vars(module),'_e5_native_meta_check':native_check}
    exec(compile(changed,__file__+'#native_meta_head_contract','exec'),namespace)
    saved_argv=sys.argv
    sys.argv=[str(old),'--runtime',str(args.runtime),'--contract',str(args.stage/'manifests/wc_h0_eval_mode_contract_20261003.json')]
    try:namespace['main']()
    finally:sys.argv=saved_argv
    assert len(meta)==1 and meta[0]['parameter_count']==2059174912
    from check_e5_early_head_complete_sampling_cpu_r1 import run
    value=run(args.runtime,lambda p,**kw:torch.load(p,**kw),args.stage/'CPU-artifacts')
    value['actual_native_meta_head']=meta[0]
    value['native_meta_derivation_inverse_bytes_AST_equal']=True
    value['CUDA_initialized']=torch.cuda.is_initialized();assert not value['CUDA_initialized']
    args.output.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in value.items() if k!='checks'}))


if __name__=='__main__':main()
