"""Reuse accepted GPU-hidden dual-host CPU transport for affected video entry."""
import argparse,base64,hashlib,json,subprocess
from pathlib import Path
from wc_cara_ig_b1_gpu_r2 import remote,ROOT,read,write
from wc_cara_innovation_gain_cpu_r2 import PREPARE,CAPTURE


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','capture'])
    p.add_argument('--host',choices=['two_card','four_card'],required=True)
    p.add_argument('--launch-ref',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    if a.command=='capture':v=remote(a.host,CAPTURE,read(a.launch_ref))
    else:
        rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        assert subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=ROOT,text=True).split()[0]==rev
        paths=[p for folder in ('src','scripts','tests') for p in (ROOT/folder).rglob('*.py') if '__pycache__' not in p.parts]
        paths += [ROOT/n for n in ['plans/cara_predictor_refresh_scout_v2_20261026/E1_STATE_METADATA_V22.json',
            'manifests/cara_shared_CAL66_scope_quote_r1_20261025.json',
            'manifests/cara_IG_B2_predeclared_matrix_r1_20261027.json','configs/wc_scout_cal12_production_entry_r1_20261018.json']]
        files={str(p.relative_to(ROOT)):p.read_bytes() for p in paths}
        assert all(subprocess.check_output(['git','show',rev+':'+n],cwd=ROOT)==b for n,b in files.items())
        code=PREPARE.replace('scripts/check_cara_innovation_gain_cpu_r2.py','scripts/check_cara_ig_b2_cpu_r1.py')
        marker="cmd[cmd.index('--memory')+1]='8g'"
        assert code.count(marker)==1
        code=code.replace(marker,marker+"\ncmd[2:2]=['--cpuset-cpus','4,5']")
        v=remote(a.host,code,dict(host=a.host,stage_name='cara-ig-b2-cpu-'+('a6000' if a.host=='two_card' else 'ada')+'-r1-20261027',
            revision=rev,files={n:base64.b64encode(b).decode() for n,b in files.items()},
            hashes={n:hashlib.sha256(b).hexdigest() for n,b in files.items()}))
    write(a.output,v);print(json.dumps({k:v.get(k) for k in ('status','stage','container_state')}))


if __name__=='__main__':main()
