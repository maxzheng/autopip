import re

from mock import Mock, call


def test_autopip(monkeypatch, autopip):
    mock_run = Mock()
    monkeypatch.setattr('autopip.crontab.run', mock_run)
    monkeypatch.setattr('autopip.crontab.randint', Mock(return_value=10))

    # Install latest
    stdout = autopip('install bumper')
    assert 'Installing bumper to' in stdout
    assert 'Updating script symlinks in' in stdout
    assert '+ bump' in stdout
    assert len(stdout.split('\n')) == 5

    assert len(mock_run.call_args_list) == 3
    assert mock_run.call_args_list[0:2] == [
        call('which crontab', shell=True, stderr=-2),
        call('pgrep cron', shell=True, stderr=-2)]
    install_call = re.sub('/tmp/.*/system/', '/tmp/system/', re.sub('/home/.*virtualenvs/', '/home/venv/',
                          mock_run.call_args_list[-1][0][0]))
    assert install_call == (
        '( crontab -l | grep -vi "autopip install \\"bumper[^a-z]*\\""; '
        'echo "10 * * * * PATH=/usr/local/bin:\$PATH /home/venv/autopip/bin/autopip install \\"bumper\\" 2>&1 '
        '>> /tmp/system/log/cron.log" ) | crontab -')

    assert 'system/bumper/0.1.13' in autopip('list')
    assert autopip('list --scripts').split('\n')[1].strip().endswith('/bin/bump')

    # Already installed
    stdout = autopip('install bumper')
    assert re.sub('/tmp/.*/system', '/tmp/system', stdout) == """\
bumper is already installed
Hourly auto-update enabled via cron service
Scripts are in /tmp/system/bin: bump
"""
    assert mock_run.call_count == 6

    # Uninstall
    mock_run.reset_mock()
    assert autopip('uninstall bumper') == 'Uninstalling bumper\n'
    assert mock_run.call_args_list == [
        call('which crontab', shell=True, stderr=-2),
        call('pgrep cron', shell=True, stderr=-2),
        call('( crontab -l | grep -vi "autopip install \\"bumper[^a-z]*\\"" ) | crontab -', shell=True, stderr=-2)
    ]

    assert autopip('list') == 'No apps are installed yet.\n'


def test_install_lib(autopip):
    stdout, e = autopip('install utils-core', raises=SystemExit)
    assert 'Uninstalling utils-core' in stdout
    assert '! Odd, there are no scripts included in the app' in stdout


def test_install_bad_version(autopip):
    stdout, _ = autopip('install bumper==100.*', raises=SystemExit)
    assert '! No app version matching bumper==100.*' in stdout
    assert 'Available versions: 0.1.8, 0.1.9, 0.1.10, 0.1.11, 0.1.12' in stdout


def test_install_failed(autopip, monkeypatch, mock_run):
    mock_run.side_effect = Exception('install failed')
    monkeypatch.setattr('autopip.manager.run', mock_run)
    stdout, _ = autopip('install utils-core', raises=SystemExit)
    assert '! install failed' in stdout


def test_autopip_group(monkeypatch, autopip):
    mock_run = Mock()
    monkeypatch.setattr('autopip.crontab.run', mock_run)
    monkeypatch.setattr('autopip.crontab.randint', Mock(return_value=10))

    def mock_group_specs(self, path=None, name_only=False):
        if self.name == 'developer-tools':
            return ['bumper'] if name_only else [('bumper==0.1.10', None)]
        else:
            return []

    monkeypatch.setattr('autopip.manager.App.group_specs', mock_group_specs)

    # Install latest
    stdout = autopip('install developer-tools==0.0.3 --update weekly')
    assert 'Installing developer-tools to' in stdout
    assert 'Updating script symlinks in' in stdout
    assert 'This app has defined "autopip" entry points to install: bumper==0.1.10' in stdout
    assert '+ bump' in stdout
    assert len(stdout.split('\n')) == 7

    assert len(mock_run.call_args_list) == 3
    assert mock_run.call_args_list[0:2] == [
        call('which crontab', shell=True, stderr=-2),
        call('pgrep cron', shell=True, stderr=-2)]
    install_call = re.sub('/tmp/.*/system/', '/tmp/system/', re.sub('/home/.*virtualenvs/', '/home/venv/',
                          mock_run.call_args_list[-1][0][0]))
    assert install_call == (
        '( crontab -l | grep -vi "autopip install \\"developer-tools[^a-z]*\\""; echo "10 * * * * '
        'PATH=/usr/local/bin:\$PATH /home/venv/autopip/bin/autopip install \\"developer-tools==0.0.3\\" '
        '--update weekly 2>&1 >> /tmp/system/log/cron.log" ) | crontab -')

    assert 'system/bumper/0.1.10' in autopip('list')
    assert 'system/developer-tools/0.0.3' in autopip('list')
    assert autopip('list --scripts').split('\n')[1].strip().endswith('/bin/bump')

    # Already installed
    stdout = autopip('install developer-tools==0.0.3')
    assert re.sub('/tmp/.*/system', '/tmp/system', stdout) == """\
developer-tools is already installed
Hourly auto-update enabled via cron service
This app has defined "autopip" entry points to install: bumper==0.1.10
bumper is already installed
Scripts are in /tmp/system/bin: bump
"""
    assert mock_run.call_count == 6

    # Uninstall
    mock_run.reset_mock()
    assert autopip('uninstall developer-tools') == """\
Uninstalling developer-tools
This app has defined "autopip" entry points to uninstall: bumper
Uninstalling bumper
"""
    assert mock_run.call_args_list == [
        call('which crontab', shell=True, stderr=-2),
        call('pgrep cron', shell=True, stderr=-2),
        call('( crontab -l | grep -vi "autopip install \\"developer-tools[^a-z]*\\"" ) | crontab -',
             shell=True, stderr=-2),
        call('which crontab', shell=True, stderr=-2),
        call('pgrep cron', shell=True, stderr=-2),
        call('( crontab -l | grep -vi "autopip install \\"bumper[^a-z]*\\"" ) | crontab -',
             shell=True, stderr=-2)
    ]

    assert autopip('list') == 'No apps are installed yet.\n'
