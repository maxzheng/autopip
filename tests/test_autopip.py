from pathlib import Path
import re
from time import time

from mock import MagicMock, Mock, call


def test_autopip_common(monkeypatch, autopip, capsys, mock_paths):
    system_root, _, _ = mock_paths
    mock_run = MagicMock()
    monkeypatch.setattr('autopip.crontab.run', mock_run)
    monkeypatch.setattr('autopip.crontab.randint', Mock(return_value=10))

    # Install latest
    stdout = autopip('install bumper')
    assert 'Installing bumper to' in stdout
    assert 'Updating script symlinks in' in stdout
    assert '+ bump' in stdout
    assert len(stdout.split('\n')) == 5

    assert len(mock_run.call_args_list) == 6
    assert mock_run.call_args_list[0:-1] == [
        call('which crontab', shell=True, stderr=-2),
        call('ps -ef | grep /usr/sbin/cron | grep -v grep', shell=True, stderr=-2),
        call('crontab -l | grep autopip', shell=True, stderr=-2),
        call('which crontab', shell=True, stderr=-2),
        call('ps -ef | grep /usr/sbin/cron | grep -v grep', shell=True, stderr=-2)
        ]
    update_call = re.sub('/tmp/.*/system/', '/tmp/system/', re.sub('/home/.*virtualenvs/', '/home/venv/',
                         mock_run.call_args_list[-1][0][0]))
    assert update_call == (
        '( crontab -l | grep -vi "autopip update"; echo "10 * * * * PATH=/usr/local/bin:\$PATH '
        '/home/venv/autopip/bin/autopip update 2>&1 >> /tmp/system/log/cron.log" ) | crontab -')

    assert 'system/bumper/0.1.13' in autopip('list')
    assert autopip('list --scripts').split('\n')[1].strip().endswith('/bin/bump')

    # Already installed
    mock_run.reset_mock()
    stdout = autopip('install bumper')
    assert re.sub('/tmp/.*/system', '/tmp/system', stdout) == """\
bumper is up-to-date
Hourly auto-update enabled via cron service
Scripts are in /tmp/system/bin: bump
"""
    assert mock_run.call_count == 6

    # Update manually
    assert autopip('update') == 'bumper is up-to-date\n'
    assert autopip('update blah') == 'No apps found matching: blah\nAvailable apps: bumper\n'

    # Update via cron
    assert autopip('update', isatty=False) == ''
    bumper_root = system_root / 'bumper'
    last_modified = bumper_root.stat().st_mtime
    with monkeypatch.context() as m:
        m.setattr('autopip.manager.time', Mock(return_value=time() + 3600))
        assert autopip('update', isatty=False) == ''
        current_modified = bumper_root.stat().st_mtime
        assert current_modified > last_modified

    # Wait for new version
    mock_sleep = Mock(side_effect=[0, 0, 0, Exception('No new version')])
    monkeypatch.setattr('autopip.manager.sleep', mock_sleep)

    stdout, e = autopip('update bumper --wait', raises=SystemExit)
    assert stdout.startswith('! No new version')

    stdout, _ = capsys.readouterr()
    lines = stdout.split('\n')
    assert len(lines) == 5
    assert lines[0] == 'Waiting for new version of bumper to be published...'.ljust(80)
    assert lines[-2] == '\033[1AWaiting for new version of bumper to be published...'.ljust(80)

    assert mock_sleep.call_count == 4

    # Uninstall
    mock_run.reset_mock()
    assert autopip('uninstall bumper') == 'Uninstalling bumper\n'
    assert mock_run.call_args_list == [
        call('which crontab', shell=True, stderr=-2),
        call('ps -ef | grep /usr/sbin/cron | grep -v grep', shell=True, stderr=-2),
        call('( crontab -l | grep -vi "autopip install \\"bumper[^a-z]*\\"" ) | crontab -', shell=True, stderr=-2),
        call('which crontab', shell=True, stderr=-2),
        call('ps -ef | grep /usr/sbin/cron | grep -v grep', shell=True, stderr=-2),
        call('( crontab -l | grep -vi "autopip" ) | crontab -', shell=True, stderr=-2)
    ]

    assert autopip('list') == 'No apps are installed yet.\n'


def test_update(autopip):
    assert autopip('update') == 'No apps installed yet.\n'


def test_install_lib(autopip):
    stdout, e = autopip('install utils-core', raises=SystemExit)
    assert 'Uninstalling utils-core' in stdout
    assert '! Odd, there are no scripts included in the app' in stdout


def test_install_bad_version(autopip, monkeypatch):
    pip_conf_parser = Mock(read=Mock(side_effect=Exception('Force use of PyPI index')))
    monkeypatch.setattr('autopip.manager.RawConfigParser', pip_conf_parser)

    stdout, _ = autopip('install bumper==100.*', raises=SystemExit)
    assert '! No app version matching bumper==100.*' in stdout
    assert 'Available versions: 0.1.8, 0.1.9, 0.1.10, 0.1.11, 0.1.12' in stdout

    pip_conf_parser().read.assert_called_with(Path('/home/mzheng/.pip/pip.conf'))


def test_install_nonexisting(autopip):
    stdout, _ = autopip('install this-does-not-exist-blah-blah', raises=SystemExit)
    assert stdout.startswith('! No app version found in http')


def test_install_failed(autopip, monkeypatch, mock_run):
    mock_run.side_effect = Exception('install failed')
    monkeypatch.setattr('autopip.manager.run', mock_run)
    stdout, _ = autopip('install utils-core', raises=SystemExit)
    assert '! install failed' in stdout


