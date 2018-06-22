import logging
import os
from pathlib import Path
import re

from mock import Mock
import pytest

from autopip import main

logging.basicConfig(format='%(message)s', stream=open(os.devnull, 'w'), level=logging.INFO)


@pytest.fixture(autouse=True)
def mock_paths(monkeypatch, tmpdir):
    system_root = Path(tmpdir) / 'system'
    monkeypatch.setattr('autopip.manager.AppsPath.SYSTEM_INSTALL_ROOT', system_root)
    monkeypatch.setattr('autopip.manager.AppsPath.SYSTEM_SYMLINK_ROOT', system_root / 'bin')
    monkeypatch.setattr('autopip.manager.AppsPath.SYSTEM_LOG_ROOT', system_root / 'log')
    (system_root / 'bin').mkdir(parents=True)

    local_root = Path(tmpdir) / 'local'
    monkeypatch.setattr('autopip.manager.AppsPath.LOCAL_INSTALL_ROOT', local_root)
    monkeypatch.setattr('autopip.manager.AppsPath.LOCAL_SYMLINK_ROOT', local_root / 'bin')
    monkeypatch.setattr('autopip.manager.AppsPath.LOCAL_LOG_ROOT', local_root / 'log')
    (local_root / 'bin').mkdir(parents=True)

    user_root = Path(tmpdir) / '.apps'
    monkeypatch.setattr('autopip.manager.AppsPath.USER_INSTALL_ROOT', user_root)
    monkeypatch.setattr('autopip.manager.AppsPath.USER_SYMLINK_ROOT', user_root / 'bin')
    monkeypatch.setattr('autopip.manager.AppsPath.USER_LOG_ROOT', user_root / 'log')

    return system_root, local_root, user_root


@pytest.fixture()
def mock_run(monkeypatch):
    r = Mock()
    monkeypatch.setattr('autopip.crontab.run', r)
    monkeypatch.setattr('autopip.manager.run', r)
    return r


@pytest.fixture()
def autopip(monkeypatch, caplog):
    tmp_re = re.compile('/tmp/.*/system/')

    def _run(args, isatty=True, raises=None):
        if isinstance(args, str):
            args = args.split()

        monkeypatch.setattr('sys.argv', ['autopip', '--debug'] + args)
        monkeypatch.setattr('sys.stdout.isatty', Mock(return_value=isatty))

        caplog.clear()

        if raises:
            with pytest.raises(raises) as e:
                main()
            return tmp_re.sub('/tmp/system/', caplog.text), e

        else:
            main()
            return tmp_re.sub('/tmp/system/', caplog.text)

    return _run
