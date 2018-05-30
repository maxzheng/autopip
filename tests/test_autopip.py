import re

from mock import Mock, call


def test_list_no_apps(autopip):
    assert autopip('list') == 'No apps are installed yet\n'


def test_install_and_uninstall(monkeypatch, autopip):
    mock_run = Mock()
    monkeypatch.setattr('autopip.crontab.run', mock_run)

    # Install
    stdout = autopip('install bumper')
    assert 'Installing bumper to' in stdout
    assert 'Updating symlinks in' in stdout
    assert '+ bump' in stdout
    assert len(stdout.split('\n')) == 5

    assert len(mock_run.call_args_list) == 3
    assert mock_run.call_args_list[0:2] == [
        call('which crontab', shell=True, stderr=-2),
        call('pgrep cron', shell=True, stderr=-2)]
    install_call = re.sub('/tmp/.*/.apps/', '/tmp/.apps/', re.sub('/home/.*virtualenvs/', '/home/venv/',
                          mock_run.call_args_list[2][0][0]))
    assert install_call == ('( crontab -l | grep -vF "/home/venv/autopip/bin/autopip install \\"bumper\\" '
                            '2>&1 >> /tmp/.apps/log/cron.log" ) | crontab -')

    assert '.apps/bumper/0.1.11' in autopip('list')

    # Uninstall
    mock_run.reset_mock()
    assert autopip('uninstall bumper') == 'Uninstalling bumper\n'
    assert mock_run.call_args_list == [
        call('which crontab', shell=True, stderr=-2),
        call('pgrep cron', shell=True, stderr=-2),
        call('( crontab -l | grep -vF "autopip install \\"bumper" ) | crontab -', shell=True)
    ]

    assert autopip('list') == 'No apps are installed yet\n'
