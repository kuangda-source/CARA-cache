"""Saved source-parent kinds, without network, dispatch or filesystem mutation."""
import copy
import unittest

from cara_source_lifecycle_p0_cpu_chunk_transport_r1 import require_ended_source_parent


class SourceParentTests(unittest.TestCase):
    def host(self):
        identity=dict(pid=123,start_ticks=456)
        return dict(launch=dict(identity=identity,parent_Docker_container=False,CPU_fixture_only=True),
            host_terminal=dict(identity=identity,error=None),original_host_observation=dict(original_live=False),
            CPU_proof=dict(CPU_fixture_only=True))

    def test_original_container_default_is_preserved(self):
        require_ended_source_parent(dict(container_state=dict(Pid=0,Running=False)))

    def test_active_container_cannot_supply_an_ended_parent(self):
        with self.assertRaises(AssertionError):require_ended_source_parent(dict(container_state=dict(Pid=42,Running=True)))

    def test_explicit_ended_bounded_host_CPU_is_accepted_as_source_only(self):
        require_ended_source_parent(self.host(),host_parent=True)

    def test_unknown_failed_or_non_CPU_host_refuses(self):
        for mode in ('unknown','live','failed','missing-proof','production'):
            entry=self.host()
            if mode=='unknown':entry['original_host_observation']['original_live']=None
            if mode=='live':entry['original_host_observation']['original_live']=True
            if mode=='failed':entry['host_terminal']['error']={'type':'RuntimeError'}
            if mode=='missing-proof':entry['CPU_proof']=None
            if mode=='production':entry['launch']['CPU_fixture_only']=False
            with self.subTest(mode=mode),self.assertRaises(AssertionError):require_ended_source_parent(entry,host_parent=True)

    def test_other_original_process_cannot_supply_host_source(self):
        entry=self.host();entry['host_terminal']['identity']=dict(pid=123,start_ticks=789)
        with self.assertRaises(AssertionError):require_ended_source_parent(entry,host_parent=True)


if __name__=='__main__':unittest.main()
