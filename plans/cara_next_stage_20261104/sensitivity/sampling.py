"""Native recording and single-C suffixes using CAL35's unchanged paired path."""
import ast
import copy
import inspect
import io
import json
from pathlib import Path
import pickle
import types

import torch

from wcomr import clean_speed20_r1 as clean
from wcomr.cara_fast_spec_r1 import profile_from
from wcomr.cfg_paired_probe_velocity import compile_velocity
from wcomr.cpu_owned_state_snapshot import CPUOwnedStateImage
from wcomr.mid_coverage import WC_FIELDS
from wcomr.mid_coverage import tree_digest
from wcomr.partial_mlp_deployment_state import plain
from wcomr.paper_latency_r1 import SAMPLER_PATH, SAMPLER_SHA, _verified_function
from wcomr.policy_generator_r1.interval_grammar import Edge, compile_policy
from wcomr.policy_generator_r1.production_sampling import PolicyOwner, complete_request_seconds
from wcomr.prepared_input import RNGState
from wcomr.rv0_fork import object_state, restore_object_state


def policy_for(profile, target=None):
    dense = [t for t in range(1, 37) if t != target]+[37]
    return compile_policy(profile, [Edge(a, b) for a, b in zip(dense, dense[1:])])


def save_state(path,image,step):
    # Serialize byte stores once; typed aliases are descriptors. torch.save
    # itself cannot encode uint8 and float views of one shared storage.
    keys={prototype.untyped_storage()._cdata:key for key,prototype in image._CPU_views.values()}
    stream=io.BytesIO()
    class StatePickler(pickle.Pickler):
        def persistent_id(self,value):
            if isinstance(value,torch.Tensor):
                return (id(value),keys[value.untyped_storage()._cdata],value.dtype,
                    value.storage_offset(),tuple(value.shape),tuple(value.stride()))
    StatePickler(stream).dump(image.saved)
    torch.save(dict(stores=image._storage_images,devices=image._original_devices,
        state_bytes=stream.getvalue(),digest=image.digest,rng=RNGState(),step=step),path)


def load_state(saved):
    stores={key:value.to(device=saved['devices'][key],copy=True) for key,value in saved['stores'].items()}
    tensors={}
    class StateUnpickler(pickle.Unpickler):
        def persistent_load(self,descriptor):
            identity,key,dtype,offset,shape,stride=descriptor
            if identity not in tensors:
                tensors[identity]=torch.empty(0,dtype=dtype,device=stores[key].device).set_(
                    stores[key].untyped_storage(),offset,shape,stride)
            return tensors[identity]
    state=StateUnpickler(io.BytesIO(saved['state_bytes'])).load()
    if tree_digest(plain(state))!=saved['digest']:
        raise ValueError('Serialized complete state differs')
    return state


def resume_sampler(model, runtime, start):
    """One insertion before the original loop; all loop equations stay intact."""
    function, original = _verified_function(model.generate_samples_from_batch,
        Path(runtime)/SAMPLER_PATH, SAMPLER_SHA, 'generate_samples_from_batch')
    node = copy.deepcopy(original)
    sites = [i for i, n in enumerate(node.body) if isinstance(n, ast.For)
             and ast.unparse(n.iter) == 'enumerate(timesteps_iter)']
    if len(sites) != 1:
        raise ValueError('Expected the pinned single solver loop')
    i = sites[0]
    node.body.insert(i, ast.parse('noise, latents, timesteps_iter = _sensitivity_start(self, noise, latents, seed_g)').body[0])
    inverse = copy.deepcopy(node);inverse.body.pop(i)
    if ast.dump(inverse) != ast.dump(original):
        raise ValueError('Sampler changed outside the resume insertion')
    module = ast.Module(body=[ast.ImportFrom(module='__future__',
        names=[ast.alias(name='annotations')], level=0), node], type_ignores=[])
    scope = dict(function.__globals__, _sensitivity_start=start)
    exec(compile(ast.fix_missing_locations(module), '<sensitivity-sampler>', 'exec'), scope)
    return types.MethodType(scope[node.name], model)


