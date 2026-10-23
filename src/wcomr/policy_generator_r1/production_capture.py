"""Read original PG artifacts after child exit; never load CUDA or rerun a request."""
import hashlib,json
from pathlib import Path
from .production_stage import RUN,read
from .production_evidence import artifact,verify_artifact

def collect(project,stage,launch):
    root=Path(project);stage=Path(stage);out=root/'outputs'/RUN
    value=dict(files={},launch=launch,requests={},scores={},artifact_checks={})
    def keep(key,path,target=None):
        target=value['files'] if target is None else target
        path=Path(path);target[key]=dict(exists=path.exists())
        if path.exists():
            raw=path.read_bytes();target[key].update(raw_utf8=raw.decode(),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
    for key,name in [('runner','runner.json'),('consumer','consumer.json'),('native_clock','native-clock.json'),('post','post-results.json'),('post_exit','post-exit.json'),('supervisor','supervisor.json'),('billing','billing.json'),('monitor_final','exclusive-monitor-final.json')]:keep(key,out/name)
    for key,name in [('registration','registration.json'),('config','pg-config.json'),('quote','pg-whole-quote.json'),('CPU_acceptance','pg-independent-CPU-acceptance.json'),('authorization','pg-GPU-authorization.json'),('guardian','pg-host-guardian.json'),('ready','pg-runner-context-ready.json'),('grant','pg-runner-context-granted.json'),('old_bundle','pg-old-labels.json'),('new_bundle','pg-clean-prices.json'),('old_acceptance','pg-old-acceptance.json'),('price_acceptance','pg-price-acceptance.json')]:keep(key,stage/name)
    value['native_monitor_prefix_raw_utf8']=(out/'native-monitor-prefix.jsonl').read_text()
    value['monitor_raw_utf8']=(out/'exclusive-monitor.jsonl').read_text()
    value['select_members']=[r['name'] for r in read(stage/'plans/cara_policy_generator_20261020/CAL_SELECT_INPUTS_R1_20261022.json')['selected_sources']]
    from ..rv0_video_reader import probe_video
    for row in read(out/'runner.json')['batch']['rows']:
        if row['status']=='UNUSED_REGISTERED_UPPER_BOUND':continue
        keep(row['id'],out/row['id']/'request.json',value['requests'])
        if row.get('score_artifact'):keep(row['id'],verify_artifact(row['score_artifact'],out),value['scores'])
        if row['status']=='COMPLETE':
            value['artifact_checks'][row['id']]={k:artifact(verify_artifact(row[k],out),out) for k in ('video_artifact','final_latent_artifact')}
            value['artifact_checks'][row['id']]['frames']=probe_video(row['video_artifact']['path'])['frames']
    return value
