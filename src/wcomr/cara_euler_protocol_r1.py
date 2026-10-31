"""Explicit Euler protocol prototype; never installed into existing UniPC runs."""
import math
import struct

def f32(x):
    return struct.unpack('<f',struct.pack('<f',x))[0]

def reconstructed_grid(updates=35):
    """Declared Karras-rho7 reconstruction, not the paper's unspecified grid."""
    if updates < 2:raise ValueError('At least two evaluation sigmas required')
    hi,lo=200**(1/7),0.01**(1/7)
    raw=[(hi+i/(updates-1)*(lo-hi))**7 for i in range(updates)]
    transformed=[x/(1+x) for x in raw]
    return dict(sigmas=[f32(x) for x in transformed]+[0.0],
                timesteps=[int(x*1000) for x in transformed],updates=updates,CFG_calls=2*updates)

class ExplicitEuler:
    """Consume the scheduler-facing flow velocity, dx/dsigma, without a sign flip."""
    def __init__(self,grid):
        sigmas,times=grid['sigmas'],grid['timesteps']
        if not(len(sigmas)==len(times)+1 and sigmas[-1]==0 and
               all(math.isfinite(x) for x in sigmas) and
               all(a>b for a,b in zip(sigmas,sigmas[1:]))):
            raise ValueError('Strict descending explicit sigmas ending at zero required')
        self.sigmas=tuple(sigmas);self.timesteps=tuple(times);self.index=0
    def step(self,velocity,timestep,sample):
        if self.index>=len(self.timesteps) or timestep!=self.timesteps[self.index]:
            raise ValueError('Out-of-order or repeated Euler update')
        i=self.index;self.index+=1
        return sample+(self.sigmas[i+1]-self.sigmas[i])*velocity

def noise_coordinates(sigmas):
    values=[math.log(s/(1-s)) for s in sigmas[:-1]]
    width=values[0]-values[-1]
    return [(values[0]-x)/width for x in values]

def remap_dense(old_sigmas,new_sigmas,dense,early_protected=7):
    """Minimum squared log-SNR-coordinate matching, injective and order preserving.

    A prototype remapping rule only. It does not select a scientific method or
    infer quality. Preserve early dense anchors and final dense update explicitly.
    """
    source,target=noise_coordinates(old_sigmas),noise_coordinates(new_sigmas)
    dense=sorted(dense);n=len(target)
    if dense[:early_protected]!=list(range(1,early_protected+1)) or dense[-1]!=len(source) or len(dense)>n:
        raise ValueError('Protected source anchors or target capacity differ')
    states={0:(0.0,[])}
    for k,old in enumerate(dense):
        next_states={}
        candidates=([k+1] if k<early_protected else [n] if k==len(dense)-1 else range(early_protected+1,n))
        for j in candidates:
            feasible=[(cost+(source[old-1]-target[j-1])**2,path+[j])
                      for prev,(cost,path) in states.items() if prev<j]
            if feasible:next_states[j]=min(feasible,key=lambda v:(v[0],v[1]))
        states=next_states
    if n not in states:raise ValueError('No legal injective noise-coordinate mapping')
    return states[n][1]
