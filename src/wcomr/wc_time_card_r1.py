"""Seven-role guarded request adapter; one canonical paper_latency_r1 clock.

No launch, budget reservation, GPU acquisition, or parameter search at import.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
from . import clean_speed20_r1 as clean
from .paper_latency_r1 import execute_with_timing
from .wc_time_protocol_p0 import compile_wc_adapter
from .policy_generator_r1 import p2_native_sampling, production_sampling
from .policy_generator_r1.interval_grammar import Profile
from .cfg_ra_joint_control import Calibration


def digest(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def select_tau(rows, scenes):
    """Finite complete candidate grid; never select from a failed subset."""
    if len(rows)!=4 or len({(r['scene'],r['tau']) for r in rows})!=4:
        raise ValueError('Complete two-scene two-tau grid required')
    options=[]
    for tau in (.04,.06):
        pair=[r for r in rows if r['tau']==tau]
        if {r['scene'] for r in pair}!=set(scenes):raise ValueError('Selection cohort differs')
        for r in pair:
            if r['status']!='COMPLETE' or not all(type(r[k]) in (int,float) and math.isfinite(r[k]) and r[k]>=0 for k in ('T_DD','CARA_T_DD','Alex')) or min(r['T_DD'],r['CARA_T_DD'])<=0:
                raise ValueError('Incomplete finite selection denominator')
        mismatch=max(abs(r['T_DD']/r['CARA_T_DD']-1) for r in pair)
        options.append(dict(tau=tau,mismatch=mismatch,Alex=sum(r['Alex'] for r in pair)/2,eligible=mismatch<=.05))
    eligible=[r for r in options if r['eligible']]
    chosen=min(eligible,key=lambda r:(r['Alex'],r['tau'])) if eligible else min(options,key=lambda r:(r['mismatch'],r['Alex'],r['tau']))
    return dict(selected_tau=chosen['tau'],time_match='MATCHED' if eligible else 'UNMATCHED',candidates=options,selection_rows_sha256=digest(rows))


def load_calibration(binding):
    c=binding['calibration']
    return Calibration(fingerprint=c['fingerprint'],rho_at={(a,b):v for a,b,v in c['rho_at']},gains={int(k):v for k,v in c['gains'].items()})


class Requests:
    def __init__(self, *, inference, samples, card, common, ra_binding, host, cpu_validation=False, frozen=None):
        self.inference,self.samples,self.card,self.common=inference,samples,card,common
        self.host,self.cpu_validation,self.frozen=host,cpu_validation,frozen
        self.seen=set();self.slots={r['id']:r for r in card['physical_matrix']}
        self.calibration=load_calibration(ra_binding)
        if self.calibration.fingerprint!=card['roles']['RA_LOCAL_U36']['calibration_fingerprint']:raise ValueError('RA binding mismatch')
        self.profile=Profile(**{k:tuple(v) if k in ('protected_dense','alpha_candidates') else v for k,v in ra_binding['profile'].items()})
        self.adapters={}
        for name,kw in [('ALLD',dict(force_full=True)),('PORT',dict(paper_port=True))]:
            self.adapters[name]=compile_wc_adapter(common['runtime'],common['wc'],**kw)[0]

    def __call__(self, slot, output, *, timing=None):
        if self.slots.get(slot['id'])!=slot:raise ValueError('Unregistered or altered physical slot')
        if slot['id'] in self.seen:raise ValueError('Physical slot already attempted; no automatic retry')
        role=slot['role'];stage=slot['section'][0]
        if stage=='B' and not self.frozen:raise ValueError('Phase B requires released phase A and frozen selection')
        if self.frozen and not self.cpu_validation and self.frozen.get('scope_sha256')!=self.card['scope_sha256']:raise ValueError('Freeze belongs to another scope')
        if self.frozen and (self.frozen.get('selected_tau') not in (.04,.06) or not self.frozen.get('phase_A_GPU_released')):raise ValueError('Invalid release/freeze receipt')
        sample=self.samples[slot['scene']]
        if sample.num_steps!=35 or sample.seed!=slot['seed']:raise ValueError('Frozen sample schedule/seed mismatch')
        self.seen.add(slot['id'])
        settings=copy.deepcopy(self.card['roles']['WC_README_U36']['settings'])
        module=self.common['wc'];execute=clean.execute;args=();extra={};method='WC'
        if role=='NATIVE_U36':execute=p2_native_sampling.execute;extra['schedule']=self.card['schedule']
        elif role=='WC_WRAPPER_ALLD_U36':module=self.adapters['ALLD']
        elif role=='CARA_SHARED25_C_U36':
            execute=production_sampling.execute;extra.update(profile=self.profile,policy=self.card['roles'][role]['policy'])
        elif role=='RA_LOCAL_U36':method='RA'
        elif role in ('WC_PAPER_PORT_U36','WC_TUNED_U36','TAU_0.04','TAU_0.06'):
            module=self.adapters['PORT'];settings=copy.deepcopy(self.card['roles']['WC_PAPER_PORT_U36']['settings'])
            if role.startswith('TAU_'):settings['worldcache_rel_l1_thresh']=float(role[4:])
            elif role=='WC_TUNED_U36':settings['worldcache_rel_l1_thresh']=self.frozen['selected_tau']
        elif role!='WC_README_U36':raise ValueError('Unknown role')
        if execute is clean.execute:args=(method,)
        diagnostic=not slot['eligible_clean_time'] and 'DIAGNOSTIC' in slot['section']
        kw={**self.common,**extra,'wc':module,'settings':settings,'calibration':self.calibration,
            'specs':{'SOURCE_RA':self.card['roles']['RA_LOCAL_U36']['RA_spec']},'output':Path(output),'audit':diagnostic or self.cpu_validation}
        enabled=slot.get('timing_enabled',True) if timing is None else timing
        if timing is not None and not self.cpu_validation:raise ValueError('Timing override is CPU-test-only')
        if enabled:
            result=execute_with_timing(execute,self.inference,sample,*args,host=self.host,expected_updates=36,cpu_validation=self.cpu_validation,diagnostic=diagnostic,**kw)
        else:
            result=execute(self.inference,sample,*args,**kw)
            if result.get('core_seconds'):result['full_request_seconds']=production_sampling.complete_request_seconds(result)
        result.update(slot_id=slot['id'],role=role,T_DD=result.get('paper_denoise_decode_seconds'),T_generate=result.get('core_seconds'),T_request=result.get('full_request_seconds'),canonical_timing='wcomr.paper_latency_r1',CPU_fixture=self.cpu_validation)
        return result
