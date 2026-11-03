"""Fresh whole admission -> exact central reservation -> original dispatch once."""
import argparse,json,sys,time
from pathlib import Path
from cara_f19_speed190_control_r1 import CENTRAL,DISPATCH,ROOT,local_python_closure
from cara_f19_speed190_ops_r1 import ADMIT
from cara_f19_speed190_transport_r1 import rpc


def main():
    p=argparse.ArgumentParser();p.add_argument('--receipt',type=Path,required=True);p.add_argument('--route',choices=('ipv4','v6'),default='ipv4');a=p.parse_args()
    assert not a.receipt.exists()
    state=dict(status='FRESH_ADMISSION',started_unix=time.time(),GPU_submissions_by_dispatcher=0)
    def save():
        temp=a.receipt.with_suffix('.tmp');temp.write_text(json.dumps(state,indent=2)+'\n');temp.replace(a.receipt)
    save()
    try:
        admitted=rpc(ADMIT,{},route=a.route);state['admitted']=admitted;save()
        assert admitted.get('status')=='CAL35_FRESH_ADMISSION_NO_GPU',admitted.get('stderr',admitted.get('status'))
        binding=json.loads((ROOT/'.sync/cara-f19-CAL35-original-binding.json').read_text())
        assert binding['authority']==admitted['admission']['authorization']
        source=local_python_closure(ROOT,['src/wcomr/cara_f19_speed190_execution_r1.py'])
        booked=rpc(CENTRAL,dict(action='reserve',authority=binding['authority'],hashes=source,admission=admitted['admission']),host='four_card',route=a.route)
        state['central']=booked;save()
        assert booked.get('status')=='CAL35_CENTRAL_RESERVE',booked.get('stderr',booked.get('status'))
        assert 0<=time.time()-booked['observed_unix']<=30,'Fresh central snapshot needed before original dispatch'
        launch=rpc(DISPATCH,dict(envelope=booked['envelope'],snapshot=dict(ledger=booked['ledger'],observed_unix=booked['observed_unix'])),route=a.route)
        state['dispatch']=launch;save()
        assert launch.get('status')=='ORIGINAL_CAL35_GUARDIAN_DISPATCHED',launch.get('stderr',launch.get('status'))
        state['status']='ORIGINAL_GUARDIAN_DISPATCHED_PENDING_ACTUAL_START'
    except BaseException as error:
        state.update(status='STOPPED_PRESERVE_ORIGINAL_RECEIPTS',error_type=type(error).__name__,error=str(error));raise
    finally:state['ended_unix']=time.time();save();print(json.dumps(dict(status=state['status'],report=str(a.receipt),error=state.get('error'))))


if __name__=='__main__':main()
