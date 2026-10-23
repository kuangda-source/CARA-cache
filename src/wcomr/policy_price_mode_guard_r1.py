"""Only an idle selected UUID may change mode; restore only when still idle."""
from .policy_asset_price_review_r1 import exclusive_gate


class ModeGuard:
    def __init__(self, gpu_uuid, query, set_mode, clock):
        self.uuid=gpu_uuid;self.query=query;self.set_mode=set_mode;self.clock=clock
        self.changed=False;self.prior=None;self.enable_attempted=False

    def idle_snapshot(self):
        s=self.query(self.uuid)
        if (s.get('gpu_uuid')!=self.uuid or s.get('compute_apps')!=[] or s.get('mps_processes')!=[]
                or not 0<=self.clock()-s.get('observed_unix',0)<=10):
            raise ValueError('Selected GPU is busy, stale, MPS present, or unknown; no mode change')
        return s

    def acquire(self):
        s=self.idle_snapshot();self.prior=s['compute_mode']
        if self.prior not in ('Default','Exclusive_Process'):
            raise ValueError('Unsupported prior mode; no change')
        if self.prior=='Default':
            # The driver validates this again atomically; no reset or eviction.
            self.enable_attempted=True
            self.set_mode(self.uuid,'EXCLUSIVE_PROCESS');self.changed=True
        s=self.idle_snapshot()
        if not exclusive_gate(s,gpu_uuid=self.uuid,phase='idle',now=self.clock())['observation_passed']:
            raise ValueError('Hardware did not confirm Exclusive_Process')
        return dict(prior_mode=self.prior,changed=self.changed,verified_snapshot=s)

    def restore(self):
        if not self.enable_attempted:
            return dict(status='PRIOR_MODE_UNCHANGED',restored=True,changed=False)
        try:
            s=self.idle_snapshot()
            if s['compute_mode']=='Default':
                return dict(status='ALREADY_PRIOR_MODE',restored=True,changed=False,snapshot=s)
            if s['compute_mode']!='Exclusive_Process':
                raise ValueError('Mode changed externally; retain current mode')
            self.set_mode(self.uuid,'DEFAULT')
            s=self.idle_snapshot()
            if s['compute_mode']!='Default':raise ValueError('Restoration not verified')
            return dict(status='PRIOR_MODE_RESTORED_IDLE',restored=True,changed=True,snapshot=s)
        except Exception as e:
            return dict(status='RESTORE_DEFERRED_NO_FOREIGN_PROCESS_TOUCHED',restored=False,
                changed=False,error_type=type(e).__name__,error=str(e))
