import logging
import os
from pathlib import Path

from mock import Mock
import pytest

from autopip import main

logging.basicConfig(format='%(message)s', stream=open(os.devnull, 'w'), level=logging.INFO)


@pytest.fixture(autouse=True)
def mock_paths(monkeypatch, tmpdir):
    install_root = Path(tmpdir) / '.apps'
    monkeypatch.setattr('autopip.manager.AppsPath.USER_INSTALL_ROOT', install_root)
    monkeypatch.setattr('autopip.manager.AppsPath.USER_SYMLINK_ROOT', install_root / 'bin')
    monkeypatch.setattr('autopip.manager.AppsPath.USER_LOG_ROOT', install_root / 'log')


@pytest.fixture()
def mock_run(monkeypatch):
    r = Mock()
    monkeypatch.setattr('autopip.crontab.run', r)
    monkeypatch.setattr('autopip.manager.run', r)
    return r


@pytest.fixture()
def autopip(monkeypatch, caplog):
    def _run(args, isatty=True, raises=None):
        if isinstance(args, str):
            args = args.split()

        monkeypatch.setattr('sys.argv', ['autopip', '--debug'] + args)
        monkeypatch.setattr('sys.stdout.isatty', Mock(return_value=True))

        caplog.clear()

        if raises:
            with pytest.raises(raises) as e:
                main()
            return caplog.text, e

        else:
            main()
            return caplog.text

    return _run
