"""Check the full S ownership schema before the original copy-budget call.

The existing numerical collector and sampler stay unchanged. This entry adds
metadata-only refusal; it neither reserves resources nor authorizes a GPU.
"""
import copy
import hashlib
import json

from .clean_speed20_r1 import patched
from .source_aware_phase_sampling import bind_globals
from .sq_s_batch_r1 import Requests, digest, require
from .sq_s_resources_r1 import before_pair_inventory, check_limits

GROUPS={'native','solver','buffers','owner_history','readout_history','calibrators','paired_inputs','conditions'}


class ResourceGuard:
    def __init__(self,contract):
        self.contract=copy.deepcopy(contract)
        require(contract['contract_sha256']==digest({k:v for k,v in contract.items() if k!='contract_sha256'}),
            'S resource contract bytes changed')
        require(contract['schema']=='SQ_S_BEFORE_SNAPSHOT_RESOURCE_CONTRACT_R1'
            and type(contract['CPU_fixture_only']) is bool and set(contract['tensor_schema'])==GROUPS,
            'Complete S resource contract required')

    def check_metadata(self,report,buffer_names):
        c=self.contract;limits=c['limits']
        check_limits(report,limits)
        require(set(report['group_inventories'])==GROUPS
            and report['native_field_names']==c['native_field_names']
            and report['solver_field_names']==c['solver_field_names']
            and list(buffer_names)==c['buffer_names'],'Original S state/buffer fields changed')
        backing=0;groups=report['group_inventories']
        for name,group in groups.items():
            require(not group['any_meta_tensors'] and group['tensor_values_read'] is False
                and group['tensor_copies_performed']==0,'Only actual metadata inventory is admissible')
            registry=c['tensor_schema'][name]
            for row in group['tensors']:
                expected=registry.get(row['path'])
                require(expected is not None and row['shape']==expected['shape']
                    and row['dtype'] in expected['dtypes'] and row['requires_grad'] is False,
                    'Unknown or changed S tensor schema: '+name+' '+row['path'])
            # Snapshots own groups separately. Do not deduplicate an allocation
            # across group boundaries when bounding deep-copy storage work.
            backing+=sum(group['backing_storage_bytes_by_device'].values())+group['numpy_backing_bytes']
        require(report['numpy_backing_bytes']<=limits['numpy_backing_bytes'],
            'Unregistered S NumPy backing storage')
        require(8*backing<=limits['backing_copy_guard_bytes'],
            'S full backing-storage copy cap exceeded before snapshots')
        raw=json.dumps(report,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
        return dict(contract_sha256=c['contract_sha256'],inventory_sha256=hashlib.sha256(raw).hexdigest(),
            original_logical_copy_guard_bytes=report['logical_copy_guard_bytes'],
            full_backing_copy_guard_bytes=8*backing,mutable_buffer_bytes=groups['buffers']['logical_tensor_bytes'],
            live_backing_storage_bytes_by_device=dict(report['backing_storage_bytes_by_device']),
            all_eight_groups_checked=True,unknown_tensor_fields_refused=True,
            tensor_values_read=False,tensor_copies_performed=0,GPU_admission=False)

    def before_pair(self,owner,inputs):
        return self.check_metadata(before_pair_inventory(owner,inputs),
            [name for name,_ in owner.net.named_buffers()])


def checked_collector(original,guard,record):
    class CheckedCollector(original):
        def copy_budget(self,inputs):
            checked=guard.before_pair(self.owner,inputs)
            logical=super().copy_budget(inputs)
            require(logical==checked['original_logical_copy_guard_bytes'],
                'Resource guard changed the original logical counter')
            record(dict(checked,step=self.owner.readout.completed+1))
            return logical
    return CheckedCollector


class ResourceCheckedRequests(Requests):
    """Original complete request, with a scoped pre-snapshot collector guard."""
    def __init__(self,*,resource_contract,resource_observer=None,**kwargs):
        super().__init__(**kwargs)
        self.resource_guard=ResourceGuard(resource_contract)
        require(self.scope['CPU_fixture_only']==resource_contract['CPU_fixture_only']
            and self.copy_cap==resource_contract['limits']['logical_copy_guard_bytes'],
            'CPU/real resource scope or original logical cap differs')
        if not self.cpu_validation:
            require(kwargs['production_context'].get('S_resource_contract_sha256')==resource_contract['contract_sha256'],
                'Separately admitted S context must bind the full resource contract')
        require(resource_observer is None or callable(resource_observer),'Explicit metadata observer required')
        self.resource_observer=resource_observer;self.resource_checks=[]

    def __call__(self,slot,output):
        from . import sq_s_collection_r1 as collection
        original=collection.execute;checks=[]
        def record(value):
            row=dict(value,slot_id=slot['id'],prompt=slot['prompt'],parent=slot['parent'])
            checks.append(row);self.resource_checks.append(row)
            if self.resource_observer:self.resource_observer(copy.deepcopy(row))
        collector=checked_collector(collection.SParentCollector,self.resource_guard,record)
        execute=bind_globals(original,{'SParentCollector':collector})
        with patched(collection,'execute',execute):result=super().__call__(slot,output)
        require(collection.execute is original,'Original S collection entry was not restored')
        from .sq_risk_r1 import TARGETS
        require([r['step'] for r in checks]==(list(TARGETS) if slot['enabled'] else [])
            and all(r['contract_sha256']==self.resource_guard.contract['contract_sha256'] for r in checks),
            'Complete selected-target resource denominator differs')
        return result
