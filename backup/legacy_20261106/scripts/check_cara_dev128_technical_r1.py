"""DEV128 original-handle read-only health; reuses accepted monitor-prefix audit."""
import argparse,json
from pathlib import Path
from cara_two_card_transport_r1 import ssh
from check_cara_cal66_a6000_technical_r1 import REMOTE
from wc_four_card_resource_cpu_r4 import write
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--launch-ref',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 L=json.loads(a.launch_ref.read_text());assert L['host']=='two_card' and L['run_id']=='cara-shared25-dev128-r1' and L['scope_counts']['total_paths']==128
 v=ssh(REMOTE.replace('CAL66_A6000_TECHNICAL_READONLY','DEV128_A6000_TECHNICAL_READONLY'),L,docker_group=True);write(a.output,v)
 print(json.dumps({k:v[k] for k in ('status','health','runner_live','monitor_prefix_samples','maximum_interval_seconds','violations','storage','cross_disk_telemetry_age_seconds')}))
