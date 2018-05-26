from random import randint
from subprocess import check_call as run


def _ensure_cron():
    """ Ensure cron is running and crontab is available """
    try:
        run('which crontab', shell=True)

    except Exception:
        raise RuntimeError('crontab is not available. Please install cron or ensure PATH is set correctly.')

    try:
        run('pgrep cron', shell=True)

    except Exception:
        raise RuntimeError('cron service does not seem to be running. Try starting it: sudo service cron start')


def add(cmd, schedule='? * * * *', name=None):
    """
    Schedule a command to run. This method is idempotent.

    :param str cmd: The command to run.
    :param str schedule: The schedule to run. Defaults to every hour with a random minute.
                         If '?' is used (default), it will be replaced with a random value from 0 to 59.
    :param str name: Unique name used to identify this command so we can remove/update it later. Defaults to the
                     same value as `cmd` param.
    """
    _ensure_cron()

    cmd = cmd.replace('"', r'\"')
    if not name:
        name = cmd
    if '?' in schedule:
        schedule = schedule.replace('?', str(randint(0, 60)))

    crontab_cmd = f'( crontab -l | grep -vF "{name}"; echo "{schedule} {cmd}" ) | crontab -'

    run(crontab_cmd, shell=True)


def list(name_filter='autopip'):
    """ List current schedules """
    _ensure_cron()

    run(f'crontab -l | grep {name_filter}', shell=True)


def remove(name):
    """ Remove cmd with the given name """
    _ensure_cron()

    run('( crontab -l | grep -vF "{name}" ) | crontab -', shell=True)
