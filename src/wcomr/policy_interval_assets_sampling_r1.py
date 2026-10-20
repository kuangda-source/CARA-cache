"""Stream all legal source/time readouts beside an unchanged all-D trajectory."""
import copy
import json
import time
import weakref
from pathlib import Path

import torch

from . import clean_speed20_r1 as clean
from .simple26d_memory_r2 import collect_boundary
from .source_phase_fixed_mask_r1 import FixedMaskH1Owner
from .policy_interval_assets_r1 import cells, rounds_for, sha
from .policy_interval_readout_r1 import ReadoutKernel, guided, reduce_outputs
from .post_probe_action_clock_r1 import observe_post_probe_action
from .light_sampling import synchronize
from .mid_coverage import tree_digest
from .partial_mlp_deployment_state import plain


class IntervalAssetsOwner(FixedMaskH1Owner):
    def __init__(self, *args, collector_enabled, collector_output, **kwargs):
        super().__init__(*args, replay_plan=('D',)*36, **kwargs)
        self.collector_enabled=collector_enabled; self.directory=Path(collector_output)
        self.by_target={t:[s for s,tt in cells() if tt==t] for t in range(1,37)}
        self.bank={}; self.points=[]; self.action_clocks=[]; self._current_features={}
        self._kernel=None
        self._old_hidden=self.deployment.readout.semantic_hidden
        self.deployment.readout.semantic_hidden=self._capture_hidden

    @torch.no_grad()
    def _capture_hidden(self, net, skipped, branch, original, probe, hidden, kwargs, embedding, adaln):
        if skipped:
            raise ValueError('The actual parent is all-D; shadow readouts cannot select it')
        # References only here. CPU transfer/hash/readout work is after the D
        # action clock and never inserted into a measured deep continuation.
        self._current_features[branch]=dict(original=original,probe=probe,
            embedding=embedding,adaln=adaln,residual=net.residual_cache[branch],
            anchor_probe=net.probe_residual_cache[branch])
        return self._old_hidden(net,skipped,branch,original,probe,hidden,kwargs,embedding,adaln)

    def _source(self,s,device):
        result=[]
        for b in (0,1):
            latest=self.bank[s][b];older=self.bank[s-1][b]
            probe=latest['probe'].to(device);residual=latest['residual'].to(device)
            result.append(dict(probe=probe,residual=residual,
                residual_window=[older['residual'].to(device),residual],
                probe_window=[older['probe'].to(device),probe]))
        return result

    @torch.no_grad()
    def pair(self,noise,latent,timestep,conditions,choose):
        step=len(self.history)+1;self._current_features={}
        synchronize();begin=time.perf_counter()
        with observe_post_probe_action(self,synchronize=synchronize) as timer:
            actual=super().pair(noise,latent,timestep,conditions,choose)
            if timer.start is not None:action=timer.finish()
            else:action=None
        synchronize();ended=time.perf_counter()
        if self.history[-1]['action']!='DD' or set(self._current_features)!={0,1}:
            raise ValueError('Actual all-D parent and both branch observations required')
        self.action_clocks.append(dict(step=step,protected=action is None,
            shared_prefix_seconds=0. if action is None else timer.start-begin,
            D_action_seconds=ended-begin if action is None else action['synchronized_wall_seconds'],
            whole_pair_seconds=ended-begin,boundary='SHARED_PREFIX_PLUS_NONOVERLAPPING_POST_PROBE_D',
            diagnostics_included=False))
        if not self.collector_enabled:
            self._current_features.clear();return actual
        if self._kernel is None:
            self._kernel=ReadoutKernel(self.model,self._runtime,self._wc,self._rf,self.deployment.warp)
        pair_inputs=(noise,latent,timestep,conditions)
        self.directory.mkdir(parents=True,exist_ok=True)
        teacher=guided(actual).detach().cpu().clone()
        teacher_path=self.directory/('teacher-'+str(step)+'.pt')
        with teacher_path.open('xb') as f:torch.save({'D':teacher},f)
        teacher_ref=dict(path=str(teacher_path),sha256=sha(teacher_path),bytes=teacher_path.stat().st_size)
        input_sha=tree_digest((noise,latent,timestep))
        protected_before=tree_digest(plain((self.deployment.working,[vars(c) for c in self.deployment.dense])))
        for source_step in self.by_target[step]:
            source=self._source(source_step,latent.device)
            source_sha=tree_digest(self.bank[source_step]);older_sha=tree_digest(self.bank[source_step-1])
            trials=[];reference={};C=Phi=half=None
            for round_name,order in rounds_for(source_step,step):
                for label in order:
                    synchronize();start=time.perf_counter()
                    returned,c,p=self._kernel.run(label,source=source,current=self._current_features,pair_inputs=pair_inputs)
                    synchronize();seconds=time.perf_counter()-start
                    # Independent repetitions include all real heads/warp and
                    # RF/fusion again. Copies, equality and writing are charged
                    # to the whole card outside the component clock.
                    if label not in reference:reference[label]=tuple(v.detach().clone() for v in returned)
                    elif any(not torch.equal(a,b) for a,b in zip(reference[label],returned)):
                        raise ValueError('Repeated same-state action produced different output')
                    if label=='C':C=c
                    if label=='A_HALF':half=returned;Phi=p
                    trials.append(dict(round=round_name,action=label,seconds=seconds,
                        boundary='AFTER_ALREADY_PAID_PROBES_THROUGH_WC_HEAD_RF_AND_SHARED_FUSION',
                        shared_prefix_included=False,restore_copy_hash_write_included=False))
            stats,raw=reduce_outputs(C,Phi,actual,half)
            if any(not torch.equal(a,b) for a,b in zip(reference['A_ONE'],Phi)):
                raise ValueError('alpha1 output differs from the actual Phi endpoint')
            path=self.directory/('source-'+str(source_step)+'-target-'+str(step)+'.pt')
            with path.open('xb') as f:torch.save(raw,f)
            row=dict(source=source_step,target=step,source_anchor_steps=[source_step-1,source_step],
                source_sha256=source_sha,older_source_sha256=older_sha,input_sha256=input_sha,
                label_basis='TEACHER_CONDITIONED_PROPOSAL',free_policy_history_truth=False,
                actual_parent_action='DD',actual_same_state_teacher_ref=teacher_ref,
                statistics=stats,price_trials=trials,
                artifact=dict(path=str(path),sha256=sha(path),bytes=path.stat().st_size),
                source_shadow_writes_parent=False,extra_deep_teacher_pairs=0)
            with (self.directory/'cells.jsonl').open('a') as f:f.write(json.dumps(row,allow_nan=False)+'\n')
            self.points.append(row)
            from .gpu_budget_pool_v2 import atomic_json
            atomic_json(self.directory/'technical-progress.json',dict(stage='READOUT_COLLECTION',
                completed_source_time_cells=len(self.points),registered_source_time_cells=406,
                current_target=step,current_source=source_step,errors=0))
            del source,reference,C,Phi,half,returned,c,p,raw
        if (tree_digest((noise,latent,timestep))!=input_sha
            or tree_digest(plain((self.deployment.working,[vars(c) for c in self.deployment.dense])))!=protected_before):
            raise ValueError('Readout collection changed the actual trajectory or D history')
        # Store exactly the actual teacher anchors, never a C/A reconstruction.
        self.bank[step]=[dict(probe=self._current_features[b]['anchor_probe'].detach().cpu().clone(),
            residual=self._current_features[b]['residual'].detach().cpu().clone()) for b in (0,1)]
        self._current_features.clear()
        return actual

    def close(self):
        self.deployment.readout.semantic_hidden=self._old_hidden
        self.bank.clear();self._current_features.clear();self._kernel=None
        return super().close()


