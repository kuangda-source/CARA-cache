"""Explicit metadata-only complete P1 fixture; never a real authorization."""
import copy
import json
from pathlib import Path
import time

import test_cara_source_lifecycle_p1_entry_r1 as entry
from wcomr import cara_source_lifecycle_p1_dispatch_r1 as dispatch
from wcomr import cara_source_lifecycle_p1_central_r1 as central
from wcomr.cara_budget_host_policy_r1 import POLICY_SHA256
from wcomr.gpu_budget_pool_v2 import SCHEMA,atomic_json,sha
from wcomr.wc73_execution_r1 import Pool

ROOT=Path(__file__).resolve().parents[1]


class Fixture(entry.Fixture):
    def __init__(self,root):
        super().__init__(root)
        for name in dispatch.REQUIRED:
            path=self.stage/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/name).read_bytes())
            self.reg['payload_sha256'][name]=sha(path)
        self.environment=dict(torch_home=str(self.project/'offline/torch'),piq_site=str(self.project/'offline/site'),
            weights_sha256={str(self.project/'offline/torch/hub/checkpoints/alexnet-owt-7be5be79.pth'):
                '7be5be791159472b1fbf3c69796f7cb30dca7ad8466c2df70058c37116cdee02',
                str(self.project/'offline/lpips/weights/v0.1/alex.pth'):'df73285e35b22355a2df87cdb6b70b343713b667eddbda73e1977e0c860835c0'})
        atomic_json(self.stage/dispatch.ENVIRONMENT,self.environment)
        self.authority.update(central_transaction_authorized=True,central_user_quote='EXPLICIT_CPU_METADATA_ONLY_NOT_USER_PERMISSION',
            central_exception_run_id=self.authority['run_id'],standing_cap_increment24_authorized=True,
            FIT_environment_sha256=sha(self.stage/dispatch.ENVIRONMENT))
        self.storage.config.update(output_mount=str(self.output),journal_path=str(self.stage/'CPU-journal'),
            image_path=str(self.stage/'CPU-private.ext4'))
        from types import SimpleNamespace
        self.storage.journal=SimpleNamespace(path=self.stage/'CPU-journal')
        (self.project/'.sync/gpu-locks').mkdir(exist_ok=True)
        self.write()
        self.pool=Pool(self.project);self.pool.path.parent.mkdir(parents=True,exist_ok=True)
        holds={}
        for i,cost in enumerate((4.5,12.)):
            holds['CPU-old-hold-'+str(i)]=dict(kind='UNCONFIRMED_RETIRED_HOST_WHOLE_CARD_LIABILITY_HOLD',
                confirmed_GPU_submission=False,actual_cost_unknown=True,launch_id='NOT_A_CONFIRMED_GPU_SUBMISSION',
                supervisor_pid=None,supervisor_start_ticks=None,status='RESERVED_OR_RUNNING',
                billed_limit_GPUh=cost,gpu_uuid=self.authority['gpu_uuid'])
        ledger=dict(schema=SCHEMA,cap_gpu_hours=226.,origin_used_gpu_hours=197.,origin_gpu_jobs_launched=10,jobs=holds,events=[])
        ledger.update(Pool.accounting(ledger));atomic_json(self.pool.path,ledger)
        (self.project/'reports').mkdir(exist_ok=True)

    def admission(self):
        now=time.time()
        return dict(status='P1_COMPLETE_FRESH_ADMISSION_NO_GPU',authorization=copy.deepcopy(self.authority),
            authorization_raw_utf8=(self.stage/'GPU-authorization.json').read_text(),
            authorization_sha256=sha(self.stage/'GPU-authorization.json'),registration_sha256=sha(self.stage/'registration.json'),
            central_operator_sha256=sha(ROOT/central.SOURCE),required_host_whole_card_CPU_accepted=True,
            required_hosts=['two_card'],execution_host_policy_sha256=POLICY_SHA256,
            semantic_positions=146,physical_generation_upper=142,physical_model_pairs_upper=5176,
            postrelease_new_pairs_upper=32,observed_unix=now,forecast_GPUh=self.quote['forecast_GPUh'],
            resources=dict(gpu=dict(uuid=self.authority['gpu_uuid'],name='NVIDIA RTX A6000',compute_cap='8.6',
                utilization_percent=0,pids=[],memory_used_mib=344,temperature_C=55,compute_mode='Default',unix=now)))

    def absence(self):
        return {'two_card':dict(host='two_card',stage=str(self.stage),run_id=self.authority['run_id'],
            observation_complete=True,observed_unix=time.time(),dispatch_records=[],container=None)}

    def reserved(self):
        envelope=central.reserve(self.project,self.admission(),self.absence())
        atomic_json(self.stage/'central-reservation.json',envelope)
        return envelope,dict(central_ledger_host='four_card',observed_unix=time.time(),ledger=self.pool.read())
