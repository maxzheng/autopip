#!/usr/bin/env python

import argparse
import os
import platform
import re
import shutil
import subprocess
import sys

SUPPORTED_VERSIONS = ('3.6', '3.7')
IS_DEBIAN = platform.system() == 'Linux' and os.path.exists('/etc/debian_version')
IS_OLD_UBUNTU = (IS_DEBIAN and os.path.exists('/etc/lsb-release') and
                 re.search('RELEASE=1[46]', open('/etc/lsb-release').read()))
IS_MACOS = platform.system() == 'Darwin'
SUDO = 'sudo ' if os.getuid() else ''

parser = argparse.ArgumentParser(description='Check and fix Python installation')
parser.add_argument('--autofix', action='store_true', help='Automatically fix any problems found')
parser.add_argument('--version', default=SUPPORTED_VERSIONS[0], choices=SUPPORTED_VERSIONS,
                    help='Python version to check')
args = parser.parse_args()

PY_VERSION = args.version
AUTOFIX = args.autofix


def check_sudo():
    if not run('which sudo', return_output=True):
        error('! sudo is not installed.')
        print('  Please ask an administrator to install it and run this again.')
        sys.exit(1)


def check_apt():
    os.environ['DEBIAN_FRONTEND'] = 'noninteractive'
    run(SUDO + 'apt-get install -y apt-utils', return_output=True)


def check_curl():
    if not run('which curl', return_output=True):
        error('! curl is not installed.')
        if IS_DEBIAN:
            raise AutoFixSuggestion('To install, run', SUDO + 'apt-get install -y curl')
        sys.exit(1)


def check_python():
    py3_path = run('which python' + PY_VERSION, return_output=True)
    if not py3_path:
        error('! Python ' + PY_VERSION + ' is not installed.')
        if '--version' not in sys.argv:
            print('  autopip supports Python {}.'.format(', '.join(SUPPORTED_VERSIONS)) +
                  ' To check a different version, re-run using "python - --version x.y"')

        if IS_OLD_UBUNTU:
            raise AutoFixSuggestion('To install, run',
                                    (SUDO + 'apt-get update',
                                     SUDO + 'apt-get install -y software-properties-common',
                                     SUDO + 'add-apt-repository -y ppa:deadsnakes/ppa',
                                     SUDO + 'apt-get update',
                                     SUDO + 'apt-get install -y python' + PY_VERSION))

        elif IS_DEBIAN:
            raise AutoFixSuggestion('To install, run',
                                    (SUDO + 'apt-get update', SUDO + 'apt-get install -y python' + PY_VERSION))

        elif IS_MACOS:
            raise AutoFixSuggestion('To install, run', 'brew install python')

        print('  Please install Python ' + PY_VERSION +
              ' per http://docs.python-guide.org/en/latest/starting/installation/')
        sys.exit(1)


def check_pip():
    if not run('which pip3', return_output=True):
        error('! pip3 is not installed.')
        if IS_DEBIAN:
            raise AutoFixSuggestion('To install, run', SUDO + 'apt-get install -y python3-pip')

        elif IS_MACOS:
            raise AutoFixSuggestion('To install, run', 'curl -s https://bootstrap.pypa.io/get-pip.py | ' +
                                    SUDO + 'python' + PY_VERSION)
        print('  If your package repo has a *-pip package for Python ' + PY_VERSION +
              ', then installing it from there is recommended.')
        print('  To install directly, run: curl -s https://bootstrap.pypa.io/get-pip.py | ' +
              SUDO + 'python' + PY_VERSION)
        sys.exit(1)

    version_full = run('pip3 --version', return_output=True)

    if 'python ' + PY_VERSION not in version_full:
        print('  ' + version_full.strip())
        error('! pip3 is pointing to another Python version and not Python ' + PY_VERSION)
        if '--version' not in sys.argv:
            print('  autopip supports Python {}.'.format(', '.join(SUPPORTED_VERSIONS)) +
                  ' To check a different version, re-run using "python - --version x.y"')

        raise AutoFixSuggestion('To re-install for Python ' + PY_VERSION + ', run',
                                'curl -s https://bootstrap.pypa.io/get-pip.py | ' + SUDO + 'python' + PY_VERSION)

    version_str = version_full.split()[1]
    version = tuple(map(_int_or, version_str.split('.', 2)))
    if version < (9, 0, 3):
        error('! Version is', version_str + ', but should be 9.0.3+')
        raise AutoFixSuggestion('To upgrade, run', SUDO + 'pip3 install pip==9.0.3')


