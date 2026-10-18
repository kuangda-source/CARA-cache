"""Exact reversible adaptation of the registered ordinary guarded GPU entry."""
import ast
import hashlib

RUNNER_SHA='3a4aa59bc8559a82e43717bc7d04592a8a346e2812f209bd8f98243045a63b4c'


def adapt(source):
    if hashlib.sha256(source.encode()).hexdigest()!=RUNNER_SHA:raise ValueError('Exact original runner required')
    save='''            vectors=result.pop('scout_vectors',None)
            if vectors is not None:
                path=directory/'scout-step20-21.pt';assert not path.exists()
                torch.save(vectors,path)
                result['scout_vectors_artifact']={'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size}
                result['scout_vector_metadata']={k:{'shape':list(v.shape),'dtype':str(v.dtype),'tree_sha256':tree_digest(v)} for k,v in vectors.items()}
                del vectors
'''
    replacements=[
        ('from wcomr.drop1_full18_r1 import','from wcomr.scout_production_entry_r1 import',4),
        ('COUNTS,PRODUCTION_CPU_STATUS','COUNTS,PRODUCTION_CPU_STATUS,METHODS',1),
        ("execute(dummy,samples[0],'S26-C'","execute(dummy,samples[0],METHODS[0]",1),
        ('production-CPU-result.json','scout-entry-production-CPU-result.json',2),
        ("sha(a.stage/'drop1-sampling-CPU-result.json')","c['references']['numeric_capture']['sha256']",1),
        ('sampling_CPU_sha256=','numerical_CPU_capture_sha256=',1),
        ("'scientific_paths':11","'formal_paths':1",1),
        ("audit=diagnostic_warm(planned))","audit=diagnostic_warm(planned),observer=planned['observer'])",1),
        ("            guides=result.pop('guided',None)\n",save+"            guides=result.pop('guided',None)\n",1),
        ("life['observed_owners']==1","life['observed_owners']==(0 if planned['method']=='NATIVE35' else 1)",1),
        ("len(state['runs'])==18","len(state['runs'])==COUNTS['total_paths']",1),
        ('DROP1_INITIALIZING_SINGLE_RESIDENT_MODEL','SCOUT_INITIALIZING_SINGLE_RESIDENT_MODEL',1),
        ('DROP1_ALL18_FULL_PATHS_RUNNING','SCOUT_COMPLETE_REGISTERED_PATHS_RUNNING',1),
        ('DROP1_ALL18_FULL12_SCIENCE_GPU_COMPLETE_CPU_AUDIT_PENDING','SCOUT_GPU_COMPLETE_CPU_AUDIT_PENDING',1),
        ('DROP1_TECHNICAL_STOP_FULL12_SCOPE_RETAINED','SCOUT_TECHNICAL_STOP_COMPLETE_SCOPE_RETAINED',1)]
    value=source
    for before,after,count in replacements:
        if value.count(before)!=count:raise ValueError('Exact scout entry substitution failed: '+before[:80])
        value=value.replace(before,after)
    restored=value
    for before,after,count in reversed(replacements):
        if restored.count(after)!=count:raise ValueError('Reversible scout entry count differs')
        restored=restored.replace(after,before)
    if restored!=source:raise ValueError('The original guarded model entry must be recoverable')
    ast.parse(value);return value
