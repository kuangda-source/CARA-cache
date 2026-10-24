"""P1 R2 adapters: deferred complete block scoring, independent Native prefix."""
import json
import time
from pathlib import Path
from .production_evidence import artifact,score_videos,validate_score,native_clock,sha
from .continuation_preparation import generator_input,TIME_BOUNDARY,require
from .production_stage import accepted_assets,read
from ..gpu_budget_pool_v2 import atomic_json


class Callbacks:
    def __init__(self,*,project,stage,out,execute_request,metric,metric_identity,fit_members,select_members,launch,runner):
        self.project,self.stage,self.out=map(Path,(project,stage,out))
        self.execute_request=execute_request;self.metric=metric;self.metric_identity=metric_identity
        self.fit_members=fit_members;self.select_members=select_members;self.launch=launch;self.runner=runner
        self.old_raw,self.new_raw,self.old_accept,self.price_accept=accepted_assets(stage)
        self.price_profile=json.loads(self.new_raw)['profile_identity']
        self.events=[];self.consumer=None;self.clock=None

    def endpoint(self,slot,policy=None,reference=None):
        identifier=slot['id'];directory=self.out/identifier
        require(not directory.exists(),'Original slot already exists; no GPU replay')
        start=time.time()
        # No instrumentation copying/scoring is included in the request clock.
        result=self.execute_request(slot,policy,directory)
        result.update(started_unix=start,ended_unix=time.time())
        latent=result.pop('final_latent',None)
        if latent is not None:
            import torch
            p=directory/'final-latent.pt'
            with p.open('xb') as f:torch.save({'final_latent':latent},f)
            result['final_latent_artifact']=artifact(p,self.out)
        if result['status']=='COMPLETE':
            require(latent is not None,'Complete path missing final latent')
            result['video_artifact']=artifact(result['video_path'],self.out)
            require(result['solver_steps']==result['guided_pairs']==36,'Incomplete full36 request')
        atomic_json(directory/'request.json',dict(slot=slot,policy=policy,result=result))
        result['request_artifact']=artifact(directory/'request.json',self.out)
        self.events.append(dict(id=identifier,request_sha256=result['request_artifact']['sha256']))
        return result

    def score(self,row,reference):
        require(reference and reference['status']=='COMPLETE' and reference['member']==row['member'] and reference['seed']==row['seed'],'Matched Native original required')
        destination=self.out/row['id']/'score.json'
        require(not destination.exists(),'Original score cannot be silently replaced')
        score=score_videos(reference['video_artifact'],row['video_artifact'],self.metric,root=self.out,metric_identity=self.metric_identity)
        value=validate_score(score,reference['video_artifact'],row['video_artifact'],self.metric_identity)
        atomic_json(destination,score)
        return dict(LPIPS=value,score_artifact=artifact(destination,self.out))

    def accept_clock(self,rows):
        require([e['id'] for e in self.events]==['native_warm_1','native_warm_2']+['native_fit_'+str(i) for i in range(4)],'Native clock must precede any candidate')
        raw=(self.out/'exclusive-monitor.jsonl').read_text()
        self.clock=native_clock(rows,fit_members=self.fit_members,profile_identity=self.price_profile,
            monitor_raw=raw,runner=self.runner,gpu_uuid=self.launch['gpu_uuid'],now=time.time(),
            source_revision=self.launch['source_revision'],launch_id=self.launch['launch_id'])
        (self.out/'native-monitor-prefix.jsonl').write_text(raw)
        atomic_json(self.out/'native-clock.json',self.clock)
        return self.clock

    def build_consumer(self,clock):
        self.consumer=generator_input(self.new_raw,self.price_accept,self.old_raw,self.old_accept,clock)
        atomic_json(self.out/'consumer.json',self.consumer)
        return self.consumer

    def exposure(self):
        from ..frozen_input_exposure_r1 import collect_outputs
        baseline=read(self.stage/'pg-exposure-baseline.json')
        require(baseline.get('scoped_no_execution_evidence') is True,'Original local and remote SELECT audit not clear')
        manifest=read(self.stage/'plans/cara_policy_generator_20261020/CAL_SELECT_INPUTS_R1_20261022.json')
        catalog=read(self.stage/'reports/dataset_source_group_audit_20260930.json')['records']
        protected={m for row in manifest['selected_sources'] for m in row['group_members']}
        fresh=collect_outputs(self.project,catalog)
        hits={k:v for k,v in fresh['identity_hits'].items() if k in protected}
        value=dict(passed=not hits and not fresh['read_errors'],baseline_sha256=sha(self.stage/'pg-exposure-baseline.json'),
            selected_names=sorted(protected),remote=fresh,selected_hits=hits,scope='FROZEN_LOCAL_BASELINE_PLUS_FRESH_REMOTE_OUTPUT_METADATA',
            local_baseline_revalidated_at_launch=True,observed_unix=time.time(),endpoint_values_used=False)
        atomic_json(self.out/'select-exposure.json',value)
        return value
