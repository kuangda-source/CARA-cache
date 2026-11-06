"""Thin dual-host adapter of the accepted S/Q CPU-only launch/capture path."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess

import cara_sq_two_card_cpu_r1 as previous
import cara_two_card_transport_r1 as transport

ROOT=Path(__file__).resolve().parents[1]
FILES=('src/wcomr/sq_q1_readout_r1.py','src/wcomr/sq_q1_spec_r1.py','src/wcomr/sq_schedule_profile_r2.py',
       'src/wcomr/sq_codec_r1.py','src/wcomr/sq_risk_r1.py',
       'src/wcomr/innovation_gain_observer_r1.py','src/wcomr/scout_readout_v22.py',
       'src/wcomr/policy_interval_readout_r1.py','src/wcomr/cfg_guided_w1_forward.py',
       'tests/test_sq_q1_readout_r1.py','tests/test_scout_readout_v22.py',
       'tests/check_rv0_video_actions_cpu.py','tests/check_rv0_restore_cpu.py',
       'manifests/cara_DEV128_scope_r1_20261026.json','scripts/check_cara_sq_q1_cpu_r1.py')


def launch_source():
    code=previous.LAUNCH
    changes=[
        ("assert sha(assets/'manifest.json')==p['manifest_sha256']",
         "if p['profile']=='two_card':assert sha(assets/'manifest.json')==p['manifest_sha256']"),
        ('cara-sq-CPU-only-r1.lock','cara-sq-q1-CPU-only-r1.lock'),
        ('CARA_SQ_CPU_ONLY_R1','CARA_SQ_Q1_CPU_PREPARATION_R1'),
        ('scripts/cara_sq_saved_cpu_r1.py','scripts/check_cara_sq_q1_cpu_r1.py'),
        ("'--manifest-sha256',p['manifest_sha256'],'--output'",
         "'--manifest-sha256',p['manifest_sha256'],'--profile',p['profile'],'--output'"),
        ("cmd[2:2]=['--cpuset-cpus','4,5','--memory-swap','8g','--ulimit','fsize=67108864:67108864','-v',str(assets.parent)+':'+str(assets.parent)+':ro']",
         "cmd[2:2]=['--cpuset-cpus','4,5','--memory-swap','8g','--ulimit','fsize=67108864:67108864']+(['-v',str(assets.parent)+':'+str(assets.parent)+':ro'] if p['profile']=='two_card' else [])")]
    for before,after in changes:
        if code.count(before)!=1:raise ValueError('Accepted CPU launch boundary changed: '+before)
        code=code.replace(before,after)
    return code


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=('launch','capture','recover'))
    p.add_argument('--host',choices=('two_card','four_card'),required=True);p.add_argument('--launch-ref',type=Path)
    p.add_argument('--attempt',choices=('r1','r2'),default='r2')
    p.add_argument('--output',type=Path,required=True);args=p.parse_args();assert not args.output.exists()
    stage='cara-sq-q1-cpu-'+args.host.replace('_','-')+'-'+args.attempt+'-20261028'
    def remote(code,data=None):
        return transport.ssh(code,data,docker_group=True) if args.host=='two_card' else transport.four_ssh(code,data)
    if args.command=='launch':
        revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        if subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,text=True).split()[0]!=revision:
            raise ValueError('Publish exact source before CPU dispatch')
        files={name:(ROOT/name).read_bytes() for name in FILES}
        if not all(subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT)==raw for name,raw in files.items()):
            raise ValueError('Unpublished source in Q1 CPU payload')
        base_ref={'two_card':'cara_IG_grouped_two_card_CPU_finished_r1_20261027.json',
                  'four_card':'cara_IG_four_card_CPU_terminal_r3_20261027.json'}[args.host]
        base=json.loads((ROOT/'reports'/base_ref).read_text())['launch']
        value=remote(launch_source(),dict(stage_name=stage,profile=args.host,manifest_sha256=previous.MANIFEST,
            base=base,revision=revision,files={n:base64.b64encode(v).decode() for n,v in files.items()},
            hashes={n:hashlib.sha256(v).hexdigest() for n,v in files.items()}))
    elif args.command=='capture':
        value=remote(previous.CAPTURE,json.loads(args.launch_ref.read_text()))
    else:
        code="import pathlib,json;p=pathlib.Path('/data20t/gaokuangda/worldcache_workspace/.sync/"+stage+"/launch.json');print(p.read_text() if p.exists() else json.dumps({'status':'NO_Q1_CPU_LAUNCH','stage_exists':p.parent.exists()}))"
        value=remote(code)
    with args.output.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:value.get(k) for k in ('status','container_state','result_sha256')}))


if __name__=='__main__':main()
