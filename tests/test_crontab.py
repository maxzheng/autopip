from mock import Mock, call

from autopip import crontab


def test_add(mock_run, monkeypatch):
    monkeypatch.setattr('autopip.crontab.randint', Mock(return_value=10))
    crontab.add('echo hello')
    mock_run.assert_called_with('( crontab -l | grep -vF "echo hello"; echo "10 * * * * echo hello" ) | crontab -',
                                shell=True)

    crontab.add('echo hello', schedule='* * * * *')
    mock_run.assert_called_with('( crontab -l | grep -vF "echo hello"; echo "* * * * * echo hello" ) | crontab -',
                                shell=True)

    crontab.add('echo hello', schedule='* * * * *', name='hello')
    mock_run.assert_called_with('( crontab -l | grep -vF "hello"; echo "* * * * * echo hello" ) | crontab -',
                                shell=True)


def test_list(mock_run):
    crontab.list()
    mock_run.call_args_list == [
        call('which crontab'),
        call('pgrep cron'),
        call('crontab -l | grep autopip', shell=True)]


def test_remove(mock_run):
    crontab.remove('hello')
    mock_run.assert_called_with('( crontab -l | grep -vF "{name}" ) | crontab -',
                                shell=True)
