#!/usr/bin/env python

import platform
import shutil
import subprocess
import sys


is_linux = platform.system() == 'Linux'


def check_python():
    print('Checking Python...')
    py3_path = run('which python3', return_output=True)
    if not py3_path:
        error('! Python 3 does not seem to be installed')
        print('  Please install Python 3.6 per http://docs.python-guide.org/en/latest/starting/installation/')
        sys.exit(1)

    version = run('python3 --version', return_output=True)
    version = version.split()[1]
    major, minor, _ = map(_int_or, version.split('.', 2))
    if minor < 6:
        error('! Version is', version, 'but should be 3.6+')

        py36_path = run('which python3.6', return_output=True)
        if py36_path:
            print('  Python 3.6 is installed, so try updating the symlink: ln -sfn ' + py36_path.strip() +
                  ' ' + py3_path.strip())
        else:
            print('  Please install Python 3.6 per http://docs.python-guide.org/en/latest/starting/installation/')

        sys.exit(1)


def check_venv():
    print('\nChecking venv...')
    test_venv_path = '/tmp/check-python-venv'

    try:
        try:
            run('python3 -m venv ' + test_venv_path, stderr=subprocess.STDOUT, return_output=True)
        except Exception:
            error('! Could not create virtual environment. Please make sure *-venv package is installed.')
            if is_linux:
                print('  For Debian/Ubuntu, try: sudo apt install python3.6-venv')
            sys.exit(1)

    finally:
        shutil.rmtree(test_venv_path, ignore_errors=True)


def check_pip():
    print('\nChecking pip...')

    if not run('which pip3', return_output=True):
        error('! pip3 does not seem to be installed.')
        print('  Try installing it with: curl https://bootstrap.pypa.io/get-pip.py | sudo python3.6')
        if is_linux:
            print('  If your package repo (e.g. apt) has a *-pip package for Python 3.6, then install it from there.')
            print('  E.g. For Debian/Ubuntu, try: apt install python3-pip')
        sys.exit(1)

    version_full = run('pip3 --version', return_output=True)
    version_str = version_full.split()[1]
    version = tuple(map(_int_or, version_str.split('.', 2)))
    if version < (9, 0, 3):
        error('! Version is', version_str, 'but should be 9.0.3+')
        print('  Try upgrading it: pip3 install -U pip3==9.0.3')
        sys.exit(1)

    if 'python3.6' not in version_full:
        error('! pip3 seems to be for another Python version and not Python 3.6')
        print('  See output: ' + version_full.strip())
        print('  Try re-installing it with: curl https://bootstrap.pypa.io/get-pip.py | sudo python3.6')
        sys.exit(1)


def run(cmd, return_output=False, **kwargs):
    print('+ ' + str(cmd))
    if isinstance(cmd, str):
        cmd = cmd.split()

    check_call = subprocess.check_output if return_output else subprocess.check_call

    try:
        return check_call(cmd, **kwargs)

    except Exception:
        if return_output:
            return
        else:
            raise


def _int_or(value):
    try:
        return int(value)
    except Exception as e:
        return value


def error(*msg):
    msg = ' '.join(map(str, msg))
    echo(msg, color='red')


def echo(msg, color=None):
    if sys.stdout.isatty() and color:
        if color == 'red':
            color = '\033[0;31m'
        elif color == 'green':
            color = '\033[92m'

        msg = color + msg + '\033[0m'

    print(msg)


check_python()
check_pip()
check_venv()

echo('\nPython is alive and well. Good job!', color='green')
