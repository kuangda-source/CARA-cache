#!/usr/bin/env python3
"""One common D versus three fixed selective-S encoded diagnostics."""
import argparse
import importlib.util
import importlib.metadata
import json
from pathlib import Path

spec=importlib.util.spec_from_file_location('existing_pairs',Path(__file__).with_name('analyze_wc_light_video_pairs_cpu.py'))
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)


def analyze(audit,*,control_only=False):
    if control_only:
        assert audit['status']=='SELECTIVE_DD_TWO_OUTPUT_AUDIT_PASS_SIX_CARD_PENDING'
        assert len(audit['files'])==2
        pairs=[base.pair(*audit['files'],'human_199',diagnostic_control=True)]
    else:
        assert audit['status']=='SIX_SELECTIVE_SOURCE_POLICY_MASK_VIDEO_AUDIT_PASS_NOT_QUALITY'
        assert len(audit['files'])==6 and audit['measurement_outputs']==4
        files=audit['measurement_files']
        assert [p['variant'] for p in files]==['fixed_D','full_S','small_S','cadenced_S']
        pairs=[]
        for file in files[1:]:
            result=base.pair(files[0],file,'human_199');result['variant']=file['variant'];pairs.append(result)
    return {'status':'SELECTIVE_DD_ENCODED_CONTROL_PASS' if control_only else
        'EXPOSED_HUMAN_THREE_SELECTIVE_ENCODED_PROXY_RESULTS_NOT_ACCEPTANCE',
        'CPU_only':True,'planned_card_outputs':6,'control_only':control_only,'pairs':pairs,
        'metric_packages':{k:importlib.metadata.version(k) for k in ('numpy','scikit-image')},
        'quality_acceptance':False,'semantic_or_physics_acceptance':False,'independent_confirmation':False,
        'deployment_speed_claim':False,
        'limits':['One exposed human seed0; shared offline38-deep mask and one fixed-order run per variant.',
            'Full-S exact previous-output reproduction is a technical gate, not a new independent quality scene.',
            'Encoded WC-relative proxies do not establish Native/semantic/physics quality or CONF.',
            'Cadenced full D is exact on its own state; it does not undo accumulated latent differences.',
            'No same-quality faster claim from single pair timings or an unregistered quality threshold.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--audit',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--control-only',action='store_true');a=p.parse_args()
    r=analyze(json.loads(a.audit.read_text()),control_only=a.control_only)
    r.update(input_audit_sha256=base.metrics.sha(a.audit),analysis_code_sha256=base.metrics.sha(Path(__file__)),
        reused_pair_code_sha256=base.metrics.sha(Path(__file__).with_name('analyze_wc_light_video_pairs_cpu.py')),
        reused_metric_code_sha256=base.metrics.sha(Path(__file__).with_name('analyze_wc_video_pairs_cpu.py')))
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':r['status'],'whole_video':[q['whole_video'] for q in r['pairs']]}))
