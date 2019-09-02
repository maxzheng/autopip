from logging import debug
import re
from subprocess import check_output


def run(*args, **kwargs):
    debug('Running: %s', args[0])
    return check_output(*args, **kwargs).decode('utf-8')


def sorted_versions(versions):
    version_sep_re = re.compile('[^0-9]+')
    return sorted(versions, key=lambda v: tuple(map(int, version_sep_re.split(v))))
