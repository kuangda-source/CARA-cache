"""Join pinned upstream prompts to primary benchmark reference-clip metadata.

No videos are generated or downloaded. Reference names identify benchmark clips,
not proven independent recordings. Near-template grouping is a lexical proxy.
"""
import argparse
from collections import Counter,defaultdict
import hashlib
import json
from pathlib import Path
import re
import numpy as np

p=argparse.ArgumentParser()
p.add_argument('--source',type=Path,required=True,help='Downloaded, pinned benchmark full_info JSON')
p.add_argument('--source-receipt',type=Path,required=True)
p.add_argument('--prompts',type=Path,default=Path('vendor/WorldCache/Evaluation/PAI-Eval/cosmos_eval_jsons_text_only'))
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
meta=json.loads(a.source_receipt.read_text());raw=a.source.read_bytes()
assert hashlib.sha256(raw).hexdigest()==meta['sha256']
rows=json.loads(raw);index={r['video_id']:r for r in rows};assert len(index)==len(rows)
local=[json.loads(f.read_text()) for f in sorted(a.prompts.glob('*.json'))]
normalize=lambda s:' '.join(re.findall(r'[a-z0-9]+',s.lower()))
joined=[];missing=[];mismatch=[]
for row in local:
    name=row['name'];primary=index.get(name)
    if primary is None:missing.append(name);continue
    if normalize(row['prompt'])!=normalize(primary['prompt_en']):mismatch.append(name);continue
    joined.append({'name':name,'category':name.split('_')[0] if not name.startswith('common_sense_') else 'common_sense',
                   'reference_video':primary['reference_video'],'image_name':primary['image_name'],
                   'prompt_sha256':hashlib.sha256(row['prompt'].encode()).hexdigest(),'prompt':row['prompt']})
assert not missing and not mismatch,'Missing/mismatched source join'
# Freeze this transparent threshold before computing pair scores. It is not a
# learned semantic test or evidence that lower-scoring prompts are independent.
threshold=.85
stop=set('the a an and or of in on at to from with by for is are was were this that as it its their there video scene camera frame shot view shows showing begins continues'.split())
tokens=[Counter(w for w in re.findall(r'[a-z]+',r['prompt'].lower()) if w not in stop and len(w)>2) for r in joined]
df=Counter(w for doc in tokens for w in doc);vocab=sorted(df);axis={w:i for i,w in enumerate(vocab)}
matrix=np.zeros((len(joined),len(vocab)),dtype=np.float32)
for i,doc in enumerate(tokens):
    for word,count in doc.items():matrix[i,axis[word]]=(1+np.log(count))*(1+np.log((1+len(tokens))/(1+df[word])))
norms=np.linalg.norm(matrix,axis=1);assert np.all(norms>0);matrix/=norms[:,None]
assert np.isfinite(matrix).all()
# Avoid platform BLAS floating-point status warnings on macOS; explicit
# reduction also makes the finite/bounded audit independent of that path.
cosines=np.einsum('ik,jk->ij',matrix,matrix,optimize=False)
assert np.isfinite(cosines).all()
assert np.allclose(np.diag(cosines),1,atol=1e-5)
assert np.allclose(cosines,cosines.T,atol=1e-6)
assert cosines.min()>=-1e-6 and cosines.max()<=1+1e-5
parent=list(range(len(joined)))
def find(i):
    while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
    return i

def union(i,j):
    x,y=find(i),find(j)
    if x!=y:parent[max(x,y)]=min(x,y)
references=defaultdict(list)
for i,row in enumerate(joined):references[row['reference_video']].append(i)
for members in references.values():
    for i in members[1:]:union(members[0],i)
edges=[]
for i in range(len(joined)):
    for j in range(i+1,len(joined)):
        if cosines[i,j]>=threshold:
            union(i,j);edges.append({'left':joined[i]['name'],'right':joined[j]['name'],'tfidf_cosine':float(cosines[i,j])})
groups=defaultdict(list)
for i,row in enumerate(joined):groups[find(i)].append(row['name'])
excluded=set(json.loads(Path('reports/dataset_inventory_20260930.json').read_text())['excluded_engineering_cases'])
group_members={name:sorted(members) for members in groups.values() for name in members}
excluded_groups={name for name in group_members if excluded.intersection(group_members[name])}
output={'status':'PRIMARY_REFERENCE_CLIP_JOIN_AND_LEXICAL_GROUP_AUDIT_NOT_CAL_FREEZE','source':meta,
        'local_upstream_manifest_sha256':hashlib.sha256(Path('manifests/upstream.json').read_bytes()).hexdigest(),
        'counts':{'local_prompts':len(local),'primary_records':len(rows),'joined':len(joined),'missing':len(missing),
                  'mismatched_prompts':len(mismatch),'reference_groups':len(references),'combined_groups':len(groups)},
        'source_fields':dict(Counter(key for r in rows for key in r)),
        'same_reference_multiple_prompt_groups':[[joined[i]['name'] for i in group] for group in references.values() if len(group)>1],
        'lexical_protocol':{'method':'word TFIDF, sublinear tf, smooth idf, explicit stopwords, connected components',
                            'threshold':threshold,'stopwords':sorted(stop),'vocabulary':len(vocab),'dtype':'float32','cosines_finite_symmetric_bounded_unit_diagonal':True},
        'near_template_edges':edges,'non_singleton_groups':[sorted(g) for g in groups.values() if len(g)>1],
        'engineering_excluded_groups':sorted(excluded_groups),
        'records':[{k:v for k,v in row.items() if k!='prompt'}|{'group_members':group_members[row['name']]} for row in joined],
        'limitation':'Reference-clip metadata only; original recording/session IDs and semantic near-duplicate independence are not established. Unique reference names or below-threshold cosine are not proof of independence. No CAL/DEV/CONF membership frozen, GPU or quality evidence.'}
a.output.write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps({'counts':output['counts'],'edges':len(edges),'excluded_group_members':len(excluded_groups),'source_fields':output['source_fields']},indent=2))
