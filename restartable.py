#!/usr/bin/env python3
#
# Copyright 2019 Ricardo Branco <rbranco@suse.de>
# MIT License
#
"""
list restartable programs or services using deleted libraries
"""

import os
import pwd
import re
import sys
from argparse import ArgumentParser

from procpid import ProcPid

VERSION = "0.3"

USAGE = """%s [OPTIONS]

List running processes using files deleted by recent upgrades

Options:
    -h, --help      Get help
    -V, --version   Show version and exit
    -s, --short
         Create a short table not showing the deleted files. Given twice,
         show only processes which are associated with a system service.
         Given three times, list the associated system service names only.
""" % os.path.basename(sys.argv[0])

# Ignore deleted files in these directories
IGNORE = ('/dev',
          '/home',
          '/i915',
          '/memfd:',
          '/run',
          '/SYSV',
          '/tmp',
          '/var',
          '/[aio]',
          '[')

# Regular expression to find systemd service unit in /proc/<pid>/cgroup
SYSTEMD_REGEX = r"\d+:name=systemd:/system\.slice/(?:.*/)?(.*)\.service$"

opts = None


def print_info(proc, deleted):
    """
    Print information
    """
    uid = proc.status.Uid.real
    try:
        username = pwd.getpwuid(uid).pw_name
    except KeyError:
        username = uid
    try:
        service = re.findall(SYSTEMD_REGEX, proc.cgroup, re.MULTILINE)[0]
    except IndexError:
        if opts.short > 1:
            return
        service = "-"
    # cmdline is empty if zombie
    cmdline = " ".join(proc.cmdline)
    if not cmdline:
        cmdline = proc.stat.comm
    if opts.short > 2:
        print(service)
    else:
        print("%s\t%s\t%s\t%-30s\t%40s\t%s" % (
            proc.pid, proc.stat.ppid, uid, username, service, cmdline))
    if not opts.short:
        for path in sorted(deleted):
            print("\t%s" % path)


def main():
    """
    Main function
    """
    argparser = ArgumentParser(usage=USAGE, add_help=False)
    argparser.add_argument('-h', '--help', action='store_true')
    argparser.add_argument('-s', '--short', action='count', default=0)
    argparser.add_argument('-V', '--version', action='store_true')
    global opts
    opts = argparser.parse_args()
    if opts.help:
        print(USAGE)
        sys.exit(0)
    elif opts.version:
        print(VERSION)
        sys.exit(0)

    if os.geteuid() != 0:
        print("WARN: Run this program as root", file=sys.stderr)

    if opts.short < 3:
        print("%s\t%s\t%s\t%-30s\t%40s\t%s" % (
            "PID", "PPID", "UID", "User", "Service", "Command"))
    for pid in [_ for _ in os.listdir("/proc") if _.isdigit()]:
        with ProcPid(pid) as proc:
            deleted = set()
            for path in {_['pathname'] for _ in proc.maps if _['pathname']}:
                if path == "/ (deleted)":
                    continue
                if path.endswith(' (deleted)') and not path.startswith(IGNORE):
                    deleted.add(path[:-len(' (deleted)')])
            if deleted:
                print_info(proc, deleted)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)