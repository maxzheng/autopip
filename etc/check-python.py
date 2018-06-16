#!/usr/bin/env python

import os
import platform
import shutil
import subprocess
import sys


IS_LINUX = platform.system() == 'Linux'
PY_VERSION = '3.6'
SUDO = 'sudo ' if os.getuid() else ''


def check_python():
    print('Checking Python...')
    py3_path = run('which python' + PY_VERSION, return_output=True)
    if not py3_path:
        error('! Python ' + PY_VERSION + ' is not installed.')
        print('  Please install Python ' + PY_VERSION +
              ' per http://docs.python-guide.org/en/latest/starting/installation/')
        sys.exit(1)


def check_pip():
    print('\nChecking pip...')

    if not run('which pip3', return_output=True):
        error('! pip3 does not seem to be installed.')
        print('  Install it with: curl https://bootstrap.pypa.io/get-pip.py | ' + SUDO + 'python' + PY_VERSION)
        if IS_LINUX:
            print('  If your package repo (e.g. apt) has a *-pip package for Python ' + PY_VERSION +
                  ', then install it from there.')
            print('  To install in Debian/Ubuntu, run: ' + SUDO + 'apt install python3-pip')
        sys.exit(1)

    version_full = run('pip3 --version', return_output=True)

    if 'python' + PY_VERSION not in version_full:
        print('  ' + version_full.strip())
        error('! pip3 is pointing to another Python version and not Python ' + PY_VERSION)
        print('  Re-install it with: curl https://bootstrap.pypa.io/get-pip.py | ' +
              SUDO + 'python' + PY_VERSION)
        sys.exit(1)

    version_str = version_full.split()[1]
    version = tuple(map(_int_or, version_str.split('.', 2)))
    if version < (9, 0, 3):
        error('! Version is', version_str + ', but should be 9.0.3+')
        print('  To upgrade, run: ' + SUDO + 'pip3 install pip==9.0.3')
        sys.exit(1)


def check_venv():
    print('\nChecking venv...')
    test_venv_path = '/tmp/check-python-venv'

    try:
        try:
            run('python' + PY_VERSION + ' -m venv ' + test_venv_path, stderr=subprocess.STDOUT, return_output=True,
                raises=True)

        except Exception:
            error('! Could not create virtual environment. Please make sure *-venv package is installed.')
            if IS_LINUX:
                print('  To install in Debian/Ubuntu, run: ' + SUDO + 'apt install python' + PY_VERSION + '-venv')
            sys.exit(1)

    finally:
        shutil.rmtree(test_venv_path, ignore_errors=True)


def check_setuptools():
    print('\nChecking setuptools...')

    try:
        version_str = run('python' + PY_VERSION + ' -m easy_install --version', return_output=True)

    except Exception:
        error('! setuptools is not installed.')
        print('  To install, run: ' + SUDO + 'pip3 install setuptools')
        sys.exit(1)

    version_str = version_str.split()[1]
    version = tuple(map(_int_or, version_str.split('.')))
    if version < (39,):
        error('! Version is', version_str + ', but should be 39+')
        print('  To upgrade, run: ' + SUDO + 'pip3 install -U setuptools')
        sys.exit(1)


def check_wheel():
    print('\nChecking wheel...')

    try:
        version_str = run('python' + PY_VERSION + ' -m wheel version ', return_output=True)

    except Exception:
        error('! wheel is not installed.')
        print('  To install, run: ' + SUDO + 'pip3 install wheel')
        sys.exit(1)

    version_str = version_str.split()[1]
    version = tuple(map(_int_or, version_str.split('.')))
    if version < (0, 31):
        error('! Version is', version_str + ', but should be 0.31+')
        print('  To upgrade, run: ' + SUDO + 'pip3 install -U wheel')
        sys.exit(1)


def check_devel():
    print('\nChecking dev...')

    include_path = run('python' + PY_VERSION +
                       ' -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())"',
                       return_output=True)
    if not include_path:
        error('! Failed to get Python include path, so not sure if Python dev package is installed')
        print('  To install in Debian/Ubuntu, run: ' + SUDO + ' apt install python' + PY_VERSION + '-dev')
        sys.exit(1)

    python_h = os.path.join(include_path.strip(), 'Python.h')

    if not os.path.exists(python_h):
        error('! Python dev package is not installed as', python_h, 'does not exist')
        print('  To install in Debian/Ubuntu, run: ' + SUDO + 'apt install python' + PY_VERSION + '-dev')
        sys.exit(1)


def run(cmd, return_output=False, raises=False, **kwargs):
    print('+ ' + str(cmd))

    if '"' in cmd:
        kwargs['shell'] = True
    elif isinstance(cmd, str):
        cmd = cmd.split()

    check_call = subprocess.check_output if return_output else subprocess.check_call

    try:
        output = check_call(cmd, **kwargs)

        if isinstance(output, bytes):
            output = output.decode()

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
check_setuptools()
check_wheel()
check_devel()

echo('\nPython is alive and well. Good job!', color='green')
