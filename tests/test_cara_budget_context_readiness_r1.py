"""Real Linux child publishes readiness during an already-started GPU sample."""
from pathlib import Path
import time
import unittest

import test_cara_budget_supervisor_r1 as original


@unittest.skipUnless(Path('/proc/self').exists(), 'Actual Linux child identities required')
class ContextReadinessTests(unittest.TestCase):
    def test_sample_started_before_readiness_cannot_be_treated_as_ready(self):
        fixture = original.SupervisorTests()
        self.addCleanup(fixture.doCleanups)
        fixture.setUp()
        marker = fixture.stage/'CPU-observation-started'
        ready = fixture.stage/'pg-runner-context-ready.json'
        child_path = fixture.stage/'CPU-runner.py'
        child = child_path.read_text()
        anchor = "identity={k:process_identity(os.getpid())[k]"
        self.assertEqual(child.count(anchor), 1)
        child_path.write_text(child.replace(anchor, """until=time.monotonic()+5
while not (stage/'CPU-observation-started').exists():
 if time.monotonic()>until:raise TimeoutError('CPU observation did not start')
 time.sleep(.01)
"""+anchor))
        observe = fixture.observe
        late_samples = []

        def sampled_before_readiness(uuid):
            if (fixture.stage/'runner-start.json').exists() and not marker.exists():
                snapshot = observe(uuid)
                self.assertFalse(ready.exists())
                self.assertEqual(snapshot['compute_apps'], [])
                marker.touch()
                deadline = time.monotonic()+5
                while not ready.exists():
                    if time.monotonic()>deadline:
                        raise TimeoutError('Original CPU child did not publish readiness')
                    time.sleep(.01)
                late_samples.append(snapshot)
                return snapshot
            return observe(uuid)

        fixture.observe = sampled_before_readiness
        result = fixture.run_scenario('complete')
        self.assertEqual(len(late_samples), 1)
        self.assertTrue(result['context_granted'])
        self.assertEqual(result['runner_exit_code'], 0)


if __name__ == '__main__':
    unittest.main()
