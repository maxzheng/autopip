from enum import Enum


class UpdateFreq(Enum):
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