class RecordingOwner(PolicyOwner):
    def __init__(self, *args, record_root=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.record_root = Path(record_root) if record_root is not None else None
        self.generator = None
        self.intervention = None
        self.target = None
        self.previous = {}
        self.metrics = []
        self.block_previous = {}
        self.block_rows = {}
        self.hook = self.net.blocks[0].register_forward_hook(self.first_block) if self.record_root else None

    def first_block(self, module, args, value):
        branch = int(self.net.cnt) % 2
        value = value[0] if isinstance(value, tuple) else value
        current = value.detach().float()
        previous = self.block_previous.get(branch)
        self.block_rows[branch] = (None if previous is None else
            float((current-previous).abs().mean()/previous.abs().mean()))
        self.block_previous[branch] = current.clone()

    def state(self, noise, latent, conditions):
        return dict(latent=latent, noise=noise, solver=object_state(self.model.sample_scheduler),
            net={k:getattr(self.net,k) for k in WC_FIELDS if hasattr(self.net,k)},
            buffers=dict(self.net.named_buffers()),
            readout={k:getattr(self.readout,k) for k in ('completed','history','current','poisoned')},
            calibrators=[vars(c) for c in self.readout.calibrators],
            executor={k:getattr(self.executor,k) for k in ('poisoned','running','last')},
            owner={k:getattr(self,k) for k in ('history','fallback_reason','force_dense')},
            conditions=[object_state(c) for c in conditions], generator=self.generator.get_state())

    @torch.no_grad()
    def pair(self, noise, latent, timestep, conditions, choose):
        step = self.readout.completed+1
        if self.record_root:
            self.record_root.mkdir(parents=True,exist_ok=True)
            torch.save(latent.detach().cpu(), self.record_root/f'latent_before_{step:02d}.pt')
            if step in range(8,35,2):
                image = CPUOwnedStateImage(self.state(noise,latent,conditions),
                    logical_copy_cap_bytes=24*2**30, CPU_storage_cap_bytes=16*2**30)
                save_state(self.record_root/f'state_before_{step:02d}.pt',image,step)
        values = super().pair(noise,latent,timestep,conditions,choose)
        if self.history[-1]['fallback_reason'] is not None:
            raise ValueError('Registered sensitivity action entered fallback')
        if self.record_root:
            guided = values[0]+7*(values[0]-values[1])
            if step in range(8,35,2):
                torch.save(guided.detach().cpu(),self.record_root/f'guided_{step:02d}.pt')
            row = dict(step=step,first_block_rel_l1_c=self.block_rows[0],first_block_rel_l1_u=self.block_rows[1])
            for label,value in zip(('v_c','v_u','guided'),(*values,guided)):
                current = value.detach().float()
                previous = self.previous.get(label)
                row[label+'_delta_RMS'] = None if previous is None else float((current-previous).square().mean().sqrt())
                self.previous[label] = current.clone()
            self.metrics.append(row)
        if step == self.target:
            self.intervention = (values[0]+7*(values[0]-values[1])).detach().cpu()
        return values

    def close(self):
        if self.hook is not None:
            self.hook.remove();self.hook=None
        self.previous.clear();self.block_previous.clear()
        super().close()


def restore(owner, saved, conditions, generator):
    data = load_state(saved)
    for name in set(WC_FIELDS)-set(data['net']):
        vars(owner.net).pop(name,None)
    for name,value in data['net'].items():
        setattr(owner.net,name,value)
    for name,value in owner.net.named_buffers():
        value.copy_(data['buffers'][name])
    restore_object_state(owner.model.sample_scheduler,data['solver'])
    for name,value in data['readout'].items():
        setattr(owner.readout,name,value)
    for calibrator,state in zip(owner.readout.calibrators,data['calibrators']):
        vars(calibrator).clear();vars(calibrator).update(state)
    for name,value in data['executor'].items():
        setattr(owner.executor,name,value)
    for name,value in data['owner'].items():
        setattr(owner,name,value)
    for condition,state in zip(conditions,data['conditions']):
        restore_object_state(condition,state)
    generator.set_state(data['generator'])
    saved['rng'].restore()
    return data['noise'],data['latent']


def execute(inference, sample, *, card, common, output, record_root=None, checkpoint=None, target=None):
    profile = profile_from(card['profile'])
    policy = policy_for(profile,target)
    holder = {}
    def install(model,method,context,runtime,wc,rf,settings,calibration,specs,audit=False):
        wc.apply_worldcache(model.net,**{k.removeprefix('worldcache_'):v for k,v in settings.items()})
        owner = RecordingOwner(model,policy=policy,profile=profile,context=context,
            runtime=runtime,wc=wc,rf=rf,record_root=record_root)
        holder['owner'] = owner
        owner.target = target
        velocity,_ = compile_velocity(runtime,rf,owner,owner.choose)
        def factory(bound,*args,**kwargs):
            actual = velocity(bound,*args,**kwargs)
            cells = inspect.getclosurevars(actual).nonlocals
            holder['conditions'] = (cells['condition'],cells['uncondition'])
            return actual
        return factory,owner,None,owner.readout
    model = inference.pipe.model
    saved = torch.load(checkpoint,weights_only=False,map_location='cpu') if checkpoint else None
    remaining = 36 if saved is None else 37-saved['step']
    def start(bound,noise,latent,generator):
        owner = holder['owner'];owner.generator=generator
        if saved is not None:
            noise,latent = restore(owner,saved,holder['conditions'],generator)
        return noise,latent,model.sample_scheduler.timesteps[36-remaining:]
    # clean.execute counts physical updates, whereas owner history contains the restored prefix.
    tree = ast.parse(inspect.getsource(clean.execute))
    class Bounds(ast.NodeTransformer):
        def visit_Constant(self,node):
            return ast.copy_location(ast.Constant(remaining),node) if type(node.value) is int and node.value==36 else node
    tree = ast.fix_missing_locations(Bounds().visit(tree))
    scope = dict(vars(clean),install=install)
    exec(compile(tree,'<sensitivity-guarded-request>','exec'),scope)
    sampler = resume_sampler(model,common['runtime'],start)
    with clean.patched(model,'generate_samples_from_batch',sampler):
        result = scope['execute'](inference,sample,'KEEP_A_P',output=output,
            settings=card['settings'],calibration=None,specs={},audit=False,**common)
    owner = holder['owner']
    result.update(semantic_history=copy.deepcopy(owner.history),full_request_seconds=complete_request_seconds(result),
        eligible_clean_time=False,resumed_from_update=None if saved is None else saved['step'])
    if result['status']!='COMPLETE' or result['solver_steps']!=remaining or len(owner.history)!=36:
        raise ValueError('Incomplete recorded/resumed request')
    if [h['actual'] for h in owner.history]!=policy['actions']:
        raise ValueError('Actual action sequence differs from the frozen single-C sequence')
    if checkpoint and target is not None:
        reference = torch.load(Path(checkpoint).parent/f'guided_{target:02d}.pt',map_location='cpu',weights_only=True)
        result['local_guided_delta_RMS'] = float((owner.intervention-reference).float().square().mean().sqrt())
    if record_root:
        Path(record_root,'metrics.json').write_text(json.dumps(owner.metrics,indent=2)+'\n')
        torch.save(result['final_latent'],Path(record_root,'latent_after_36.pt'))
    return result
