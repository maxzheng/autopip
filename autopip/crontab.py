from logging import info
import platform
from random import randint
import re
from subprocess import STDOUT

from autopip.constants import IS_MACOS, PYTHON_PATH
from autopip.exceptions import MissingError
from autopip.utils import run


def _ensure_cron():
    """ Ensure cron is running and crontab is available """
    try:
        run('which crontab', stderr=STDOUT, shell=True)

    except Exception:
        raise MissingError('crontab is not available. Please install cron or ensure PATH is set correctly.')

    try:
        run('ps -ef | grep /usr/sbin/cron | grep -v grep', stderr=STDOUT, shell=True)

    except Exception:
        if platform.system() == 'Darwin':
            # macOS does not start cron until there is a crontab entry: https://apple.stackexchange.com/a/266836
            return

        raise MissingError('cron service does not seem to be running. Try starting it: sudo service cron start')


def add(cmd, schedule='? * * * *', cmd_id=None):
    """
    Schedule a command to run. This method is idempotent.

    :param str cmd: The command to run.
    :param str schedule: The schedule to run. Defaults to every hour with a random minute.
                         If '?' is used (default), it will be replaced with a random value from 0 to 59.
    :param str cmd_id: Short version of cmd that we can use to uniquely identify the command for updating purpose.
                       Defaults to cmd without any redirect chars. It must a regex that matches cmd.
    """
    if IS_MACOS:
        info('Adding to crontab (may require admin permission)')
    _ensure_cron()

    cmd = cmd.replace('"', r'\"')

    if cmd_id:
        cmd_id = cmd_id.replace('"', r'\"')
        if not re.search(cmd_id.replace('\\', r'\\'), cmd):
            raise ValueError(f'cmd_id does not match cmd where:\n\tcmd_id = {cmd_id}\n\tcmd = {cmd}')

    else:
        cmd_id = re.sub('[ &12]*[>|<=].*', '', cmd)

    if '?' in schedule:
        schedule = schedule.replace('?', str(randint(0, 59)))

    crontab_cmd = (rf'( crontab -l | grep -vi "{cmd_id}"; echo "{schedule} PATH={PYTHON_PATH}:\$PATH {cmd}" )'
                   ' | crontab -')
    run(crontab_cmd, stderr=STDOUT, shell=True)


def list_entries(name='autopip'):
    """ List current schedules """
    _ensure_cron()

    name = name.replace('"', r'\"')

    return run(f'crontab -l | grep -i "{name}"', stderr=STDOUT, shell=True)


def remove(name):
    """ Remove cmd with the given name """
    if name not in list_entries(name):
        return

    if IS_MACOS:
        info('Removing from crontab (may require admin permission)')
    _ensure_cron()

    name = name.replace('"', r'\"')

    run(f'( crontab -l | grep -vi "{name}" ) | crontab -', stderr=STDOUT, shell=True)
