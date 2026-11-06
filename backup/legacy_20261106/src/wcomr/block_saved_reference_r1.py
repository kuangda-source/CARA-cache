"""CPU-only loader for previously accepted, strictly bound B point outputs."""
import hashlib
from pathlib import Path
import torch
from .mid_coverage import tree_digest


def load_reference(point, project, *, tensor_loader=torch.load):
    artifact=point['artifact'];root=(Path(project)/'outputs/wc-fb-probe-full432-r1').resolve()
    path=Path(artifact['path']).resolve()
    if (not path.is_relative_to(root) or not path.is_file()
            or path.stat().st_size != artifact['bytes']
            or hashlib.sha256(path.read_bytes()).hexdigest() != artifact['sha256']):
        raise ValueError('Only exact accepted old B raw artifacts may be reused')
    payload=tensor_loader(path,map_location='cpu',weights_only=True)
    if tree_digest(payload) != artifact['tensor_sha256']:
        raise ValueError('Old B tensor payload differs')
    vectors={}
    for label,mode in [('DENSE_VELOCITY','DENSE_PLAIN'),('L2_VELOCITY','L2')]:
        first=payload[mode+'_repeat0']
        if (not isinstance(first,tuple) or len(first)!=2
                or any(not isinstance(v,torch.Tensor) or v.device.type!='cpu'
                       or list(v.shape)!=[1,16,24,54,96] or v.requires_grad
                       or v.dtype not in (torch.float32,torch.float16,torch.bfloat16)
                       or not torch.isfinite(v).all() for v in first)):
            raise ValueError('Full real CPU c/u velocity pair required')
        for repeat in (1,2,3):
            current=payload[mode+'_repeat'+str(repeat)]
            if (not isinstance(current,tuple) or len(current)!=2
                    or any(not isinstance(b,torch.Tensor) or a.dtype!=b.dtype or a.shape!=b.shape
                           or not torch.equal(a,b) for a,b in zip(first,current))):
                raise ValueError('Preserved B repeats no longer equal')
        vectors[label]=tuple(v.clone() for v in first)
    return {k:point[k] for k in ('scene','step','input_sha256','source_state_sha256','true_D_state_sha256')} | dict(
        vectors=vectors,artifact_sha256=artifact['sha256'],
        raw_pair_repeats_verified=True,saved_offline_only_not_online_action=True)
