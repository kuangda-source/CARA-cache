"""Observe retained official guardrails without changing their return values."""
import functools


class GuardrailObservation:
    def __init__(self, owner):
        self.originals = []
        self.reset()
        for attribute, label in [('run_text_guardrail', 'text'), ('run_video_guardrail', 'video')]:
            original = getattr(owner, attribute)
            self.originals.append((owner, attribute, original))
            setattr(owner, attribute, self._wrap(original, label))

    def _wrap(self, original, label):
        @functools.wraps(original)
        def observed(*args, **kwargs):
            result = original(*args, **kwargs)  # exceptions propagate unchanged
            self.events.append({'stage': label, 'accepted': bool(result) if label == 'text' else result is not None})
            return result
        return observed

    def reset(self):
        self.events = []

    def classify(self, paths):
        if self.events == [{'stage': 'text', 'accepted': True}, {'stage': 'video', 'accepted': True}]:
            if len(paths) != 1:
                raise RuntimeError('Accepted guardrails without exactly one video')
            return 'ACCEPTED'
        if not paths and self.events == [{'stage': 'text', 'accepted': False}]:
            return 'TEXT_REJECTED'
        if not paths and self.events == [{'stage': 'text', 'accepted': True}, {'stage': 'video', 'accepted': False}]:
            return 'VIDEO_REJECTED'
        raise RuntimeError('Unexplained output/guardrail mismatch')

    def close(self):
        for owner, attribute, original in reversed(self.originals):
            setattr(owner, attribute, original)
