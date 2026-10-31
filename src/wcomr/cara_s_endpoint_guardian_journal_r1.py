"""Durable allocation attempts and one original guardian bill.

This record writer grants no dispatch or scientific authority. The production
caller must supply admitted bindings and original container observations.
"""
import copy
import hashlib
import json
from pathlib import Path
import time

from .cara_s_endpoint_lifecycle_r1 import IDENTITY
from .cara_budget_original_handles_r1 import ROLES
from .cara_budget_search_journal_r1 import create_record
from .gpu_budget_pool_v2 import atomic_json, finite, sha
from .history104_storage_r2 import KEYS,SLOT_BYTES
from .policy_price_terminal_r1 import require

SOURCE='src/wcomr/cara_s_endpoint_guardian_journal_r1.py'
ATTEMPTS=('mode_lock_attempted','device_lease_attempted','mode_change_attempted','container_dispatch_attempted')


def encoded_sha(value):
    return hashlib.sha256((json.dumps(value,indent=2,allow_nan=False)+'\n').encode()).hexdigest()


class GuardianJournal:
    def __init__(self,stage,launch,registration,storage,*,cpu_validation=False,
                 monotonic=time.monotonic,wall=time.time,writer=atomic_json):
        self.stage=Path(stage);self.launch=copy.deepcopy(launch);self.storage=storage
        self.monotonic=monotonic;self.wall=wall;self.writer=writer;self.finished=False;self.failed=False
        require(launch['CPU_fixture_only'] is cpu_validation,'CPU fixture cannot record a production allocation')
        require(launch['stage']==str(self.stage) and registration['stage']==str(self.stage)
                and registration['payload_sha256'][SOURCE]==sha(__file__)
                and encoded_sha(registration)==launch['registration_sha256'],
                'Original stage and source-bound guardian writer required')
        require(finite(launch['billed_limit_GPUh']) and launch['billed_limit_GPUh']>0,'Whole allocation limit required')
        # Existing or corrupt control bytes cannot be treated as a fresh run.
        with storage.journal.path.open('rb') as stream:
            for key in ('guardian','billing'):
                stream.seek(KEYS.index(key)*2*SLOT_BYTES)
                for _ in (0,1):
                    require(stream.read(SLOT_BYTES)==bytes(SLOT_BYTES),'Original guardian journal exists; recover only')
        require(not any((self.stage/name).exists() for name in ('guardian.json','billing.json')),
                'Original guardian files exist; recover only')
        create_record(self.stage/'guardian-intent.json',dict(launch_sha256=encoded_sha(launch),
            guardian_identity=launch['guardian_identity'],source_sha256=sha(__file__),authorizes_replay=False))
        start=monotonic();require(finite(start) and start>=0,'Monotonic allocation start required')
        self.state={k:launch[k] for k in IDENTITY}
        self.state.update(status='CARA_ENDPOINT_GUARDIAN_ADMITTING_R1',started_monotonic=start,
            started_unix=wall(),original_handles={r:launch['guardian_identity'] if r=='guardian' else None for r in ROLES},
            allocation_attempts={key:False for key in ATTEMPTS},container_dispatch_state='NOT_ATTEMPTED',
            mode_owner_fenced=False,GPU_mode_change_attempted=False,CPU_fixture_only=cpu_validation)
        self.save()

    def save(self):
        self.storage.persist('guardian',self.stage/'guardian.json',self.state,self.writer)

    def remaining_seconds(self,release_margin):
        require(finite(release_margin) and 0<release_margin<self.launch['billed_limit_GPUh']*3600,
                'Bounded release margin required')
        remaining=self.launch['billed_limit_GPUh']*3600-release_margin-(self.monotonic()-self.state['started_monotonic'])
        if remaining<=0:raise TimeoutError('Original allocation reached its release margin; no new work')
        return remaining

    def operation(self,attempt,action):
        """A failed durable write never invokes the allocation action."""
        require(not self.finished and not self.failed and attempt in ATTEMPTS and self.state['allocation_attempts'][attempt] is False,
                'Each original allocation operation may be attempted only once')
        self.state['allocation_attempts'][attempt]=True
        if attempt=='mode_change_attempted':self.state['GPU_mode_change_attempted']=True
        if attempt=='container_dispatch_attempted':self.state['container_dispatch_state']='ATTEMPTED'
        try:
            self.save()
            result=action()
            if attempt=='mode_lock_attempted':self.state['mode_owner_fenced']=True
            if attempt=='container_dispatch_attempted':self.state['container_dispatch_state']='STARTED'
            self.save()
            return result
        except BaseException as error:
            self.failed=True
            self.state.update(error_type=type(error).__name__,error=str(error))
            raise

    def bind_child(self,role,identity):
        require(not self.finished and role in ROLES[1:] and self.state['original_handles'][role] is None,
                'Bind each original child once')
        require(identity['host_view']==self.launch['guardian_identity']['host_view']
                and type(identity['pid']) is int and identity['pid']>0
                and type(identity['start_ticks']) is int and identity['start_ticks']>0
                and all(h is None or (h['pid'],h['start_ticks'])!=(identity['pid'],identity['start_ticks'])
                        for h in self.state['original_handles'].values()),'Distinct original host-view child required')
        self.state['original_handles'][role]=copy.deepcopy(identity);self.save()

    def finish(self,*,container_terminal_witness,mode_restoration,container_exit_code=None,error=None):
        require(not self.finished,'Original terminal bill already recorded; recover only')
        self.finished=True
        if error is not None:self.state.update(error_type=type(error).__name__,error=str(error))
        self.state.update(container_terminal_witness=copy.deepcopy(container_terminal_witness),
            mode_restoration=copy.deepcopy(mode_restoration),container_exit_code=container_exit_code)
        attempts=self.state['allocation_attempts']
        if not any(attempts.values()):
            require(bool(self.state.get('error_type')) and container_terminal_witness.get('kind')=='NO_CONTAINER_DISPATCH'
                    and all(self.state['original_handles'][r] is None for r in ROLES[1:]),
                    'Never-attempted allocation needs an original failure and no children')
            self.state['allocation_never_attempted_witness']=copy.deepcopy(attempts)
        end=self.monotonic();start=self.state['started_monotonic']
        require(finite(end) and end>start,'Complete positive original monotonic interval required')
        bill={k:self.launch[k] for k in IDENTITY}
        bill.update(status='CARA_ENDPOINT_ORIGINAL_WALL_BILL_R1',started_monotonic=start,ended_monotonic=end,
            wall_seconds=end-start,actual_GPUh=(end-start)/3600,ended_unix=self.wall(),
            billing_clock_owner='HOST_GUARDIAN',wall_interval_complete=container_terminal_witness.get('complete') is True,
            central_settlement_pending=True,CPU_fixture_only=self.launch['CPU_fixture_only'])
        # FixedJournal sorts JSON keys; use that same order for the bound bill
        # so restoring its mirror reproduces the exact originally hashed bytes.
        bill=json.loads(json.dumps(bill,sort_keys=True,allow_nan=False))
        self.state.update(status='CARA_ENDPOINT_GUARDIAN_TERMINAL_R1',ended_monotonic=end,
            ended_unix=bill['ended_unix'],billing_sha256=encoded_sha(bill))
        # Complete both independent records before either best-effort mirror.
        # If any journal write fails, there is no complete accepted closure.
        self.storage.journal.write('billing',bill)
        self.storage.journal.write('guardian',self.state)
        self.writer(self.stage/'billing.json',bill)
        self.writer(self.stage/'guardian.json',self.state)
        return copy.deepcopy(bill)


