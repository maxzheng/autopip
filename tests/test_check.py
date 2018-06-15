from pathlib import Path
import subprocess

import pytest


@pytest.mark.parametrize('python', ['python2', 'python3'])
def test_check(python):
    check_script = str(Path(__file__).parent.parent / 'etc' / 'check-python.py')
    subprocess.check_call([python, check_script])
