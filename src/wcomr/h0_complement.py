"""Same-state H0 shadow C/S/D costs and errors. No deployed sparse output or labels."""
import ast
import copy
import inspect
import hashlib
from pathlib import Path
import statistics
import textwrap
import time
import torch
from .prepared_input import RNGState
from .mid_coverage import WC_FIELDS, tree_digest
from .shadow_metrics import tensor_error


def cached_branch_source(source):
    start='    # --- Execution Branching ---\n    if skip_forward:\n'
    end='    else:\n        # CACHE MISS or PROBE PHASE'
    if source.count(start)!=1 or source.count(end)!=1:raise ValueError('Pinned C branch changed')
    cached=textwrap.dedent(source.split(start,1)[1].split(end,1)[0])
    function='def cached_prediction(self, ori_x, test_x, current_idx):\n    x_B_T_H_W_D=ori_x\n    T=ori_x.shape[1]\n    residual_x=self.residual_cache[current_idx]\n'
    function+=textwrap.indent(cached,'    ')+'\n    return x_B_T_H_W_D\n'
    ast.parse(function)
    return function


def build_h0_forward(original, probe):
    source=inspect.getsource(original);ns=dict(original.__globals__)
    exec(compile(cached_branch_source(source),'<h0-exact-official-C>','exec'),ns)
    probe.cached_prediction=ns['cached_prediction']
    edits=[
        ('    current_idx = self.cnt % 2','    _h0_start(self)\n    current_idx = self.cnt % 2'),
        ('    # --- Execution Branching ---','    _h0_before(self, skipped=skip_forward, branch=current_idx, original_input=ori_x, probe=test_x, block_kwargs=block_kwargs, embedding=t_embedding_B_T_D, adaln=adaln_lora_B_T_3D)\n\n    # --- Execution Branching ---'),
        ('        # Update Cache','        _h0_collect(self, x_B_T_H_W_D)\n\n        # Update Cache'),
        ('    # Increment Step Counter','    if not skip_forward:\n        _h0_observe(self, current_idx)\n\n    # Increment Step Counter')]
    for anchor,new in edits:
        if source.count(anchor)!=1:raise ValueError('Pinned H0 injection anchor changed: '+anchor)
        source=source.replace(anchor,new)
    ns.update(_h0_start=probe.start,_h0_before=probe.before,_h0_collect=probe.collect,_h0_observe=probe.observe)
    exec(compile(source,'<h0-shadow-forward>','exec'),ns)
    return ns[original.__name__]


