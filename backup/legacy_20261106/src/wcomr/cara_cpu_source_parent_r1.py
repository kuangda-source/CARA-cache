"""Validate saved ended CPU source parents without importing transport clients."""


def require_ended_source_parent(entry,*,host_parent=False):
    if host_parent:
        launch,terminal=entry['launch'],entry['host_terminal']
        assert launch['parent_Docker_container'] is False and launch['CPU_fixture_only'] is True
        assert entry['original_host_observation']['original_live'] is False
        assert terminal['identity']==launch['identity'] and terminal['error'] is None
        assert entry['CPU_proof'] is not None and entry['CPU_proof']['CPU_fixture_only'] is True
    else:
        assert entry['container_state']['Pid']==0 and not entry['container_state']['Running']
