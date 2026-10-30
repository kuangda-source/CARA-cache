"""Exact retained NPY bytes; whole GPU storage admission remains separate."""
import io
import math
import numpy as np


def rgb_storage_plan(*, shape, max_queries, native_teachers, extra_full_rgb_paths,
                     reserved_other_bytes):
    if (not isinstance(shape,(tuple,list)) or len(shape)!=4 or tuple(shape[:2])!=(3,93)
            or any(type(n) is not int or n<=0 for n in shape)):
        raise ValueError('Full three-channel93-frame geometry required')
    for value in (max_queries,native_teachers,extra_full_rgb_paths,reserved_other_bytes):
        if type(value) is not int or value<0:
            raise ValueError('Explicit nonnegative integer storage scope required')
    if max_queries<1 or native_teachers!=2:
        raise ValueError('Full dual-FIT search with two original Native teachers required')
    header=io.BytesIO()
    np.lib.format.write_array_header_1_0(header,dict(descr='<f4',fortran_order=False,shape=tuple(shape)))
    raw_bytes=math.prod(shape)*4
    paths=2*max_queries+native_teachers+extra_full_rgb_paths
    npy_bytes=raw_bytes+header.tell()
    return dict(RGB_shape=list(shape),dtype='<f4',max_queries=max_queries,
        Native_teacher_paths=native_teachers,extra_full_RGB_paths=extra_full_rgb_paths,
        maximum_retained_RGB_paths=paths,raw_bytes_per_path=raw_bytes,
        NPY_header_bytes_per_path=header.tell(),NPY_bytes_per_path=npy_bytes,
        retained_NPY_bytes=paths*npy_bytes,reserved_other_bytes=reserved_other_bytes,
        total_accounted_bytes=paths*npy_bytes+reserved_other_bytes,
        full_GPU_storage_quote=False,physical_storage_admitted=False)
