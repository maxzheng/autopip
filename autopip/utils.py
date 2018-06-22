from logging import debug
from subprocess import check_output


def run(*args, **kwargs):
    debug('Running: %s', args[0])
    return check_output(*args, **kwargs).decode('utf-8')
