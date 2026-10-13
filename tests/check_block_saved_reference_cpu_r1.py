"""CPU synthetic artifact loader controls; actual four B files are read separately."""
import copy
import hashlib
from pathlib import Path
import torch
from wcomr.block_saved_reference_r1 import load_reference
from wcomr.mid_coverage import tree_digest


def run(root):
    root=Path(root);data=root/'outputs/wc-fb-probe-full432-r1/0_DIAGNOSTIC/point-21.pt'
    data.parent.mkdir(parents=True);data.write_bytes(b'EXPLICIT_SYNTHETIC_LOADER_FIXTURE_NOT_MODEL_WEIGHTS')
    shape=(1,16,24,54,96);c=torch.zeros(shape);u=torch.ones(shape)
    payload={mode+'_repeat'+str(n):(c,u) for mode in ('DENSE_PLAIN','L2') for n in range(4)}
    point=dict(scene='FIXTURE',step=21,input_sha256='input',source_state_sha256='work',true_D_state_sha256='D',
        artifact=dict(path=str(data),bytes=data.stat().st_size,sha256=hashlib.sha256(data.read_bytes()).hexdigest(),tensor_sha256=tree_digest(payload)))
    def loader(path,**kwargs):
        assert Path(path).resolve()==data.resolve() and kwargs=={'map_location':'cpu','weights_only':True}
        return payload
    def refused(p):
        try:load_reference(p,root,tensor_loader=loader)
        except ValueError:return
        raise AssertionError('Changed saved-reference artifact accepted')
    value=load_reference(point,root,tensor_loader=loader);assert value['raw_pair_repeats_verified']
    bad=copy.deepcopy(point);bad['artifact']['path']=str(root/'outside.pt');refused(bad)
    bad=copy.deepcopy(point);bad['artifact']['sha256']='0'*64;refused(bad)
    bad=copy.deepcopy(point);bad['artifact']['bytes']+=1;refused(bad)
    bad=copy.deepcopy(point);bad['artifact']['tensor_sha256']='0'*64;refused(bad)
    payload['L2_repeat1']=(c.to(torch.float16),u.to(torch.float16))
    bad=copy.deepcopy(point);bad['artifact']['tensor_sha256']=tree_digest(payload);refused(bad)
    payload['L2_repeat1']=(c,u)
    payload['L2_repeat0']=(torch.zeros((1,16,1,1,1)),torch.zeros((1,16,1,1,1)))
    bad=copy.deepcopy(point);bad['artifact']['tensor_sha256']=tree_digest(payload);refused(bad)
    return dict(status='CPU_SAVED_REFERENCE_PATH_SHA_SIZE_TREE_DTYPE_SHAPE_REFUSALS_PASS',
        synthetic_only=True,GPU_submissions=0,CUDA_initialized=False,
        refused=['outside_path','file_SHA','bytes','tensor_SHA','repeat_dtype','velocity_shape'])
