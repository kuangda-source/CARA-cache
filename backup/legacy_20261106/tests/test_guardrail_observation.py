from types import SimpleNamespace
import pytest
from wcomr.guardrail_observation import GuardrailObservation


def test_video_rejection_then_next_sample_preserves_filter_returns():
    frame = object()
    owner = SimpleNamespace(run_text_guardrail=lambda accepted: accepted,
                            run_video_guardrail=lambda accepted: frame if accepted else None)
    original = owner.run_video_guardrail
    observer = GuardrailObservation(owner)
    assert owner.run_text_guardrail(True) is True
    assert owner.run_video_guardrail(False) is None
    assert observer.classify([]) == 'VIDEO_REJECTED'
    rejected_events = observer.events
    observer.reset()
    assert owner.run_text_guardrail(True) is True
    assert owner.run_video_guardrail(True) is frame
    assert observer.classify(['accepted.mp4']) == 'ACCEPTED'
    assert rejected_events[-1]['accepted'] is False
    observer.close()
    assert owner.run_video_guardrail is original


def test_text_rejection_and_unexplained_missing_output_fail_closed():
    owner = SimpleNamespace(run_text_guardrail=lambda: False, run_video_guardrail=lambda: object())
    observer = GuardrailObservation(owner)
    owner.run_text_guardrail()
    assert observer.classify([]) == 'TEXT_REJECTED'
    with pytest.raises(RuntimeError):
        observer.classify(['must-not-exist.mp4'])
    observer.reset()
    with pytest.raises(RuntimeError):
        observer.classify([])
    owner.run_video_guardrail()
    with pytest.raises(RuntimeError):
        observer.classify(['missing-text-check.mp4'])


def test_filter_exception_is_not_reclassified_as_rejection():
    def failed():
        raise ValueError('filter crashed')
    owner = SimpleNamespace(run_text_guardrail=failed, run_video_guardrail=failed)
    observer = GuardrailObservation(owner)
    with pytest.raises(ValueError, match='filter crashed'):
        owner.run_text_guardrail()
    assert observer.events == []
    with pytest.raises(RuntimeError):
        observer.classify([])
