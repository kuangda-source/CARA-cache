"""One streaming reference-fidelity implementation, prospectively versioned.

All calculations run on CPU; geometry/PTS/hash failures are retained as failures.
No model downloads, implicit resizing, clipping, frame trimming or GPU work.
"""
import hashlib
import itertools
import math
from pathlib import Path


class Fidelity:
    def __init__(self, alex, *, expected_frames=93):
        self.alex = alex
        self.expected_frames = expected_frames
        self.sse = 0.; self.elements = 0; self.temporal_sum = 0.; self.temporal_elements = 0
        self.gradient_sum = 0.; self.gradient_elements = 0
        self.energy_candidate = 0.; self.energy_reference = 0.
        self.previous_error = None; self.shape = None; self.alex_frames = []; self.ssim_frames = []

    def add(self, candidate, reference):
        import torch
        import piq
        x, n = candidate, reference
        if (x.device.type != 'cpu' or n.device.type != 'cpu' or x.shape != n.shape
                or x.ndim != 4 or x.shape[:2] != (1,3) or min(x.shape[-2:]) < 11
                or not x.is_floating_point() or not n.is_floating_point()
                or not bool(torch.isfinite(x).all() and torch.isfinite(n).all())
                or float(min(x.min(), n.min())) < 0 or float(max(x.max(), n.max())) > 1
                or len(self.alex_frames) >= self.expected_frames):
            raise ValueError('One finite same-geometry CPU RGB frame in [0,1] required')
        if self.shape is not None and self.shape != tuple(x.shape):
            raise ValueError('Frame geometry changed')
        self.shape = tuple(x.shape)
        with torch.inference_mode():
            e = x.double()-n.double()
            self.sse += float(e.square().sum()); self.elements += e.numel()
            if self.previous_error is not None:
                self.temporal_sum += float((e-self.previous_error).abs().sum())
                self.temporal_elements += e.numel()
            self.previous_error = e
            for dim in (-2,-1):
                gx, gn = x.double().diff(dim=dim), n.double().diff(dim=dim)
                self.gradient_sum += float((gx-gn).abs().sum()); self.gradient_elements += gx.numel()
                self.energy_candidate += float(gx.square().sum()); self.energy_reference += float(gn.square().sum())
            alex = float(self.alex(x.float()*2-1,n.float()*2-1).reshape(-1).mean())
            ssim = float(piq.ssim(x.float(),n.float(),kernel_size=11,kernel_sigma=1.5,
                data_range=1.,reduction='none',full=False,k1=.01,k2=.03,downsample=False).reshape(-1).mean())
        if not math.isfinite(alex) or not math.isfinite(ssim):
            raise ValueError('Nonfinite Alex/SSIM score')
        self.alex_frames.append(alex); self.ssim_frames.append(ssim)

    def finish(self):
        if len(self.alex_frames) != self.expected_frames or not self.elements:
            raise ValueError('Full registered frame denominator required')
        mse = self.sse/self.elements
        qindex = math.ceil(.95*(len(self.alex_frames)-1))
        worst = max(self.alex_frames)
        return dict(frames=len(self.alex_frames),MSE_video=mse,
            PSNR_video_dB=10*math.log10(1/mse) if mse else '+inf',
            PSNR_is_infinite=(mse==0),SSIM=sum(self.ssim_frames)/len(self.ssim_frames),
            Alex=sum(self.alex_frames)/len(self.alex_frames),Alex_frames=self.alex_frames,
            Alex_q95_higher=sorted(self.alex_frames)[qindex],Alex_worst=worst,
            Alex_first_worst_frame_zero_based=self.alex_frames.index(worst),
            SSIM_frames=self.ssim_frames,
            reference_temporal_L1=self.temporal_sum/self.temporal_elements if self.temporal_elements else None,
            temporal_frame_pairs=max(0,len(self.alex_frames)-1),
            reference_gradient_L1=self.gradient_sum/self.gradient_elements,
            gradient_energy_ratio=self.energy_candidate/self.energy_reference if self.energy_reference else None,
            gradient_ratio_status='FINITE' if self.energy_reference else 'ZERO_REFERENCE_ENERGY',
            candidate_gradient_energy=self.energy_candidate/self.gradient_elements,
            reference_gradient_energy=self.energy_reference/self.gradient_elements)


def file_sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda:handle.read(4*1024*1024), b''):
            value.update(chunk)
    return value.hexdigest()


def score_video_pair(candidate, reference, alex, *, expected_shape=(93,432,768,3), fps=16):
    """Descriptors contain frozen path+SHA; decode at original geometry/PTS."""
    import av
    import numpy as np
    import torch
    inputs = [candidate,reference]
    for item in inputs:
        if file_sha(item['path']) != item['sha256']:
            raise ValueError('Frozen input video SHA differs')
    metric = Fidelity(alex,expected_frames=expected_shape[0]); stream_sha=[hashlib.sha256(),hashlib.sha256()]
    with av.open(candidate['path']) as ca, av.open(reference['path']) as na:
        for con in (ca,na):
            stream=con.streams.video[0]
            if stream.average_rate != fps or (stream.height,stream.width,3) != expected_shape[1:]:
                raise ValueError('Frozen fps/geometry differs; no resampling permitted')
        previous_pts=None
        for i,pair in enumerate(itertools.zip_longest(ca.decode(video=0),na.decode(video=0))):
            if None in pair or i >= expected_shape[0]:
                raise ValueError('Frame counts differ')
            a,b=pair
            if a.pts is None or b.pts is None or a.pts*a.time_base != b.pts*b.time_base:
                raise ValueError('Missing/mismatched original frame PTS')
            current_pts=a.pts*a.time_base
            if previous_pts is not None and current_pts-previous_pts != 1/fps:
                # Fraction equality uses the exact rational 1/fps below.
                from fractions import Fraction
                if current_pts-previous_pts != Fraction(1,fps):
                    raise ValueError('Nonconstant original frame cadence')
            previous_pts=current_pts
            arrays=[f.to_ndarray(format='rgb24') for f in pair]
            if any(v.shape != expected_shape[1:] or v.dtype != np.uint8 for v in arrays):
                raise ValueError('Decoded RGB24 geometry/dtype differs')
            for h,v in zip(stream_sha,arrays):h.update(v.tobytes())
            metric.add(*(torch.from_numpy(v.copy()).permute(2,0,1).unsqueeze(0).float()/255 for v in arrays))
    for item in inputs:
        if file_sha(item['path']) != item['sha256']:
            raise ValueError('Input changed while scoring')
    return dict(status='COMPLETE',candidate=candidate,reference=reference,PTS_equal=True,
                decoded_RGB_sha256=[h.hexdigest() for h in stream_sha],**metric.finish())
