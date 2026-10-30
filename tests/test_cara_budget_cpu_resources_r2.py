import unittest
from wcomr.cara_budget_cpu_resources_r2 import bind_cpu_limits, HOST_CONFIG


class CPUResourceTests(unittest.TestCase):
    def test_inherited_swap_and_affinity_are_replaced(self):
        original=['docker','run','--cpus','2','--memory','8g','--memory-swap','16g',
                  '--cpuset-cpus','26','--network','none','--read-only','image','worker']
        expected=['docker','run','--cpus','1','--memory','4g','--memory-swap','4g',
                  '--network','none','--read-only','image','worker']
        self.assertEqual(bind_cpu_limits(original),expected)
        self.assertEqual(original[3],'2')
        self.assertEqual(bind_cpu_limits(expected),expected)
        self.assertEqual(HOST_CONFIG['Memory'],HOST_CONFIG['MemorySwap'])
        self.assertEqual(HOST_CONFIG['CpusetCpus'],'')

    def test_equals_and_missing_optional_limits(self):
        self.assertEqual(bind_cpu_limits(['docker','run','--memory=8g','--cpuset-cpus=26','image']),
            ['docker','run','--cpus','1','--memory','4g','--memory-swap','4g','image'])
        self.assertEqual(bind_cpu_limits(['docker','run','image'])[-1],'image')

    def test_ambiguous_or_gpu_commands_refused(self):
        for args in (['--memory','4g','--memory=8g'],['--cpus'],['--memory','--network','none'],
                     ['--gpus','all'],['--gpus=all']):
            with self.subTest(args=args),self.assertRaises(ValueError):
                bind_cpu_limits(['docker','run',*args])
        with self.assertRaises(ValueError):bind_cpu_limits(['docker','start','old'])


if __name__=='__main__':unittest.main()
