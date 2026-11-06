"""Frozen first H0 local complementarity card; no Torch dependency."""
def validate_h0_scope(c):
    fixed={'card':'WC-H0-COMPLEMENT-R1-20261003-A','max_gpu_wall_seconds':1200,'sample_name':'common_sense_6487f37f-ef57-49ca-afdc-d898922b5191','eligible_call_range':[25,40],'dense_fallback_layers':[6,23,27],'stop_after_solver_steps':20,'state_steps':[13,20],'phases':['baseline_prefix','observed_prefix'],'policy':{'sim':.1,'cdf':.98},'warmups':1,'repeats':3,'pv_skipping':False,'deployment_sparse':False,'planned_cfg_denominator':2}
    if any(c.get(k)!=v for k,v in fixed.items()):raise ValueError('Frozen H0 card altered')
    return {0,1}

def cost_gate(c):
    e=c['cost_admission']
    if e['planning_envelope_seconds']+e['shutdown_settlement_margin_seconds']>c['max_gpu_wall_seconds']:raise ValueError('Cost admission failed')
