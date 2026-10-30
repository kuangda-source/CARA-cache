"""Exact CPU-only Docker limits shared by preparation and acceptance."""

HOST_CONFIG = dict(NanoCpus=10**9, Memory=4*2**30, MemorySwap=4*2**30,
                   CpusetCpus='', DeviceRequests=None, NetworkMode='none', ReadonlyRootfs=True)


def bind_cpu_limits(command):
    """Replace inherited CPU limits; never inherit swap or CPU affinity."""
    result = []
    limits = {'--cpus', '--memory', '--memory-swap', '--cpuset-cpus'}
    seen = set()
    index = 0
    while index < len(command):
        value = command[index]
        key = value.split('=', 1)[0]
        if key == '--gpus':
            raise ValueError('CPU worker cannot request GPUs')
        if key in limits:
            if key in seen:
                raise ValueError('Duplicate inherited resource option: ' + key)
            seen.add(key)
            if '=' not in value:
                index += 1
                if index >= len(command) or command[index].startswith('--'):
                    raise ValueError('Missing inherited resource value: ' + key)
        else:
            result.append(value)
        index += 1
    if result[:2] != ['docker', 'run']:
        raise ValueError('Expected original Docker run command')
    return result[:2] + ['--cpus', '1', '--memory', '4g', '--memory-swap', '4g'] + result[2:]
