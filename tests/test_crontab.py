from mock import Mock, call

from autopip.constants import PYTHON_PATH
from autopip import crontab


def test_add(mock_run, monkeypatch):
    monkeypatch.setattr('autopip.crontab.randint', Mock(return_value=10))
    crontab.add('echo hello')
    mock_run.assert_called_with('( crontab -l | grep -vi "echo hello"; '
                                rf'echo "10 * * * * PATH={PYTHON_PATH}:\$PATH echo hello" ) | crontab -',
                                shell=True, stderr=-2)

    crontab.add('echo hello', schedule='* * * * *')
    mock_run.assert_called_with('( crontab -l | grep -vi "echo hello"; '
                                rf'echo "* * * * * PATH={PYTHON_PATH}:\$PATH echo hello" ) | crontab -',
                                shell=True, stderr=-2)

    crontab.add('echo hello', schedule='* * * * *', cmd_id='hello')
    mock_run.assert_called_with('( crontab -l | grep -vi "hello"; '
                                rf'echo "* * * * * PATH={PYTHON_PATH}:\$PATH echo hello" ) | crontab -',
                                shell=True, stderr=-2)

    crontab.add('echo hello > /dev/null')
    mock_run.assert_called_with('( crontab -l | grep -vi "echo hello"; '
                                rf'echo "10 * * * * PATH={PYTHON_PATH}:\$PATH echo hello > /dev/null" ) | crontab -',
                                shell=True, stderr=-2)

    crontab.add('echo hello < /dev/null')
    mock_run.assert_called_with('( crontab -l | grep -vi "echo hello"; '
                                rf'echo "10 * * * * PATH={PYTHON_PATH}:\$PATH echo hello < /dev/null" ) | crontab -',
                                shell=True, stderr=-2)

    crontab.add('echo hello | tee /tmp/log')
    mock_run.assert_called_with('( crontab -l | grep -vi "echo hello"; '
                                rf'echo "10 * * * * PATH={PYTHON_PATH}:\$PATH echo hello | tee /tmp/log" ) | crontab -',
                                shell=True, stderr=-2)

    crontab.add('echo hello &> /dev/null')
    mock_run.assert_called_with('( crontab -l | grep -vi "echo hello"; '
                                rf'echo "10 * * * * PATH={PYTHON_PATH}:\$PATH echo hello &> /dev/null" ) | crontab -',
                                shell=True, stderr=-2)

    crontab.add('echo hello 2>&1 > /dev/null')
    mock_run.assert_called_with('( crontab -l | grep -vi "echo hello"; echo "10 * * * * '
                                rf'PATH={PYTHON_PATH}:\$PATH echo hello 2>&1 > /dev/null" ) | crontab -',
                                shell=True, stderr=-2)


def test_list(mock_run):
    crontab.list_entries()
    mock_run.call_args_list == [
        call('which crontab'),
        call('pgrep cron'),
        call('crontab -l | grep autopip', shell=True, stderr=-2)]


def test_remove(mock_run):
    crontab.remove('autopip')
    mock_run.assert_called_with('( crontab -l | grep -vi "autopip" ) | crontab -',
                                shell=True, stderr=-2)
