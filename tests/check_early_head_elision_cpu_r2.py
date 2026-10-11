"""R2 comparison repair: map installation-local parameter IDs by native name.

R1's methods, head prototype, full scope and own-version strict restoration
remain unchanged. Save raw and canonical projection records before comparing.
"""
import ast
import copy
import inspect
import json
from pathlib import Path

import check_early_head_elision_cpu_r1 as original


def canonical_projection(cache,net):
    from wcomr.partial_mlp_deployment_state import plain
    from wcomr.mid_coverage import tree_digest
    names={id(p):name for name,p in net.named_parameters()}
    data=copy.deepcopy(plain(cache))
    for value in data.values():
        pairs=value['parameter_versions']
        if not all(identity in names and type(version) is int for identity,version in pairs):
            raise ValueError('Projection parameter identity is not owned by installed net')
        value['parameter_versions']=tuple((names[identity],version) for identity,version in pairs)
    return tree_digest(data)


def main():
    source=inspect.getsource(original.main)
    edits=[
        ("'projections':tree_digest(plain(d.core.cache)),",
         "'projections':_e5_canonical(d.core.cache,net), 'raw_projection':tree_digest(plain(d.core.cache)),"),
        ("if k!='fields'", "if k not in ('fields','raw_projection')"),
        ("records.append(record);return record",
         "(args.output/(label+'.record.json')).write_text(json.dumps(record,indent=2)+'\\n')\n        records.append(record);return record")]
    expected=[1,2,1]
    for (old,new),count in zip(edits,expected):
        if source.count(old)!=count:raise ValueError('R1 fixture repair site changed')
        source=source.replace(old,new)
    inverse=source
    for old,new in reversed(edits):inverse=inverse.replace(new,old)
    if inverse!=inspect.getsource(original.main):raise ValueError('R2 changed R1 outside parameter-ID comparison/recording')
    node=ast.parse(source);namespace=dict(vars(original),_e5_canonical=canonical_projection)
    exec(compile(node,__file__+'#R1_unchanged_method_and_scope','exec'),namespace)
    namespace['main']()


if __name__=='__main__':main()
