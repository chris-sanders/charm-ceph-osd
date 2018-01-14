#!/usr/bin/env python2

from __future__ import print_function

import sys
import copy

from ceph_disk import main as ceph_disk


def create_partitions(argv):
    args = ceph_disk.parse_args(argv)
    ceph_disk.setup_logging(args.verbose, args.log_stdout)
    ceph_disk.setup_statedir(args.statedir)
    ceph_disk.setup_sysconfdir(args.sysconfdir)
    factory = ceph_disk.Prepare(args).factory(args)

    if args.dmcrypt:
        # Setup lockbox partition
        lockbox = ceph_disk.Lockbox(args)
        device_args = copy.copy(args)
        device_args.dmcrypt = False
        lockbox.device = ceph_disk.Device.factory(args.lockbox, device_args)
        partition_num = lockbox.device.create_partition(uuid=args.lockbox_uuid,
                                                        name='lockbox',
                                                        size=10)
        lockbox.partition = lockbox.device.get_partition(partition_num)
        factory.lockbox = lockbox
        factory.lockbox.populate()

    # Setup data partition
    factory.data.sanity_checks()
    factory.data.set_variables()
    factory.data.device = ceph_disk.Device.factory(args.data, args)

    partition_num = factory.data.device.create_partition(uuid=args.osd_uuid,
                                                         name='data',
                                                         size=factory.data.get_space_size())
    factory.data.partition = factory.data.device.get_partition(partition_num)

    # Setup block prtition
    args.data = 'dummy'
    factory.block.prepare()
    args.data = args.block

    # Populate data partitions
    factory.data.populate_data_path_device(factory.block)


if __name__ == '__main__':
    argv = sys.argv[1:]
    create_partitions(argv)

