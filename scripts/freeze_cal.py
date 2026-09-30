"""Freeze group-separated CAL membership before observing generated outputs."""
import hashlib
import json
from pathlib import Path

root=Path.cwd()
audit_path=root/'reports/dataset_source_group_audit_20260930.json'
audit=json.loads(audit_path.read_text())
assert audit['counts']['joined']==1044 and audit['counts']['missing']==audit['counts']['mismatched_prompts']==0
records=audit['records'];lookup={r['name']:r for r in records}
excluded=set(audit['engineering_excluded_groups'])
# Fixed CAL stratification: four cases in each primary motion/task domain,
# two industry and two misc. This is calibration membership, not confirmation.
quotas={'av':4,'common_sense':4,'human':4,'physics':4,'robot':4,'industry':2,'misc':2}
salt='worldcache-omr-cal-v1-20260930'
def order(name):return hashlib.sha256((salt+'|'+name).encode()).hexdigest()
seen=set();candidates=[]
for row in records:
    group=tuple(row['group_members'])
    if group in seen or excluded.intersection(group):continue
    seen.add(group)
    candidates.append(lookup[min(group)])
selected=[]
for category,count in quotas.items():
    pool=sorted([r for r in candidates if r['category']==category],key=lambda r:order(r['name']))
    assert len(pool)>=count
    selected.extend(pool[:count])
assert len(selected)==24 and len({tuple(r['group_members']) for r in selected})==24
assert not excluded.intersection(r['name'] for r in selected)
source_dir=root/'vendor/WorldCache/Evaluation/PAI-Eval/cosmos_eval_jsons_text_only'
cases=[]
for row in selected:
    path=source_dir/(row['name']+'.json');data=json.loads(path.read_text())
    assert hashlib.sha256(data['prompt'].encode()).hexdigest()==row['prompt_sha256']
    cases.append({**row,'config_path':str(path.relative_to(root)),
                  'config_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
# W1-D screen: first hashed member in every category, plus second AV.
subset=[next(r['name'] for r in cases if r['category']==cat) for cat in sorted(quotas)]
subset.append([r['name'] for r in cases if r['category']=='av'][1])
assert len(set(subset))==8
manifest={'status':'CAL_MEMBERSHIP_FROZEN_BEFORE_GENERATION_REFERENCE_CLIP_AND_LEXICAL_GROUPING',
    'version':1,'date':'2026-09-30','upstream_commit':'60a486df6d2e6d2aa3c21815895aac157a88e95d',
    'source_revision':audit['source']['revision'],'source_sha256':audit['source']['sha256'],
    'group_audit_sha256':hashlib.sha256(audit_path.read_bytes()).hexdigest(),'salt':salt,
    'selection':'SHA256 order within fixed category quotas, one representative per joined reference/lexical component',
    'category_quotas':quotas,'cases':cases,'w1d_first8':subset,'excluded_engineering_groups':sorted(excluded),
    'generation':{'seed':0,'num_steps':35,'num_output_frames':93,'resolution':'432,768','guidance':7},
    'limitation':'Membership only, no new samples generated. Benchmark reference clips plus lexical threshold0.85 identify observed groups; original recording/session independence and semantic duplicates are not proven. CAL is reusable development/calibration, never blind confirmation. DEV/CONF not frozen.'}
(root/'manifests/cal_v1.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'cal_count':len(cases),'first8':subset,'quotas':quotas},indent=2))
