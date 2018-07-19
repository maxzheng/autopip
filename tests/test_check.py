from pathlib import Path
import subprocess

import pytest

from autopip.constants import PYTHON_VERSION


@pytest.mark.parametrize('python', ['python2', 'python3'])
def test_check(python):
    check_script = str(Path(__file__).parent.parent / 'etc' / 'check-python.py')
    cmd = [python, check_script]

    if not(PYTHON_VERSION == '3.6' and python == 'python2'):
        cmd.extend(['--version', PYTHON_VERSION])

    subprocess.check_call(cmd)