def execute(inference,sample,mode,*,table_parameters,previous_parameters,**kw):
    if inference.text_guardrail_runner is None or inference.video_guardrail_runner is None:
        raise ValueError('Ordinary guardrails required')
    if mode not in ('NATIVE','CONTROL','COLLECT'):
        raise ValueError('Complete registered reference/control/collection mode required')
    before=collect_boundary();holder={};refs=[]
    def factory(*args,**kwargs):
        owner=IntervalAssetsOwner(*args,collector_enabled=mode=='COLLECT',
            collector_output=Path(kw['output'])/'interval-raw',
            table_parameters=table_parameters['SOURCE_PHASE'],math_parameters=previous_parameters,
            horizon=1,source_mode='FUSION',**kwargs)
        owner._runtime,owner._wc,owner._rf=kw['runtime'],kw['wc'],kw['rf']
        holder['owner']=owner;refs.append(weakref.ref(owner));return owner
    try:
        if mode=='NATIVE':result=clean.execute(inference,sample,'NATIVE',**kw)
        else:
            with clean.patched(clean,'CurrentBirthSamplingOwner',factory):
                result=clean.execute(inference,sample,'KEEP_A_P',**kw)
            owner=holder['owner']
            result.update(interval_cells=copy.deepcopy(owner.points),action_clocks=copy.deepcopy(owner.action_clocks),
                reference_parent_all_D=True,collector_enabled=mode=='COLLECT')
            del owner
        if result['status'] in ('COMPLETE','VIDEO_REJECTED'):
            if result['guided_pairs']!=36 or result['solver_steps']!=36:
                raise ValueError('All 36 original updates required')
            if mode!='NATIVE' and result['actions']!=['DD']*36:
                raise ValueError('A shadow must not alter an all-D parent')
            if mode=='COLLECT' and [(r['source'],r['target']) for r in result['interval_cells']]!=cells():
                raise ValueError('Full 406 source/time cells per input required')
        return result
    finally:
        holder.clear();after=collect_boundary()
        if any(ref() is not None for ref in refs):
            raise ValueError('Completed request retained an interval collector')
        if 'result' in locals():result['request_memory_lifecycle']=dict(before=before,after=after,
            observed_owners=len(refs),owners_alive_after=0)