class H0ComplementProbe:
    def __init__(self, config, kernel=None, raw_output=None):
        self.config=config;self.kernel=kernel;self.raw_output=Path(raw_output) if raw_output is not None else None;self.call=0;self.records=[];self.attempts=[]
        self.histories=[[],[]];self.selected=set();self.pending=None;self.mode='dense';self.restores=[]
        self.cached_prediction=None

    def start(self,net):
        self.call+=1
        if net.cnt==0:self.histories=[[],[]];self.selected=set();self.pending=None
        if self.pending is not None:raise ValueError('Unconsumed H0 pending comparison')

    def observe(self,net,branch):
        self.histories[branch].append(net.cnt)
        self.histories[branch]=self.histories[branch][-2:]

    @staticmethod
    def sync(tensor):
        if tensor.device.type=='cuda':torch.cuda.synchronize(tensor.device)

    @staticmethod
    def buffers(net):return [(x,x.detach().clone()) for x in net.buffers()]

    @staticmethod
    def restore_buffers(buffers):
        for x,saved in buffers:x.copy_(saved)

    def state(self,net):return tree_digest({k:getattr(net,k) for k in WC_FIELDS if hasattr(net,k)})

    def save_raw(self,attempt,arm,residual,velocity):
        if self.raw_output is None:return None
        directory=self.raw_output/('call%02d-cfg%d'%(attempt['call'],attempt['cfg_slot']))
        directory.mkdir(parents=True,exist_ok=True);path=directory/(arm+'.pt')
        if path.exists():raise ValueError('Raw diagnostic overwrite refused')
        tensors={'postwarp_residual':residual.detach().contiguous().cpu(),'velocity':velocity.detach().contiguous().cpu()}
        if not all(bool(torch.isfinite(x).all()) for x in tensors.values()):raise ValueError('Raw diagnostic nonfinite')
        torch.save(tensors,path)
        h=hashlib.sha256()
        with path.open('rb') as f:
            for part in iter(lambda:f.read(1<<20),b''):h.update(part)
        return {'path':str(path),'bytes':path.stat().st_size,'sha256':h.hexdigest(),'tensors':{k:{'dtype':str(v.dtype),'shape':list(v.shape),'raw_sha256':hashlib.sha256(memoryview(v.reshape(-1).view(torch.uint8).numpy())).hexdigest()} for k,v in tensors.items()},'role':'H0_RAW_SCORE_EVIDENCE_NOT_EXPERT_LABELS_OR_TRAINING_INPUT'}

    @torch.no_grad()
    def before(self,net,*,skipped,branch,original_input,probe,block_kwargs,embedding,adaln):
        lo,hi=self.config['eligible_call_range']
        if skipped or not lo<=self.call<=hi or branch in self.selected:return
        if not net.resume_flag[branch] or len(self.histories[branch])<2:return
        self.selected.add(branch)
        attempt={'call':self.call,'cfg_slot':branch,'cache_counter_before':net.cnt,'historical_true_full_counters':list(self.histories[branch]),'historical_dense_cache_and_last_two_windows_sha256':tree_digest([net.residual_cache[branch],net.residual_window[branch][-2:],net.probe_residual_window[branch][-2:]]),'current_input_sha256':tree_digest(original_input),'current_probe_sha256':tree_digest(probe),'status':'STARTED_ALL_ARMS_REMAIN_IN_DENOMINATOR'}
        self.attempts.append(attempt)
        if not all(x<net.cnt and x%2==branch for x in self.histories[branch]):raise ValueError('History not strictly past same CFG')
        if net.training or any(m.training for m in net.modules()):raise ValueError('H0 requires eval')
        p={'attempt':attempt,'original_input':original_input.detach().clone(),'probe':probe.detach().clone(),'kwargs':block_kwargs,'embedding':embedding,'adaln':adaln,'rng_before':RNGState(),'buffers_before':self.buffers(net)}
        signature=self.state(net);rng_after=RNGState();buffers_after=self.buffers(net)
        wall=[];c_hidden=c_velocity=None
        try:
            net._w1_shadow_active=True
            for i in range(self.config['warmups']+self.config['repeats']):
                p['rng_before'].restore();self.restore_buffers(p['buffers_before'])
                self.sync(original_input);start=time.perf_counter()
                proxy=copy.copy(net);proxy.previous_internal_states=list(net.previous_internal_states);proxy.previous_input=list(net.previous_input)
                c_hidden=self.cached_prediction(proxy,p['original_input'],p['probe'],branch)
                c_velocity=net.unpatchify(net.final_layer(c_hidden,embedding,adaln_lora_B_T_3D=adaln))
                self.sync(original_input)
                if i>=self.config['warmups']:wall.append((time.perf_counter()-start)*1000)
            if not bool(torch.isfinite(c_hidden).all() and torch.isfinite(c_velocity).all()):raise ValueError('Nonfinite C')
            p.update(c_hidden=c_hidden.detach().clone(),c_velocity=c_velocity.detach().clone(),c_wall_ms=wall)
            p['c_raw']=self.save_raw(attempt,'C',p['c_hidden']-p['original_input'],p['c_velocity'])
        except BaseException:
            attempt['status']='FAILED_C_BEFORE_CURRENT_DENSE';raise
        finally:
            rng_after.restore();self.restore_buffers(buffers_after);net._w1_shadow_active=False
        if self.state(net)!=signature:raise ValueError('C modified deployed cache state')
        self.pending=p

    def install_operators(self,net):
        if self.restores:raise ValueError('Operators already installed')
        for layer in range(net.probe_depth,len(net.blocks)):
            op=net.blocks[layer].self_attn.attn_op;original=op.forward;owned='forward' in vars(op);prior=vars(op).get('forward')
            def restore(op=op,owned=owned,prior=prior):
                if owned:setattr(op,'forward',prior)
                else:delattr(op,'forward')
            self.restores.append(restore)
            def operation(*args,_layer=layer,_original=original,**kwargs):
                if self.mode=='dense' or _layer in self.config['dense_fallback_layers']:return _original(*args,**kwargs)
                if len(args)!=3 or kwargs:raise ValueError('Frozen self-attention call contract differs')
                q,k,v=args
                if q.ndim!=4 or q.shape!=k.shape or q.shape!=v.shape:raise ValueError('Self-attention NHD layout differs')
                b,n,h,d=q.shape
                mask=torch.ones(b,h,n//128,n//64,device=q.device,dtype=torch.bool)
                if self.kernel is None:
                    from .sparge_routed_no_pv import routed_no_pv
                    kernel=routed_no_pv
                else:kernel=self.kernel
                value,metadata=kernel(q,k,v,mask,self.config['policy']['sim'],self.config['policy']['cdf'],self.mode=='matched_full')
                if value.shape!=(b,n,h*d):raise ValueError('Candidate flattened attention layout differs')
                return value  # MinimalA2AAttnOp returns flattened [B,N,H*D].
            setattr(op,'forward',operation)

    def close(self):
        for restore in reversed(self.restores):restore()
        self.restores=[];self.mode='dense'

    @torch.no_grad()
    def collect(self,net,actual_dense_hidden):
        if self.pending is None:return
        p=self.pending;self.pending=None;attempt=p['attempt'];signature=self.state(net)
        rng_after=RNGState();buffers_after=self.buffers(net);rows=[]
        attempt['completed_arms']=rows
        try:
            net._w1_shadow_active=True
            actual_velocity=net.unpatchify(net.final_layer(actual_dense_hidden,p['embedding'],adaln_lora_B_T_3D=p['adaln']))
            truth_residual=actual_dense_hidden-p['original_input']
            rows.append({'arm':'C_OFFICIAL_PAST_DENSE_GAMMA_WARP','wall_ms':p['c_wall_ms'],'median_wall_ms':statistics.median(p['c_wall_ms']),'postwarp_residual':tensor_error(p['c_hidden']-p['original_input'],truth_residual),'velocity':tensor_error(p['c_velocity'],actual_velocity),'source':'HISTORICAL_DEPLOYED_TRUE_FULL_ONLY','raw_snapshot':p['c_raw']})
            if any(rows[0][key]['status']!='OK' or rows[0][key]['relative_rmse'] is None for key in ['postwarp_residual','velocity']):raise ValueError('Nonfinite/zero-energy C reference')
            for arm in ['dense','matched_full','sparse']:
                self.mode=arm;wall=[];all_equal=True
                for i in range(self.config['warmups']+self.config['repeats']):
                    p['rng_before'].restore();self.restore_buffers(p['buffers_before'])
                    self.sync(actual_dense_hidden);start=time.perf_counter();self.mode=arm;hidden=p['probe'].clone()
                    for block in net.blocks[net.probe_depth:]:hidden=block(hidden,**p['kwargs'])
                    velocity=net.unpatchify(net.final_layer(hidden,p['embedding'],adaln_lora_B_T_3D=p['adaln']))
                    self.sync(actual_dense_hidden)
                    if i>=self.config['warmups']:wall.append((time.perf_counter()-start)*1000)
                    if arm=='dense':all_equal=all_equal and torch.equal(hidden,actual_dense_hidden) and torch.equal(velocity,actual_velocity)
                residual_error=tensor_error(hidden-p['original_input'],truth_residual);velocity_error=tensor_error(velocity,actual_velocity)
                row={'arm':arm,'wall_ms':wall,'median_wall_ms':statistics.median(wall),'postwarp_residual':residual_error,'velocity':velocity_error,'source':'CURRENT_RECOMPUTE_NO_CACHE_WRITE','dense_repeat_bitwise_matches_deployed':all_equal if arm=='dense' else None}
                rows.append(row)
                if residual_error['status']!='OK' or velocity_error['status']!='OK' or residual_error['relative_rmse'] is None or velocity_error['relative_rmse'] is None:raise ValueError('Nonfinite/undefined H0 metric')
                if arm=='dense' and not all_equal:raise ValueError('True dense replay not bitwise same deployed full')
                row['raw_snapshot']=self.save_raw(attempt,arm,hidden-p['original_input'],velocity)
            attempt['status']='FOUR_ARMS_COMPLETE'
            self.records.append(dict(attempt,arms=rows,dense_fallback_layers=self.config['dense_fallback_layers'],scope='ONE_OFFICIAL_STATE_NO_VIDEO_NO_DEPLOYMENT_NO_SPARSE_HISTORY_OR_LIFETIME',c_computed_before_current_dense=True))
        except BaseException:
            attempt['status']='FAILED_RETAINED_IN_DENOMINATOR';raise
        finally:
            self.mode='dense';rng_after.restore();self.restore_buffers(buffers_after);net._w1_shadow_active=False
        if self.state(net)!=signature:raise ValueError('Shadow changed deployed WC state')
