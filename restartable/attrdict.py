#
# Copyright 2019 Ricardo Branco <rbranco@suse.de>
# MIT License
#
"""
Module for AttrDict
"""
import os
import stat
from collections import UserDict


# pylint: disable=too-many-ancestors

# As dict is not supposed to be subclassed directly, use UserDict instead
# We use dict as the last class so isinstance(foo, dict) works
class AttrDict(UserDict, dict):
    """
    Class for accessing dictionary keys with attributes
    """
    def __getattr__(self, attr):
        if attr.startswith('__') and attr.endswith('__'):
            raise AttributeError    # Make help() work
        return self.__getitem__(attr)

    def __delattr__(self, attr):
        self.__delitem__(attr)


class FSDict(AttrDict):
    def __init__(self, path="", dir_fd=None, handler=None):
        if dir_fd is not None:
            self._dir_fd = dir_fd
        self._path = path
        self._handler = handler
        super().__init__()

    def __getitem__(self, item):
        value = super().__getitem__(item)
        super().__setitem__(item, value)
        return value

    def _opener(self, path, flags):
        return os.open(path, flags, dir_fd=self._dir_fd)

    def __missing__(self, path):
        """
        Get contents from file, symlink or directory
        """
        if self._handler:
            return self._handler(path)
        path = os.path.join(self._path, path)
        mode = os.lstat(path, dir_fd=self._dir_fd).st_mode
        if stat.S_ISLNK(mode):
            return os.readlink(path, dir_fd=self._dir_fd)
        if stat.S_ISREG(mode):
            with open(path, opener=self._opener) as file:
                return file.read()
        if stat.S_ISDIR(mode):
            return FSDict(path=path, dir_fd=self._dir_fd)
        return None
