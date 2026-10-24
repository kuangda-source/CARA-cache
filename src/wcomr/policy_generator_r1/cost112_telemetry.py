"""Read-only thermal/clock evidence; no fan, power or frequency modification."""
import math,subprocess,time
FIELDS='uuid,temperature.gpu,clocks.sm,power.draw,clocks_throttle_reasons.sw_thermal_slowdown,clocks_throttle_reasons.sw_power_cap'
def parse(raw,uuid):
    v=[x.strip() for x in raw.strip().split(',')]
    if len(v)!=6 or v[0]!=uuid:raise ValueError('Thermal UUID/fields differ')
    nums=[float(x) for x in v[1:4]]
    if not all(math.isfinite(x) and x>=0 for x in nums) or any(x not in ('Active','Not Active') for x in v[4:]):raise ValueError('Invalid thermal values')
    return dict(gpu_uuid=uuid,temperature_C=nums[0],SM_MHz=nums[1],power_W=nums[2],SW_thermal_slowdown=v[4],SW_power_cap=v[5])
def observe(uuid):
    value=parse(subprocess.check_output(['/usr/bin/nvidia-smi','-i',uuid,'--query-gpu='+FIELDS,'--format=csv,noheader,nounits'],text=True,timeout=10),uuid)
    value['observed_unix']=time.time();return value
