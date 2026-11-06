#!/usr/bin/env python3
"""All ten nonreference workpoints versus paired Native35; encoded proxies only."""
import argparse
import importlib.util
import json
from pathlib import Path

spec=importlib.util.spec_from_file_location('light_metrics',Path(__file__).with_name('analyze_wc_light_video_pairs_cpu.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)


def analyze(audit):
    assert audit['status']=='FOURTEEN_FAIR_CAL_NATIVE_WC_STAGE_VIDEO_AUDIT_PASS_NOT_QUALITY'
    assert len(audit['files'])==14 and audit['measurement_outputs']==12
    assert audit['metric_reference']=='native35' and audit['planned_native_relative_pairs']==10
    pairs=[]
    for group in audit['measurement_groups']:
        files=group['files']
        assert [f['variant'] for f in files]==['native35','native23','wc004','wc006','wc008','stage_every1']
        for candidate in files[1:]:
            r=base.pair(files[0],candidate,group['sample_name'])
            r.update(reference='native35',variant=candidate['variant']);pairs.append(r)
    assert len(pairs)==10
    return {'status':'TWO_EXPOSED_CAL_TEN_NATIVE_RELATIVE_FAIR_DIAGNOSTICS_NOT_ACCEPTANCE',
        'CPU_only':True,'planned_card_outputs':14,'metric_reference':'native35','pairs':pairs,
        'quality_acceptance':False,'semantic_or_physics_acceptance':False,'deployment_speed_claim':False,
        'limits':['All five alternatives per scene retained with Native35 fixed before calculation.',
            'Encoded RGB/luma/motion/temporal proxies do not establish semantic or physical behavior.',
            'Exposed CAL and single ordered timings are not CONF or stable speed.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('audit','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();r=analyze(json.loads(a.audit.read_text()))
    r.update(input_audit_sha256=base.metrics.sha(a.audit),analysis_code_sha256=base.metrics.sha(Path(__file__)),
        reused_pair_code_sha256=base.metrics.sha(Path(__file__).with_name('analyze_wc_light_video_pairs_cpu.py')),
        reused_metric_code_sha256=base.metrics.sha(Path(__file__).with_name('analyze_wc_video_pairs_cpu.py')))
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':r['status'],'pairs':len(r['pairs']),'whole_video':[q['whole_video'] for q in r['pairs']]}))
