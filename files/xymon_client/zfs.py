#!/usr/bin/env python3

import os
import sys
import pyxymon as pymon
from optparse import OptionParser
import subprocess

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


CHECK_NAME = 'zfs'
CHECK_VERSION = 1.0
CHECK_LIFETIME = 60


def check_capacity(capacity, warn, crit):
    if capacity < warn:
        color = pymon.STATUS_OK
    elif capacity < crit:
        color = pymon.STATUS_WARNING
    else:
        color = pymon.STATUS_CRITICAL
    return color


def convert_bytes(size):
    power = 2**10
    n = 0
    power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return { "value": size, "unit": power_labels[n] }


def run_check():

    xymon = pymon.XymonClient(CHECK_NAME)

    check_script = os.path.basename(__file__)
    xymon.lifetime = CHECK_LIFETIME

    parser = OptionParser()
    parser.add_option("--warn", dest="capacity_warn", type="int", default=75, metavar="WARN", help="warn if usage > WARN")
    parser.add_option("--crit", dest="capacity_crit", type="int", default=90, metavar="CRIT", help="crit if usage > CRIT")
    (options, args) = parser.parse_args()

    xymon.color = pymon.STATUS_OK # default
    xymon.title('ZFS datasets')

    try:
        zfs_datasets = run_command(['zfs', 'list', '-Hpo', 'name,used,avail,quota,reservation,type'])
    except:
        xymon.section('ZFS ', "Cannot retrieve datasets")
        xymon.color = pymon.STATUS_CRITICAL
        zfs_datasets=""

    # TODO: Make all that q&d spacing right, sorry..
    content = ["        USED      AVAIL  USED[%]    QUOTA  RESERVATION   TYPE  NAME"]

    for ds in zfs_datasets.splitlines():
        ds=ds.split()
        name = ds[0]
        used = convert_bytes(int(ds[1]))
        avail = convert_bytes(int(ds[2]))

        # pretty print quota if set
        if ds[3] == '-' or ds[3] == '0':
            quota = "     none"
        else:
            quota = convert_bytes(int(ds[3]))
            quota = f'{quota["value"]:8.2f}{quota["unit"]}'

        # pretty print reservation if set
        if ds[4] == '-' or ds[4] == '0':
            reserv = "     none"
        else:
            reserv = convert_bytes(int(ds[4]))
            reserv = f'{reserv["value"]:8.2f}{reserv["unit"]}'

        # % = used * 100 / ( used * avail )
        p_used = int(ds[1]) * 100 / ( int(ds[1]) + int(ds[2]) )

        if ds[5] == "filesystem":
            zfs_type = "  fs"
        elif ds[5] == "volume":
            zfs_type = "zvol"
        else:
            zfs_type = ds[5]

        color = check_capacity(p_used, options.capacity_warn, options.capacity_crit)
        xymon.color = color
        content.append(f'{color} {used["value"]:8.2f}{used["unit"]} {avail["value"]:8.2f}{avail["unit"]} {p_used:7.2f}% {quota}    {reserv}   {zfs_type}  {name}')

    xymon.section("", '<br>'.join(content))
    xymon.footer(check_script, CHECK_VERSION)
    xymon.send()



def main():
    run_check()

if __name__ == '__main__':
    main()
    sys.exit(0)

