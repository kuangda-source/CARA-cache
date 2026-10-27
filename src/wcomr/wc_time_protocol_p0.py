"""Incremental P0 timing/parameter adapters; no dispatch and no upstream edits."""
import ast
import copy
import contextlib
import hashlib
import inspect
import time
import types
from pathlib import Path

RF_SHA = 'c6c68f297859e11c76d2921667a29cabfecef3a7b5d3ab831bf9bb54b25b7d87'
WC_SHA = 'b485cb8fd6e262a40e5823365c34ef7db1bc036c591d7577489e04077c515903'
RF_REL = 'cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py'
WC_REL = 'cosmos_predict2/_src/predict2/inference/worldcache_utils.py'

def require(ok, message):
    if not ok: raise ValueError(message)

def tree_at(runtime, relative, expected):
    p = Path(runtime)/relative
    require(hashlib.sha256(p.read_bytes()).hexdigest() == expected, 'Pinned source differs: '+relative)
    return ast.parse(p.read_bytes())

class BoundaryClock:
    def __init__(self, synchronize, clock=time.perf_counter):
        self.sync, self.clock = synchronize, clock
        self.start = self.loop_end = self.end = None
        self.sync_calls = 0
    def begin(self):
        require(self.start is None, 'Duplicate denoise loop')
        self.sync(); self.sync_calls += 1; self.start = self.clock()
    def denoise_end(self):
        require(self.start is not None and self.loop_end is None, 'Unexpected loop end')
        self.loop_end = self.clock()  # Host timestamp, intentionally no CUDA sync.
    def finish(self):
        require(self.loop_end is not None and self.end is None, 'Decode before loop or duplicate decode')
        self.sync(); self.sync_calls += 1; self.end = self.clock()
    def receipt(self):
        complete = self.end is not None
        if complete: require(self.start <= self.loop_end <= self.end, 'Nonmonotonic clock')
        return dict(T_DD=self.end-self.start if complete else None,
                    denoise_start=self.start, denoise_end_host_unsynchronized=self.loop_end,
                    decode_end=self.end, boundary_sync_calls=self.sync_calls,
                    status='MEASURED_CONTINUOUS_DENOISE_TO_DECODE' if complete else 'UNAVAILABLE_NO_COMPLETE_DECODE')

@contextlib.contextmanager
def installed_timing(model, runtime, synchronize, clock=time.perf_counter):
    """Scope to one request. Same sampler body, only loop boundary calls inserted."""
    original = model.generate_samples_from_batch
    target = inspect.unwrap(getattr(original, '__func__', original))
    module = tree_at(runtime, RF_REL, RF_SHA)
    fn = copy.deepcopy(next(n for n in ast.walk(module) if isinstance(n, ast.FunctionDef) and n.name == 'generate_samples_from_batch'))
    loops = [(i,n) for i,n in enumerate(fn.body) if isinstance(n,ast.For) and ast.unparse(n.iter)=='enumerate(timesteps_iter)']
    require(len(loops)==1, 'Exact solver loop not found')
    at, loop = loops[0]
    witness = BoundaryClock(synchronize, clock)
    fn.body[at:at+1] = [ast.parse('_p0_clock.begin()').body[0], loop, ast.parse('_p0_clock.denoise_end()').body[0]]
    tree=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),fn],type_ignores=[])
    env={**target.__globals__, '_p0_clock':witness}
    exec(compile(ast.fix_missing_locations(tree),str(Path(runtime)/RF_REL)+'#P0-two-boundaries','exec'),env)
    old_decode=model.decode
    own={k:(k in vars(model),vars(model).get(k)) for k in ('generate_samples_from_batch','decode')}
    def decode(*a,**kw):
        value=old_decode(*a,**kw);witness.finish();return value
    model.generate_samples_from_batch=types.MethodType(env[fn.name],model)
    model.decode=decode
    try: yield witness
    finally:
        for k,(exists,value) in own.items():
            if exists:setattr(model,k,value)
            else:delattr(model,k)

def compile_wc_adapter(runtime, wc, *, force_full=False, paper_port=False):
    """Explicit local variants: keep 70-call horizon; paper beta=4 * cnt/70.

    PaperPort retains per-CFG step parity and is NOT Euler35/paper exact.
    AllD changes only the skip predicate; probe/history/head execute normally.
    """
    tree=tree_at(runtime,WC_REL,WC_SHA)
    fn=copy.deepcopy(next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='worldcache_mini_train_dit_forward'))
    found={'skip':0,'ATS':0}
    for n in ast.walk(fn):
        if isinstance(n,ast.If) and ast.unparse(n.test)=='self.accumulated_rel_l1_distance[current_idx] < dynamic_thresh':
            found['skip']+=1
            if force_full:n.test=ast.Constant(False)
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='base_mult' for t in n.targets):
            found['ATS']+=1
            if paper_port:n.value=ast.Constant(4.0)
    require(found=={'skip':1,'ATS':1}, 'Pinned WC control sites changed')
    env=dict(vars(wc))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(Path(runtime)/WC_REL)+'#P0-explicit-variant','exec'),env)
    proxy=types.SimpleNamespace(**vars(wc))
    def apply(model,*a,**kw):
        result=wc.apply_worldcache(model,*a,**kw)
        model.forward=types.MethodType(env[fn.name],model)
        return result
    proxy.apply_worldcache=apply
    proof=dict(source_sha256=WC_SHA,force_full=force_full,paper_port=paper_port,
               changed_sites=['skip_predicate_false']*force_full+['ATS_base_mult_4']*paper_port,
               compiled_AST_sha256=hashlib.sha256(ast.dump(fn).encode()).hexdigest(),
               paper_exact=False)
    return proxy, proof
