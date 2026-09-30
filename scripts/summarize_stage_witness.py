"""Compare two terminal, fresh-process pipeline witnesses; no quality claims."""
import argparse
import json
from pathlib import Path
from wcomr.stage_witness import compare_stages

p=argparse.ArgumentParser()
p.add_argument('--left',type=Path,required=True)
p.add_argument('--right',type=Path,required=True)
p.add_argument('--supervisor',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
left,right=[json.loads(path.read_text()) for path in [a.left,a.right]]
s=json.loads(a.supervisor.read_text())
assert s['status']=='STAGE_WITNESS_EXITED_REQUIRES_REVIEW'
assert len(s['arms'])==2 and all(arm['exit_code']==0 and arm['stop_reason'] is None for arm in s['arms'])
assert left['pid']!=right['pid'],'Not fresh processes'
assert sum(arm['wall_seconds'] for arm in s['arms'])<=900,'Aggregate deadline exceeded'
for receipt in [left,right]:
    assert receipt['status']=='STAGE_WITNESS_ACCEPTED_SINGLE_FRESH_PROCESS'
    assert len(receipt['forward_output_sha256'])==72 and len(receipt['decoded_rgb'])==93
assert left['source_sha256']==right['source_sha256']
result=compare_stages(left,right)
result.update(left=str(a.left),right=str(a.right),source_sha256=left['source_sha256'],
              wall_seconds=sum(arm['wall_seconds'] for arm in s['arms']),
              limitation='Two engineering witnesses only; a matching result does not explain the historical differing video. A differing boundary locates an interval, not a cause.')
a.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
