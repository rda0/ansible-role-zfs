#!/usr/bin/env python3

import os
import sys
import pyxymon as pymon
from optparse import OptionParser
import subprocess
import re

# run system command and capture output
def run_command(command):
    try:
        cmd = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        if cmd.returncode != 0:
            raise Exception("command returned non-zero exit code: " + str(cmd.returncode))
        if cmd.stderr:
            stderr = cmd.stderr.decode("utf-8")
            raise Exception("command returned output to stderr: " + stderr)
        else:
            command_output = cmd.stdout.decode("utf-8")
    except subprocess.TimeoutExpired:
        raise Exception("command timeout")

    return command_output


CHECK_NAME = 'zpool'
CHECK_VERSION = 1.1
CHECK_LIFETIME = 60

def check_vdev(state, strict):
    if state == "ONLINE":
        color = pymon.STATUS_OK
    elif state == "OFFLINE" and not strict:
        color = pymon.STATUS_WARNING
    elif state == "DEGRADED" and not strict:
        color = pymon.STATUS_WARNING
    else:
        color = pymon.STATUS_CRITICAL
    return color

def check_capacity(capacity, warn, crit):
    if capacity < warn:
        color = pymon.STATUS_OK
    elif capacity < crit:
        color = pymon.STATUS_WARNING
    else:
        color = pymon.STATUS_CRITICAL
    return color

def run_check():
    xymon = pymon.XymonClient(CHECK_NAME)

    check_script = os.path.basename(__file__)
    xymon.lifetime = CHECK_LIFETIME

    regex = re.compile(r'(?<=state:).*')
    # detect lines containing header or "cache"
    head = re.compile(r'(\s*NAME\s*STATE\s*READ\s*WRITE\s*CKSUM|\s*cache\s*)')
    zpool = None

    parser = OptionParser()
    parser.add_option("--strict", action="store_true", dest="strict", default=False, help="enable strict mode (DEGRADED/OFFLINE => red)")
    parser.add_option("--pool", dest="zpool", metavar="ZPOOL", help="only check POOL")
    parser.add_option("--warn", dest="capacity_warn", type="int", default=70, metavar="WARN", help="warn if usage > WARN")
    parser.add_option("--crit", dest="capacity_crit", type="int", default=80, metavar="CRIT", help="crit if usage > CRIT")
    (options, args) = parser.parse_args()

    xymon.color = pymon.STATUS_OK # default
    xymon.title('zfs zpool status')

    if options.zpool:
        zfs_pools = options.zpool
    else:
        # get a list of zpools
        try:
            zfs_pools = run_command(['zpool', 'list', '-Ho', 'name'])
        except:
            xymon.section('zpool ???', "Cannot retrieve zpools")
            xymon.color = pymon.STATUS_CRITICAL
            zfs_pools=""

    content = []

    for pool in zfs_pools.splitlines():
        try:
            data = run_command(["zpool", "status", pool])
        except:
            xymon.section('zpool {}'.format(pool), "Cannot retrieve status")
            xymon.color = pymon.STATUS_CRITICAL
            break

        try:
            capacity = int(run_command(["zpool", "list", "-Hp", "-o", "capacity", pool]).strip())
        except:
            xymon.section('zpool {}'.format(pool), "Cannot retrieve zpool capacity")
            xymon.color = pymon.STATUS_CRITICAL
            break

        pool_state = regex.search(data).group().strip()

        vdev_color = check_vdev(pool_state, options.strict)
        xymon.color = vdev_color  # update color if necessary

        capacity_color = check_capacity(capacity, options.capacity_warn, options.capacity_crit)
        content.append("{} zpool usage: {}%".format(capacity_color, capacity))
        content.append("{} zpool status: {}".format(vdev_color, pool_state))

        # read output line by line and loook for vdev info lines
        in_device_section = False   # are we in the vdev table?
        for line in data.splitlines():
            # skip everything that is not in the vdev table
            if head.match(line):    # vdev table begins
                in_device_section = True
                continue
            if not line:
                in_device_section = False
            if not in_device_section:
                continue

            # name, state, read_err, write_err, check_sum
            vdev_info = line.split()
            vdev_color = check_vdev(vdev_info[1], options.strict)
            xymon.color = vdev_color  # update color if necessary

            content.append("  {} {} status: {}".format(vdev_color, vdev_info[0], vdev_info[1]))

            if vdev_info[2] != "0":
                content.append("    &red vdev {} has read errors".format(vdev_info[0]))
                xymon.color = pymon.STATUS_CRITICAL  # update color if necessary
            if vdev_info[3] != "0":
                content.append("    &red vdev {} has write errors".format(vdev_info[0]))
                xymon.color = pymon.STATUS_CRITICAL  # update color if necessary
            if vdev_info[4] != "0":
                content.append("    &red vdev {} has checksum errors".format(vdev_info[0]))
                xymon.color = pymon.STATUS_CRITICAL  # update color if necessary

        xymon.section('zpool {}'.format(pool), '<br>'.join(content))
        content = []

    xymon.footer(check_script, CHECK_VERSION)
    xymon.send()



def main():
    run_check()

if __name__ == '__main__':
    main()
    sys.exit(0)
