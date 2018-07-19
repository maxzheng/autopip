from enum import IntEnum
import sys


PYTHON_VERSION = '{}.{}'.format(*sys.version_info[0:2])
WAIT_TIMEOUT_MSG = 'No new version was published after an hour, so not gonna wait anymore.'
INSTALL_TIMEOUT_MSG = """Uh oh, something is wrong...
  autopip has been running for an hour and is likely stuck, so exiting to prevent resource issues.
  Please report this issue at https://github.com/maxzheng/autopip/issues"""


class UpdateFreq(IntEnum):
    HOURLY = 3600
    DAILY = 86400
    WEEKLY = 604800
    MONTHLY = 2592000

    DEFAULT = HOURLY

    @classmethod
    def from_name(cls, name):
        return getattr(cls, name.upper())

    @property
    def seconds(self):
        return self.value