def check_venv():
    test_venv_path = '/tmp/check-python-venv-{}'.format(os.getpid())

    try:
        try:
            run('python' + PY_VERSION + ' -m venv ' + test_venv_path, stderr=subprocess.STDOUT, return_output=True,
                raises=True)

        except Exception:
            error('! Could not create virtual environment.')
            if IS_DEBIAN:
                raise AutoFixSuggestion('To install, run', SUDO + 'apt-get install -y python' + PY_VERSION + '-venv')
            print('  Please make sure Python venv package is installed.')
            sys.exit(1)

    finally:
        shutil.rmtree(test_venv_path, ignore_errors=True)

    try:
        try:
            run('virtualenv --python python' + PY_VERSION + ' ' + test_venv_path, stderr=subprocess.STDOUT,
                return_output=True,
                raises=True)

        except Exception as e:
            if run('which virtualenv', return_output=True):
                error('! Could not create virtual environment.')
                print('  ' + str(e))
                sys.exit(1)

            else:
                error('! virtualenv is not installed.')
                raise AutoFixSuggestion('To install, run', SUDO + 'pip3 install virtualenv')

    finally:
        shutil.rmtree(test_venv_path, ignore_errors=True)


def check_setuptools():
    try:
        version_str = run('python' + PY_VERSION + ' -m easy_install --version', return_output=True, raises=True)

    except Exception:
        error('! setuptools is not installed.')
        raise AutoFixSuggestion('To install, run', SUDO + 'pip3 install setuptools')

    version_str = version_str.split()[1]
    version = tuple(map(_int_or, version_str.split('.')))
    if version < (39,):
        error('! Version is', version_str + ', but should be 39+')
        raise AutoFixSuggestion('To upgrade, run', SUDO + 'pip3 install -U setuptools')


def check_wheel():
    try:
        version_str = run('python' + PY_VERSION + ' -m wheel version ', return_output=True, raises=True)

    except Exception:
        error('! wheel is not installed.')
        raise AutoFixSuggestion('To install, run', SUDO + 'pip3 install wheel')

    version_str = version_str.split()[1]
    version = tuple(map(_int_or, version_str.split('.')))
    if version < (0, 31):
        error('! Version is', version_str + ', but should be 0.31+')
        raise AutoFixSuggestion('To upgrade, run', SUDO + 'pip3 install -U wheel')


def check_python_dev():
    include_path = run('python' + PY_VERSION +
                       ' -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())"',
                       return_output=True)
    if not include_path:
        error('! Failed to get Python include path, so not sure if Python dev package is installed')
        if IS_DEBIAN:
            raise AutoFixSuggestion('To install, run', SUDO + ' apt-get install -y python' + PY_VERSION + '-dev')
        sys.exit(1)

    python_h = os.path.join(include_path.strip(), 'Python.h')

    if not os.path.exists(python_h):
        error('! Python dev package is not installed as', python_h, 'does not exist')
        if IS_DEBIAN:
            raise AutoFixSuggestion('To install, run', SUDO + 'apt-get install -y python' + PY_VERSION + '-dev')
        sys.exit(1)


def run(cmd, return_output=False, raises=False, **kwargs):
    print('+ ' + str(cmd))

    if '"' in cmd or '|' in cmd:
        kwargs['shell'] = True
    elif isinstance(cmd, str):
        cmd = cmd.split()

    check_call = subprocess.check_output if return_output else subprocess.check_call

    try:
        output = check_call(cmd, **kwargs)

        if isinstance(output, bytes):
            output = output.decode('utf-8')

        return output

    except Exception:
        if return_output and not raises:
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
    echo(msg, color=None if AUTOFIX else 'red')


def echo(msg, color=None):
    if sys.stdout.isatty() and color:
        if color == 'red':
            color = '\033[0;31m'
        elif color == 'green':
            color = '\033[92m'

        msg = color + msg + '\033[0m'

    print(msg)


class AutoFixSuggestion(Exception):
    def __init__(self, instruction, cmd):
        super(AutoFixSuggestion, self).__init__(instruction)
        self.cmd = cmd


checks = [check_python, check_pip, check_venv, check_setuptools, check_wheel, check_python_dev]

if AUTOFIX:
    checks.insert(0, check_curl)
    if IS_DEBIAN:
        checks.insert(0, check_apt)
    if SUDO:
        checks.insert(0, check_sudo)

try:
    last_fix = None

    for check in checks:
        print('Checking ' + check.__name__.split('_', 1)[1].replace('_', ' '))

        while True:
            try:
                check()
                break

            except AutoFixSuggestion as e:
                cmds = e.cmd if isinstance(e.cmd, tuple) else (e.cmd,)
                if AUTOFIX:
                    if cmds == last_fix:
                        error('! Failed to fix automatically, so you gotta fix it yourself.')
                        sys.exit(1)

                    else:
                        for cmd in cmds:
                            run(cmd, return_output=True, raises=True)

                        last_fix = cmds

                else:
                    print('  ' + str(e) + ': ' + ' && '.join(cmds) + '\n')
                    print('# Run the above suggested command(s) manually and then re-run to continue checking,')
                    print('  or re-run using "python - --autofix" to run all suggested commands automatically.')
                    sys.exit(1)

        print('')

except Exception as e:
    error('!', str(e))
    sys.exit(1)

except KeyboardInterrupt:
    sys.exit(1)

echo('Python is alive and well. Good job!', color='green')
