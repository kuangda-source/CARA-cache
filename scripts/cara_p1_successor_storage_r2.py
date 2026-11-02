"""Only the distinct successor's private storage; preserve the ended R1 volume."""
import cara_source_lifecycle_p1_storage_r1 as transport

transport.OPERATOR = 'scripts/provision_cara_source_lifecycle_p1_storage_r2.py'
transport.REMOTE = transport.REMOTE.replace(
    'cara-source-lifecycle-V1-P1-full146-r1-20261102',
    'cara-source-lifecycle-V1-P1-full146-r2-20261102').replace(
    'cara-source-lifecycle-P1-storage-provision-r1-20261102',
    'cara-source-lifecycle-P1-storage-provision-r2-20261102').replace(
    'source-lifecycle-P1-full146-r1', 'source-lifecycle-P1-full146-r2').replace(
    "(label+'-r1')", "(label+'-r2')")

if __name__ == '__main__':
    transport.main()
