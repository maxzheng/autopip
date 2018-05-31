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
    install_call = re.sub('/tmp/.*/.apps/', '/tmp/.apps/', re.sub('/home/.*virtualenvs/', '/home/venv/',
                          mock_run.call_args_list[2][0][0]))
    assert install_call == ('( crontab -l | grep -vF "/home/venv/autopip/bin/autopip install \\"bumper\\" '
                            '2>&1 >> /tmp/.apps/log/cron.log" ) | crontab -')

    assert '.apps/bumper/0.1.11' in autopip('list')
    assert autopip('list --scripts').split('\n')[1].strip().endswith('/bin/bump')

    # Install bad-version
    stdout, _ = autopip('install bumper==100.*', raises=SystemExit)
    assert '! No app version matching bumper==100.*' in stdout
    assert 'Available versions: 0.1.8, 0.1.9, 0.1.10, 0.1.11' in stdout

    # Failed install
    with monkeypatch.context() as m:
        mock_run.side_effect = Exception('install failed')
        m.setattr('autopip.manager.run', mock_run)
        stdout, _ = autopip('install bumper-lib', raises=SystemExit)
        assert '! install failed' in stdout
        mock_run.side_effect = None

    # Already installed
    stdout = autopip('install bumper')
    assert stdout == 'bumper is already installed\n'

    # Install lib
    stdout, e = autopip('install bumper-lib', raises=SystemExit)
    assert 'Uninstalling bumper-lib' in stdout
    assert '! Odd, there are no scripts included in the app' in stdout

    # Uninstall
    mock_run.reset_mock()
    assert autopip('uninstall bumper') == 'Uninstalling bumper\n'
    assert mock_run.call_args_list == [
        call('which crontab', shell=True, stderr=-2),
        call('pgrep cron', shell=True, stderr=-2),
        call('( crontab -l | grep -vF "autopip install \\"bumper" ) | crontab -', shell=True)
    ]

    assert autopip('list') == 'No apps are installed yet\n'
