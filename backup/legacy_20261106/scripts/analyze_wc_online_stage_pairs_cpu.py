#!/usr/bin/env python3
"""All four online candidates versus their paired WC; encoded proxies only."""
import argparse
import importlib.util
import json
from pathlib import Path

spec=importlib.util.spec_from_file_location('light_metrics',Path(__file__).with_name('analyze_wc_light_video_pairs_cpu.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)


def analyze(audit):
    assert audit['status']=='EIGHT_ONLINE_STAGE_ADAPTIVE_SOURCE_POLICY_VIDEO_AUDIT_PASS_NOT_QUALITY'
    assert len(audit['files'])==8 and audit['measurement_outputs']==6
    pairs=[]
    for group in audit['measurement_groups']:
        a,b,c=group['files']
        assert [f['variant'] for f in (a,b,c)]==['adaptive_WC','stage_every1','stage_every2']
        for candidate in (b,c):
            result=base.pair(a,candidate,group['sample_name'])
            result['variant']=candidate['variant'];pairs.append(result)
    assert len(pairs)==4
    return {'status':'TWO_EXPOSED_CAL_FOUR_ONLINE_STAGE_FIDELITY_DIAGNOSTICS_NOT_ACCEPTANCE',
        'CPU_only':True,'planned_card_outputs':8,'pairs':pairs,
        'quality_acceptance':False,'semantic_or_physics_acceptance':False,
        'deployment_speed_claim':False,
        'limits':['All four candidates included, fixed WC references; no selection by observed metric.',
                  'Encoded RGB reference is official WC, not Native; metrics do not establish physical behavior.',
                  'Exposed CAL and single ordered timings are not CONF or stable speed.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('audit','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();r=analyze(json.loads(a.audit.read_text()))
    r.update(input_audit_sha256=base.metrics.sha(a.audit),analysis_code_sha256=base.metrics.sha(Path(__file__)),
        reused_pair_code_sha256=base.metrics.sha(Path(__file__).with_name('analyze_wc_light_video_pairs_cpu.py')),
        reused_metric_code_sha256=base.metrics.sha(Path(__file__).with_name('analyze_wc_video_pairs_cpu.py')))
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':r['status'],'pairs':len(r['pairs']),
                     'whole_video':[q['whole_video'] for q in r['pairs']]}))
