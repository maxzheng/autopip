from random import randint
import re
from logging import info
from subprocess import check_output as run, STDOUT

from autopip.exceptions import MissingCommandError


def _ensure_cron():
    """ Ensure cron is running and crontab is available """
    try:
        run('which crontab', stderr=STDOUT, shell=True)

    except Exception:
        raise MissingCommandError('crontab is not available. Please install cron or ensure PATH is set correctly.')

    try:
        run('pgrep cron', stderr=STDOUT, shell=True)

    except Exception:
        raise RuntimeError('cron service does not seem to be running. Try starting it: sudo service cron start')


def add(cmd, schedule='? * * * *', cmd_id=None):
    """
    Schedule a command to run. This method is idempotent.

    :param str cmd: The command to run.
    :param str schedule: The schedule to run. Defaults to every hour with a random minute.
                         If '?' is used (default), it will be replaced with a random value from 0 to 59.
    :param str cmd_id: Short version of cmd that we can use to uniquely identify the command for updating purpose.
                       Defaults to cmd without any redirect chars. It must be a substring of cmd.
    """
    _ensure_cron()

    cmd = cmd.replace('"', r'\"')

    if cmd_id:
        cmd_id = cmd_id.replace('"', r'\"')
        if cmd_id not in cmd:
            raise ValueError('cmd_id must be a substring of cmd')

    else:
        cmd_id = re.sub('[ &12]*[>|<=].*', '', cmd)

    if '?' in schedule:
        schedule = schedule.replace('?', str(randint(0, 59)))

    crontab_cmd = f'( crontab -l | grep -vF "{cmd_id}"; echo "{schedule} {cmd}" ) | crontab -'
    run(crontab_cmd, shell=True)


def list(name_filter='autopip'):
    """ List current schedules """
    _ensure_cron()

    info(run(f'crontab -l | grep {name_filter}', shell=True))


def remove(name):
    """ Remove cmd with the given name """
    _ensure_cron()

    name = name.replace('"', r'\"')

    run(f'( crontab -l | grep -vF "{name}" ) | crontab -', shell=True)
