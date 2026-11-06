import argparse,json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from wcomr.same_state_summary import summarize
p=argparse.ArgumentParser()
p.add_argument('--receipt',type=Path,required=True)
p.add_argument('--supervisor',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
result=summarize(json.loads(a.receipt.read_text()),json.loads(a.supervisor.read_text()))
result['inputs']={'receipt':str(a.receipt),'supervisor':str(a.supervisor)}
a.output.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['status','candidate_screen_signals','candidates','supervised_gpu_hours']},indent=2))
