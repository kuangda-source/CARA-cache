"""Calibration artifact accounting; physical filesystem quota is admitted separately."""
from dataclasses import asdict, dataclass
from pathlib import Path
import stat

from .cara_budget_rgb_objective_r1 import file_sha


@dataclass(frozen=True)
class StorageLimits:
    volume_bytes: int
    generation_bytes_per_path: int
    identity_bytes_per_path: int
    RGB_bytes_per_path: int
    temporary_bytes: int
    reserved_other_bytes: int

    def __post_init__(self):
        if any(type(v) is not int or v<=0 for v in asdict(self).values()):
            raise ValueError('Explicit positive integer storage limits required')
        if self.next_request_bytes+self.reserved_other_bytes>=self.volume_bytes:
            raise ValueError('Storage limit cannot admit even one complete request')

    @property
    def next_request_bytes(self):
        return self.generation_bytes_per_path+self.identity_bytes_per_path+self.RGB_bytes_per_path+self.temporary_bytes


def tree_usage(root):
    """Count incomplete files too; links and special files cannot escape the budget."""
    root=Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Original regular artifact directory required')
    files={};used=0
    for path in [root,*root.rglob('*')]:
        info=path.lstat()
        if not (stat.S_ISREG(info.st_mode) or stat.S_ISDIR(info.st_mode)):
            raise ValueError('Artifact tree contains a link or special file: '+str(path))
        if stat.S_ISREG(info.st_mode):
            if info.st_nlink!=1:raise ValueError('Artifact files must not share storage through hard links')
            files[str(path.relative_to(root))]=info.st_size
            used+=max(info.st_size,info.st_blocks*512)
        else:
            used+=info.st_blocks*512
    return used,files


def check_scope(root,limits,*,reserve_next=False):
    used,_=tree_usage(root)
    reserved=limits.reserved_other_bytes+(limits.next_request_bytes if reserve_next else 0)
    if used+reserved>limits.volume_bytes:
        raise ValueError('Calibration storage allowance exhausted; retain original files and stop')
    return dict(observed_artifact_bytes=used,reserved_bytes=reserved,volume_limit_bytes=limits.volume_bytes,
                physical_filesystem_quota_verified=False)


def generation_snapshot(path,limits):
    used,files=tree_usage(path)
    if used>limits.generation_bytes_per_path:
        raise ValueError('Original generation payload exceeds its registered per-path allowance')
    return dict(accounted_bytes=used,files={name:dict(bytes=size,sha256=file_sha(Path(path)/name))
                                         for name,size in sorted(files.items())})


def check_path_metadata(path,limits):
    _,files=tree_usage(path)
    size=sum(v for name,v in files.items() if not name.startswith(('generation/','endpoint/')))
    if size>limits.identity_bytes_per_path:
        raise ValueError('Original physical identity/result metadata exceeds its allowance')