def test_install_autopip(autopip):
    stdout = autopip('install autopip==1.4.2')
    print(stdout)
    assert re.sub('/tmp/.*/system/', '/tmp/system/', stdout) == """\
Installing autopip to /tmp/system/autopip/1.4.2
Auto-update will be disabled since we are pinning to a specific version.
To enable, re-run without pinning to specific version with --update option
Updating script symlinks in /tmp/system/bin
+ app
+ autopip
"""
    stdout = autopip('list auto --scripts')
    assert re.sub(' +autopip', ' ' * 32 + 'autopip', re.sub('/tmp/.*/system/', '/tmp/system/', stdout)) == """\
autopip  1.4.2  /tmp/system/autopip/1.4.2  
                /tmp/system/bin/app        
                                autopip    
"""  # noqa

    assert autopip('uninstall autopip') == 'Uninstalling autopip\n'


def test_autopip_group(monkeypatch, autopip):
    mock_run = MagicMock()
    monkeypatch.setattr('autopip.crontab.run', mock_run)
    monkeypatch.setattr('autopip.crontab.randint', Mock(return_value=10))

    def mock_group_specs(self, path=None, name_only=False):
        if self.name == 'developer-tools':
            return ['bumper'] if name_only else [('bumper==0.1.10', None)]
        else:
            return []

    monkeypatch.setattr('autopip.manager.App.group_specs', mock_group_specs)

    # Install latest
    stdout = autopip('install developer-tools --update weekly')
    installed_version = stdout.split('\n')[0].split('/')[-1]
    assert 'Installing developer-tools to' in stdout
    assert 'Updating script symlinks in' in stdout
    assert 'This app has defined "autopip" entry points to install: bumper==0.1.10' in stdout
    assert '+ bump' in stdout
    assert len(stdout.split('\n')) == 7

    assert len(mock_run.call_args_list) == 6
    assert mock_run.call_args_list[0:-1] == [
        call('which crontab', shell=True, stderr=-2),
        call('ps -ef | grep /usr/sbin/cron | grep -v grep', shell=True, stderr=-2),
        call('crontab -l | grep autopip', shell=True, stderr=-2),
        call('which crontab', shell=True, stderr=-2),
        call('ps -ef | grep /usr/sbin/cron | grep -v grep', shell=True, stderr=-2)
        ]
    update_call = re.sub('/tmp/.*/system/', '/tmp/system/', re.sub('/home/.*virtualenvs/', '/home/venv/',
                         mock_run.call_args_list[-1][0][0]))
    assert update_call == (
        '( crontab -l | grep -vi "autopip update"; echo "10 * * * * PATH=/usr/local/bin:\$PATH '
        '/home/venv/autopip/bin/autopip update 2>&1 >> /tmp/system/log/cron.log" ) | crontab -')

    assert 'system/bumper/0.1.10' in autopip('list')
    assert f'system/developer-tools/{installed_version}' in autopip('list')
    assert autopip('list --scripts').split('\n')[1].strip().endswith('/bin/bump')
    assert autopip('list blah') == 'No apps matching "blah"\n'

    # Uninstall autopip
    assert autopip('uninstall autopip') == ('! autopip can not be uninstalled until other apps are uninstalled: '
                                            'bumper developer-tools\n')

    # Update
    assert autopip('update') == """\
bumper is up-to-date [per spec: ==0.1.10]
developer-tools is up-to-date
This app has defined "autopip" entry points to install: bumper==0.1.10
"""

    # Already installed
    mock_run.reset_mock()
    stdout = autopip(f'install developer-tools=={installed_version}')
    assert re.sub('/tmp/.*/system', '/tmp/system', stdout) == """\
developer-tools is up-to-date [per spec: ==1.0.7]
Auto-update will be disabled since we are pinning to a specific version.
To enable, re-run without pinning to specific version with --update option
This app has defined "autopip" entry points to install: bumper==0.1.10
bumper is up-to-date [per spec: ==0.1.10]
Scripts are in /tmp/system/bin: bump
"""
    assert mock_run.call_args_list == [
        call('which crontab', shell=True, stderr=-2),
        call('ps -ef | grep /usr/sbin/cron | grep -v grep', shell=True, stderr=-2),
        call('( crontab -l | grep -vi "autopip install \\"developer-tools[^a-z]*\\"" ) | crontab -',
             shell=True, stderr=-2)
    ]

    # Uninstall
    mock_run.reset_mock()
    assert autopip('uninstall developer-tools') == """\
Uninstalling developer-tools
This app has defined "autopip" entry points to uninstall: bumper
Uninstalling bumper
"""
    assert mock_run.call_args_list == [
        call('which crontab', shell=True, stderr=-2),
        call('ps -ef | grep /usr/sbin/cron | grep -v grep', shell=True, stderr=-2),
        call('( crontab -l | grep -vi "autopip install \\"developer-tools[^a-z]*\\"" ) | crontab -',
             shell=True, stderr=-2),
        call('which crontab', shell=True, stderr=-2),
        call('ps -ef | grep /usr/sbin/cron | grep -v grep', shell=True, stderr=-2),
        call('( crontab -l | grep -vi "autopip install \\"bumper[^a-z]*\\"" ) | crontab -',
             shell=True, stderr=-2),
        call('which crontab', shell=True, stderr=-2),
        call('ps -ef | grep /usr/sbin/cron | grep -v grep', shell=True, stderr=-2),
        call('( crontab -l | grep -vi "autopip" ) | crontab -', shell=True, stderr=-2)
    ]

    assert autopip('list') == 'No apps are installed yet.\n'
