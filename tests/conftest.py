from mock import Mock
import pytest


@pytest.fixture()
def mock_run(monkeypatch):
    r = Mock()
    monkeypatch.setattr('autopip.crontab.run', r)
    return r
