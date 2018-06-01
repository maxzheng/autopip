import re

from mock import Mock, call


def test_autopip(monkeypatch, autopip):
    mock_run = Mock()
    monkeypatch.setattr('autopip.crontab.run', mock_run)

    # Install latest
    stdout = autopip('install bumper')
    assert 'Installing bumper to' in stdout
    assert 'Updating symlinks in' in stdout
    assert '+ bump' in stdout
    assert len(stdout.split('\n')) == 5

    assert len(mock_run.call_args_list) == 3
    assert mock_run.call_args_list[0:2] == [
        call('which crontab', shell=True, stderr=-2),
        call('pgrep cron', shell=True, stderr=-2)]
    install_call = re.sub('/tmp/.*/system/', '/tmp/system/', re.sub('/home/.*virtualenvs/', '/home/venv/',
                          mock_run.call_args_list[2][0][0]))
    assert install_call == ('( crontab -l | grep -vF "/home/venv/autopip/bin/autopip install \\"bumper\\" '
                            '2>&1 >> /tmp/system/log/cron.log" ) | crontab -')

    assert 'system/bumper/0.1.11' in autopip('list')
    assert autopip('list --scripts').split('\n')[1].strip().endswith('/bin/bump')

    # Already installed
    stdout = autopip('install bumper')
    assert stdout == 'bumper is already installed\n'
    assert mock_run.call_count == 6

    # Uninstall
    mock_run.reset_mock()
    assert autopip('uninstall bumper') == 'Uninstalling bumper\n'
    assert mock_run.call_args_list == [
        call('which crontab', shell=True, stderr=-2),
        call('pgrep cron', shell=True, stderr=-2),
        call('( crontab -l | grep -vF "autopip install \\"bumper" ) | crontab -', shell=True, stderr=-2)
    ]

    assert autopip('list') == 'No apps are installed yet.\n'


def test_install_lib(autopip):
    stdout, e = autopip('install utils-core', raises=SystemExit)
    assert 'Uninstalling utils-core' in stdout
    assert '! Odd, there are no scripts included in the app' in stdout


def test_install_bad_version(autopip):
    stdout, _ = autopip('install bumper==100.*', raises=SystemExit)
    assert '! No app version matching bumper==100.*' in stdout
    assert 'Available versions: 0.1.8, 0.1.9, 0.1.10, 0.1.11' in stdout


def test_install_failed(autopip, monkeypatch, mock_run):
    mock_run.side_effect = Exception('install failed')
    monkeypatch.setattr('autopip.manager.run', mock_run)
    stdout, _ = autopip('install utils-core', raises=SystemExit)
    assert '! install failed' in stdout