def recover_terminal_mirrors(stage,launch,storage,*,writer=atomic_json):
    """Restore the same closed bill from the independent journal; never remeasure."""
    stage=Path(stage);guardian=storage.journal.read('guardian');bill=storage.journal.read('billing')
    require(launch['stage']==str(stage) and guardian['status']=='CARA_ENDPOINT_GUARDIAN_TERMINAL_R1'
            and all(row[k]==launch[k] for row in (guardian,bill) for k in IDENTITY)
            and guardian['original_handles']['guardian']==launch['guardian_identity']
            and guardian['billing_sha256']==encoded_sha(bill)
            and guardian['started_monotonic']==bill['started_monotonic']
            and guardian['ended_monotonic']==bill['ended_monotonic'],
            'Recover only the paired original terminal journal records')
    for name,value in (('billing.json',bill),('guardian.json',guardian)):
        path=stage/name
        if path.exists():
            existing=json.loads(path.read_text())
            if name=='guardian.json' and existing.get('status')!='CARA_ENDPOINT_GUARDIAN_TERMINAL_R1':
                require(all(existing[k]==launch[k] for k in IDENTITY)
                        and existing['original_handles']['guardian']==launch['guardian_identity']
                        and existing['started_monotonic']==guardian['started_monotonic'],
                        'Existing guardian mirror belongs to another allocation')
            else:require(existing==value,'Existing terminal mirror differs; preserve it')
        writer(path,value)
    return dict(status='ORIGINAL_TERMINAL_MIRRORS_RECOVERED',billing_sha256=encoded_sha(bill),
                remeasured=False,GPU_submissions=0,ledger_written=False)
