"""The complete S CPU paths with the actual bounded streaming artifact store."""
from pathlib import Path

from wcomr.sq_s_storage_r1 import SCollectionStore


def run(runtime,artifact_root,tiny_tensor_loader):
    import check_cara_pg_production_sampling_cpu_r1 as previous
    import check_sq_s_collection_cpu_r1 as topology
    def storage(root,prompts):
        return SCollectionStore(root,prompts=prompts,maximum_total_bytes=16*2**20,
            maximum_file_bytes=8*2**20,minimum_free_bytes=2**20)
    def body(*args,**kwargs):return topology.body(*args,storage_factory=storage,**kwargs)
    original=previous.body;loader=topology._tiny_tensor_loader
    previous.body=body;topology._tiny_tensor_loader=tiny_tensor_loader
    try:return previous.run(Path(runtime),artifact_root)
    finally:previous.body=original;topology._tiny_tensor_loader=loader
