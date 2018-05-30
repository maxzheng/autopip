import logging

from mock import Mock
import pytest


logging.basicConfig(format='%(message)s', level=logging.INFO)


@pytest.fixture()
def mock_run(monkeypatch):
    r = Mock()
    monkeypatch.setattr('autopip.crontab.run', r)
    return r
