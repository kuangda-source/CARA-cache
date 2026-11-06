#!/usr/bin/env python3
"""Pinned CPU alias, independence, continuation and restoration controls for E1."""
import argparse
import copy
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import time


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--stage',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('No repeated E1 CPU result identity')
    reg=json.loads((args.stage/'preregistration.json').read_text())
    for name,expected in reg['payload_sha256'].items():
        assert hashlib.sha256((args.stage/name).read_bytes()).hexdigest()==expected
    os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',OMP_NUM_THREADS='2')
    sys.path.insert(0,str(args.stage/'src'))
    import numpy as np
    import torch
    assert torch.__version__=='2.7.1+cu128' and not torch.cuda.is_initialized()
    def forbidden(*a,**kw):raise RuntimeError('E1 CPU primitive validation forbids CUDA and downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden;torch.set_num_threads(2)
    from wcomr.cpu_owned_state_snapshot import CPUOwnedStateImage,CPUDeploymentRoundtrip,storage_inventory
    from wcomr.partial_mlp_deployment_state import DeploymentRoundtrip,plain
    from wcomr.partial_mlp import ProjectionCache
    from wcomr.mid_coverage import tree_digest
    started=time.perf_counter()
    @dataclass
    class Anchor:
        step:int
        probe:torch.Tensor
        residual:torch.Tensor
    class Owner:
        def __init__(self,state):
            self.state=state;self.poisoned=False;self.generation=1
            self.parameter=torch.nn.Parameter(torch.ones(3),requires_grad=False)
        def check_healthy(self):
            if self.poisoned:raise ValueError('Poisoned owner cannot snapshot or restore')
        def installation(self):return (id(self),id(self.parameter),self.parameter._version,self.generation)
        def own_state(self):return self.state
        def restore_own_state(self,state):self.state=state
        def fingerprint(self):return tree_digest(plain(self.state))
    def state():
        base=torch.arange(128,dtype=torch.float32).reshape(8,16)
        cache=torch.linspace(-2,2,1024,dtype=torch.float32).reshape(32,32)
        shared={'shared_history':[{'step':12,'action':'PP','working_step':11,'true_D_step':9}]}
        return {'dense_calibrators':[{'anchors':[Anchor(7,base,base.t()),Anchor(9,base[:,::2],base[1:7,2:12])]}],
            'projection':{(4,0):ProjectionCache(cache,torch.arange(32),torch.ones(32,dtype=torch.uint8),
                ('request','condition','u'),((11,0),(12,0)),9)},
            'working':{'probe':base,'projection_t':cache.t(),'byte_alias':cache.view(torch.uint8),
                'broadcast_alias':base[0,:].expand(3,16),'scalar_alias':base[2,3],
                'empty':torch.empty(0)},'pair_last':base,'base_last':base,
            'solver_probe':{'numerical_step':12,'trajectory':base[:2,:8]},
            'source_controller':shared,'A_readout':shared,'head_calls':[{'step':12,'slot':0}],
            'owned_numpy':np.arange(8),'metadata':('P',12,0.1,True,None)}
    def topology(x):
        base=x['pair_last'];work=x['working'];anchors=x['dense_calibrators'][0]['anchors']
        assert base is x['base_last'] is work['probe'] is anchors[0].probe
        assert x['source_controller'] is x['A_readout']
        assert anchors[0].residual.stride()==(1,16) and anchors[1].probe.stride()==(16,2)
        assert anchors[1].residual.storage_offset()==18 and work['scalar_alias'].storage_offset()==35
        assert work['broadcast_alias'].stride()==(0,1)
        assert base.untyped_storage()._cdata==anchors[1].residual.untyped_storage()._cdata
        cache=x['projection'][(4,0)].value
        assert cache.untyped_storage()._cdata==work['projection_t'].untyped_storage()._cdata==work['byte_alias'].untyped_storage()._cdata
        assert cache.dtype==torch.float32 and work['byte_alias'].dtype==torch.uint8
    def RNG():return (random.getstate(),np.random.get_state(),torch.random.get_rng_state().clone())
    def assert_RNG(a,b):
        assert a[0]==b[0] and a[1][0]==b[1][0] and np.array_equal(a[1][1],b[1][1]) and a[1][2:]==b[1][2:]
        assert torch.equal(a[2],b[2])
    def continuation(x):
        # Same downstream arithmetic through two overlapping views. Tensor
        # alias preservation is consequential, not just metadata equality.
        result=x['solver_probe']['trajectory'].clone()
        for step in range(13,37):
            x['working']['probe'][0,0].add_(.01*step)
            x['projection'][(4,0)].value[1,2].mul_(.999)
            result=result+.01*x['dense_calibrators'][0]['anchors'][0].residual[:8,:2].t()
        return result
    checks=[];refusals=[]
    with torch.no_grad():
        random.seed(82);np.random.seed(82);torch.manual_seed(82)
        original=state();before=tree_digest(plain(original));rng=RNG()
        image=CPUOwnedStateImage(original,logical_copy_cap_bytes=1<<20,CPU_storage_cap_bytes=1<<20)
        assert_RNG(rng,RNG());topology(image.saved);assert before==image.digest
        original['pair_last'].add_(100);original['source_controller']['shared_history'].clear()
        original['owned_numpy'].fill(99)
        assert tree_digest(plain(image.saved))==before
        first=image.materialize();second=image.materialize();topology(first);topology(second)
        assert first['pair_last'].untyped_storage()._cdata!=second['pair_last'].untyped_storage()._cdata
        assert first['pair_last'].untyped_storage()._cdata!=image.saved['pair_last'].untyped_storage()._cdata
        assert np.array_equal(first['owned_numpy'],np.arange(8)) and not np.shares_memory(first['owned_numpy'],image.saved['owned_numpy'])
        first['pair_last'].fill_(-8);first['source_controller']['shared_history'].clear()
        assert tree_digest(plain(second))==before and tree_digest(plain(image.saved))==before
        checks.append('storage_views_object_aliases_and_numpy_independence')
        normal=copy.deepcopy(state());cpu=image.materialize()
        assert torch.equal(continuation(normal),continuation(cpu))
        checks.append('overlapping_view_updates_same_complete24_step_continuation')
        old_owner,new_owner=Owner(state()),Owner(state())
        old=DeploymentRoundtrip(old_owner,logical_copy_cap_bytes=1<<20)
        new=CPUDeploymentRoundtrip(new_owner,logical_copy_cap_bytes=1<<20,CPU_storage_cap_bytes=1<<20)
        assert old.origin==new.origin and old.bytes==new.bytes and new.image.GPU_snapshot_storage_allocation_bytes==0
        for owner in (old_owner,new_owner):
            owner.state['pair_last'].fill_(100);owner.state['head_calls'].append({'injected':True})
            owner.state['source_controller']['shared_history'].clear()
        old.restore();new.restore();topology(new_owner.state)
        assert old_owner.fingerprint()==new_owner.fingerprint()==new.origin
        assert torch.equal(continuation(old_owner.state),continuation(new_owner.state))
        checks.append('original_deepcopy_roundtrip_equivalent_values_and_continuation')
        for fault in ('poison','parameter_changed','installation_changed'):
            owner=Owner(state());snap=CPUDeploymentRoundtrip(owner,logical_copy_cap_bytes=1<<20,CPU_storage_cap_bytes=1<<20)
            if fault=='poison':owner.poisoned=True
            elif fault=='parameter_changed':owner.parameter.add_(1)
            else:owner.generation+=1
            try:snap.restore()
            except ValueError:refusals.append(fault)
            else:raise AssertionError('Bad installation or poison accepted')
        bad_images=[('logical_cap',state(),1,1<<20),('CPU_storage_cap',state(),1<<20,1),
            ('grad_tensor',{'x':torch.ones(1,requires_grad=True)},1<<20,1<<20),
            ('nonfinite_tensor',{'x':torch.tensor([float('nan')])},1<<20,1<<20),
            ('unsupported_state',{'x':object()},1<<20,1<<20),
            ('sparse_tensor',{'x':torch.ones(2,2).to_sparse()},1<<20,1<<20)]
        cycle=[];cycle.append(cycle);bad_images.append(('cyclic_state',cycle,1<<20,1<<20))
        for fault,value,cap,CPU_cap in bad_images:
            try:CPUOwnedStateImage(value,logical_copy_cap_bytes=cap,CPU_storage_cap_bytes=CPU_cap)
            except (ValueError,TypeError):refusals.append(fault)
            else:raise AssertionError('Bad state or capacity accepted')
        corrupt=CPUOwnedStateImage(state(),logical_copy_cap_bytes=1<<20,CPU_storage_cap_bytes=1<<20)
        corrupt.saved['pair_last'].add_(1)
        try:corrupt.materialize()
        except ValueError:refusals.append('corrupt_saved_image')
        else:raise AssertionError('Corrupt saved image accepted')
        checks.append('no_CPU_Python_numpy_RNG_consumption')
        assert_RNG(rng,RNG())
        assert len(checks)==4 and len(refusals)==11 and not torch.cuda.is_initialized()
    result={'status':'E1_CPU_STORAGE_PRIMITIVE_PASS_NOT_SAMPLER_OR_GPU_REPAIR',
        'source_revision':reg['source_revision'],'payload_sha256':reg['payload_sha256'],
        'checks':checks,'refusals':refusals,'inventory':storage_inventory(image.saved),
        'restored_original_inventory':image.inventory,'CPU_wall_seconds':time.perf_counter()-started,
        'Torch_version':torch.__version__,'CUDA_initialized':torch.cuda.is_initialized(),'GPU_submissions':0,
        'real_current_birth_owner_integration':False,'full_sampler_CPU_acceptance':False,
        'real_GPU_headroom_or_repair_claim':False,'old_sources_modified':False}
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'checks':len(checks),'refusals':len(refusals),'CPU_wall_seconds':result['CPU_wall_seconds']}))


if __name__=='__main__':main()
