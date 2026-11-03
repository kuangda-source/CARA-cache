"""Bounded RPC over the already configured two-card/central-bookkeeping route.

This transports explicit operator source and input, never credentials in argv.
Four-card calls are restricted by their caller to central ledger bookkeeping.
"""
import base64,gzip,json,shlex,subprocess,time
from pathlib import Path
from cara_two_card_transport_r1 import password

ROOT=Path(__file__).resolve().parents[1]
BOOT="import base64,gzip,json,sys;packet=json.loads(gzip.decompress(base64.b64decode(sys.stdin.read().splitlines()[-1])));exec(compile(packet['operator'],'<F19-CAL35-scoped-operator>','exec'))"


def rpc(operator,data,*,host='two_card',timeout=55,route='ipv4'):
    assert host in ('two_card','four_card')
    assert route in ('ipv4','v6')
    prefix='.sync/cara-f19-capture-ssh-ipv4.json' if route=='ipv4' else '.sync/cara-C1-capture-ssh-v6.json'
    argv=json.loads((ROOT/prefix).read_text())
    argv[1:1]=['-C','-o','ControlMaster=auto','-o','ControlPersist=300','-o','ControlPath=/tmp/cara-f19-CAL35-%C.sock']
    argv[-1]=host+'_lan'
    secret=password()
    packet=dict(operator=operator,arguments=data,sudo_password=secret)
    encoded=base64.b64encode(gzip.compress(json.dumps(packet).encode())).decode()
    command="python3 -c "+shlex.quote(BOOT)
    if host=='two_card':command="sudo -S -p '' -u gaokuangda -g docker "+command
    try:
        run=subprocess.run(argv+[command],input=secret+'\n'+encoded+'\n',capture_output=True,text=True,timeout=timeout)
    except subprocess.TimeoutExpired:
        return dict(status='TRANSPORT_TIMEOUT_ORIGINAL_STATE_MUST_BE_RECOVERED',host=host,observed_unix=time.time())
    if run.returncode:
        return dict(status='TRANSPORT_OR_OPERATOR_ERROR',exit_code=run.returncode,
            stderr=run.stderr.replace(secret,'[REDACTED]')[-3500:],host=host,observed_unix=time.time())
    return json.loads(run.stdout)
